// Copyright (c) 2023, Ahmad and contributors
// For license information, please see license.txt

frappe.ui.form.on('Pre-Sales Quarter Quota', {
	engineer: function(frm){
        frm.trigger("set_kpi");
        frm.trigger("set_incentive_value");
    },
    year: function(frm){
        frm.trigger("set_kpi");
    },
    quarter: function(frm){
        frm.trigger("set_kpi");
    },
    set_incentive_value: function(frm){
        frappe.call({
            "method": "sabaintegration.sabaintegration.doctype.pre_sales_quarter_quota.pre_sales_quarter_quota.set_incentive_percentage",
            "args": {
                "engineer": frm.doc.engineer,
            },
            callback: function(r){
                if (r.message)
                frappe.model.set_value(frm.doc.doctype, frm.doc.name, "incentive_percentage", r.message);
                
            }
        })
    },
    set_kpi: function(frm){
        frappe.call({
            "method": "sabaintegration.sabaintegration.doctype.default_kpi.default_kpi.get_default_kpi",
            "args": {
                "doc": frm.doc.doctype,
                "person": frm.doc.engineer,
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
