from django.urls import path
from . import views

app_name = 'households'

urlpatterns = [
    # Dashboard
    path('', views.households_dashboard, name='dashboard'),
    
    # Households
    path('households/', views.household_list, name='household_list'),
    path('households/create/', views.household_create, name='household_create'),
    path('households/<int:pk>/', views.household_detail, name='household_detail'),
    path('households/<int:pk>/update/', views.household_update, name='household_update'),
    path('households/<int:pk>/delete/', views.household_delete, name='household_delete'),
    path('households/<int:pk>/verify/', views.household_verify, name='household_verify'),
    
    # Residents
    path('residents/', views.resident_list, name='resident_list'),
    path('residents/create/', views.resident_create, name='resident_create'),
    path('residents/<int:pk>/', views.resident_detail, name='resident_detail'),
    path('residents/<int:pk>/update/', views.resident_update, name='resident_update'),
    path('residents/<int:pk>/delete/', views.resident_delete, name='resident_delete'),
    path('residents/<int:pk>/create-user/', views.create_user_account, name='create_user_account'),
    
    # Household Services
    path('services/', views.household_service_list, name='service_list'),
    path('services/create/', views.household_service_create, name='service_create'),
    path('services/<int:pk>/update/', views.household_service_update, name='service_update'),
    path('services/<int:pk>/delete/', views.household_service_delete, name='service_delete'),
    
    # Reports
    path('reports/', views.household_reports, name='reports'),
    path('reports/demographics/', views.demographics_report, name='demographics_report'),
    path('reports/services/', views.services_report, name='services_report'),
    
    # AJAX endpoints
    path('ajax/ward-committees/', views.get_ward_committees_by_village, name='get_ward_committees_by_village'),
    path('ajax/households/', views.get_households_by_village, name='get_households_by_village'),
    path('ajax/validate-id/', views.validate_id_number, name='validate_id_number'),
]