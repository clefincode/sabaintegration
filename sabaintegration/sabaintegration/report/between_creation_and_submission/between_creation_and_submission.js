// Copyright (c) 2023, Ahmad and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Between Creation and Submission"] = {
	"filters": [
		{
			"label": ("Doctype"),
			"fieldname": "doctype",
			"fieldtype": "Link",
			"options": "DocType",
			"width": 100,
			"get_query": function() {
				return{
					query: "sabaintegration.sabaintegration.report.between_creation_and_submission.between_creation_and_submission.get_doctypes",					
				}
			},
		},
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
			"label": ("Supplier"),
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
		{
			"label": ("Opportunity Owner"),
			"fieldname": "opportunity_owner",
			"fieldtype": "Link",
			"options": "User",
			"width": 100,
		}
	],
};
