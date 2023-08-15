// Copyright (c) 2023, Ahmad and contributors
// For license information, please see license.txt
/* eslint-disable */


frappe.query_reports["Sales Commission Details"] = {
	"filters": [
		{
			"fieldname":"primary_sales_man",
			"label": ("Primary Sales Man"),
			"fieldtype": "Link",
			"options": "Sales Person"
		},
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
			"fieldname":"supervisior",
			"label": ("Supervisior"),
			"fieldtype": "Link",
			"options": "Sales Person"
		},
		{
			"fieldname":"quarter",
			"label": ("Quarter"),
			"fieldtype": "Select",
			"options": ["Q1", "Q2", "Q3", "Q4"],
			"reqd": 1,
		},
		{
			"fieldname":"year",
			"label": ("Year"),
			"fieldtype": "Data",
            "default": moment().year(),
			"reqd": 1
		},
	],
	"onload": async function(report) {
        frappe.query_report.set_filter_value({'quarter': await get_quarter()});
		frappe.query_report.refresh();
    }
};

function get_quarter(){
	var today = new Date();
	var quarter = Math.floor((today.getMonth() + 3) / 3);
	console.log(quarter)
	return "Q" + quarter;
}
