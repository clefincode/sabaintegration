// Copyright (c) 2023, Ahmad and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Between RFQ submit & SQ submit"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": ("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd":1
		},
		{
			"fieldname":"to_date",
			"label": ("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.now_date(),
			"reqd":1
		},
		{
			"label": ("Supplier Employee"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 100,
			"get_query": function() {
				return {
					"filters": {
						"supplier_group": "SABA Employees",
					}
				}
			}
		},
	]
};