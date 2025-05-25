from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # Dashboard
    path('', views.DocumentDashboardView.as_view(), name='dashboard'),
    
    # Proof of Residence
    path('proof-of-residence/', views.ProofOfResidenceListView.as_view(), name='proof_list'),
    path('proof-of-residence/new/', views.ProofOfResidenceCreateView.as_view(), name='proof_create'),
    path('proof-of-residence/<int:pk>/', views.ProofOfResidenceDetailView.as_view(), name='proof_detail'),
    path('proof-of-residence/<int:pk>/edit/', views.ProofOfResidenceUpdateView.as_view(), name='proof_update'),
    path('proof-of-residence/<int:pk>/approve/', views.approve_proof_of_residence, name='proof_approve'),
    path('proof-of-residence/<int:pk>/generate/', views.generate_proof_of_residence, name='proof_generate'),
    path('proof-of-residence/<int:pk>/deliver/', views.deliver_proof_of_residence, name='proof_deliver'),
    path('proof-of-residence/<int:pk>/download/', views.download_proof_of_residence, name='proof_download'),
    
    # Document Templates
    path('templates/', views.DocumentTemplateListView.as_view(), name='template_list'),
    path('templates/new/', views.DocumentTemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/', views.DocumentTemplateDetailView.as_view(), name='template_detail'),
    path('templates/<int:pk>/edit/', views.DocumentTemplateUpdateView.as_view(), name='template_update'),
    
    # Batch Processing
    path('batches/', views.BatchProcessListView.as_view(), name='batch_list'),
    path('batches/new/', views.BatchProcessCreateView.as_view(), name='batch_create'),
    path('batches/<int:pk>/', views.BatchProcessDetailView.as_view(), name='batch_detail'),
    path('batches/<int:pk>/process/', views.process_batch, name='batch_process'),
    
    # Reports
    path('reports/batch/<int:pk>/', views.download_batch_report, name='batch_report'),
    path('reports/monthly/', views.monthly_report, name='monthly_report'),
    path('reports/generate/', views.generate_report, name='generate_report'),
    
    # API endpoints for AJAX
    path('api/residents/<int:village_id>/', views.get_residents_by_village, name='api_residents_by_village'),
    path('api/households/<int:village_id>/', views.get_households_by_village, name='api_households_by_village'),
]