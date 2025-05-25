from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from .models import (
    Province, District, Municipality, TraditionalCouncil, Village, 
    CouncilMember, CouncilMeeting, Resolution, WardCommittee, WardCommitteeMember, CommunityIssue
)
from .forms import (
    ProvinceForm, DistrictForm, MunicipalityForm, TraditionalCouncilForm, 
    VillageForm, CouncilMemberForm, CouncilMeetingForm, ResolutionForm,
    WardCommitteeForm, WardCommitteeMemberForm
)

from .models import Province, District, Municipality, TraditionalCouncil, Village
from .forms import ProvinceForm, DistrictForm, MunicipalityForm, TraditionalCouncilForm, VillageForm

# Update governance dashboard to include ward committee statistics

@login_required
def governance_dashboard(request):
    """Enhanced governance dashboard with ward committee data"""
    
    # Basic counts
    total_provinces = Province.objects.count()
    total_districts = District.objects.count()
    total_municipalities = Municipality.objects.filter(is_active=True).count()
    total_ward_committees = WardCommittee.objects.filter(is_active=True).count()
    total_councils = TraditionalCouncil.objects.filter(is_active=True).count()
    total_villages = Village.objects.filter(is_active=True).count()
    
    # Recent activities
    recent_ward_committees = WardCommittee.objects.filter(is_active=True).order_by('-created_at')[:5]
    recent_councils = TraditionalCouncil.objects.filter(is_active=True).order_by('-created_at')[:5]
    
    # Municipality statistics
    municipality_stats = Municipality.objects.filter(is_active=True).annotate(
        ward_count=Count('ward_committees', filter=Q(ward_committees__is_active=True)),
        council_count=Count('traditional_councils', filter=Q(traditional_councils__is_active=True))
    ).order_by('-ward_count', '-council_count')[:10]
    
    context = {
        'total_provinces': total_provinces,
        'total_districts': total_districts,
        'total_municipalities': total_municipalities,
        'total_ward_committees': total_ward_committees,
        'total_councils': total_councils,
        'total_villages': total_villages,
        'recent_ward_committees': recent_ward_committees,
        'recent_councils': recent_councils,
        'municipality_stats': municipality_stats,
    }
    
    return render(request, 'governance/dashboard.html', context)

# Province Views
@login_required
def province_list(request):
    provinces = Province.objects.annotate(district_count=Count('districts')).order_by('name')
    return render(request, 'governance/provinces/province_list.html', {'provinces': provinces})

@login_required
def province_create(request):
    if request.method == 'POST':
        form = ProvinceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Province created successfully.')
            return redirect('governance:province_list')
    else:
        form = ProvinceForm()
    return render(request, 'governance/provinces/province_form.html', {'form': form, 'action': 'Create'})

@login_required
def province_update(request, pk):
    province = get_object_or_404(Province, pk=pk)
    if request.method == 'POST':
        form = ProvinceForm(request.POST, instance=province)
        if form.is_valid():
            form.save()
            messages.success(request, 'Province updated successfully.')
            return redirect('governance:province_list')
    else:
        form = ProvinceForm(instance=province)
    return render(request, 'governance/provinces/province_form.html', {'form': form, 'action': 'Update'})


@login_required
def province_detail(request, pk):
    province = get_object_or_404(Province, pk=pk)
    districts = province.districts.annotate(
        municipality_count=Count('municipalities')
    ).order_by('name')
    
    context = {
        'province': province,
        'districts': districts,
    }
    return render(request, 'governance/provinces/province_detail.html', context)

# Add these district views
@login_required
def district_list(request):
    districts = District.objects.select_related('province').annotate(
        municipality_count=Count('municipalities')
    ).order_by('name')
    
    # Filter by province
    province_filter = request.GET.get('province')
    if province_filter:
        districts = districts.filter(province_id=province_filter)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        districts = districts.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(province__name__icontains=search_query)
        )
    
    paginator = Paginator(districts, 15)
    page_number = request.GET.get('page')
    districts = paginator.get_page(page_number)
    
    provinces = Province.objects.all().order_by('name')
    
    context = {
        'districts': districts,
        'provinces': provinces,
        'selected_province': province_filter,
        'search_query': search_query,
    }
    return render(request, 'governance/districts/district_list.html', context)

@login_required
def district_create(request):
    if request.method == 'POST':
        form = DistrictForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'District created successfully.')
            return redirect('governance:district_list')
    else:
        form = DistrictForm()
    
    context = {
        'form': form, 
        'action': 'Create',
        'provinces': Province.objects.all().order_by('name')
    }
    return render(request, 'governance/districts/district_form.html', context)

@login_required
def district_update(request, pk):
    district = get_object_or_404(District, pk=pk)
    if request.method == 'POST':
        form = DistrictForm(request.POST, instance=district)
        if form.is_valid():
            form.save()
            messages.success(request, 'District updated successfully.')
            return redirect('governance:district_list')
    else:
        form = DistrictForm(instance=district)
    
    context = {
        'form': form, 
        'action': 'Update',
        'district': district,
        'provinces': Province.objects.all().order_by('name')
    }
    return render(request, 'governance/districts/district_form.html', context)

@login_required
def district_detail(request, pk):
    district = get_object_or_404(
        District.objects.select_related('province').annotate(
            municipality_count=Count('municipalities')
        ), 
        pk=pk
    )
    municipalities = district.municipalities.all()
    
    context = {
        'district': district,
        'municipalities': municipalities,
    }
    return render(request, 'governance/districts/district_detail.html', context)

