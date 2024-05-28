// Copyright (c) 2023, Ahmad and contributors
// For license information, please see license.txt

frappe.ui.form.on('Quarter Quota', {
    refresh: function(frm){
		if (frm.doc.docstatus == 1){
			frm.add_custom_button(__("Update Incentive in Sales Order"), function() {
				frm.events.update_incentive_percentage(frm);
			});
		}
	},
    update_incentive_percentage: function(frm){
		frm.call({
			"method": "sabaintegration.www.api.update_sales_man_incentive_percentage",
			"args": {
                "sales_man": frm.doc.sales_man,
                "commission_percentage": frm.doc.commission_percentage,
				"year": frm.doc.year,
				"quarter": frm.doc.quarter
			},
			freeze: true,
			callback: function(r){
				if (r.message && r.message.length > 0){
                    let sales_orders = r.message;  
                    let sales_order_links = sales_orders.map(function(so) {                        
                        return `<a href="/app/sales-order/${so}">${so}</a>`;
                    });  
                    let sales_order_links_str = sales_order_links.join(", ");                
					frappe.msgprint(`Sales Orders have been updated<br><br>${sales_order_links_str}`);
				}
				else{
					frappe.msgprint("No Sales Orders to Update")
				}
			}
		})
	},
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
