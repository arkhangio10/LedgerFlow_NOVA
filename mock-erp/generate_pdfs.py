from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

def create_invoice_pdf(filename, invoice_num, vendor, date, amount, tax, total, po_ref, description):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Headers
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 50, "INVOICE")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Invoice #: {invoice_num}")
    c.drawString(50, height - 100, f"Date: {date}")
    
    # Vendor
    c.setFont("Helvetica-Bold", 14)
    c.drawString(300, height - 50, "FROM:")
    c.setFont("Helvetica", 12)
    c.drawString(300, height - 70, vendor)
    
    # PO
    c.drawString(50, height - 140, f"PO Reference: {po_ref}")
    
    # Items
    c.line(50, height - 170, 550, height - 170)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 190, "Description")
    c.drawString(450, height - 190, "Amount")
    
    c.line(50, height - 200, 550, height - 200)
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 230, description)
    c.drawString(450, height - 230, f"${amount:.2f}")
    
    # Totals
    c.line(50, height - 260, 550, height - 260)
    c.drawString(350, height - 290, "Subtotal:")
    c.drawString(450, height - 290, f"${amount:.2f}")
    
    c.drawString(350, height - 310, "Tax:")
    c.drawString(450, height - 310, f"${tax:.2f}")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(350, height - 340, "Total:")
    c.drawString(450, height - 340, f"${total:.2f}")
    
    c.save()

def main():
    os.makedirs('examples', exist_ok=True)
    
    # 1. Vendor Name Discrepancy
    create_invoice_pdf(
        'examples/invoice_INV-8822_vendor_discrepancy.pdf',
        'INV-8822',
        'CloudNet Inc.',  # Should be CloudNet Services
        '2025-12-23',
        8500.00,
        1020.00,
        9520.00,
        'PO-10455',
        'Annual Cloud License & Support'
    )
    
    # 2. Tax/Math Discrepancy + missing cost center
    create_invoice_pdf(
        'examples/invoice_INV-8823_math_discrepancy.pdf',
        'INV-8823',
        'SecureIT Partners',
        '2025-12-24',
        22000.00,
        2800.00,  # Math is wrong? Or tax rate is 15% but they say 12% in other parts?
        24800.00,
        'PO-10458',
        'Firewall Appliance & Setup'
    )

    # 3. Suspended Vendor
    create_invoice_pdf(
        'examples/invoice_INV-8824_suspended_vendor.pdf',
        'INV-8824',
        'DataFlow Analytics',
        '2025-12-25',
        3500.00,
        420.00,
        3920.00,
        '',
        'Analytics Consulting'
    )

    print("Generated PDF examples in the 'examples' folder.")

if __name__ == "__main__":
    main()
