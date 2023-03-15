# Copyright (c) 2023, Ahmad and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	return [
		{
			"label": _("Request for Quotation"),
			"fieldtype": "Link",
			"fieldname": "request_for_quotation",
			"options": "Request for Quotation",
			"width": 200,
		},		
		{
			"label": _("Supplier Quotation"),
			"fieldtype": "Link",
			"fieldname": "supplier_quotation",
			"options": "Supplier Quotation",
			"width": 140,
		},
		{
			"label": _("Title"),
			"fieldtype": "Data",
			"fieldname": "title",
			"width": 200,
		},
		{
			"label": _("Creation Date"),
			"fieldname": "creation",
			"fieldtype": "Date",
			"width": 140,
		},
		{
			"label": _("Submitting Date"),
			"fieldname": "submitting_date",
			"fieldtype": "Date",
			"width": 140,
		},
		{
			"label": _("Product Manager"),
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Number of Days"),
			"fieldname": "days",
			"fieldtype": "Data",
			"width": 140,
		},
	]

def get_data(filters):
	conditions = get_conditions(filters)
	results = frappe.db.sql("""
	select distinct rfq.name as request_for_quotation, sq.name as supplier_quotation,
		sq.title, cast(sq.creation as date) as creation , sq.submitting_date, sq.supplier_name
	from `tabRequest for Quotation` as rfq 
		inner join `tabSupplier Quotation Item` as sqi on rfq.name = sqi.request_for_quotation
		inner join `tabSupplier Quotation` as sq on sqi.parent = sq.name
		inner join `tabSupplier` as supplier on supplier.name = sq.supplier
		where {0} and sq.docstatus = 1 
		and supplier.supplier_group = 'SABA Employees'
		order by sq.supplier_name
	""".format(conditions), filters , as_dict = True)
	if results:
		for result in results:
			from datetime import timedelta
			creation = result.creation
			submitting_date = result.submitting_date
			if creation and submitting_date:
				delta = submitting_date - creation  # output -> ex:48:00:00
				days = delta.days
				holiday_list = frappe.db.sql("""SELECT holiday_date FROM `tabHoliday` WHERE parent = '2023'""")
				for i in range(1 , delta.days):
					day = creation + timedelta(days=i)
					for j in holiday_list:
						if j[0] == day:
							days = days - 1				
				result.days = days

	return results

def get_conditions(filters):
	conditions = "1=1 "

	if filters.get("from_date"):
		conditions += " and sq.creation >= %(from_date)s"

	if filters.get("to_date"):
		conditions += " and sq.creation <= %(to_date)s"

	if filters.get("supplier"):
		conditions += " and sq.supplier_name = %(supplier)s"

	return conditions