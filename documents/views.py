import os
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse, Http404
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
import json
from datetime import datetime, timedelta

from .models import ProofOfResidence, DocumentTemplate, BatchProcess, BatchItem, DocumentLog
from .forms import ProofOfResidenceForm, DocumentTemplateForm, BatchProcessForm
from governance.models import Village
from households.models import Resident, Household

class DocumentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'documents/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistics
        context['total_documents'] = ProofOfResidence.objects.count()
        context['pending_documents'] = ProofOfResidence.objects.filter(status='pending').count()
        context['approved_documents'] = ProofOfResidence.objects.filter(status='approved').count()
        context['generated_documents'] = ProofOfResidence.objects.filter(status='generated').count()
        context['delivered_documents'] = ProofOfResidence.objects.filter(status='delivered').count()
        
        # Recent documents
        context['recent_documents'] = ProofOfResidence.objects.select_related(
            'resident', 'village', 'household'
        ).order_by('-requested_at')[:10]
        
        # Documents by status
        context['status_stats'] = ProofOfResidence.objects.values('status').annotate(
            count=Count('id')
        )
        
        # Documents by village
        context['village_stats'] = ProofOfResidence.objects.values(
            'village__name'
        ).annotate(count=Count('id')).order_by('-count')[:5]
        
        # Active templates
        context['active_templates'] = DocumentTemplate.objects.filter(is_active=True).count()
        
        return context

