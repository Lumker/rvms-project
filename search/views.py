from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse

from households.models import Resident, Household
from governance.models import Village, Municipality, District, Province
from documents.models import ProofOfResidence

@login_required
def global_search(request):
    """Global search across all modules"""
    query = request.GET.get('q', '').strip()
    results = {}
    
    if query and len(query) >= 2:  # Minimum 2 characters
        # Search Residents
        residents = Resident.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(id_number__icontains=query) |
            Q(phone_number__icontains=query)
        ).select_related('household', 'household__village')[:10]
        
        # Search Households
        households = Household.objects.filter(
            Q(head_of_household__icontains=query) |
            Q(address__icontains=query)
        ).select_related('village')[:10]
        
        # Search Villages
        villages = Village.objects.filter(
            Q(name__icontains=query) |
            Q(traditional_name__icontains=query)
        ).select_related('municipality')[:10]
        
        # Search Documents
        documents = ProofOfResidence.objects.filter(
            Q(document_number__icontains=query) |
            Q(purpose__icontains=query) |
            Q(resident__first_name__icontains=query) |
            Q(resident__last_name__icontains=query)
        ).select_related('resident', 'village')[:10]
        
        # Search Municipalities
        municipalities = Municipality.objects.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query)
        ).select_related('district')[:5]
        
        results = {
            'residents': residents,
            'households': households,
            'villages': villages,
            'documents': documents,
            'municipalities': municipalities,
        }
    
    context = {
        'query': query,
        'results': results,
        'total_results': sum(len(result) for result in results.values()) if results else 0
    }
    
    return render(request, 'search/results.html', context)

@login_required
def search_autocomplete(request):
    """AJAX autocomplete for search"""
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if query and len(query) >= 2:
        # Get top suggestions from each category
        residents = Resident.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )[:3]
        
        villages = Village.objects.filter(
            name__icontains=query
        )[:3]
        
        documents = ProofOfResidence.objects.filter(
            document_number__icontains=query
        )[:3]
        
        # Format suggestions
        for resident in residents:
            suggestions.append({
                'text': f"{resident.full_name} - {resident.household.village.name if resident.household else 'Unknown'}",
                'type': 'resident',
                'url': f'/households/residents/{resident.id}/'
            })
        
        for village in villages:
            suggestions.append({
                'text': f"{village.name} - {village.municipality.name}",
                'type': 'village',
                'url': f'/governance/villages/{village.id}/'
            })
        
        for document in documents:
            suggestions.append({
                'text': f"Document {document.document_number} - {document.resident.full_name}",
                'type': 'document',
                'url': f'/documents/proof-of-residence/{document.id}/'
            })
    
    return JsonResponse(suggestions, safe=False)