// Copyright (c) 2023, Ahmad and contributors
// For license information, please see license.txt

frappe.ui.form.on('Quarter Quota', {
	sales_man: function(frm){
        frm.trigger("set_kpi");
    },
    year: function(frm){
        frm.trigger("set_kpi");
    },
    quarter: function(frm){
        frm.trigger("set_kpi");
    },
    set_kpi: function(frm){
        frappe.call({
            "method": "sabaintegration.sabaintegration.doctype.default_kpi.default_kpi.get_default_kpi",
            "args": {
                "doc": frm.doc.doctype,
                "person": frm.doc.sales_man,
                "year": frm.doc.year,
                "quarter": frm.doc.quarter
            },
            callback: function(r){
                if (r.message)
                frappe.model.set_value(frm.doc.doctype, frm.doc.name, "kpi", r.message);
                else
                frappe.model.set_value(frm.doc.doctype, frm.doc.name, "kpi", 0);
                
            }
        })
    }
});
