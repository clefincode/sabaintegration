# Copyright (c) 2023, Ahmad and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_columns(filters):
	columns =  [
		{
			"label": _("Employee"),
			"fieldname": "employee_name",
			"fieldtype" : "Data",
			"width": 200,
		},		
		{
			"label": _("Number of Working Days"),
			"fieldname": "total_working_day",
			"fieldtype" : "number",
			"width": 200,
		},
		{
			"label": _("Total Working Hours"),
			"fieldname": "actual_working_hours",
			"fieldtype" : "data",
			"width": 150,
		},
		{
			"label": _("Average Working Hours per Day"),
			"fieldname": "avg_working_day",
			"fieldtype" : "data",
			"width": 250,
		},
		
	]

	return columns

def get_data(filters):
	results = frappe.db.sql("""
	SELECT 	employee_name , 
			SUM(actual_working_hours) AS actual_working_hours , 
			COUNT(*) AS total_working_day,
			TRUNCATE(SUM(actual_working_hours)  / COUNT(*) , 3)  AS avg_working_day
	FROM `tabAttendance`
	WHERE docstatus = 1 
		AND status in ('present' , 'Half Day')
		AND attendance_date BETWEEN %(from_date)s AND %(to_date)s
	GROUP BY employee_name 
	ORDER BY attendance_date DESC
	""" , filters , as_dict = True)
	return results
