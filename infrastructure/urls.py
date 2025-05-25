# infrastructure/urls.py (updated)

from django.urls import path
from . import views

app_name = 'infrastructure'

urlpatterns = [
    # Dashboard
    path('', views.infrastructure_dashboard, name='dashboard'),
    
    # Infrastructure Assets
    path('assets/', views.InfrastructureAssetListView.as_view(), name='asset_list'),
    path('assets/<int:pk>/', views.InfrastructureAssetDetailView.as_view(), name='asset_detail'),
    path('assets/create/', views.InfrastructureAssetCreateView.as_view(), name='asset_create'),
    path('assets/<int:pk>/update/', views.InfrastructureAssetUpdateView.as_view(), name='asset_update'),
    
    # Water Infrastructure
    path('water/sources/', views.WaterSourceListView.as_view(), name='water_source_list'),
    path('water/sources/<int:pk>/', views.WaterSourceDetailView.as_view(), name='water_source_detail'),
    path('water/sources/create/', views.WaterSourceCreateView.as_view(), name='water_source_create'),
    path('water/sources/<int:pk>/update/', views.WaterSourceUpdateView.as_view(), name='water_source_update'),
    
    path('water/distribution/', views.WaterDistributionPointListView.as_view(), name='water_distribution_list'),
    path('water/distribution/<int:pk>/', views.WaterDistributionPointDetailView.as_view(), name='water_distribution_detail'),
    path('water/distribution/create/', views.WaterDistributionPointCreateView.as_view(), name='water_distribution_create'),
    path('water/distribution/<int:pk>/update/', views.WaterDistributionPointUpdateView.as_view(), name='water_distribution_update'),
    
    # Maintenance
    path('maintenance/', views.MaintenanceRecordListView.as_view(), name='maintenance_list'),
    path('maintenance/<int:pk>/', views.MaintenanceRecordDetailView.as_view(), name='maintenance_detail'),
    path('maintenance/create/', views.MaintenanceRecordCreateView.as_view(), name='maintenance_create'),
    path('maintenance/<int:pk>/update/', views.MaintenanceRecordUpdateView.as_view(), name='maintenance_update'),
    path('maintenance/bulk/', views.BulkMaintenanceView.as_view(), name='bulk_maintenance'),
    
    # Service Interruptions
    path('interruptions/', views.ServiceInterruptionListView.as_view(), name='interruption_list'),
    path('interruptions/<int:pk>/', views.ServiceInterruptionDetailView.as_view(), name='interruption_detail'),
    path('interruptions/create/', views.ServiceInterruptionCreateView.as_view(), name='interruption_create'),
    path('interruptions/<int:pk>/update/', views.ServiceInterruptionUpdateView.as_view(), name='interruption_update'),
    path('interruptions/<int:pk>/resolve/', views.mark_interruption_resolved, name='interruption_resolve'),
    
    # Inspections
    path('inspections/', views.AssetInspectionListView.as_view(), name='inspection_list'),
    path('inspections/<int:pk>/', views.AssetInspectionDetailView.as_view(), name='inspection_detail'),
    path('inspections/create/', views.AssetInspectionCreateView.as_view(), name='inspection_create'),
    path('inspections/<int:pk>/update/', views.AssetInspectionUpdateView.as_view(), name='inspection_update'),
    
    # Analytics & Reports
    path('analytics/', views.infrastructure_analytics, name='analytics'),
    path('reports/maintenance/', views.maintenance_report, name='maintenance_report'),
    path('reports/water-coverage/', views.water_coverage_report, name='water_coverage_report'),
    path('reports/asset-condition/', views.asset_condition_report, name='asset_condition_report'),
    
    # Quick Actions
    path('assets/<int:asset_id>/schedule-maintenance/', views.schedule_maintenance, name='schedule_maintenance'),
    path('assets/<int:pk>/quick-inspection/', views.QuickInspectionView.as_view(), name='quick_inspection'),
    
    # AJAX endpoints
    path('ajax/water-sources/', views.get_water_sources_by_village, name='get_water_sources_by_village'),
    path('ajax/distribution-points/', views.get_distribution_points_by_source, name='get_distribution_points_by_source'),
    path('ajax/assets-by-category/', views.get_assets_by_category, name='get_assets_by_category'),
    path('ajax/maintenance-calendar/', views.maintenance_calendar_data, name='maintenance_calendar_data'),
    path('ajax/dashboard-alerts/', views.dashboard_alerts, name='dashboard_alerts'),
    
    # Export endpoints
    # path('export/assets/', views.export_assets, name='export_assets'),
    path('export/maintenance/', views.export_maintenance_records, name='export_maintenance'),
    path('export/water-sources/', views.export_water_sources, name='export_water_sources'),
    
    
    path('debug/relationships/', views.debug_relationships, name='debug_relationships'),
]