@login_required
def district_delete(request, pk):
    district = get_object_or_404(District, pk=pk)
    
    if request.method == 'POST':
        district_name = district.name
        district.delete()
        messages.success(request, f'District "{district_name}" has been deleted successfully.')
        return redirect('governance:district_list')
    
    return redirect('governance:district_detail', pk=pk)


# Update existing municipality_list view to include ward committee counts
@login_required
def municipality_list(request):
    """List all municipalities with enhanced statistics"""
    municipalities = Municipality.objects.select_related('district').annotate(
        council_count=Count('traditional_councils', filter=Q(traditional_councils__is_active=True)),
        ward_committee_count=Count('ward_committees', filter=Q(ward_committees__is_active=True))
    )
    
    # Apply existing filters...
    search_query = request.GET.get('search', '')
    district_filter = request.GET.get('district', '')
    type_filter = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')
    
    if search_query:
        municipalities = municipalities.filter(
            Q(name__icontains=search_query) | Q(code__icontains=search_query)
        )
    
    if district_filter:
        municipalities = municipalities.filter(district_id=district_filter)
    
    if type_filter:
        municipalities = municipalities.filter(municipality_type=type_filter)
    
    if status_filter:
        if status_filter == 'active':
            municipalities = municipalities.filter(is_active=True)
        elif status_filter == 'inactive':
            municipalities = municipalities.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(municipalities, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    districts = District.objects.filter(is_active=True).order_by('name')
    municipality_types = Municipality.MUNICIPALITY_TYPES
    
    context = {
        'page_obj': page_obj,
        'districts': districts,
        'municipality_types': municipality_types,
        'search_query': search_query,
        'current_filters': {
            'district': district_filter,
            'type': type_filter,
            'status': status_filter,
        },
    }
    
    return render(request, 'governance/municipality_list.html', context)

# Update existing municipality_detail view to include ward committees
@login_required
def municipality_detail(request, pk):
    """Display detailed information about a municipality"""
    municipality = get_object_or_404(
        Municipality.objects.select_related('district', 'district__province')
        .prefetch_related('ward_committees', 'traditional_councils'),
        pk=pk
    )
    
    # Get ward committees
    ward_committees = municipality.ward_committees.filter(is_active=True).annotate(
        council_count=Count('traditional_councils', filter=Q(traditional_councils__is_active=True)),
        member_count=Count('committee_members', filter=Q(committee_members__is_active=True))
    )
    
    # Get traditional councils
    traditional_councils = municipality.traditional_councils.filter(is_active=True).select_related('ward_committee')
    
    # Calculate statistics
    total_villages = sum(council.total_villages for council in traditional_councils)
    
    context = {
        'municipality': municipality,
        'ward_committees': ward_committees,
        'traditional_councils': traditional_councils,
        'total_villages': total_villages,
    }
    
    return render(request, 'governance/municipality_detail.html', context)

@login_required
def municipality_create(request):
    """Create new municipality"""
    if request.method == 'POST':
        form = MunicipalityForm(request.POST)
        if form.is_valid():
            municipality = form.save()
            messages.success(request, f'Municipality "{municipality.name}" created successfully.')
            return redirect('governance:municipality_detail', pk=municipality.pk)
    else:
        form = MunicipalityForm()
        # Pre-select district if passed as parameter
        district_id = request.GET.get('district')
        if district_id:
            form.fields['district'].initial = district_id
    
    context = {'form': form, 'title': 'Create Municipality'}
    return render(request, 'governance/municipalities/municipality_form.html', context)

@login_required
def municipality_update(request, pk):
    """Update municipality"""
    municipality = get_object_or_404(Municipality, pk=pk)
    
    if request.method == 'POST':
        form = MunicipalityForm(request.POST, instance=municipality)
        if form.is_valid():
            form.save()
            messages.success(request, f'Municipality "{municipality.name}" updated successfully.')
            return redirect('governance:municipality_detail', pk=municipality.pk)
    else:
        form = MunicipalityForm(instance=municipality)
    
    context = {'form': form, 'municipality': municipality, 'title': 'Update Municipality'}
    return render(request, 'governance/municipalities/municipality_form.html', context)

@login_required
def municipality_delete(request, pk):
    """Delete municipality"""
    municipality = get_object_or_404(Municipality, pk=pk)
    
    if request.method == 'POST':
        municipality_name = municipality.name
        municipality.delete()
        messages.success(request, f'Municipality "{municipality_name}" deleted successfully.')
        return redirect('governance:municipality_list')
    
    context = {'municipality': municipality}
    return render(request, 'governance/municipalities/municipality_confirm_delete.html', context)


# Update your get_municipalities function name and add new AJAX views
@login_required
def get_municipalities_by_district(request):
    """Get municipalities for a specific district (AJAX)"""
    district_id = request.GET.get('district_id')
    municipalities = Municipality.objects.filter(
        district_id=district_id, is_active=True
    ).values('id', 'name').order_by('name')
    
    return JsonResponse({'municipalities': list(municipalities)})

@login_required
def get_councils_by_municipality(request):
    """Get traditional councils for a specific municipality (AJAX)"""
    municipality_id = request.GET.get('municipality_id')
    councils = TraditionalCouncil.objects.filter(
        municipality_id=municipality_id, is_active=True
    ).values('id', 'name').order_by('name')
    
    return JsonResponse({'councils': list(councils)})


# Traditional Council Views
@login_required
def council_list(request):
    councils = TraditionalCouncil.objects.select_related('municipality__district__province').annotate(
        village_count=Count('villages'),
        member_count=Count('council_members')
    ).order_by('name')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        councils = councils.filter(
            Q(name__icontains=search_query) |
            Q(leader_name__icontains=search_query) |
            Q(municipality__name__icontains=search_query)
        )
    
    paginator = Paginator(councils, 10)
    page_number = request.GET.get('page')
    councils = paginator.get_page(page_number)
    
    return render(request, 'governance/councils/council_list.html', {'councils': councils})

@login_required
def council_detail(request, pk):
    council = get_object_or_404(
        TraditionalCouncil.objects.select_related('municipality__district__province'),
        pk=pk
    )
    villages = council.villages.all()
    members = council.council_members.select_related('user').filter(is_active=True)
    recent_meetings = council.meetings.order_by('-date')[:5]
    
    context = {
        'council': council,
        'villages': villages,
        'members': members,
        'recent_meetings': recent_meetings,
    }
    return render(request, 'governance/councils/council_detail.html', context)

# Update traditional council form to populate ward committees based on municipality
@login_required
def council_create(request):
    """Create a new traditional council with ward committee support"""
    if request.method == 'POST':
        form = TraditionalCouncilForm(request.POST)
        if form.is_valid():
            council = form.save()
            messages.success(request, f'Traditional Council "{council.name}" created successfully!')
            return redirect('governance:council_detail', pk=council.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TraditionalCouncilForm()
        # Pre-populate municipality and ward committee if passed in URL
        municipality_id = request.GET.get('municipality')
        ward_committee_id = request.GET.get('ward_committee')
        if municipality_id:
            form.fields['municipality'].initial = municipality_id
        if ward_committee_id:
            form.fields['ward_committee'].initial = ward_committee_id
    
    municipalities = Municipality.objects.filter(is_active=True).order_by('name')
    ward_committees = WardCommittee.objects.filter(is_active=True).order_by('ward_number', 'name')
    
    context = {
        'form': form,
        'municipalities': municipalities,
        'ward_committees': ward_committees,
        'title': 'Create Traditional Council'
    }
    
    return render(request, 'governance/council_form.html', context)

# Update your existing council views to add missing CRUD operations
@login_required
def council_update(request, pk):
    """Update traditional council"""
    council = get_object_or_404(TraditionalCouncil, pk=pk)
    
    if request.method == 'POST':
        form = TraditionalCouncilForm(request.POST, instance=council)
        if form.is_valid():
            form.save()
            messages.success(request, f'Traditional Council "{council.name}" updated successfully.')
            return redirect('governance:council_detail', pk=council.pk)
    else:
        form = TraditionalCouncilForm(instance=council)
    
    context = {'form': form, 'council': council, 'title': 'Update Traditional Council'}
    return render(request, 'governance/councils/council_form.html', context)

@login_required
def council_delete(request, pk):
    """Delete traditional council"""
    council = get_object_or_404(TraditionalCouncil, pk=pk)
    
    if request.method == 'POST':
        council_name = council.name
        council.delete()
        messages.success(request, f'Traditional Council "{council_name}" deleted successfully.')
        return redirect('governance:council_list')
    
    context = {'council': council}
    return render(request, 'governance/councils/council_confirm_delete.html', context)


# Village Views
# Update your existing village_list view to include filtering
@login_required
def village_list(request):
    villages = Village.objects.select_related(
        'traditional_council__municipality__district__province'
    ).order_by('name')
    
    # Filter by council
    council_filter = request.GET.get('council')
    if council_filter:
        villages = villages.filter(traditional_council_id=council_filter)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        villages = villages.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        villages = villages.filter(is_active=True)
    elif status_filter == 'inactive':
        villages = villages.filter(is_active=False)
    
    paginator = Paginator(villages, 15)
    page_number = request.GET.get('page')
    villages = paginator.get_page(page_number)
    
    councils = TraditionalCouncil.objects.filter(is_active=True).order_by('name')
    
    context = {
        'villages': villages,
        'councils': councils,
        'selected_council': council_filter,
        'search_query': search_query,
        'current_filters': {
            'status': status_filter,
        }
    }
    return render(request, 'governance/villages/village_list.html', context)

# Update your existing village_create view
@login_required
def village_create(request):
    if request.method == 'POST':
        form = VillageForm(request.POST)
        if form.is_valid():
            village = form.save()
            messages.success(request, f'Village "{village.name}" created successfully.')
            return redirect('governance:village_detail', pk=village.pk)
    else:
        form = VillageForm()
        # Pre-select council if passed as parameter
        council_id = request.GET.get('council')
        if council_id:
            form.fields['traditional_council'].initial = council_id
    
    context = {'form': form, 'title': 'Create Village'}
    return render(request, 'governance/villages/village_form.html', context)

# Add the missing village_detail view
@login_required
def village_detail(request, pk):
    """View village details"""
    village = get_object_or_404(
        Village.objects.select_related(
            'traditional_council__municipality__district__province'
        ),
        pk=pk
    )
    
    context = {'village': village}
    return render(request, 'governance/villages/village_detail.html', context)

# Add the missing village_update view
@login_required
def village_update(request, pk):
    """Update village"""
    village = get_object_or_404(Village, pk=pk)
    
    if request.method == 'POST':
        form = VillageForm(request.POST, instance=village)
        if form.is_valid():
            form.save()
            messages.success(request, f'Village "{village.name}" updated successfully.')
            return redirect('governance:village_detail', pk=village.pk)
    else:
        form = VillageForm(instance=village)
    
    context = {'form': form, 'village': village, 'title': 'Update Village'}
    return render(request, 'governance/villages/village_form.html', context)

# Add the missing village_delete view
@login_required
def village_delete(request, pk):
    """Delete village"""
    village = get_object_or_404(Village, pk=pk)
    
    if request.method == 'POST':
        village_name = village.name
        village.delete()
        messages.success(request, f'Village "{village_name}" deleted successfully.')
        return redirect('governance:village_list')
    
    context = {'village': village}
    return render(request, 'governance/villages/village_confirm_delete.html', context)


# Meeting Views
@login_required
def meeting_list(request):
    """List all meetings with search and filtering"""
    meetings = CouncilMeeting.objects.select_related('council').order_by('-date', '-time')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        meetings = meetings.filter(
            Q(title__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(council__name__icontains=search_query)
        )
    
    # Filter by council
    council_filter = request.GET.get('council')
    if council_filter:
        meetings = meetings.filter(council_id=council_filter)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        meetings = meetings.filter(status=status_filter)
    
    # Filter by date
    date_filter = request.GET.get('date_filter')
    if date_filter == 'upcoming':
        meetings = meetings.filter(date__gte=timezone.now().date())
    elif date_filter == 'past':
        meetings = meetings.filter(date__lt=timezone.now().date())
    elif date_filter == 'today':
        meetings = meetings.filter(date=timezone.now().date())
    
    paginator = Paginator(meetings, 10)
    page_number = request.GET.get('page')
    meetings = paginator.get_page(page_number)
    
    councils = TraditionalCouncil.objects.filter(is_active=True).order_by('name')
    
    context = {
        'meetings': meetings,
        'councils': councils,
        'status_choices': CouncilMeeting.STATUS_CHOICES,
        'selected_council': council_filter,
        'selected_status': status_filter,
        'date_filter': date_filter,
        'search_query': search_query,
        'today': timezone.now().date(),
    }
    return render(request, 'governance/councils/meetings/meeting_list.html', context)

@login_required
def meeting_detail(request, pk):
    """View meeting details"""
    meeting = get_object_or_404(CouncilMeeting.objects.select_related('council'), pk=pk)
    resolutions = meeting.resolutions.select_related('proposed_by__user').all()
    attendees = meeting.attendees.select_related('user').all()
    
    context = {
        'meeting': meeting,
        'resolutions': resolutions,
        'attendees': attendees,
    }
    return render(request, 'governance/councils/meetings/meeting_detail.html', context)

@login_required
def meeting_create(request):
    """Create new meeting"""
    if request.method == 'POST':
        form = CouncilMeetingForm(request.POST)
        if form.is_valid():
            meeting = form.save()
            messages.success(request, f'Meeting "{meeting.title}" scheduled successfully.')
            return redirect('governance:meeting_detail', pk=meeting.pk)
    else:
        form = CouncilMeetingForm()
        # Pre-select council if passed as parameter
        council_id = request.GET.get('council')
        if council_id:
            form.fields['council'].initial = council_id
    
    context = {'form': form, 'title': 'Schedule Meeting'}
    return render(request, 'governance/councils/meetings/meeting_form.html', context)

@login_required
def meeting_update(request, pk):
    """Update meeting"""
    meeting = get_object_or_404(CouncilMeeting, pk=pk)
    
    if request.method == 'POST':
        form = CouncilMeetingForm(request.POST, instance=meeting)
        if form.is_valid():
            form.save()
            messages.success(request, f'Meeting "{meeting.title}" updated successfully.')
            return redirect('governance:meeting_detail', pk=meeting.pk)
    else:
        form = CouncilMeetingForm(instance=meeting)
    
    context = {'form': form, 'meeting': meeting, 'title': 'Update Meeting'}
    return render(request, 'governance/councils/meetings/meeting_form.html', context)

@login_required
def meeting_delete(request, pk):
    """Delete meeting"""
    meeting = get_object_or_404(CouncilMeeting, pk=pk)
    resolutions = meeting.resolutions.all()
    attendees = meeting.attendees.all()
    
    if request.method == 'POST':
        meeting_title = meeting.title
        meeting.delete()
        messages.success(request, f'Meeting "{meeting_title}" deleted successfully.')
        return redirect('governance:meeting_list')
    
    context = {
        'meeting': meeting,
        'resolutions': resolutions,
        'attendees': attendees,
    }
    return render(request, 'governance/councils/meetings/meeting_confirm_delete.html', context)

# AJAX Views
@login_required
def get_districts(request):
    province_id = request.GET.get('province_id')
    districts = District.objects.filter(province_id=province_id).values('id', 'name')
    return JsonResponse(list(districts), safe=False)

@login_required
def get_municipalities(request):
    district_id = request.GET.get('district_id')
    municipalities = Municipality.objects.filter(district_id=district_id).values('id', 'name')
    return JsonResponse(list(municipalities), safe=False)

# Add AJAX view for council members
@login_required
def get_council_members(request):
    """Get council members for a specific council (AJAX)"""
    council_id = request.GET.get('council_id')
    members = CouncilMember.objects.filter(
        council_id=council_id, is_active=True
    ).select_related('user').values(
        'id', 
        'user__first_name', 
        'user__last_name', 
        'role'
    ).order_by('role', 'user__last_name')
    
    members_data = []
    for member in members:
        members_data.append({
            'id': member['id'],
            'name': f"{member['user__first_name']} {member['user__last_name']}",
            'role': member['role']
        })
    
    return JsonResponse({'members': members_data})


# Council Member Views
@login_required
def council_member_list(request):
    """List all council members with filtering"""
    members = CouncilMember.objects.select_related('user', 'council').order_by('council__name', 'role')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        members = members.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(council__name__icontains=search_query)
        )
    
    # Filter by council
    council_filter = request.GET.get('council')
    if council_filter:
        members = members.filter(council_id=council_filter)
    
    # Filter by role
    role_filter = request.GET.get('role')
    if role_filter:
        members = members.filter(role=role_filter)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        members = members.filter(is_active=True)
    elif status_filter == 'inactive':
        members = members.filter(is_active=False)
    elif status_filter == 'expired':
        members = members.filter(term_end_date__lt=timezone.now().date())
    
    paginator = Paginator(members, 20)
    page_number = request.GET.get('page')
    members = paginator.get_page(page_number)
    
    councils = TraditionalCouncil.objects.filter(is_active=True).order_by('name')
    
    context = {
        'members': members,
        'councils': councils,
        'role_choices': CouncilMember.ROLE_CHOICES,
        'selected_council': council_filter,
        'selected_role': role_filter,
        'selected_status': status_filter,
        'search_query': search_query,
        'today': timezone.now().date(),
    }
    return render(request, 'governance/councils/council_members/council_member_list.html', context)

@login_required
def council_member_detail(request, pk):
    """View council member details"""
    member = get_object_or_404(CouncilMember.objects.select_related('user', 'council'), pk=pk)
    attended_meetings = member.attended_meetings.order_by('-date')[:10]
    proposed_resolutions = member.proposed_resolutions.order_by('-created_at')[:5]
    
    context = {
        'member': member,
        'attended_meetings': attended_meetings,
        'proposed_resolutions': proposed_resolutions,
        'today': timezone.now().date(),
    }
    return render(request, 'governance/councils/council_members/council_member_detail.html', context)

@login_required
def council_member_create(request):
    """Create new council member"""
    if request.method == 'POST':
        form = CouncilMemberForm(request.POST)
        if form.is_valid():
            member = form.save()
            messages.success(request, f'Member "{member.user.get_full_name()}" added successfully.')
            return redirect('governance:council_member_detail', pk=member.pk)
    else:
        form = CouncilMemberForm()
        # Pre-select council if passed as parameter
        council_id = request.GET.get('council')
        if council_id:
            form.fields['council'].initial = council_id
    
    context = {'form': form, 'title': 'Add Council Member'}
    return render(request, 'governance/councils/council_members/council_member_form.html', context)

@login_required
def council_member_update(request, pk):
    """Update council member"""
    member = get_object_or_404(CouncilMember, pk=pk)
    
    if request.method == 'POST':
        form = CouncilMemberForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f'Member "{member.user.get_full_name()}" updated successfully.')
            return redirect('governance:council_member_detail', pk=member.pk)
    else:
        form = CouncilMemberForm(instance=member)
    
    context = {'form': form, 'member': member, 'title': 'Update Council Member'}
    return render(request, 'governance/councils/council_members/council_member_form.html', context)

@login_required
def council_member_delete(request, pk):
    """Delete council member"""
    member = get_object_or_404(CouncilMember, pk=pk)
    
    if request.method == 'POST':
        member_name = member.user.get_full_name()
        member.delete()
        messages.success(request, f'Member "{member_name}" removed successfully.')
        return redirect('governance:council_member_list')
    
    context = {'member': member}
    return render(request, 'governance/councils/council_members/council_member_confirm_delete.html', context)

# Resolution Views
@login_required
def resolution_list(request):
    """List all resolutions with filtering"""
    resolutions = Resolution.objects.select_related('meeting', 'proposed_by__user').order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        resolutions = resolutions.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by meeting
    meeting_filter = request.GET.get('meeting')
    if meeting_filter:
        resolutions = resolutions.filter(meeting_id=meeting_filter)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        resolutions = resolutions.filter(status=status_filter)
    
    # Filter by proposer
    proposer_filter = request.GET.get('proposer')
    if proposer_filter:
        resolutions = resolutions.filter(proposed_by_id=proposer_filter)
    
    paginator = Paginator(resolutions, 15)
    page_number = request.GET.get('page')
    resolutions = paginator.get_page(page_number)
    
    meetings = CouncilMeeting.objects.order_by('-date')[:20]
    proposers = CouncilMember.objects.filter(is_active=True).select_related('user')
    
    context = {
        'resolutions': resolutions,
        'meetings': meetings,
        'proposers': proposers,
        'status_choices': Resolution.STATUS_CHOICES,
        'selected_meeting': meeting_filter,
        'selected_status': status_filter,
        'selected_proposer': proposer_filter,
        'search_query': search_query,
    }
    return render(request, 'governance/councils/resolutions/resolution_list.html', context)

@login_required
def resolution_detail(request, pk):
    """View resolution details"""
    resolution = get_object_or_404(
        Resolution.objects.select_related('meeting', 'proposed_by__user'),
        pk=pk
    )
    
    context = {'resolution': resolution}
    return render(request, 'governance/councils/resolutions/resolution_detail.html', context)

@login_required
def resolution_create(request):
    """Create new resolution"""
    if request.method == 'POST':
        form = ResolutionForm(request.POST)
        if form.is_valid():
            resolution = form.save()
            messages.success(request, f'Resolution "{resolution.title}" created successfully.')
            return redirect('governance:resolution_detail', pk=resolution.pk)
    else:
        form = ResolutionForm()
        # Pre-select meeting if passed as parameter
        meeting_id = request.GET.get('meeting')
        if meeting_id:
            form.fields['meeting'].initial = meeting_id
    
    context = {'form': form, 'title': 'Create Resolution'}
    return render(request, 'governance/councils/resolutions/resolution_form.html', context)

@login_required
def resolution_update(request, pk):
    """Update resolution"""
    resolution = get_object_or_404(Resolution, pk=pk)
    
    if request.method == 'POST':
        form = ResolutionForm(request.POST, instance=resolution)
        if form.is_valid():
            form.save()
            messages.success(request, f'Resolution "{resolution.title}" updated successfully.')
            return redirect('governance:resolution_detail', pk=resolution.pk)
    else:
        form = ResolutionForm(instance=resolution)
    
    context = {'form': form, 'resolution': resolution, 'title': 'Update Resolution'}
    return render(request, 'governance/councils/resolutions/resolution_form.html', context)

@login_required
def resolution_delete(request, pk):
    """Delete resolution"""
    resolution = get_object_or_404(Resolution, pk=pk)
    
    if request.method == 'POST':
        resolution_title = resolution.title
        resolution.delete()
        messages.success(request, f'Resolution "{resolution_title}" deleted successfully.')
        return redirect('governance:resolution_list')
    
    context = {'resolution': resolution}
    return render(request, 'governance/councils/resolutions/resolution_confirm_delete.html', context)

# AJAX status update views
@login_required
def update_resolution_status(request, pk):
    """Update resolution status via AJAX"""
    if request.method == 'POST':
        resolution = get_object_or_404(Resolution, pk=pk)
        new_status = request.POST.get('status')
        
        if new_status in [choice[0] for choice in Resolution.STATUS_CHOICES]:
            resolution.status = new_status
            if new_status == 'implemented':
                resolution.date_implemented = timezone.now().date()
            resolution.save()
            return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})

