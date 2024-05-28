// Copyright (c) 2023, Ahmad and contributors
// For license information, please see license.txt

frappe.ui.form.on('Pre-Sales Quarter Quota', {
    refresh: function(frm){
		if (frm.doc.docstatus == 1){
			frm.add_custom_button(__("Update Incentive in Sales Order"), function() {
				frm.events.update_incentive_percentage(frm);
			});
		}
	},
    update_incentive_percentage: function(frm){
		frm.call({
			"method": "sabaintegration.www.api.update_engineer_incentive_percentage",
			"args": {
                "engineer": frm.doc.engineer,
                "incentive_percentage": frm.doc.incentive_percentage,
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
					frappe.msgprint(`Sales Orders have been updated<br><br>${sales_order_links_str} `);
				}
				else{
					frappe.msgprint("No Sales Orders to Update")
				}
			}
		})
	},
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
