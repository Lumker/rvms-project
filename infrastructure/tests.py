from django.test import TestCase, Client
from django.urls import reverse
from unittest import mock
from io import BytesIO
import csv

from .models import Village
from governance.models import TraditionalCouncil, Municipality, District
from .views import export_water_coverage_excel, export_water_coverage_csv, export_water_coverage_pdf

class ExportWaterCoverageTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create related models for foreign keys
        self.district = District.objects.create(name="Test District")
        self.municipality = Municipality.objects.create(name="Test Municipality", district=self.district)
        self.traditional_council = TraditionalCouncil.objects.create(name="Test Council", municipality=self.municipality)
        # Create sample village data for testing
        self.village = Village.objects.create(
            name="Test Village",
            traditional_council=self.traditional_council,
            population=100,
            is_active=True
        )
        # Set additional attributes for export functions
        self.village.total_population = 100
        self.village.total_households = 50
        self.village.households_with_water = 40
        self.village.water_coverage_percentage = 80.0
        self.village.water_infrastructure_count = 5

        self.villages = [self.village]

    def test_export_water_coverage_csv(self):
        response = export_water_coverage_csv(self.villages)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        content = response.content.decode('utf-8')
        self.assertIn('Village,Traditional Council,Municipality,District', content)
        self.assertIn('Test Village', content)

    def test_export_water_coverage_excel_with_openpyxl(self):
        # Test Excel export when openpyxl is available
        response = export_water_coverage_excel(self.villages)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertIn('attachment; filename="water_coverage_report.xlsx"', response['Content-Disposition'])
        self.assertTrue(len(response.content) > 0)

    @mock.patch('infrastructure.views.openpyxl', side_effect=ImportError)
    def test_export_water_coverage_excel_fallback_csv(self, mock_openpyxl):
        # Test fallback to CSV when openpyxl is not installed
        response = export_water_coverage_excel(self.villages)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        content = response.content.decode('utf-8')
        self.assertIn('Error: Excel export requires openpyxl', content)

    def test_export_water_coverage_pdf_with_reportlab(self):
        # Test PDF export when reportlab is available
        # We mock reportlab imports to simulate presence
        with mock.patch('infrastructure.views.SimpleDocTemplate'), \
             mock.patch('infrastructure.views.Table'), \
             mock.patch('infrastructure.views.Paragraph'), \
             mock.patch('infrastructure.views.Spacer'), \
             mock.patch('infrastructure.views.getSampleStyleSheet'), \
             mock.patch('infrastructure.views.ParagraphStyle'):
            response = export_water_coverage_pdf(self.villages, {
                'total_villages': 1,
                'villages_with_water': 1,
                'villages_without_water': 0,
                'total_population': 100,
                'average_coverage': 80.0,
                'report_date': None,
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')
            self.assertIn('attachment; filename="water_coverage_report.pdf"', response['Content-Disposition'])

    @mock.patch('infrastructure.views.reportlab', side_effect=ImportError)
    def test_export_water_coverage_pdf_fallback_html(self, mock_reportlab):
        # Test fallback to HTML error message when reportlab is not installed
        response = export_water_coverage_pdf(self.villages, {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/html')
        self.assertIn('PDF export requires reportlab', response.content.decode('utf-8'))

    def test_water_coverage_report_view_csv(self):
        url = reverse('infrastructure:water_coverage_report')
        response = self.client.get(url, {'export': 'csv'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_water_coverage_report_view_excel(self):
        url = reverse('infrastructure:water_coverage_report')
        response = self.client.get(url, {'export': 'excel'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(response['Content-Type'], [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/csv'  # fallback if openpyxl missing
        ])

    def test_water_coverage_report_view_pdf(self):
        url = reverse('infrastructure:water_coverage_report')
        response = self.client.get(url, {'export': 'pdf'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(response['Content-Type'], ['application/pdf', 'text/html'])  # html fallback if reportlab missing

