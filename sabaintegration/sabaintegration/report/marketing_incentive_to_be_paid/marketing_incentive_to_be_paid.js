// Copyright (c) 2024, Ahmad and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Marketing Incentive to be Paid"] = {
	"filters": [
		{
			"fieldname":"sales_order",
			"label": ("Sales Order"),
			"fieldtype": "Link",
			"options": "Sales Order"
		},
		{
			"fieldname":"product_manager",
			"label": ("Product Manager"),
			"fieldtype": "Link",
			"options": "Product Manager"
		},
		{
			"fieldname":"brand",
			"label": ("Brand"),
			"fieldtype": "Link",
			"options": "Brand"
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
};

function get_quarter(){
	var today = new Date();
	var quarter = Math.floor((today.getMonth() + 3) / 3);
	return "Q" + quarter;;
}