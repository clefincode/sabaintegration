// Copyright (c) 2022, Ahmad and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["ToDo List"] = {
	"filters": [
		{
			"label": ("Status"),
			"fieldtype": "Select",
			"fieldname": "status",
			"options": ["Open", "Completed", "Closed"],
			"default": "Open",
			"width": 100,
		},
		{
			"label": ("Owner"),
			"fieldtype": "Link",
			"fieldname": "owner",
			"options": "User",
			"width": 100,
		},
		{
			"label": ("Due Date"),
			"fieldtype": "Date",
			"fieldname": "date",
			"width": 100,
			"default": frappe.datetime.get_today()
		},
	]
};