@login_required
def activate_council_member(request, pk):
    """Activate council member via AJAX"""
    if request.method == 'POST':
        member = get_object_or_404(CouncilMember, pk=pk)
        member.is_active = True
        member.save()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})

@login_required
def deactivate_council_member(request, pk):
    """Deactivate council member via AJAX"""
    if request.method == 'POST':
        member = get_object_or_404(CouncilMember, pk=pk)
        member.is_active = False
        member.save()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})



# Ward Committee Views
@login_required
def ward_committee_list(request):
    """List all ward committees with filtering and pagination"""
    ward_committees = WardCommittee.objects.select_related('municipality', 'municipality__district').annotate(
        council_count=Count('traditional_councils', filter=Q(traditional_councils__is_active=True)),
        member_count=Count('committee_members', filter=Q(committee_members__is_active=True))
    )
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    municipality_filter = request.GET.get('municipality', '')
    status_filter = request.GET.get('status', '')
    ward_number_filter = request.GET.get('ward_number', '')
    
    # Apply filters
    if search_query:
        ward_committees = ward_committees.filter(
            Q(name__icontains=search_query) |
            Q(ward_code__icontains=search_query) |
            Q(ward_councillor__icontains=search_query)
        )
    
    if municipality_filter:
        ward_committees = ward_committees.filter(municipality_id=municipality_filter)
    
    if status_filter:
        if status_filter == 'active':
            ward_committees = ward_committees.filter(is_active=True)
        elif status_filter == 'inactive':
            ward_committees = ward_committees.filter(is_active=False)
        else:
            ward_committees = ward_committees.filter(status=status_filter)
    
    if ward_number_filter:
        ward_committees = ward_committees.filter(ward_number__icontains=ward_number_filter)
    
    # Pagination
    paginator = Paginator(ward_committees, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get municipalities for filter dropdown
    municipalities = Municipality.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'municipalities': municipalities,
        'search_query': search_query,
        'current_filters': {
            'municipality': municipality_filter,
            'status': status_filter,
            'ward_number': ward_number_filter,
        },
        'ward_committee_status_choices': WardCommittee.COMMITTEE_STATUS,
    }
    
    return render(request, 'governance/ward_committees/ward_committee_list.html', context)

