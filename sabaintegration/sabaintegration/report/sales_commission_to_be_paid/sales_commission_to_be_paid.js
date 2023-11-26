// Copyright (c) 2023, Ahmad and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Commission to be Paid"] = {
	"filters": [
		{
			"fieldname":"sales_order",
			"label": ("Sales Order"),
			"fieldtype": "Link",
			"options": "Sales Order"
		},
		{
			"fieldname":"sales_man",
			"label": ("Sales Man"),
			"fieldtype": "Link",
			"options": "Sales Person"
		},
		{
			"fieldname":"quarter",
			"label": ("Quarter"),
			"fieldtype": "Select",
			"options": ["Q1", "Q2", "Q3", "Q4"],
			"default": get_quarter(),
			"reqd": false,
		},
		{
			"fieldname":"year",
			"label": ("Year"),
			"fieldtype": "Data",
            "default": moment().year(),
			"reqd": 1
		},
	],
	onload: function(report) {
		// report.page.add_inner_button(__('Create Quarter Payments'), function() {
		// 	var dialog = new frappe.ui.Dialog({
		// 		title: __("Choose Year & Quarter"),
		// 		fields: [
		// 			{
		// 				"fieldname":"year",
		// 				"label": ("Year"),
		// 				"fieldtype": "Data",
		// 				"default": moment().year(),
		// 				"reqd": 1
		// 			},
		// 			{	
		// 				"fieldname":"quarter",
		// 				"label": ("Quarter"),
		// 				"fieldtype": "Select",
		// 				"options": ["1", "2", "3", "4"],
		// 				"default": get_quarter(),
		// 				"reqd": 1,
		// 			},
					

		// 		],
		// 		primary_action_label: __("Apply"),
		// 		primary_action: (args) => {
		// 			if(!args) return;
		// 			dialog.hide();
		// 			frappe.call({
		// 				method: "sabaintegration.sabaintegration.doctype.sales_order_payment.sales_order_payment.set_payment",
		// 				args: {
		// 					year: args['year'],
		// 					quarter: args['quarter']
		// 				},
		// 				freeze: true,
		// 				callback: function(r) {
		// 					if(r.message) {
		// 						frappe.msgprint("Number of Payments that are created is: <b>" + r.message + "</b>")
		// 					}
		// 				}
		// 			});
		// 		}
		// 	})
		// 	dialog.show();
		// })
		report.page.add_inner_button(__('Create Journal Entry'), function() {
			var dialog = new frappe.ui.Dialog({
				title: __("Create Journal Entry"),
				fields: [
					{
						"fieldname":"year",
						"label": ("Year"),
						"fieldtype": "Data",
						"default": moment().year(),
						"reqd": 1
					},
					{	
						"fieldname":"quarter",
						"label": ("Quarter"),
						"fieldtype": "Select",
						"options": ["Q1", "Q2", "Q3", "Q4"],
						"default": get_quarter(),
						"reqd": false,
					},
					{
						"fieldname":"sales_man",
						"label": ("Sales Man"),
						"fieldtype": "Link",
						"options": "Sales Person"
					},
					// {
					// 	"fieldname":"annual",
					// 	"label": ("Annual?"),
					// 	"fieldtype": "Check",
					// 	"change": function() {
					// 		// If Field 1 has some value, make Field 2 mandatory.
					// 		if (d.get_value('annual')) {
					// 			d.get_field('quarter').df.reqd = false;
					// 		} else {
					// 			d.get_field('quarter').df.reqd = true;
					// 		}
					// 		d.refresh_fields();
					// 	}
					// },

				],
				primary_action_label: __("Create"),
				primary_action: (args) => {
					if(!args) return;
					dialog.hide();
					frappe.call({
						method: "sabaintegration.sabaintegration.report.sales_commission_to_be_paid.sales_commission_to_be_paid.create_journal_entry",
						args: {
							args: args
						},
						callback: function(r) {
							if(!r.exc) {
								var doc = frappe.model.sync(r.message);
								frappe.set_route("Form", r.message.doctype, r.message.name);
							}
						}
					});
				}
			})
			dialog.show();
		});
	}
};

function get_quarter(){
	var today = new Date();
	var quarter = Math.floor((today.getMonth() + 3) / 3);
	return "Q" + quarter;;
}
