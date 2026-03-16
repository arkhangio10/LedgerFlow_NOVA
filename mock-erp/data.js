/**
 * LedgerFlow Mock ERP — Seed Data
 * In-memory data for the mock ERP portal with deliberate discrepancies.
 */

const VENDORS = [
    { id: "V-001", name: "TechSupply Corp", taxId: "20-5551234", status: "active", paymentTerms: "Net 30", contact: "john@techsupply.com", address: "123 Tech Ave, Suite 400" },
    { id: "V-002", name: "CloudNet Services", taxId: "20-5559876", status: "active", paymentTerms: "Net 45", contact: "sarah@cloudnet.io", address: "456 Cloud Blvd" },
    { id: "V-003", name: "OfficeMax Solutions", taxId: "20-5554567", status: "active", paymentTerms: "Net 30", contact: "mike@officemax.com", address: "789 Office Park Dr" },
    { id: "V-004", name: "DataFlow Analytics", taxId: "20-5558765", status: "suspended", paymentTerms: "Net 60", contact: "lisa@dataflow.co", address: "321 Data Lane" },
    { id: "V-005", name: "SecureIT Partners", taxId: "20-5552345", status: "active", paymentTerms: "Net 30", contact: "alex@secureit.com", address: "555 Security Way" },
];

const PURCHASE_ORDERS = [
    {
        poNumber: "PO-10450", vendor: "TechSupply Corp", vendorId: "V-001",
        total: 15000.00, currency: "USD", status: "approved", date: "2025-11-15",
        costCenter: "4100-01",
        lineItems: [
            { description: "Server Equipment", quantity: 5, unitPrice: 2500.00, total: 12500.00 },
            { description: "Installation Service", quantity: 1, unitPrice: 2500.00, total: 2500.00 },
        ],
    },
    {
        poNumber: "PO-10452", vendor: "OfficeMax Solutions", vendorId: "V-003",
        total: 4200.00, currency: "USD", status: "approved", date: "2025-12-01",
        costCenter: "3200-02",
        lineItems: [
            { description: "Office Furniture", quantity: 10, unitPrice: 350.00, total: 3500.00 },
            { description: "Delivery & Assembly", quantity: 1, unitPrice: 700.00, total: 700.00 },
        ],
    },
    {
        poNumber: "PO-10455", vendor: "CloudNet Services", vendorId: "V-002",
        total: 8500.00, currency: "USD", status: "approved", date: "2025-12-10",
        costCenter: "4100-03",
        lineItems: [
            { description: "Annual Cloud License", quantity: 1, unitPrice: 7500.00, total: 7500.00 },
            { description: "Premium Support", quantity: 1, unitPrice: 1000.00, total: 1000.00 },
        ],
    },
    {
        poNumber: "PO-10458", vendor: "SecureIT Partners", vendorId: "V-005",
        total: 22000.00, currency: "USD", status: "approved", date: "2025-12-15",
        costCenter: "4100-02",
        lineItems: [
            { description: "Firewall Appliance", quantity: 2, unitPrice: 8500.00, total: 17000.00 },
            { description: "Configuration & Setup", quantity: 1, unitPrice: 5000.00, total: 5000.00 },
        ],
    },
];

const INVOICES = [
    {
        invoiceNumber: "INV-8820", vendor: "TechSupply Corp", vendorId: "V-001",
        amount: 15000.00, taxRate: 12, taxAmount: 1800.00, total: 16800.00,
        poReference: "PO-10450", date: "2025-12-20", dueDate: "2026-01-19",
        costCenter: "4100-01", status: "approved", currency: "USD",
    },
    {
        // DISCREPANCY: Amount is 3.4% higher than PO
        invoiceNumber: "INV-8821", vendor: "OfficeMax Solutions", vendorId: "V-003",
        amount: 4343.00, taxRate: 12, taxAmount: 521.16, total: 4864.16,
        poReference: "PO-10452", date: "2025-12-22", dueDate: "2026-01-21",
        costCenter: "3200-02", status: "pending", currency: "USD",
    },
    {
        // DISCREPANCY: Different vendor name than PO
        invoiceNumber: "INV-8822", vendor: "CloudNet Inc.", vendorId: "V-002",
        amount: 8500.00, taxRate: 12, taxAmount: 1020.00, total: 9520.00,
        poReference: "PO-10455", date: "2025-12-23", dueDate: "2026-02-05",
        costCenter: "4100-03", status: "pending", currency: "USD",
    },
    {
        // DISCREPANCY: Missing cost center + tax calculation wrong
        invoiceNumber: "INV-8823", vendor: "SecureIT Partners", vendorId: "V-005",
        amount: 22000.00, taxRate: 15, taxAmount: 2800.00, total: 24800.00,
        poReference: "PO-10458", date: "2025-12-24", dueDate: "2026-01-23",
        costCenter: "", status: "pending", currency: "USD",
    },
    {
        // DISCREPANCY: Suspended vendor
        invoiceNumber: "INV-8824", vendor: "DataFlow Analytics", vendorId: "V-004",
        amount: 3500.00, taxRate: 12, taxAmount: 420.00, total: 3920.00,
        poReference: "", date: "2025-12-25", dueDate: "2026-01-24",
        costCenter: "4200-01", status: "pending", currency: "USD",
    },
    {
        invoiceNumber: "INV-8825", vendor: "TechSupply Corp", vendorId: "V-001",
        amount: 7200.00, taxRate: 12, taxAmount: 864.00, total: 8064.00,
        poReference: "", date: "2025-12-26", dueDate: "2026-01-25",
        costCenter: "4100-01", status: "approved", currency: "USD",
    },
    {
        // DISCREPANCY: Duplicate-like — same vendor, similar amount in same period
        invoiceNumber: "INV-8826", vendor: "TechSupply Corp", vendorId: "V-001",
        amount: 7190.00, taxRate: 12, taxAmount: 862.80, total: 8052.80,
        poReference: "", date: "2025-12-27", dueDate: "2026-01-26",
        costCenter: "4100-01", status: "flagged", currency: "USD",
    },
    {
        invoiceNumber: "INV-8827", vendor: "CloudNet Services", vendorId: "V-002",
        amount: 1200.00, taxRate: 12, taxAmount: 144.00, total: 1344.00,
        poReference: "", date: "2025-12-28", dueDate: "2026-01-27",
        costCenter: "4100-03", status: "approved", currency: "USD",
    },
];

// Make data globally available
if (typeof window !== 'undefined') {
    window.ERP_DATA = { VENDORS, PURCHASE_ORDERS, INVOICES };
}
