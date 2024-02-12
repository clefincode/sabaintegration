// Copyright (c) 2023, Ahmad and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Pre-Sales Activity Incentive"] = {
	"filters": [
		{
			"fieldname":"engineer",
			"label": ("Engineer"),
			"fieldtype": "Link",
			"options": "Pre-Sales Engineer"
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
		report.page.add_inner_button(__('Apply Incentive on Sales Order'), function() {
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
						method: "sabaintegration.sabaintegration.report.pre_sales_activity_incentive.pre_sales_activity_incentive.apply_incentive_on_so",
						args: {
							args: args
						},
						freeze: true,
						callback: function(r) {
							if(r.message) {
								msg = "Number of Updated Sales Order: " + r.message
								msg += "<br> You can check the latest update in Sales Orders <b><a href='/app/query-report/Pre-Sales%20Incentive%20Activity%20Details?year="+ args['year']+"&quarter="+args['quarter']+"'>here</a></b>"
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