class ProofOfResidenceListView(LoginRequiredMixin, ListView):
    model = ProofOfResidence
    template_name = 'documents/proof_list.html'
    context_object_name = 'documents'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ProofOfResidence.objects.select_related(
            'resident', 'village', 'household', 'requested_by', 'approved_by'
        ).order_by('-requested_at')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by village
        village_id = self.request.GET.get('village')
        if village_id:
            queryset = queryset.filter(village_id=village_id)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(document_number__icontains=search) |
                Q(resident__first_name__icontains=search) |
                Q(resident__last_name__icontains=search) |
                Q(purpose__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['villages'] = Village.objects.all()
        context['status_choices'] = ProofOfResidence.STATUS_CHOICES
        context['current_filters'] = {
            'status': self.request.GET.get('status', ''),
            'village': self.request.GET.get('village', ''),
            'search': self.request.GET.get('search', ''),
        }
        return context

class ProofOfResidenceDetailView(LoginRequiredMixin, DetailView):
    model = ProofOfResidence
    template_name = 'documents/proof_detail.html'
    context_object_name = 'document'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['logs'] = self.object.logs.select_related('action_by').order_by('-action_at')
        return context

class ProofOfResidenceCreateView(LoginRequiredMixin, CreateView):
    model = ProofOfResidence
    form_class = ProofOfResidenceForm
    template_name = 'documents/proof_form.html'
    success_url = reverse_lazy('documents:proof_list')
    
    def form_valid(self, form):
        form.instance.requested_by = self.request.user
        response = super().form_valid(form)
        
        # Log the creation
        DocumentLog.objects.create(
            document=self.object,
            action='Created',
            action_by=self.request.user,
            notes=f'Document requested for purpose: {self.object.purpose}'
        )
        
        messages.success(self.request, f'Proof of residence request created successfully. Document number: {self.object.document_number}')
        return response

class ProofOfResidenceUpdateView(LoginRequiredMixin, UpdateView):
    model = ProofOfResidence
    form_class = ProofOfResidenceForm
    template_name = 'documents/proof_form.html'
    
    def get_success_url(self):
        return reverse_lazy('documents:proof_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Log the update
        DocumentLog.objects.create(
            document=self.object,
            action='Updated',
            action_by=self.request.user,
            notes='Document details updated'
        )
        
        messages.success(self.request, 'Document updated successfully.')
        return response

@login_required
def approve_proof_of_residence(request, pk):
    document = get_object_or_404(ProofOfResidence, pk=pk)
    
    if not document.can_be_approved:
        messages.error(request, 'This document cannot be approved at this time.')
        return redirect('documents:proof_detail', pk=pk)
    
    if request.method == 'POST':
        document.status = 'approved'
        document.approved_by = request.user
        document.approved_at = timezone.now()
        document.save()
        
        # Log the approval
        DocumentLog.objects.create(
            document=document,
            action='Approved',
            action_by=request.user,
            notes=request.POST.get('notes', '')
        )
        
        messages.success(request, 'Document approved successfully.')
        return redirect('documents:proof_detail', pk=pk)
    
    return render(request, 'documents/proof_approve.html', {'document': document})

@login_required
def generate_proof_of_residence(request, pk):
    document = get_object_or_404(ProofOfResidence, pk=pk)
    
    if not document.can_be_generated:
        messages.error(request, 'This document cannot be generated at this time.')
        return redirect('documents:proof_detail', pk=pk)
    
    try:
        # Generate the document (you'll need to implement the actual PDF generation)
        from .utils import generate_proof_document
        file_path = generate_proof_document(document)
        
        document.status = 'generated'
        document.generated_at = timezone.now()
        document.document_file = file_path
        document.save()
        
        # Log the generation
        DocumentLog.objects.create(
            document=document,
            action='Generated',
            action_by=request.user,
            notes='Document generated successfully'
        )
        
        messages.success(request, 'Document generated successfully.')
    except Exception as e:
        messages.error(request, f'Error generating document: {str(e)}')
    
    return redirect('documents:proof_detail', pk=pk)

@login_required
def deliver_proof_of_residence(request, pk):
    document = get_object_or_404(ProofOfResidence, pk=pk)
    
    if not document.can_be_delivered:
        messages.error(request, 'This document cannot be delivered at this time.')
        return redirect('documents:proof_detail', pk=pk)
    
    if request.method == 'POST':
        document.status = 'delivered'
        document.delivered_at = timezone.now()
        document.save()
        
        # Log the delivery
        DocumentLog.objects.create(
            document=document,
            action='Delivered',
            action_by=request.user,
            notes=request.POST.get('notes', '')
        )
        
        messages.success(request, 'Document marked as delivered.')
        return redirect('documents:proof_detail', pk=pk)
    
    return render(request, 'documents/proof_deliver.html', {'document': document})

@login_required
def download_proof_of_residence(request, pk):
    document = get_object_or_404(ProofOfResidence, pk=pk)
    
    if not document.document_file:
        raise Http404("Document file not found")
    
    # Log the download
    DocumentLog.objects.create(
        document=document,
        action='Downloaded',
        action_by=request.user,
        notes='Document downloaded'
    )
    
    response = HttpResponse(document.document_file.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{document.document_number}.pdf"'
    return response

# Document Template Views
class DocumentTemplateListView(LoginRequiredMixin, ListView):
    model = DocumentTemplate
    template_name = 'documents/template_list.html'
    context_object_name = 'templates'
    paginate_by = 20

class DocumentTemplateCreateView(LoginRequiredMixin, CreateView):
    model = DocumentTemplate
    form_class = DocumentTemplateForm
    template_name = 'documents/template_form.html'
    success_url = reverse_lazy('documents:template_list')

class DocumentTemplateDetailView(LoginRequiredMixin, DetailView):
    model = DocumentTemplate
    template_name = 'documents/template_detail.html'
    context_object_name = 'template'

class DocumentTemplateUpdateView(LoginRequiredMixin, UpdateView):
    model = DocumentTemplate
    form_class = DocumentTemplateForm
    template_name = 'documents/template_form.html'
    success_url = reverse_lazy('documents:template_list')

# Batch Processing Views
class BatchProcessListView(LoginRequiredMixin, ListView):
    model = BatchProcess
    template_name = 'documents/batch_list.html'
    context_object_name = 'batches'
    paginate_by = 20

class BatchProcessCreateView(LoginRequiredMixin, CreateView):
    model = BatchProcess
    form_class = BatchProcessForm
    template_name = 'documents/batch_form.html'
    success_url = reverse_lazy('documents:batch_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class BatchProcessDetailView(LoginRequiredMixin, DetailView):
    model = BatchProcess
    template_name = 'documents/batch_detail.html'
    context_object_name = 'batch'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.select_related('document__resident').order_by('status', 'document__requested_at')
        return context

@login_required
def process_batch(request, pk):
    batch = get_object_or_404(BatchProcess, pk=pk)
    
    if batch.status != 'pending':
        messages.error(request, 'This batch has already been processed.')
        return redirect('documents:batch_detail', pk=pk)
    
    # Process the batch (implement your batch processing logic here)
    batch.status = 'in_progress'
    batch.save()
    
    messages.success(request, 'Batch processing started.')
    return redirect('documents:batch_detail', pk=pk)

from django.http import FileResponse
from .utils import generate_batch_report, generate_monthly_report

@login_required
def download_batch_report(request, pk):
    """Download batch processing report"""
    batch = get_object_or_404(BatchProcess, pk=pk)
    
    try:
        report_path = generate_batch_report(batch)
        full_path = os.path.join(settings.MEDIA_ROOT, report_path)
        
        response = FileResponse(
            open(full_path, 'rb'),
            content_type='application/pdf',
            filename=f'batch_report_{batch.id}.pdf'
        )
        return response
    except Exception as e:
        messages.error(request, f'Error generating report: {str(e)}')
        return redirect('documents:batch_detail', pk=pk)

@login_required
def monthly_report(request):
    """Generate and download monthly report"""
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    
    try:
        report_path = generate_monthly_report(year, month)
        full_path = os.path.join(settings.MEDIA_ROOT, report_path)
        
        response = FileResponse(
            open(full_path, 'rb'),
            content_type='application/pdf',
            filename=f'monthly_report_{year}_{month:02d}.pdf'
        )
        return response
    except Exception as e:
        messages.error(request, f'Error generating report: {str(e)}')
        return redirect('documents:dashboard')

# AJAX API Views
@login_required
def get_residents_by_village(request, village_id):
    residents = Resident.objects.filter(household__village_id=village_id).select_related('household')
    data = [{
        'id': resident.id,
        'name': resident.full_name,
        'household': resident.household.head_of_household if resident.household else ''
    } for resident in residents]
    return JsonResponse(data, safe=False)

@login_required
def get_households_by_village(request, village_id):
    households = Household.objects.filter(village_id=village_id)
    data = [{
        'id': household.id,
        'name': f"{household.head_of_household} - {household.address}"
    } for household in households]
    return JsonResponse(data, safe=False)

# Add these missing views to your existing views.py

@login_required
def download_batch_report(request, pk):
    """Download batch processing report"""
    batch = get_object_or_404(BatchProcess, pk=pk)
    
    try:
        from .utils import generate_batch_report
        report_path = generate_batch_report(batch)
        full_path = os.path.join(settings.MEDIA_ROOT, report_path)
        
        if os.path.exists(full_path):
            response = FileResponse(
                open(full_path, 'rb'),
                content_type='application/pdf',
                filename=f'batch_report_{batch.id}.pdf'
            )
            return response
        else:
            messages.error(request, 'Report file not found.')
            return redirect('documents:batch_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Error generating report: {str(e)}')
        return redirect('documents:batch_detail', pk=pk)

@login_required
def monthly_report(request):
    """Generate and download monthly report"""
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    
    try:
        from .utils import generate_monthly_report
        report_path = generate_monthly_report(year, month)
        full_path = os.path.join(settings.MEDIA_ROOT, report_path)
        
        if os.path.exists(full_path):
            response = FileResponse(
                open(full_path, 'rb'),
                content_type='application/pdf',
                filename=f'monthly_report_{year}_{month:02d}.pdf'
            )
            return response
        else:
            messages.error(request, 'Report could not be generated.')
            return redirect('documents:dashboard')
    except Exception as e:
        messages.error(request, f'Error generating report: {str(e)}')
        return redirect('documents:dashboard')

@login_required
def generate_report(request):
    """Report generation page"""
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        
        if report_type == 'monthly':
            year = int(request.POST.get('year', timezone.now().year))
            month = int(request.POST.get('month', timezone.now().month))
            return redirect('documents:monthly_report') + f'?year={year}&month={month}'
        
        elif report_type == 'status':
            # Generate status report
            pass
        
        elif report_type == 'village':
            # Generate village report
            pass
    
    context = {
        'current_year': timezone.now().year,
        'current_month': timezone.now().month,
        'months': [
            (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
            (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
            (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
        ],
        'years': range(2020, timezone.now().year + 2),
    }
    
    return render(request, 'documents/generate_report.html', context)

# API Views for AJAX calls
@login_required
def get_residents_by_village(request, village_id):
    """Get residents for a specific village"""
    try:
        from households.models import Resident
        residents = Resident.objects.filter(
            household__village_id=village_id
        ).select_related('household')
        
        data = []
        for resident in residents:
            data.append({
                'id': resident.id,
                'name': resident.full_name,
                'household_id': resident.household.id if resident.household else None,
                'household': str(resident.household) if resident.household else ''
            })
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_households_by_village(request, village_id):
    """Get households for a specific village"""
    try:
        from households.models import Household
        households = Household.objects.filter(village_id=village_id)
        
        data = []
        for household in households:
            data.append({
                'id': household.id,
                'name': f"{household.head_of_household} - {household.address}"
            })
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)