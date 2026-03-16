/**
 * LedgerFlow Mock ERP — Application Logic
 * In-memory CRUD operations for invoices, vendors, and purchase orders.
 */

// ─── Utility Functions ──────────────────────────────────────────

function showAlert(containerId, message, type = 'success') {
    const alert = document.getElementById(containerId);
    if (!alert) return;
    alert.className = `alert alert-${type} show`;
    alert.textContent = message;
    setTimeout(() => alert.classList.remove('show'), 4000);
}

function formatCurrency(amount) {
    return '$' + (amount || 0).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// ─── INVOICES ───────────────────────────────────────────────────

function renderInvoices(filter = null, statusFilter = null) {
    const tbody = document.getElementById('invoice-tbody');
    if (!tbody) return;

    let invoices = [...window.ERP_DATA.INVOICES];
    
    if (filter) {
        const q = filter.toLowerCase();
        invoices = invoices.filter(inv =>
            inv.invoiceNumber.toLowerCase().includes(q) ||
            inv.vendor.toLowerCase().includes(q) ||
            inv.poReference.toLowerCase().includes(q)
        );
    }
    if (statusFilter) {
        invoices = invoices.filter(inv => inv.status === statusFilter);
    }

    tbody.innerHTML = invoices.map((inv, i) => {
        const origIndex = window.ERP_DATA.INVOICES.indexOf(inv);
        return `
        <tr onclick="editInvoice(${origIndex})" id="invoice-row-${inv.invoiceNumber}">
            <td><strong>${inv.invoiceNumber}</strong></td>
            <td>${inv.vendor}</td>
            <td>${formatCurrency(inv.amount)}</td>
            <td>${formatCurrency(inv.taxAmount)} (${inv.taxRate}%)</td>
            <td><strong>${formatCurrency(inv.total)}</strong></td>
            <td>${inv.poReference || '—'}</td>
            <td>${inv.date}</td>
            <td>${inv.costCenter || '<span style="color:red">MISSING</span>'}</td>
            <td><span class="status status-${inv.status}">${inv.status}</span></td>
            <td>
                <button class="btn" onclick="event.stopPropagation(); editInvoice(${origIndex})">Edit</button>
            </td>
        </tr>`;
    }).join('');

    const countEl = document.getElementById('invoice-count');
    if (countEl) countEl.textContent = `Showing ${invoices.length} records`;
}

function filterInvoices() {
    const search = document.getElementById('invoice-search')?.value || '';
    const status = document.getElementById('invoice-status-filter')?.value || '';
    renderInvoices(search || null, status || null);
}

function editInvoice(index) {
    const inv = window.ERP_DATA.INVOICES[index];
    if (!inv) return;

    document.getElementById('edit-invoice-index').value = index;
    document.getElementById('invoice-form-title').textContent = `Edit Invoice: ${inv.invoiceNumber}`;
    document.getElementById('edit-invoice-number').value = inv.invoiceNumber;
    document.getElementById('edit-vendor').value = inv.vendor;
    document.getElementById('edit-vendor-id').value = inv.vendorId;
    document.getElementById('edit-amount').value = inv.amount;
    document.getElementById('edit-tax-rate').value = inv.taxRate;
    document.getElementById('edit-tax-amount').value = inv.taxAmount;
    document.getElementById('edit-total').value = inv.total;
    document.getElementById('edit-po-reference').value = inv.poReference;
    document.getElementById('edit-date').value = inv.date;
    document.getElementById('edit-due-date').value = inv.dueDate;
    document.getElementById('edit-cost-center').value = inv.costCenter;
    document.getElementById('edit-status').value = inv.status;
    document.getElementById('edit-currency').value = inv.currency;

    document.getElementById('invoice-form').classList.add('active');
}

function saveInvoice() {
    const index = parseInt(document.getElementById('edit-invoice-index').value);
    const inv = window.ERP_DATA.INVOICES[index];
    if (!inv) return;

    inv.vendor = document.getElementById('edit-vendor').value;
    inv.vendorId = document.getElementById('edit-vendor-id').value;
    inv.amount = parseFloat(document.getElementById('edit-amount').value) || 0;
    inv.taxRate = parseFloat(document.getElementById('edit-tax-rate').value) || 0;
    inv.taxAmount = parseFloat(document.getElementById('edit-tax-amount').value) || 0;
    inv.total = parseFloat(document.getElementById('edit-total').value) || 0;
    inv.poReference = document.getElementById('edit-po-reference').value;
    inv.date = document.getElementById('edit-date').value;
    inv.dueDate = document.getElementById('edit-due-date').value;
    inv.costCenter = document.getElementById('edit-cost-center').value;
    inv.status = document.getElementById('edit-status').value;
    inv.currency = document.getElementById('edit-currency').value;

    hideInvoiceForm();
    renderInvoices();
    showAlert('invoice-alert', `Invoice ${inv.invoiceNumber} updated successfully.`, 'success');
}

function approveInvoice() {
    const index = parseInt(document.getElementById('edit-invoice-index').value);
    if (window.ERP_DATA.INVOICES[index]) {
        window.ERP_DATA.INVOICES[index].status = 'approved';
        hideInvoiceForm();
        renderInvoices();
        showAlert('invoice-alert', `Invoice ${window.ERP_DATA.INVOICES[index].invoiceNumber} approved.`, 'success');
    }
}

function flagInvoice() {
    const index = parseInt(document.getElementById('edit-invoice-index').value);
    if (window.ERP_DATA.INVOICES[index]) {
        window.ERP_DATA.INVOICES[index].status = 'flagged';
        hideInvoiceForm();
        renderInvoices();
        showAlert('invoice-alert', `Invoice ${window.ERP_DATA.INVOICES[index].invoiceNumber} flagged for review.`, 'warning');
    }
}

function rejectInvoice() {
    const index = parseInt(document.getElementById('edit-invoice-index').value);
    if (window.ERP_DATA.INVOICES[index]) {
        window.ERP_DATA.INVOICES[index].status = 'rejected';
        hideInvoiceForm();
        renderInvoices();
        showAlert('invoice-alert', `Invoice ${window.ERP_DATA.INVOICES[index].invoiceNumber} rejected.`, 'error');
    }
}

function showInvoiceForm() {
    document.getElementById('invoice-form-title').textContent = 'New Invoice';
    document.getElementById('edit-invoice-index').value = '-1';
    document.getElementById('edit-invoice-number').value = 'INV-' + (8828 + Math.floor(Math.random() * 100));
    document.getElementById('edit-invoice-number').removeAttribute('readonly');
    ['edit-vendor', 'edit-vendor-id', 'edit-amount', 'edit-tax-rate', 'edit-tax-amount',
     'edit-total', 'edit-po-reference', 'edit-date', 'edit-due-date', 'edit-cost-center'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    document.getElementById('edit-status').value = 'pending';
    document.getElementById('edit-currency').value = 'USD';
    document.getElementById('invoice-form').classList.add('active');
}

function hideInvoiceForm() {
    document.getElementById('invoice-form').classList.remove('active');
}

function refreshInvoices() {
    renderInvoices();
    showAlert('invoice-alert', 'Invoice list refreshed.', 'info');
}

// ─── VENDORS ────────────────────────────────────────────────────

function renderVendors(filter = null, statusFilter = null) {
    const tbody = document.getElementById('vendor-tbody');
    if (!tbody) return;

    let vendors = [...window.ERP_DATA.VENDORS];
    if (filter) {
        const q = filter.toLowerCase();
        vendors = vendors.filter(v =>
            v.name.toLowerCase().includes(q) ||
            v.id.toLowerCase().includes(q) ||
            v.taxId.toLowerCase().includes(q)
        );
    }
    if (statusFilter) {
        vendors = vendors.filter(v => v.status === statusFilter);
    }

    tbody.innerHTML = vendors.map((v, i) => {
        const origIndex = window.ERP_DATA.VENDORS.indexOf(v);
        return `
        <tr onclick="editVendorByIndex(${origIndex})">
            <td><strong>${v.id}</strong></td>
            <td>${v.name}</td>
            <td>${v.taxId}</td>
            <td><span class="status status-${v.status}">${v.status}</span></td>
            <td>${v.paymentTerms}</td>
            <td>${v.contact}</td>
            <td>
                <button class="btn" onclick="event.stopPropagation(); editVendorByIndex(${origIndex})">Edit</button>
            </td>
        </tr>`;
    }).join('');
}

function filterVendors() {
    const search = document.getElementById('vendor-search')?.value || '';
    const status = document.getElementById('vendor-status-filter')?.value || '';
    renderVendors(search || null, status || null);
}

function editVendorByIndex(index) {
    const v = window.ERP_DATA.VENDORS[index];
    if (!v) return;

    document.getElementById('edit-vendor-index').value = index;
    document.getElementById('vendor-form-title').textContent = `Edit Vendor: ${v.name}`;
    document.getElementById('edit-v-id').value = v.id;
    document.getElementById('edit-v-name').value = v.name;
    document.getElementById('edit-v-taxid').value = v.taxId;
    document.getElementById('edit-v-status').value = v.status;
    document.getElementById('edit-v-terms').value = v.paymentTerms;
    document.getElementById('edit-v-contact').value = v.contact;
    document.getElementById('edit-v-address').value = v.address || '';
    document.getElementById('vendor-form').classList.add('active');
}

function saveVendor() {
    const index = parseInt(document.getElementById('edit-vendor-index').value);
    const v = window.ERP_DATA.VENDORS[index];
    if (!v) return;

    v.name = document.getElementById('edit-v-name').value;
    v.taxId = document.getElementById('edit-v-taxid').value;
    v.status = document.getElementById('edit-v-status').value;
    v.paymentTerms = document.getElementById('edit-v-terms').value;
    v.contact = document.getElementById('edit-v-contact').value;
    v.address = document.getElementById('edit-v-address').value;

    hideVendorForm();
    renderVendors();
    showAlert('vendor-alert', `Vendor ${v.name} updated successfully.`, 'success');
}

function showVendorForm() {
    document.getElementById('vendor-form-title').textContent = 'New Vendor';
    document.getElementById('edit-vendor-index').value = '-1';
    const newId = 'V-' + String(window.ERP_DATA.VENDORS.length + 1).padStart(3, '0');
    document.getElementById('edit-v-id').value = newId;
    ['edit-v-name', 'edit-v-taxid', 'edit-v-terms', 'edit-v-contact', 'edit-v-address'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    document.getElementById('edit-v-status').value = 'pending';
    document.getElementById('vendor-form').classList.add('active');
}

function hideVendorForm() {
    document.getElementById('vendor-form').classList.remove('active');
}

// ─── PURCHASE ORDERS ────────────────────────────────────────────

function renderPurchaseOrders(filter = null) {
    const tbody = document.getElementById('po-tbody');
    if (!tbody) return;

    let pos = [...window.ERP_DATA.PURCHASE_ORDERS];
    if (filter) {
        const q = filter.toLowerCase();
        pos = pos.filter(po =>
            po.poNumber.toLowerCase().includes(q) ||
            po.vendor.toLowerCase().includes(q)
        );
    }

    tbody.innerHTML = pos.map((po, i) => `
        <tr onclick="showPODetail(${i})">
            <td><strong>${po.poNumber}</strong></td>
            <td>${po.vendor}</td>
            <td>${formatCurrency(po.total)}</td>
            <td>${po.currency}</td>
            <td>${po.date}</td>
            <td>${po.costCenter}</td>
            <td><span class="status status-${po.status}">${po.status}</span></td>
            <td>
                <button class="btn" onclick="event.stopPropagation(); showPODetail(${i})">View</button>
            </td>
        </tr>`
    ).join('');
}

function filterPOs() {
    const search = document.getElementById('po-search')?.value || '';
    renderPurchaseOrders(search || null);
}

function showPODetail(index) {
    const po = window.ERP_DATA.PURCHASE_ORDERS[index];
    if (!po) return;

    document.getElementById('po-detail-title').textContent = `Purchase Order: ${po.poNumber}`;

    let html = `
        <div class="form-row">
            <div class="form-group"><label>PO Number</label><input type="text" value="${po.poNumber}" readonly></div>
            <div class="form-group"><label>Vendor</label><input type="text" value="${po.vendor}" readonly></div>
            <div class="form-group"><label>Status</label><input type="text" value="${po.status}" readonly></div>
        </div>
        <div class="form-row">
            <div class="form-group"><label>Total</label><input type="text" value="${formatCurrency(po.total)}" readonly></div>
            <div class="form-group"><label>Date</label><input type="text" value="${po.date}" readonly></div>
            <div class="form-group"><label>Cost Center</label><input type="text" value="${po.costCenter}" readonly></div>
        </div>
        <h4 style="font-size: 12px; margin: 10px 0 6px 0; color: #1a3a5c;">Line Items</h4>
        <table class="erp-table">
            <thead><tr><th>Description</th><th>Qty</th><th>Unit Price</th><th>Total</th></tr></thead>
            <tbody>
                ${po.lineItems.map(li => `
                    <tr>
                        <td>${li.description}</td>
                        <td>${li.quantity}</td>
                        <td>${formatCurrency(li.unitPrice)}</td>
                        <td>${formatCurrency(li.total)}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    document.getElementById('po-detail-body').innerHTML = html;
    document.getElementById('po-detail').classList.add('active');
}

function hidePODetail() {
    document.getElementById('po-detail').classList.remove('active');
}
