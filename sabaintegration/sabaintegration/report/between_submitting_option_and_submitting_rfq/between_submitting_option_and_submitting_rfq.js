// Copyright (c) 2023, Ahmad and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Between Submitting Option and Submitting RFQ"] = {
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
			"label": ("Opportunity Owner"),
			"fieldname": "opportunity_owner",
			"fieldtype": "Link",
			"options": "User",
			"width": 100,
		}

	]
};
