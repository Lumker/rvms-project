# type: ignore
# from reportlab.lib.pagesizes import letter, A4  # type: ignore
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle  # type: ignore

import os
from django.conf import settings
from django.utils import timezone
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from datetime import datetime
import uuid

class NumberedCanvas(canvas.Canvas):
    """Custom canvas to add page numbers and headers/footers"""
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for (page_num, page_state) in enumerate(self._saved_page_states):
            self.__dict__.update(page_state)
            self.draw_page_number(page_num + 1, num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_num, total_pages):
        self.setFont("Helvetica", 9)
        self.drawRightString(
            A4[0] - 1*cm, 1*cm,
            f"Page {page_num} of {total_pages}"
        )

def create_letterhead(canvas, doc):
    """Create a letterhead for the document"""
    canvas.saveState()
    
    # Header
    canvas.setFont('Helvetica-Bold', 16)
    canvas.drawCentredText(A4[0]/2, A4[1] - 2*cm, "RURAL VILLAGE MANAGEMENT SYSTEM")
    
    canvas.setFont('Helvetica', 12)
    canvas.drawCentredText(A4[0]/2, A4[1] - 2.5*cm, "Traditional Council Administration")
    
    # Line under header
    canvas.setStrokeColor(colors.black)
    canvas.setLineWidth(1)
    canvas.line(2*cm, A4[1] - 3*cm, A4[0] - 2*cm, A4[1] - 3*cm)
    
    canvas.restoreState()

def generate_proof_document(proof_of_residence):
    """Generate PDF document for proof of residence"""
    
    # Create filename
    filename = f"{proof_of_residence.document_number}.pdf"
    filepath = os.path.join(settings.MEDIA_ROOT, 'documents', 'generated', filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Create PDF with custom canvas
    doc = SimpleDocTemplate(
        filepath, 
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=4*cm,
        bottomMargin=2*cm
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=12,
        alignment=TA_LEFT,
        textColor=colors.darkblue,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )
    
    # Title
    story.append(Paragraph("CERTIFICATE OF RESIDENCE", title_style))
    story.append(Spacer(1, 20))
    
    # Document number in a colored box
    doc_num_data = [[f"Document Number: {proof_of_residence.document_number}"]]
    doc_num_table = Table(doc_num_data, colWidths=[6*inch])
    doc_num_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.darkblue),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 1, colors.darkblue),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(doc_num_table)
    story.append(Spacer(1, 30))
    
    # Certificate content
    story.append(Paragraph("TO WHOM IT MAY CONCERN", heading_style))
    
    content = f"""
    This is to certify that <b>{proof_of_residence.resident.full_name}</b> 
    {f'(ID Number: {proof_of_residence.resident.id_number})' if proof_of_residence.resident.id_number else ''} 
    is a bona fide resident of <b>{proof_of_residence.village.name}</b> Village, 
    <b>{proof_of_residence.village.municipality.name}</b> Municipality, 
    <b>{proof_of_residence.village.municipality.district.name}</b> District, 
    <b>{proof_of_residence.village.municipality.district.province.name}</b> Province, 
    Republic of South Africa.
    """
    
    story.append(Paragraph(content, normal_style))
    story.append(Spacer(1, 20))
    
    # Resident details table
    story.append(Paragraph("RESIDENT DETAILS", heading_style))
    
    resident_data = [
        ['Full Name:', proof_of_residence.resident.full_name],
        ['ID Number:', proof_of_residence.resident.id_number or 'N/A'],
        ['Date of Birth:', proof_of_residence.resident.date_of_birth.strftime('%d %B %Y') if proof_of_residence.resident.date_of_birth else 'N/A'],
        ['Gender:', proof_of_residence.resident.get_gender_display() if hasattr(proof_of_residence.resident, 'get_gender_display') else 'N/A'],
        ['Contact Number:', proof_of_residence.resident.phone_number or 'N/A'],
    ]
    
    resident_table = Table(resident_data, colWidths=[2*inch, 4*inch])
    resident_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(resident_table)
    story.append(Spacer(1, 20))
    
    # Address details
    story.append(Paragraph("RESIDENTIAL ADDRESS", heading_style))
    
    address_data = [
        ['Street Address:', proof_of_residence.household.address],
        ['Village:', proof_of_residence.village.name],
        ['Municipality:', proof_of_residence.village.municipality.name],
        ['District:', proof_of_residence.village.municipality.district.name],
        ['Province:', proof_of_residence.village.municipality.district.province.name],
        ['Country:', 'South Africa'],
    ]
    
    address_table = Table(address_data, colWidths=[2*inch, 4*inch])
    address_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(address_table)
    story.append(Spacer(1, 20))
    
    # Purpose
    story.append(Paragraph("PURPOSE", heading_style))
    purpose_text = f"This certificate is issued for the purpose of: <b>{proof_of_residence.purpose}</b>"
    story.append(Paragraph(purpose_text, normal_style))
    story.append(Spacer(1, 20))
    
    # Validity information
    if proof_of_residence.valid_from and proof_of_residence.valid_until:
        story.append(Paragraph("VALIDITY PERIOD", heading_style))
        validity = f"This certificate is valid from <b>{proof_of_residence.valid_from.strftime('%d %B %Y')}</b> to <b>{proof_of_residence.valid_until.strftime('%d %B %Y')}</b>"
        story.append(Paragraph(validity, normal_style))
        story.append(Spacer(1, 30))
    else:
        story.append(Spacer(1, 30))
    
    # Certificate footer
    issued_date = proof_of_residence.approved_at or timezone.now()
    footer_text = f"This certificate was issued on <b>{issued_date.strftime('%d %B %Y')}</b> by the Traditional Council Administration."
    story.append(Paragraph(footer_text, normal_style))
    story.append(Spacer(1, 40))
    
    # Signature section
    signature_data = [
        ['', '', ''],
        ['ISSUED BY:', '', 'DATE OF ISSUE:'],
        ['', '', ''],
        [f'{proof_of_residence.approved_by.get_full_name() if proof_of_residence.approved_by else "Traditional Council"}', '', issued_date.strftime('%d %B %Y')],
        ['', '', ''],
        ['', '', ''],
        ['_________________________', '', '_________________________'],
        ['Authorized Signature', '', 'Official Stamp'],
    ]
    
    signature_table = Table(signature_data, colWidths=[2.5*inch, 1*inch, 2.5*inch])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 1), (2, 1), 'Helvetica-Bold'),
        ('FONTNAME', (0, 7), (2, 7), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    
    story.append(signature_table)
    
    # Add disclaimer
    story.append(Spacer(1, 30))
    disclaimer = """
    <i>Note: This certificate is issued based on the records maintained by the Traditional Council. 
    Any queries regarding the authenticity of this document should be directed to the issuing authority.</i>
    """
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.grey,
        fontName='Helvetica-Oblique'
    )
    story.append(Paragraph(disclaimer, disclaimer_style))
    
    # Build PDF with custom canvas
    doc.build(story, onFirstPage=create_letterhead, onLaterPages=create_letterhead, canvasmaker=NumberedCanvas)
    
    return os.path.join('documents', 'generated', filename)

