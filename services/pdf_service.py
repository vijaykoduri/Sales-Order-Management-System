import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_invoice_pdf(invoice):
    """
    Generates a professional PDF document for an invoice.
    Returns a bytes buffer containing the PDF file.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=15
    )
    
    section_heading = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#2C3E50'),
        spaceBefore=10,
        spaceAfter=5
    )
    
    normal_text = ParagraphStyle(
        'InvoiceNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#333333')
    )
    
    bold_text = ParagraphStyle(
        'InvoiceBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#2C3E50')
    )
    
    right_normal = ParagraphStyle(
        'InvoiceRightNormal',
        parent=normal_text,
        alignment=2 # Right aligned
    )
    
    right_bold = ParagraphStyle(
        'InvoiceRightBold',
        parent=bold_text,
        alignment=2 # Right aligned
    )

    story = []
    
    # Header block: Logo/Company Name & Invoice Header
    header_data = [
        [
            Paragraph("<b>SALES MANAGEMENT SYSTEM</b><br/>123 Enterprise Way, Tech Park<br/>GSTIN: 29AAAAA0000A1Z5", normal_text),
            Paragraph("<b>INVOICE</b><br/>"
                      f"<b>Invoice #:</b> {invoice.invoice_number}<br/>"
                      f"<b>Date:</b> {invoice.invoice_date.strftime('%Y-%m-%d')}<br/>"
                      f"<b>Due Date:</b> {invoice.due_date.strftime('%Y-%m-%d')}<br/>"
                      f"<b>Status:</b> {invoice.payment_status}", right_normal)
        ]
    ]
    header_table = Table(header_data, colWidths=[300, 230])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))
    
    # Customer Details Block
    cust = invoice.order.customer
    customer_info = (
        f"<b>Name:</b> {cust.name}<br/>"
        f"<b>Company:</b> {cust.company or 'N/A'}<br/>"
        f"<b>Email:</b> {cust.email}<br/>"
        f"<b>Phone:</b> {cust.phone}<br/>"
        f"<b>GSTIN:</b> {cust.gst_number or 'N/A'}"
    )
    
    shipping_info = (
        f"<b>Billing / Shipping Address:</b><br/>"
        f"{cust.address or ''}<br/>"
        f"{cust.city or ''}, {cust.state or ''}<br/>"
        f"{cust.country or ''} - {cust.postal_code or ''}"
    )
    
    client_data = [
        [
            Paragraph("<b>Bill To:</b>", section_heading),
            Paragraph("<b>Ship To:</b>", section_heading)
        ],
        [
            Paragraph(customer_info, normal_text),
            Paragraph(shipping_info, normal_text)
        ]
    ]
    client_table = Table(client_data, colWidths=[265, 265])
    client_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(client_table)
    story.append(Spacer(1, 15))
    
    # Items Table
    # Table header
    table_data = [[
        Paragraph("<b>#</b>", bold_text),
        Paragraph("<b>Product / Service</b>", bold_text),
        Paragraph("<b>Qty</b>", bold_text),
        Paragraph("<b>Rate</b>", bold_text),
        Paragraph("<b>Disc</b>", bold_text),
        Paragraph("<b>GST</b>", bold_text),
        Paragraph("<b>Total</b>", right_bold)
    ]]
    
    # Fetch line items
    for idx, item in enumerate(invoice.order.items):
        table_data.append([
            Paragraph(str(idx + 1), normal_text),
            Paragraph(f"<b>{item.product.name}</b><br/>{item.product.description or ''}", normal_text),
            Paragraph(str(item.quantity), normal_text),
            Paragraph(f"${float(item.price):,.2f}", normal_text),
            Paragraph(f"${float(item.discount):,.2f}", normal_text),
            Paragraph(f"${float(item.gst):,.2f}", normal_text),
            Paragraph(f"${float(item.total):,.2f}", right_normal)
        ])
        
    items_table = Table(table_data, colWidths=[25, 215, 35, 60, 60, 60, 75])
    items_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8F9FA')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#2C3E50')),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.HexColor('#E9ECEF')),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 20))
    
    # Totals Summary
    summary_data = [
        [Paragraph("", normal_text), Paragraph("Subtotal:", bold_text), Paragraph(f"${float(invoice.order.subtotal):,.2f}", right_normal)],
        [Paragraph("", normal_text), Paragraph("Discount Amount:", bold_text), Paragraph(f"${float(invoice.order.discount_amount):,.2f}", right_normal)],
        [Paragraph("", normal_text), Paragraph("GST Amount:", bold_text), Paragraph(f"${float(invoice.order.gst_amount):,.2f}", right_normal)],
        [Paragraph("", normal_text), Paragraph("Shipping Charges:", bold_text), Paragraph(f"${float(invoice.order.shipping_charges):,.2f}", right_normal)],
        [Paragraph("", normal_text), Paragraph("<b>Grand Total:</b>", bold_text), Paragraph(f"<b>${float(invoice.grand_total):,.2f}</b>", right_bold)],
        [Paragraph("", normal_text), Paragraph("Paid Amount:", bold_text), Paragraph(f"${float(invoice.paid_amount):,.2f}", right_normal)],
        [Paragraph("", normal_text), Paragraph("Outstanding Amount:", bold_text), Paragraph(f"${float(invoice.outstanding_amount):,.2f}", right_bold)],
    ]
    summary_table = Table(summary_data, colWidths=[300, 120, 110])
    summary_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LINEABOVE', (1, 4), (2, 4), 1, colors.HexColor('#2C3E50')),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 40))
    
    # Signatures & terms
    notes_data = [
        [
            Paragraph("<b>Terms & Conditions:</b><br/>1. Goods once sold will not be taken back.<br/>2. Payment is due within 15 days.<br/>3. Interest @ 18% p.a. will be charged for delayed payments.", normal_text),
            Paragraph("<br/><br/>___________________________<br/><b>Authorized Signatory</b>", right_bold)
        ]
    ]
    notes_table = Table(notes_data, colWidths=[300, 230])
    notes_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
    ]))
    story.append(notes_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_quotation_pdf(quotation):
    """
    Generates a professional PDF document for a quotation.
    Returns a bytes buffer containing the PDF file.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    section_heading = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#2C3E50'),
        spaceBefore=10,
        spaceAfter=5
    )
    
    normal_text = ParagraphStyle(
        'QuoteNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#333333')
    )
    
    bold_text = ParagraphStyle(
        'QuoteBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#2C3E50')
    )
    
    right_normal = ParagraphStyle(
        'QuoteRightNormal',
        parent=normal_text,
        alignment=2
    )
    
    right_bold = ParagraphStyle(
        'QuoteRightBold',
        parent=bold_text,
        alignment=2
    )

    story = []
    
    # Header block
    header_data = [
        [
            Paragraph("<b>SALES MANAGEMENT SYSTEM</b><br/>123 Enterprise Way, Tech Park<br/>GSTIN: 29AAAAA0000A1Z5", normal_text),
            Paragraph("<b>QUOTATION</b><br/>"
                      f"<b>Quotation #:</b> {quotation.quotation_number}<br/>"
                      f"<b>Date:</b> {quotation.created_at.strftime('%Y-%m-%d') if quotation.created_at else datetime.utcnow().strftime('%Y-%m-%d')}<br/>"
                      f"<b>Status:</b> {quotation.status}", right_normal)
        ]
    ]
    header_table = Table(header_data, colWidths=[300, 230])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))
    
    # Customer Details Block
    cust = quotation.customer
    customer_info = (
        f"<b>Customer Name:</b> {cust.name}<br/>"
        f"<b>Company:</b> {cust.company or 'N/A'}<br/>"
        f"<b>Email:</b> {cust.email}<br/>"
        f"<b>Phone:</b> {cust.phone}<br/>"
        f"<b>GSTIN:</b> {cust.gst_number or 'N/A'}"
    )
    
    shipping_info = (
        f"<b>Billing / Shipping Address:</b><br/>"
        f"{cust.address or ''}<br/>"
        f"{cust.city or ''}, {cust.state or ''}<br/>"
        f"{cust.country or ''} - {cust.postal_code or ''}"
    )
    
    client_data = [
        [
            Paragraph("<b>Customer Details:</b>", section_heading),
            Paragraph("<b>Address Info:</b>", section_heading)
        ],
        [
            Paragraph(customer_info, normal_text),
            Paragraph(shipping_info, normal_text)
        ]
    ]
    client_table = Table(client_data, colWidths=[265, 265])
    client_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(client_table)
    story.append(Spacer(1, 15))
    
    # Items Table
    table_data = [[
        Paragraph("<b>#</b>", bold_text),
        Paragraph("<b>Product / Service</b>", bold_text),
        Paragraph("<b>Qty</b>", bold_text),
        Paragraph("<b>Rate</b>", bold_text),
        Paragraph("<b>Disc</b>", bold_text),
        Paragraph("<b>GST</b>", bold_text),
        Paragraph("<b>Total</b>", right_bold)
    ]]
    
    for idx, item in enumerate(quotation.items):
        table_data.append([
            Paragraph(str(idx + 1), normal_text),
            Paragraph(f"<b>{item.product.name}</b><br/>{item.product.description or ''}", normal_text),
            Paragraph(str(item.quantity), normal_text),
            Paragraph(f"${float(item.price):,.2f}", normal_text),
            Paragraph(f"${float(item.discount):,.2f}", normal_text),
            Paragraph(f"${float(item.gst):,.2f}", normal_text),
            Paragraph(f"${float(item.total):,.2f}", right_normal)
        ])
        
    items_table = Table(table_data, colWidths=[25, 215, 35, 60, 60, 60, 75])
    items_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8F9FA')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#2C3E50')),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.HexColor('#E9ECEF')),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 20))
    
    # Totals Summary
    summary_data = [
        [Paragraph("", normal_text), Paragraph("Subtotal:", bold_text), Paragraph(f"${float(quotation.subtotal):,.2f}", right_normal)],
        [Paragraph("", normal_text), Paragraph("Discount Amount:", bold_text), Paragraph(f"${float(quotation.discount_amount):,.2f}", right_normal)],
        [Paragraph("", normal_text), Paragraph("GST Amount:", bold_text), Paragraph(f"${float(quotation.gst_amount):,.2f}", right_normal)],
        [Paragraph("", normal_text), Paragraph("<b>Grand Total:</b>", bold_text), Paragraph(f"<b>${float(quotation.grand_total):,.2f}</b>", right_bold)],
    ]
    summary_table = Table(summary_data, colWidths=[300, 120, 110])
    summary_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LINEABOVE', (1, 3), (2, 3), 1, colors.HexColor('#2C3E50')),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 40))
    
    # Terms
    notes_data = [
        [
            Paragraph("<b>Validity & Notes:</b><br/>1. This quotation is valid for 30 days from the date of issue.<br/>2. Delivery will be made within 7 business days from order confirmation.<br/>3. Payment terms: 100% upon confirmation or conversion to Sales Order.", normal_text),
            Paragraph("<br/><br/>___________________________<br/><b>Sales Manager Signature</b>", right_bold)
        ]
    ]
    notes_table = Table(notes_data, colWidths=[300, 230])
    notes_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
    ]))
    story.append(notes_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer
