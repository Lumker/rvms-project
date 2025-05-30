# Generated by Django 4.2.10 on 2025-05-24 22:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('governance', '0004_communityissue_municipalinteraction_and_more'),
        ('households', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='InfrastructureAsset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('asset_id', models.CharField(editable=False, max_length=20, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('category', models.CharField(choices=[('water', 'Water Infrastructure'), ('electricity', 'Electricity Infrastructure'), ('roads', 'Roads & Transport'), ('health', 'Health Facilities'), ('education', 'Education Facilities'), ('communication', 'Communication Infrastructure'), ('sanitation', 'Sanitation Infrastructure'), ('community', 'Community Facilities')], max_length=20)),
                ('description', models.TextField(blank=True)),
                ('gps_coordinates', models.CharField(blank=True, help_text='Format: -26.1234, 28.5678', max_length=50)),
                ('physical_address', models.TextField()),
                ('condition', models.CharField(choices=[('excellent', 'Excellent'), ('good', 'Good'), ('fair', 'Fair'), ('poor', 'Poor'), ('critical', 'Critical'), ('non_functional', 'Non-Functional')], default='good', max_length=20)),
                ('operational_status', models.BooleanField(default=True, help_text='Is the asset currently operational?')),
                ('last_inspection_date', models.DateField(blank=True, null=True)),
                ('next_inspection_due', models.DateField(blank=True, null=True)),
                ('ownership_type', models.CharField(choices=[('government', 'Government'), ('municipality', 'Municipality'), ('community', 'Community'), ('private', 'Private'), ('ngo', 'NGO/Non-Profit'), ('traditional', 'Traditional Authority')], default='government', max_length=20)),
                ('owner_details', models.TextField(blank=True)),
                ('estimated_value', models.DecimalField(blank=True, decimal_places=2, help_text='Estimated replacement value in ZAR', max_digits=12, null=True)),
                ('annual_maintenance_cost', models.DecimalField(blank=True, decimal_places=2, help_text='Annual maintenance budget in ZAR', max_digits=10, null=True)),
                ('installation_date', models.DateField(blank=True, null=True)),
                ('expected_lifespan_years', models.PositiveIntegerField(blank=True, null=True)),
                ('contractor', models.CharField(blank=True, max_length=200)),
                ('warranty_expiry', models.DateField(blank=True, null=True)),
                ('asset_photo', models.ImageField(blank=True, null=True, upload_to='infrastructure/assets/')),
                ('technical_documents', models.FileField(blank=True, null=True, upload_to='infrastructure/documents/')),
                ('custodian', models.ForeignKey(blank=True, help_text='Person responsible for asset maintenance', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='custodian_assets', to=settings.AUTH_USER_MODEL)),
                ('village', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='infrastructure_assets', to='governance.village')),
                ('ward_committee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='governance.wardcommittee')),
            ],
            options={
                'verbose_name': 'Infrastructure Asset',
                'verbose_name_plural': 'Infrastructure Assets',
                'ordering': ['village__name', 'category', 'name'],
            },
        ),
        migrations.CreateModel(
            name='WaterSource',
            fields=[
                ('infrastructureasset_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='infrastructure.infrastructureasset')),
                ('source_type', models.CharField(choices=[('borehole', 'Borehole'), ('spring', 'Natural Spring'), ('river', 'River/Stream'), ('dam', 'Dam/Reservoir'), ('rainwater', 'Rainwater Harvesting'), ('municipal', 'Municipal Supply'), ('other', 'Other')], max_length=20)),
                ('water_quality', models.CharField(choices=[('excellent', 'Excellent'), ('good', 'Good'), ('acceptable', 'Acceptable'), ('poor', 'Poor'), ('contaminated', 'Contaminated')], default='good', max_length=20)),
                ('daily_capacity_litres', models.PositiveIntegerField(blank=True, help_text='Daily water production capacity in litres', null=True)),
                ('depth_meters', models.DecimalField(blank=True, decimal_places=2, help_text='Depth in meters (for boreholes)', max_digits=6, null=True)),
                ('yield_litres_per_hour', models.PositiveIntegerField(blank=True, help_text='Water yield per hour', null=True)),
                ('last_water_test_date', models.DateField(blank=True, null=True)),
                ('water_test_results', models.TextField(blank=True, help_text='Latest water quality test results')),
                ('pump_type', models.CharField(blank=True, max_length=100)),
                ('power_source', models.CharField(blank=True, choices=[('electric', 'Electric Grid'), ('solar', 'Solar Power'), ('generator', 'Generator'), ('hand_pump', 'Hand Pump'), ('wind', 'Wind Power'), ('gravity', 'Gravity Fed')], max_length=50)),
            ],
            options={
                'verbose_name': 'Water Source',
                'verbose_name_plural': 'Water Sources',
            },
            bases=('infrastructure.infrastructureasset',),
        ),
        migrations.CreateModel(
            name='ServiceInterruption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('interruption_type', models.CharField(choices=[('planned', 'Planned Maintenance'), ('unplanned', 'Unplanned Outage'), ('emergency', 'Emergency Shutdown'), ('shortage', 'Resource Shortage'), ('equipment_failure', 'Equipment Failure'), ('power_outage', 'Power Outage'), ('weather', 'Weather Related')], max_length=20)),
                ('severity', models.CharField(choices=[('low', 'Low Impact'), ('medium', 'Medium Impact'), ('high', 'High Impact'), ('critical', 'Critical')], max_length=10)),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('estimated_restoration', models.DateTimeField(blank=True, null=True)),
                ('estimated_affected_people', models.PositiveIntegerField(default=0)),
                ('cause', models.TextField(help_text='Cause of interruption')),
                ('description', models.TextField(help_text='Detailed description')),
                ('resolution_actions', models.TextField(blank=True)),
                ('communities_notified', models.BooleanField(default=False)),
                ('notification_method', models.CharField(blank=True, help_text='How communities were notified', max_length=100)),
                ('is_resolved', models.BooleanField(default=False)),
                ('resolution_date', models.DateTimeField(blank=True, null=True)),
                ('lessons_learned', models.TextField(blank=True)),
                ('affected_households', models.ManyToManyField(blank=True, related_name='service_interruptions', to='households.household')),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_interruptions', to='infrastructure.infrastructureasset')),
            ],
            options={
                'verbose_name': 'Service Interruption',
                'verbose_name_plural': 'Service Interruptions',
                'ordering': ['-start_time'],
            },
        ),
        migrations.CreateModel(
            name='MaintenanceRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('maintenance_type', models.CharField(choices=[('preventive', 'Preventive Maintenance'), ('corrective', 'Corrective Maintenance'), ('emergency', 'Emergency Repair'), ('upgrade', 'Upgrade/Improvement'), ('inspection', 'Inspection'), ('cleaning', 'Cleaning')], max_length=20)),
                ('status', models.CharField(choices=[('scheduled', 'Scheduled'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('deferred', 'Deferred')], default='scheduled', max_length=20)),
                ('scheduled_date', models.DateField()),
                ('completed_date', models.DateField(blank=True, null=True)),
                ('estimated_duration_hours', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('actual_duration_hours', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('contractor', models.CharField(blank=True, max_length=200)),
                ('description', models.TextField(help_text='Description of maintenance work')),
                ('work_performed', models.TextField(blank=True, help_text='Actual work performed')),
                ('parts_used', models.TextField(blank=True, help_text='Parts and materials used')),
                ('estimated_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('actual_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('next_maintenance_due', models.DateField(blank=True, null=True)),
                ('recommendations', models.TextField(blank=True)),
                ('condition_before', models.CharField(blank=True, choices=[('excellent', 'Excellent'), ('good', 'Good'), ('fair', 'Fair'), ('poor', 'Poor'), ('critical', 'Critical'), ('non_functional', 'Non-Functional')], max_length=20)),
                ('condition_after', models.CharField(blank=True, choices=[('excellent', 'Excellent'), ('good', 'Good'), ('fair', 'Fair'), ('poor', 'Poor'), ('critical', 'Critical'), ('non_functional', 'Non-Functional')], max_length=20)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maintenance_records', to='infrastructure.infrastructureasset')),
                ('technician', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='maintenance_performed', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Maintenance Record',
                'verbose_name_plural': 'Maintenance Records',
                'ordering': ['-scheduled_date'],
            },
        ),
        migrations.CreateModel(
            name='AssetInspection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('inspection_type', models.CharField(choices=[('routine', 'Routine Inspection'), ('safety', 'Safety Inspection'), ('compliance', 'Compliance Check'), ('damage_assessment', 'Damage Assessment'), ('pre_maintenance', 'Pre-Maintenance'), ('post_maintenance', 'Post-Maintenance')], max_length=20)),
                ('inspection_date', models.DateField()),
                ('overall_condition', models.CharField(choices=[('excellent', 'Excellent'), ('good', 'Good'), ('fair', 'Fair'), ('poor', 'Poor'), ('critical', 'Critical'), ('non_functional', 'Non-Functional')], max_length=20)),
                ('operational_status', models.BooleanField()),
                ('safety_concerns', models.TextField(blank=True)),
                ('structural_condition', models.CharField(blank=True, choices=[('excellent', 'Excellent'), ('good', 'Good'), ('fair', 'Fair'), ('poor', 'Poor'), ('critical', 'Critical'), ('non_functional', 'Non-Functional')], max_length=20)),
                ('electrical_condition', models.CharField(blank=True, choices=[('excellent', 'Excellent'), ('good', 'Good'), ('fair', 'Fair'), ('poor', 'Poor'), ('critical', 'Critical'), ('non_functional', 'Non-Functional')], max_length=20)),
                ('mechanical_condition', models.CharField(blank=True, choices=[('excellent', 'Excellent'), ('good', 'Good'), ('fair', 'Fair'), ('poor', 'Poor'), ('critical', 'Critical'), ('non_functional', 'Non-Functional')], max_length=20)),
                ('immediate_actions_required', models.TextField(blank=True)),
                ('maintenance_recommendations', models.TextField(blank=True)),
                ('upgrade_recommendations', models.TextField(blank=True)),
                ('next_inspection_date', models.DateField(blank=True, null=True)),
                ('priority_level', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], default='medium', max_length=10)),
                ('inspection_photos', models.ImageField(blank=True, null=True, upload_to='infrastructure/inspections/')),
                ('inspection_report', models.FileField(blank=True, null=True, upload_to='infrastructure/reports/')),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inspections', to='infrastructure.infrastructureasset')),
                ('inspector', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inspections_performed', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Asset Inspection',
                'verbose_name_plural': 'Asset Inspections',
                'ordering': ['-inspection_date'],
            },
        ),
        migrations.CreateModel(
            name='WaterDistributionPoint',
            fields=[
                ('infrastructureasset_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='infrastructure.infrastructureasset')),
                ('distribution_type', models.CharField(choices=[('communal_tap', 'Communal Tap'), ('household_tap', 'Household Tap'), ('water_tank', 'Water Tank'), ('water_kiosk', 'Water Kiosk'), ('standpipe', 'Standpipe'), ('tanker_point', 'Water Tanker Point')], max_length=20)),
                ('estimated_users', models.PositiveIntegerField(default=0, help_text='Estimated number of people using this point')),
                ('distance_from_source_meters', models.PositiveIntegerField(blank=True, help_text='Distance from water source in meters', null=True)),
                ('storage_capacity_litres', models.PositiveIntegerField(blank=True, help_text='Storage capacity for tanks', null=True)),
                ('has_meter', models.BooleanField(default=False)),
                ('meter_reading_date', models.DateField(blank=True, null=True)),
                ('last_meter_reading', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('operates_24_7', models.BooleanField(default=True)),
                ('operating_hours', models.CharField(blank=True, help_text='Operating hours if not 24/7', max_length=100)),
                ('households_served', models.ManyToManyField(blank=True, related_name='water_distribution_points', to='households.household')),
                ('water_source', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='distribution_points', to='infrastructure.watersource')),
            ],
            options={
                'verbose_name': 'Water Distribution Point',
                'verbose_name_plural': 'Water Distribution Points',
            },
            bases=('infrastructure.infrastructureasset',),
        ),
    ]