def generate_batch_report(batch_process):
    """Generate a batch processing report"""
    filename = f"batch_report_{batch_process.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(settings.MEDIA_ROOT, 'documents', 'reports', filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    story.append(Paragraph("BATCH PROCESSING REPORT", title_style))
    story.append(Spacer(1, 20))
    
    # Batch details
    batch_data = [
        ['Batch Name:', batch_process.name],
        ['Description:', batch_process.description or 'N/A'],
        ['Created By:', batch_process.created_by.get_full_name() if batch_process.created_by else 'N/A'],
        ['Created Date:', batch_process.created_at.strftime('%d %B %Y, %H:%M')],
        ['Status:', batch_process.get_status_display()],
        ['Total Documents:', str(batch_process.total_documents)],
        ['Processed:', str(batch_process.processed_documents)],
        ['Failed:', str(batch_process.failed_documents)],
        ['Success Rate:', f"{batch_process.progress_percentage}%"],
    ]
    
    batch_table = Table(batch_data, colWidths=[2*inch, 4*inch])
    batch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(batch_table)
    story.append(Spacer(1, 30))
    
    # Items details
    if batch_process.items.exists():
        story.append(Paragraph("BATCH ITEMS DETAILS", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        items_data = [['Document Number', 'Resident Name', 'Village', 'Status', 'Processed Date']]
        
        for item in batch_process.items.select_related('document__resident', 'document__village'):
            items_data.append([
                item.document.document_number,
                item.document.resident.full_name,
                item.document.village.name,
                item.get_status_display(),
                item.processed_at.strftime('%d/%m/%Y %H:%M') if item.processed_at else 'N/A'
            ])
        
        items_table = Table(items_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1*inch, 1.5*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(items_table)
    
    doc.build(story, canvasmaker=NumberedCanvas)
    return os.path.join('documents', 'reports', filename)

def generate_monthly_report(year, month):
    """Generate monthly documents report"""
    from .models import ProofOfResidence
    from django.db.models import Count
    
    filename = f"monthly_report_{year}_{month:02d}.pdf"
    filepath = os.path.join(settings.MEDIA_ROOT, 'documents', 'reports', filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Get data
    documents = ProofOfResidence.objects.filter(
        requested_at__year=year,
        requested_at__month=month
    )
    
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    
    title = f"MONTHLY DOCUMENTS REPORT - {month_names[month]} {year}"
    story.append(Paragraph(title, styles['Title']))
    story.append(Spacer(1, 30))
    
    # Summary statistics
    total_docs = documents.count()
    by_status = documents.values('status').annotate(count=Count('id'))
    by_village = documents.values('village__name').annotate(count=Count('id')).order_by('-count')[:10]
    
    # Summary table
    summary_data = [
        ['Total Documents:', str(total_docs)],
    ]
    
    for status_item in by_status:
        summary_data.append([f"{status_item['status'].title()} Documents:", str(status_item['count'])])
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    
    story.append(Paragraph("SUMMARY", styles['Heading2']))
    story.append(summary_table)
    story.append(Spacer(1, 30))
    
    # Top villages
    if by_village:
        story.append(Paragraph("TOP VILLAGES BY DOCUMENT REQUESTS", styles['Heading2']))
        village_data = [['Village', 'Number of Documents']]
        
        for village_item in by_village:
            village_data.append([village_item['village__name'], str(village_item['count'])])
        
        village_table = Table(village_data, colWidths=[4*inch, 2*inch])
        village_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(village_table)
    
    doc.build(story, canvasmaker=NumberedCanvas)
    return os.path.join('documents', 'reports', filename)