@login_required
def ward_committee_detail(request, pk):
    """Display detailed information about a ward committee"""
    ward_committee = get_object_or_404(
        WardCommittee.objects.select_related('municipality', 'municipality__district')
        .prefetch_related('committee_members__user', 'traditional_councils'),
        pk=pk
    )
    
    # Get committee members
    committee_members = ward_committee.committee_members.filter(is_active=True).select_related('user')
    
    # Get traditional councils under this ward committee
    traditional_councils = ward_committee.traditional_councils.filter(is_active=True)
    
    # Calculate statistics
    total_villages = sum(council.total_villages for council in traditional_councils)
    
    context = {
        'ward_committee': ward_committee,
        'committee_members': committee_members,
        'traditional_councils': traditional_councils,
        'total_villages': total_villages,
    }
    
    return render(request, 'governance/ward_committees/ward_committee_detail.html', context)

@login_required
def ward_committee_create(request):
    """Create a new ward committee"""
    if request.method == 'POST':
        form = WardCommitteeForm(request.POST)
        if form.is_valid():
            ward_committee = form.save()
            messages.success(request, f'Ward Committee "{ward_committee.name}" created successfully!')
            return redirect('governance:ward_committee_detail', pk=ward_committee.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = WardCommitteeForm()
        # Pre-populate municipality if passed in URL
        municipality_id = request.GET.get('municipality')
        if municipality_id:
            form.fields['municipality'].initial = municipality_id
    
    municipalities = Municipality.objects.filter(is_active=True).order_by('name')
    
    context = {
        'form': form,
        'municipalities': municipalities,
        'title': 'Create Ward Committee'
    }
    
    return render(request, 'governance/ward_committees/ward_committee_form.html', context)

@login_required
def ward_committee_update(request, pk):
    """Update an existing ward committee"""
    ward_committee = get_object_or_404(WardCommittee, pk=pk)
    
    if request.method == 'POST':
        form = WardCommitteeForm(request.POST, instance=ward_committee)
        if form.is_valid():
            ward_committee = form.save()
            messages.success(request, f'Ward Committee "{ward_committee.name}" updated successfully!')
            return redirect('governance:ward_committee_detail', pk=ward_committee.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = WardCommitteeForm(instance=ward_committee)
    
    municipalities = Municipality.objects.filter(is_active=True).order_by('name')
    
    context = {
        'form': form,
        'ward_committee': ward_committee,
        'municipalities': municipalities,
        'title': f'Update {ward_committee.name}'
    }
    
    return render(request, 'governance/ward_committees/ward_committee_form.html', context)

@login_required
def ward_committee_delete(request, pk):
    """Delete a ward committee"""
    ward_committee = get_object_or_404(WardCommittee, pk=pk)
    
    if request.method == 'POST':
        ward_committee_name = ward_committee.name
        ward_committee.delete()
        messages.success(request, f'Ward Committee "{ward_committee_name}" deleted successfully!')
        return redirect('governance:ward_committee_list')
    
    context = {
        'ward_committee': ward_committee,
        'title': f'Delete {ward_committee.name}'
    }
    
    return render(request, 'governance/ward_committees/ward_committee_confirm_delete.html', context)

# Ward Committee Member Views
@login_required
def ward_committee_member_list(request):
    """List all ward committee members with filtering"""
    members = WardCommitteeMember.objects.select_related(
        'ward_committee', 'ward_committee__municipality', 'user'
    )
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    ward_committee_filter = request.GET.get('ward_committee', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    
    # Apply filters
    if search_query:
        members = members.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(ward_committee__name__icontains=search_query)
        )
    
    if ward_committee_filter:
        members = members.filter(ward_committee_id=ward_committee_filter)
    
    if role_filter:
        members = members.filter(role=role_filter)
    
    if status_filter:
        if status_filter == 'active':
            members = members.filter(is_active=True)
        elif status_filter == 'inactive':
            members = members.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(members, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get ward committees for filter dropdown
    ward_committees = WardCommittee.objects.filter(is_active=True).order_by('ward_number', 'name')
    
    context = {
        'page_obj': page_obj,
        'ward_committees': ward_committees,
        'search_query': search_query,
        'current_filters': {
            'ward_committee': ward_committee_filter,
            'role': role_filter,
            'status': status_filter,
        },
        'member_roles': WardCommitteeMember.MEMBER_ROLES,
    }
    
    return render(request, 'governance/ward_committees/ward_committee_member_list.html', context)

@login_required
def ward_committee_member_detail(request, pk):
    """Display detailed information about a ward committee member"""
    member = get_object_or_404(
        WardCommitteeMember.objects.select_related('ward_committee', 'user'),
        pk=pk
    )
    
    context = {
        'member': member,
    }
    
    return render(request, 'governance/ward_committees/ward_committee_member_detail.html', context)

@login_required
def ward_committee_member_create(request):
    """Create a new ward committee member"""
    if request.method == 'POST':
        form = WardCommitteeMemberForm(request.POST)
        if form.is_valid():
            member = form.save()
            messages.success(request, f'Committee member "{member.user.get_full_name()}" added successfully!')
            return redirect('governance:ward_committee_member_detail', pk=member.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = WardCommitteeMemberForm()
        # Pre-populate ward committee if passed in URL
        ward_committee_id = request.GET.get('ward_committee')
        if ward_committee_id:
            form.fields['ward_committee'].initial = ward_committee_id
    
    ward_committees = WardCommittee.objects.filter(is_active=True).order_by('ward_number', 'name')
    
    context = {
        'form': form,
        'ward_committees': ward_committees,
        'title': 'Add Committee Member'
    }
    
    return render(request, 'governance/ward_committees/ward_committee_member_form.html', context)

@login_required
def ward_committee_member_update(request, pk):
    """Update an existing ward committee member"""
    member = get_object_or_404(WardCommitteeMember, pk=pk)
    
    if request.method == 'POST':
        form = WardCommitteeMemberForm(request.POST, instance=member)
        if form.is_valid():
            member = form.save()
            messages.success(request, f'Committee member "{member.user.get_full_name()}" updated successfully!')
            return redirect('governance:ward_committee_member_detail', pk=member.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = WardCommitteeMemberForm(instance=member)
    
    ward_committees = WardCommittee.objects.filter(is_active=True).order_by('ward_number', 'name')
    
    context = {
        'form': form,
        'member': member,
        'ward_committees': ward_committees,
        'title': f'Update {member.user.get_full_name()}'
    }
    
    return render(request, 'governance/ward_committees/ward_committee_member_form.html', context)

@login_required
def ward_committee_member_delete(request, pk):
    """Delete a ward committee member"""
    member = get_object_or_404(WardCommitteeMember, pk=pk)
    
    if request.method == 'POST':
        member_name = member.user.get_full_name()
        member.delete()
        messages.success(request, f'Committee member "{member_name}" removed successfully!')
        return redirect('governance:ward_committee_member_list')
    
    context = {
        'member': member,
        'title': f'Remove {member.user.get_full_name()}'
    }
    
    return render(request, 'governance/ward_committees/ward_committee_member_confirm_delete.html', context)

# AJAX Views for Ward Committees
@login_required
def get_ward_committees_by_municipality(request):
    """AJAX endpoint to get ward committees filtered by municipality"""
    municipality_id = request.GET.get('municipality_id')
    
    if municipality_id:
        ward_committees = WardCommittee.objects.filter(
            municipality_id=municipality_id, 
            is_active=True
        ).order_by('ward_number', 'name')
        
        data = [
            {
                'id': wc.id,
                'name': f"Ward {wc.ward_number} - {wc.name}",
                'ward_number': wc.ward_number,
                'ward_code': wc.ward_code
            }
            for wc in ward_committees
        ]
    else:
        data = []
    
    return JsonResponse(data, safe=False)

@login_required
def get_ward_committee_members(request):
    """AJAX endpoint to get ward committee members"""
    ward_committee_id = request.GET.get('ward_committee_id')
    
    if ward_committee_id:
        members = WardCommitteeMember.objects.filter(
            ward_committee_id=ward_committee_id,
            is_active=True
        ).select_related('user')
        
        data = [
            {
                'id': member.id,
                'name': member.user.get_full_name(),
                'role': member.get_role_display(),
                'role_code': member.role
            }
            for member in members
        ]
    else:
        data = []
    
    return JsonResponse(data, safe=False)


# governance/views.py - Add these views

@login_required
def ward_committee_dashboard(request, pk):
    """Comprehensive dashboard for ward committee performance"""
    ward_committee = get_object_or_404(WardCommittee, pk=pk)
    
    # Time periods for analysis
    today = timezone.now().date()
    last_month = today - timedelta(days=30)
    last_quarter = today - timedelta(days=90)
    
    # Recent metrics
    recent_issues = ward_committee.community_issues.filter(
        reported_date__gte=last_month
    ).order_by('-reported_date')[:10]
    
    recent_engagements = ward_committee.engagements.filter(
        date_scheduled__gte=last_month
    ).order_by('-date_scheduled')[:5]
    
    # Performance calculations
    total_issues = ward_committee.community_issues.count()
    resolved_issues = ward_committee.community_issues.filter(status='resolved').count()
    resolution_rate = (resolved_issues / total_issues * 100) if total_issues > 0 else 0
    
    # Bridge effectiveness indicators
    bridge_indicators = {
        'community_engagement': ward_committee.recent_community_engagement,
        'active_issues': ward_committee.active_issues_count,
        'resolution_rate': resolution_rate,
        'municipal_interactions': ward_committee.municipal_interactions.filter(
            date_initiated__gte=last_quarter
        ).count(),
        'performance_score': ward_committee.current_performance_score or 0,
    }
    
    # Issue categories analysis
    issue_categories = ward_committee.community_issues.values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'ward_committee': ward_committee,
        'recent_issues': recent_issues,
        'recent_engagements': recent_engagements,
        'bridge_indicators': bridge_indicators,
        'issue_categories': issue_categories,
    }
    
    return render(request, 'governance/ward_committee_dashboard.html', context)

@login_required
def community_issue_management(request, ward_committee_pk):
    """Manage community issues for a ward committee"""
    ward_committee = get_object_or_404(WardCommittee, pk=ward_committee_pk)
    
    # Filter and search
    issues = ward_committee.community_issues.all()
    
    status_filter = request.GET.get('status')
    category_filter = request.GET.get('category')
    priority_filter = request.GET.get('priority')
    
    if status_filter:
        issues = issues.filter(status=status_filter)
    if category_filter:
        issues = issues.filter(category=category_filter)
    if priority_filter:
        issues = issues.filter(priority=priority_filter)
    
    # Pagination
    paginator = Paginator(issues, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'ward_committee': ward_committee,
        'page_obj': page_obj,
        'status_choices': CommunityIssue.RESOLUTION_STATUS,
        'category_choices': CommunityIssue.ISSUE_CATEGORIES,
        'priority_choices': CommunityIssue.PRIORITY_LEVELS,
        'current_filters': {
            'status': status_filter,
            'category': category_filter,
            'priority': priority_filter,
        }
    }
    
    return render(request, 'governance/community_issue_management.html', context)

@login_required
def bridge_effectiveness_report(request):
    """Generate bridge effectiveness reports for all ward committees"""
    # Calculate effectiveness scores for all committees
    ward_committees = WardCommittee.objects.filter(is_active=True).annotate(
        issues_count=Count('community_issues'),
        resolved_count=Count('community_issues', filter=Q(community_issues__status='resolved')),
        engagements_count=Count('engagements', filter=Q(engagements__date_scheduled__gte=timezone.now() - timedelta(days=90)))
    )
    
    # Performance rankings
    performance_data = []
    for committee in ward_committees:
        resolution_rate = (committee.resolved_count / committee.issues_count * 100) if committee.issues_count > 0 else 0
        
        performance_data.append({
            'committee': committee,
            'resolution_rate': resolution_rate,
            'engagement_level': committee.engagements_count,
            'performance_score': committee.current_performance_score or 0,
        })
    
    # Sort by performance score
    performance_data.sort(key=lambda x: x['performance_score'], reverse=True)
    
    context = {
        'performance_data': performance_data,
        'total_committees': len(performance_data),
        'high_performers': len([p for p in performance_data if p['performance_score'] >= 4.0]),
        'needs_support': len([p for p in performance_data if p['performance_score'] < 2.5]),
    }
    
    return render(request, 'governance/bridge_effectiveness_report.html', context)

