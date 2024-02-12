// Copyright (c) 2023, Ahmad and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Commission"] = {
	"filters": [
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
		// {
		// 	"fieldname":"annual",
		// 	"label": ("Annual?"),
		// 	"fieldtype": "Check",
		// 	onchange: function() {
        //         if (this.value) {
        //             frappe.query_report_filters_by_name.quarter.df.reqd = false;
        //         } else {
        //             frappe.query_report_filters_by_name.quarter.df.reqd = true;
        //         }
        //         // Refresh the report page to reflect the changes.
        //         frappe.query_report.refresh();
        //     }
		// },
	],
	onload: function(report) {
		report.page.add_inner_button(__('Apply Commissions on Sales Order'), function() {
			var dialog = new frappe.ui.Dialog({
				title: __("Year & Quarter of Sales Orders"),
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
						"reqd": 1,
					},
					

				],
				primary_action_label: __("Apply"),
				primary_action: (args) => {
					if(!args) return;
					dialog.hide();
					frappe.call({
						method: "sabaintegration.sabaintegration.report.sales_commission.sales_commission.apply_comm_on_so",
						args: {
							args: args
						},
						freeze: true,
						callback: function(r) {
							if(r.message) {
								msg = "Number of Updated Sales Order: " + r.message
								msg += "<br> You can check the latest update in Sales Orders <b><a href='/app/query-report/Sales%20Commission%20Details?year="+ args['year']+"&quarter="+args['quarter']+"'>here</a></b>"
								frappe.msgprint(msg);
							}
						}
					});
				}
			})
			dialog.show();
		})	
	}
};
function get_quarter(){
	var today = new Date();
	var quarter = Math.floor((today.getMonth() + 3) / 3);
	return "Q" + quarter;;
}