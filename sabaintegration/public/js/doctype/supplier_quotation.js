
{% include 'erpnext/buying/doctype/supplier_quotation/supplier_quotation.js' %};

erpnext.buying.CustomSupplierQuotationController = class CustomSupplierQuotationController extends erpnext.buying.SupplierQuotationController {
    make_quotation() {
        frappe.model.open_mapped_doc({
            method: "sabaintegration.overrides.supplier_quotation.make_quotation",
            frm: cur_frm
        })

    }
    default_warehouse(frm){
        $.each(frm.items || [], function(i, d) {
			if(!d.warehouse) d.warehouse = frm.default_warehouse;
		});
		refresh_field("items");
    }
    default_margin(frm){
        $.each(frm.items || [], function(i, d) {
            d.profit_margin = frm.default_margin;
        });
        refresh_field("items");
    }
};

extend_cscript(cur_frm.cscript, new erpnext.buying.CustomSupplierQuotationController({frm: cur_frm}));


frappe.ui.form.on("Supplier Quotation Item",{
    item_code: function(frm, cdt, cdn){
        var d = locals[cdt][cdn];
        if (!d.profit_margin)
            frappe.model.set_value(cdt, cdn, "profit_margin", frm.doc.default_margin)
        if (!d.warehouse)
            frappe.model.set_value(cdt, cdn, "warehouse", frm.doc.default_warehouse)
    },
})