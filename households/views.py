from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from datetime import date, timedelta

from .models import Household, Resident, HouseholdService
from .forms import (
    HouseholdForm, ResidentForm, HouseholdServiceForm,
    HouseholdSearchForm, ResidentSearchForm
)
from governance.models import Village, WardCommittee, Municipality

User = get_user_model()

# Dashboard Views
@login_required
def households_dashboard(request):
    """Main dashboard for households module"""
    
    # Basic statistics
    total_households = Household.objects.filter(is_active=True).count()
    total_residents = Resident.objects.filter(is_active=True).count()
    verified_households = Household.objects.filter(verified=True, is_active=True).count()
    
    # Demographics
    children_count = Resident.objects.filter(
        is_active=True,
        date_of_birth__gt=date.today() - timedelta(days=18*365)
    ).count()
    
    adults_count = Resident.objects.filter(
        is_active=True,
        date_of_birth__lte=date.today() - timedelta(days=18*365),
        date_of_birth__gt=date.today() - timedelta(days=60*365)
    ).count()
    
    seniors_count = Resident.objects.filter(
        is_active=True,
        date_of_birth__lte=date.today() - timedelta(days=60*365)
    ).count()
    
    # Employment statistics
    employed_count = Resident.objects.filter(
        is_active=True,
        employment_status__in=['employed_formal', 'employed_informal', 'self_employed']
    ).count()
    
    unemployed_count = Resident.objects.filter(
        is_active=True,
        employment_status='unemployed'
    ).count()
    
    # Housing types distribution
    housing_types = Household.objects.filter(is_active=True).values('housing_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Service access statistics
    water_access = Household.objects.filter(
        is_active=True,
        water_source__in=['piped_indoor', 'piped_yard']
    ).count()
    
    electricity_access = Household.objects.filter(
        is_active=True,
        electricity_source='grid'
    ).count()
    
    # Recent registrations
    recent_households = Household.objects.filter(is_active=True).order_by('-created_at')[:5]
    recent_residents = Resident.objects.filter(is_active=True).order_by('-created_at')[:10]
    
    # Municipality breakdown (Fixed)
    municipality_stats = Municipality.objects.annotate(
        household_count=Count('traditional_councils__villages__households', 
                            filter=Q(traditional_councils__villages__households__is_active=True)),
        resident_count=Count('traditional_councils__villages__households__residents', 
                           filter=Q(traditional_councils__villages__households__residents__is_active=True))
    ).filter(household_count__gt=0).order_by('-household_count')[:10]
    
    context = {
        'total_households': total_households,
        'total_residents': total_residents,
        'verified_households': verified_households,
        'verification_rate': (verified_households / total_households * 100) if total_households > 0 else 0,
        'children_count': children_count,
        'adults_count': adults_count,
        'seniors_count': seniors_count,
        'employed_count': employed_count,
        'unemployed_count': unemployed_count,
        'employment_rate': (employed_count / adults_count * 100) if adults_count > 0 else 0,
        'housing_types': housing_types,
        'water_access_rate': (water_access / total_households * 100) if total_households > 0 else 0,
        'electricity_access_rate': (electricity_access / total_households * 100) if total_households > 0 else 0,
        'recent_households': recent_households,
        'recent_residents': recent_residents,
        'municipality_stats': municipality_stats,
    }
    
    return render(request, 'households/dashboard.html', context)

# Household Views
@login_required
def household_list(request):
    """List all households with filtering and search"""
    
    households = Household.objects.select_related(
        'village', 'ward_committee', 'verified_by'
    ).prefetch_related('residents').filter(is_active=True)
    
    # Apply filters
    search_form = HouseholdSearchForm(request.GET)
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        village = search_form.cleaned_data.get('village')
        housing_type = search_form.cleaned_data.get('housing_type')
        verified = search_form.cleaned_data.get('verified')
        
        if search_query:
            households = households.filter(
                Q(household_id__icontains=search_query) |
                Q(physical_address__icontains=search_query) |
                Q(residents__first_name__icontains=search_query) |
                Q(residents__last_name__icontains=search_query)
            ).distinct()
        
        if village:
            households = households.filter(village=village)
        
        if housing_type:
            households = households.filter(housing_type=housing_type)
        
        if verified:
            is_verified = verified == 'true'
            households = households.filter(verified=is_verified)
    
    # Pagination
    paginator = Paginator(households, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_count': households.count(),
    }
    
    return render(request, 'households/household_list.html', context)

@login_required
def household_detail(request, pk):
    """Display detailed information about a household"""
    
    household = get_object_or_404(
        Household.objects.select_related(
            'village', 'ward_committee', 'verified_by'
        ).prefetch_related('residents', 'services'),
        pk=pk
    )
    
    # Get residents grouped by relationship
    head_of_household = household.residents.filter(
        is_head_of_household=True, is_active=True
    ).first()
    
    other_residents = household.residents.filter(
        is_head_of_household=False, is_active=True
    ).order_by('date_of_birth')
    
    # Calculate household statistics
    total_income = household.total_household_income
    
    # Service access
    services = household.services.all()
    
    context = {
        'household': household,
        'head_of_household': head_of_household,
        'other_residents': other_residents,
        'total_income': total_income,
        'services': services,
    }
    
    return render(request, 'households/household_detail.html', context)

@login_required
def household_create(request):
    """Create a new household"""
    
    if request.method == 'POST':
        form = HouseholdForm(request.POST)
        if form.is_valid():
            household = form.save()
            messages.success(request, f'Household {household.household_id} created successfully!')
            return redirect('households:household_detail', pk=household.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = HouseholdForm()
        # Pre-populate village if passed in URL
        village_id = request.GET.get('village')
        if village_id:
            form.fields['village'].initial = village_id
    
    context = {
        'form': form,
        'title': 'Create Household',
    }
    
    return render(request, 'households/household_form.html', context)

@login_required
def household_update(request, pk):
    """Update an existing household"""
    
    household = get_object_or_404(Household, pk=pk)
    
    if request.method == 'POST':
        form = HouseholdForm(request.POST, instance=household)
        if form.is_valid():
            household = form.save()
            messages.success(request, f'Household {household.household_id} updated successfully!')
            return redirect('households:household_detail', pk=household.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = HouseholdForm(instance=household)
    
    context = {
        'form': form,
        'household': household,
        'title': f'Update {household.household_id}',
    }
    
    return render(request, 'households/household_form.html', context)

@login_required
def household_delete(request, pk):
    """Delete a household"""
    
    household = get_object_or_404(Household, pk=pk)
    
    if request.method == 'POST':
        household_id = household.household_id
        household.is_active = False  # Soft delete
        household.save()
        messages.success(request, f'Household {household_id} deactivated successfully!')
        return redirect('households:household_list')
    
    context = {
        'household': household,
        'title': f'Deactivate {household.household_id}',
    }
    
    return render(request, 'households/household_confirm_delete.html', context)

@login_required
def household_verify(request, pk):
    """Verify household data"""
    
    household = get_object_or_404(Household, pk=pk)
    
    if request.method == 'POST':
        household.verified = True
        household.verified_by = request.user
        household.verification_date = timezone.now()
        household.save()
        
        messages.success(request, f'Household {household.household_id} verified successfully!')
        return redirect('households:household_detail', pk=household.pk)
    
    context = {
        'household': household,
        'title': f'Verify {household.household_id}',
    }
    
    return render(request, 'households/household_verify.html', context)

# Resident Views
@login_required
def resident_list(request):
    """List all residents with filtering and search"""
    
    residents = Resident.objects.select_related(
        'household', 'household__village', 'user_account'
    ).filter(is_active=True)
    
    # Apply filters
    search_form = ResidentSearchForm(request.GET)
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        household = search_form.cleaned_data.get('household')
        employment_status = search_form.cleaned_data.get('employment_status')
        age_group = search_form.cleaned_data.get('age_group')
        
        if search_query:
            residents = residents.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(id_number__icontains=search_query) |
                Q(phone_number__icontains=search_query)
            )
        
        if household:
            residents = residents.filter(household=household)
        
        if employment_status:
            residents = residents.filter(employment_status=employment_status)
        
        if age_group:
            today = date.today()
            if age_group == 'child':
                cutoff_date = today - timedelta(days=18*365)
                residents = residents.filter(date_of_birth__gt=cutoff_date)
            elif age_group == 'adult':
                adult_start = today - timedelta(days=60*365)
                adult_end = today - timedelta(days=18*365)
                residents = residents.filter(
                    date_of_birth__lte=adult_end,
                    date_of_birth__gt=adult_start
                )
            elif age_group == 'senior':
                cutoff_date = today - timedelta(days=60*365)
                residents = residents.filter(date_of_birth__lte=cutoff_date)
    
    # Pagination
    paginator = Paginator(residents, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_count': residents.count(),
    }
    
    return render(request, 'households/resident_list.html', context)

@login_required
def resident_detail(request, pk):
    """Display detailed information about a resident"""
    
    resident = get_object_or_404(
        Resident.objects.select_related(
            'household', 'household__village', 'user_account'
        ),
        pk=pk
    )
    
    # Check if resident can become system user
    can_create_user = (
        not resident.user_account and 
        resident.is_adult and 
        resident.email
    )
    
    context = {
        'resident': resident,
        'can_create_user': can_create_user,
    }
    
    return render(request, 'households/resident_detail.html', context)

@login_required
def resident_create(request):
    """Create a new resident"""
    
    if request.method == 'POST':
        form = ResidentForm(request.POST, request.FILES)
        if form.is_valid():
            resident = form.save()
            messages.success(request, f'Resident {resident.full_name} created successfully!')
            return redirect('households:resident_detail', pk=resident.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ResidentForm()
        # Pre-populate household if passed in URL
        household_id = request.GET.get('household')
        if household_id:
            form.fields['household'].initial = household_id
    
    context = {
        'form': form,
        'title': 'Add Resident',
    }
    
    return render(request, 'households/resident_form.html', context)

@login_required
def resident_update(request, pk):
    """Update an existing resident"""
    
    resident = get_object_or_404(Resident, pk=pk)
    
    if request.method == 'POST':
        form = ResidentForm(request.POST, request.FILES, instance=resident)
        if form.is_valid():
            resident = form.save()
            messages.success(request, f'Resident {resident.full_name} updated successfully!')
            return redirect('households:resident_detail', pk=resident.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ResidentForm(instance=resident)
    
    context = {
        'form': form,
        'resident': resident,
        'title': f'Update {resident.full_name}',
    }
    
    return render(request, 'households/resident_form.html', context)

@login_required
def resident_delete(request, pk):
    """Delete a resident"""
    
    resident = get_object_or_404(Resident, pk=pk)
    
    if request.method == 'POST':
        resident_name = resident.full_name
        resident.is_active = False  # Soft delete
        resident.save()
        messages.success(request, f'Resident {resident_name} deactivated successfully!')
        return redirect('households:resident_list')
    
    context = {
        'resident': resident,
        'title': f'Deactivate {resident.full_name}',
    }
    
    return render(request, 'households/resident_confirm_delete.html', context)

@login_required
def create_user_account(request, pk):
    """Create system user account for resident"""
    
    resident = get_object_or_404(Resident, pk=pk)
    
    if resident.user_account:
        messages.warning(request, f'{resident.full_name} already has a user account.')
        return redirect('households:resident_detail', pk=resident.pk)
    
    if not resident.email:
        messages.error(request, 'Email address is required to create user account.')
        return redirect('households:resident_detail', pk=resident.pk)
    
    if request.method == 'POST':
        # Create user account
        username = f"{resident.first_name.lower()}.{resident.last_name.lower()}"
        
        # Ensure unique username
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Generate temporary password
        import secrets
        import string
        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        
        try:
            user = User.objects.create_user(
                username=username,
                email=resident.email,
                first_name=resident.first_name,
                last_name=resident.last_name,
                phone_number=resident.phone_number,
                id_number=resident.id_number,
                date_of_birth=resident.date_of_birth,
                password=temp_password
            )
            
            # Link to resident
            resident.user_account = user
            resident.save()
            
            # Set profile role
            user.profile.role = 'villager'
            user.profile.save()
            
            messages.success(request, 
                f'User account created for {resident.full_name}. '
                f'Username: {username}, Temporary password: {temp_password}'
            )
            
            return redirect('households:resident_detail', pk=resident.pk)
            
        except Exception as e:
            messages.error(request, f'Error creating user account: {str(e)}')
    
    context = {
        'resident': resident,
        'title': f'Create User Account for {resident.full_name}',
    }
    
    return render(request, 'households/create_user_account.html', context)

# Household Service Views
@login_required
def household_service_list(request):
    """List household services"""
    
    services = HouseholdService.objects.select_related('household').order_by(
        'household__household_id', 'service_type'
    )
    
    # Filtering
    service_type = request.GET.get('service_type')
    status = request.GET.get('status')
    
    if service_type:
        services = services.filter(service_type=service_type)
    if status:
        services = services.filter(status=status)
    
    # Pagination
    paginator = Paginator(services, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'service_types': HouseholdService.SERVICE_TYPES,
        'status_choices': HouseholdService.STATUS_CHOICES,
        'current_filters': {
            'service_type': service_type,
            'status': status,
        }
    }
    
    return render(request, 'households/service_list.html', context)

@login_required
def household_service_create(request):
    """Create household service record"""
    
    if request.method == 'POST':
        form = HouseholdServiceForm(request.POST)
        if form.is_valid():
            service = form.save()
            messages.success(request, 'Service record created successfully!')
            return redirect('households:service_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = HouseholdServiceForm()
        # Pre-populate household if passed in URL
        household_id = request.GET.get('household')
        if household_id:
            form.fields['household'].initial = household_id
    
    context = {
        'form': form,
        'title': 'Add Service Record',
    }
    
    return render(request, 'households/service_form.html', context)

@login_required
def household_service_update(request, pk):
    """Update household service record"""
    
    service = get_object_or_404(HouseholdService, pk=pk)
    
    if request.method == 'POST':
        form = HouseholdServiceForm(request.POST, instance=service)
        if form.is_valid():
            service = form.save()
            messages.success(request, 'Service record updated successfully!')
            return redirect('households:service_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = HouseholdServiceForm(instance=service)
    
    context = {
        'form': form,
        'service': service,
        'title': f'Update Service Record',
    }
    
    return render(request, 'households/service_form.html', context)

@login_required
def household_service_delete(request, pk):
    """Delete household service record"""
    
    service = get_object_or_404(HouseholdService, pk=pk)
    
    if request.method == 'POST':
        service.delete()
        messages.success(request, 'Service record deleted successfully!')
        return redirect('households:service_list')
    
    context = {
        'service': service,
        'title': 'Delete Service Record',
    }
    
    return render(request, 'households/service_confirm_delete.html', context)

# Report Views
@login_required
def household_reports(request):
    """Main reports dashboard"""
    
    context = {
        'title': 'Household Reports',
    }
    
    return render(request, 'households/reports.html', context)

@login_required
def demographics_report(request):
    """Demographics analysis report"""
    
    # Age distribution
    today = date.today()
    age_groups = {
        'children': Resident.objects.filter(
            is_active=True,
            date_of_birth__gt=today - timedelta(days=18*365)
        ).count(),
        'adults': Resident.objects.filter(
            is_active=True,
            date_of_birth__lte=today - timedelta(days=18*365),
            date_of_birth__gt=today - timedelta(days=60*365)
        ).count(),
        'seniors': Resident.objects.filter(
            is_active=True,
            date_of_birth__lte=today - timedelta(days=60*365)
        ).count(),
    }
    
    # Gender distribution
    gender_distribution = Resident.objects.filter(is_active=True).values('gender').annotate(
        count=Count('id')
    )
    
    # Employment statistics
    employment_stats = Resident.objects.filter(is_active=True).values('employment_status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Education levels
    education_stats = Resident.objects.filter(is_active=True).values('education_level').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'age_groups': age_groups,
        'gender_distribution': gender_distribution,
        'employment_stats': employment_stats,
        'education_stats': education_stats,
    }
    
    return render(request, 'households/demographics_report.html', context)

@login_required
def services_report(request):
    """Service access analysis report"""
    
    # Service access by type
    service_access = {}
    for service_type, service_name in HouseholdService.SERVICE_TYPES:
        available = HouseholdService.objects.filter(
            service_type=service_type,
            status='available'
        ).count()
        
        total_households = Household.objects.filter(is_active=True).count()
        
        service_access[service_name] = {
            'available': available,
            'percentage': (available / total_households * 100) if total_households > 0 else 0
        }
    
    # Housing types distribution
    housing_distribution = Household.objects.filter(is_active=True).values('housing_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Water source distribution
    water_distribution = Household.objects.filter(is_active=True).values('water_source').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Electricity source distribution
    electricity_distribution = Household.objects.filter(is_active=True).values('electricity_source').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'service_access': service_access,
        'housing_distribution': housing_distribution,
        'water_distribution': water_distribution,
        'electricity_distribution': electricity_distribution,
    }
    
    return render(request, 'households/services_report.html', context)

# AJAX Views
@login_required
def get_ward_committees_by_village(request):
    """AJAX endpoint to get ward committees for a village"""
    
    village_id = request.GET.get('village_id')
    
    if village_id:
        try:
            village = Village.objects.get(pk=village_id)
            if village.traditional_council:
                ward_committees = WardCommittee.objects.filter(
                    traditional_councils=village.traditional_council,
                    is_active=True
                ).values('id', 'name', 'ward_number')
                
                data = list(ward_committees)
            else:
                data = []
        except Village.DoesNotExist:
            data = []
    else:
        data = []
    
    return JsonResponse(data, safe=False)

@login_required
def get_households_by_village(request):
    """AJAX endpoint to get households for a village"""
    
    village_id = request.GET.get('village_id')
    
    if village_id:
        households = Household.objects.filter(
            village_id=village_id,
            is_active=True
        ).values('id', 'household_id')
        
        data = list(households)
    else:
        data = []
    
    return JsonResponse(data, safe=False)

@login_required
def validate_id_number(request):
    """AJAX endpoint to validate SA ID number"""
    
    id_number = request.GET.get('id_number', '').strip()
    
    if not id_number:
        return JsonResponse({'valid': False, 'message': 'ID number is required'})
    
    if len(id_number) != 13 or not id_number.isdigit():
        return JsonResponse({'valid': False, 'message': 'ID number must be 13 digits'})
    
    # Check if ID already exists
    if Resident.objects.filter(id_number=id_number).exists():
        return JsonResponse({'valid': False, 'message': 'This ID number is already registered'})
    
    # Extract date of birth and gender
    try:
        year_part = int(id_number[:2])
        month = int(id_number[2:4])
        day = int(id_number[4:6])
        gender_digit = int(id_number[6])
        
        # Determine year
        current_year = date.today().year
        if year_part <= (current_year % 100):
            year = 2000 + year_part
        else:
            year = 1900 + year_part
        
        # Validate date
        dob = date(year, month, day)
        gender = 'M' if gender_digit >= 5 else 'F'
        
        return JsonResponse({
            'valid': True,
            'date_of_birth': dob.isoformat(),
            'gender': gender,
            'message': 'Valid ID number'
        })
        
    except (ValueError, TypeError):
        return JsonResponse({'valid': False, 'message': 'Invalid ID number format'})