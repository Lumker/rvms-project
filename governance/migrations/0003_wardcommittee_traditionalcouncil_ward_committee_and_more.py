# Generated by Django 4.2.10 on 2025-05-23 10:38

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('governance', '0002_enhance_municipality_council_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='WardCommittee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('ward_number', models.CharField(max_length=20)),
                ('ward_code', models.CharField(max_length=20, unique=True, validators=[django.core.validators.RegexValidator(message='Ward code must be in format: WRD123 or WRD1234', regex='^WRD\\d{3,4}$')])),
                ('ward_councillor', models.CharField(blank=True, max_length=100)),
                ('councillor_contact', models.TextField(blank=True)),
                ('geographic_boundaries', models.TextField()),
                ('population', models.PositiveIntegerField(blank=True, null=True)),
                ('committee_secretary', models.CharField(blank=True, max_length=100)),
                ('meeting_venue', models.CharField(blank=True, max_length=255)),
                ('established_date', models.DateField()),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('dissolved', 'Dissolved'), ('forming', 'Forming')], default='active', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('municipality', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ward_committees', to='governance.municipality')),
            ],
            options={
                'verbose_name_plural': 'Ward Committees',
                'ordering': ['ward_number', 'name'],
                'unique_together': {('municipality', 'ward_number')},
            },
        ),
        migrations.AddField(
            model_name='traditionalcouncil',
            name='ward_committee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='traditional_councils', to='governance.wardcommittee'),
        ),
        migrations.CreateModel(
            name='WardCommitteeMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('role', models.CharField(choices=[('chairperson', 'Chairperson'), ('deputy_chairperson', 'Deputy Chairperson'), ('secretary', 'Secretary'), ('treasurer', 'Treasurer'), ('member', 'Member'), ('youth_rep', 'Youth Representative'), ('women_rep', 'Women Representative'), ('disability_rep', 'Disability Representative')], max_length=50)),
                ('appointed_date', models.DateField()),
                ('term_end_date', models.DateField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ward_committee_roles', to=settings.AUTH_USER_MODEL)),
                ('ward_committee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='committee_members', to='governance.wardcommittee')),
            ],
            options={
                'ordering': ['ward_committee__ward_number', 'role'],
                'unique_together': {('ward_committee', 'user', 'role')},
            },
        ),
    ]
