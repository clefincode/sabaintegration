// Copyright (c) 2023, Ahmad and contributors
// For license information, please see license.txt

frappe.ui.form.on('Marketing Quarter Quota', {
	setup: function(frm){
		frm.set_df_property('leaders', 'cannot_add_rows', true);
		frm.set_df_property('leaders', 'cannot_delete_rows', true);
	},
	refresh: function(frm){
		if (frm.doc.leaders.length == 0){
			
			frm.toggle_display('leaders', false);
		}
		else frm.toggle_display('leaders', true);
	},
	year: function(frm){
		if (!frm.doc.brands) return
        frm.trigger("reset_kpi");
    },
    quarter: function(frm){
		if (!frm.doc.brands) return
        frm.trigger("reset_kpi");
    },
	reset_kpi: async function(frm){
		frappe.dom.freeze();
		for (let row of frm.doc.brands){
			await frm.events.set_kpi(row);
		}
		frappe.dom.unfreeze();
	
	},
	set_kpi: function(row){
        frappe.call({
            "method": "sabaintegration.sabaintegration.doctype.default_kpi.default_kpi.get_default_kpi",
            "args": {
                "doc": cur_frm.doc.doctype,
                "person": row.product_manager,
                "year": cur_frm.doc.year,
                "quarter": cur_frm.doc.quarter
            },
            callback: function(r){
                if (r.message)
                frappe.model.set_value(row.doctype, row.name, "kpi", r.message);
                else
                frappe.model.set_value(row.doctype, row.name, "kpi", 0);
                
            }
        })
    }
});

frappe.ui.form.on('Brand Details', {
	brands_add: function(frm, cdt, cdn){
		frappe.model.set_value(cdt, cdn, "total_quota", 0);
		frappe.model.set_value(cdt, cdn, "incentive_percentage", 0);
	},
	product_manager: function(frm, cdt, cdn){
		let d = locals[cdt][cdn];
		get_pm_details(d);
		frm.events.set_kpi(d);
	}
})

const get_pm_details = (row) => {
	if (row.incentive_percentage > 0) return
	frappe.call({
		"method": "sabaintegration.sabaintegration.doctype.marketing_quarter_quota.marketing_quarter_quota.get_pm_details",
		"args": {
			"product_manager": row.product_manager
		},
		callback: function(r){
			if (r.message){
				row.incentive_percentage = r.message;
				cur_frm.refresh_field("brands");
			}
		}
	})
}