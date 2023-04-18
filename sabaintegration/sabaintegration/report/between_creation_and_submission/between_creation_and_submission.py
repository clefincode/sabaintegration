# Copyright (c) 2023, Ahmad and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate


def execute(filters=None):
	if not filters.get("doctype"):
		frappe.throw(_("{0} is mandatory").format(_("Doctype")))
	
	additional_data = {}
	if filters.get("doctype") == 'Supplier Quotation':
		additional_data.update({"employee" : "supplier_name"})	

	elif filters.get("doctype") == 'Quotation':
		additional_data.update({"employee" : "opportunity_owner"})	

	columns, data = get_columns(filters , additional_data), get_data(filters , additional_data)
	return columns, data

def get_columns(filters , additional_data):
	columns =  [
		{
			"label": _(filters.get("doctype")),
			"fieldname": "name",
			"fieldtype" : "Link",
			"options" : filters.get("doctype"),
			"width": 150,
		},		
		{
			"label": _("Title"),
			"fieldtype": "Data",
			"fieldname": "title",
			"width": 300,
		},
		{
			"label": _("Creation Date"),
			"fieldname": "creation",
			"fieldtype": "Date",
			"width": 200,
		},
		{
			"label": _("Submitting Date"),
			"fieldname": "submitting_date",
			"fieldtype": "Date",
			"width": 200,
		},
		{
			"label": _("Number of Days"),
			"fieldname": "days",
			"fieldtype": "Data",
			"width": 100,
		},
	]

	if additional_data.get("employee"):
		columns.append({
			"label": _("Product Manager"),
			"fieldname": additional_data["employee"] ,
			"fieldtype": "Data",
			"width": 140,
		})

	return columns

def get_data(filters , additional_data):
	conditions = get_conditions(filters)
	if additional_data.get("employee"):
		results = frappe.db.sql(f"""
		SELECT name , title , creation , submitting_date , {additional_data.get("employee")}
		FROM `tab{filters.get("doctype")}`		
		WHERE docstatus = 1 {conditions}
		ORDER BY {additional_data.get("employee")}	
		""" , filters , as_dict = True)
	else:
		results = frappe.db.sql(f"""
		SELECT name , title , creation , submitting_date
		FROM `tab{filters.get("doctype")}`		
		WHERE docstatus = 1 {conditions}			
		""" , filters , as_dict = True)

	if results:
		
		for result in results:			
			creation = result.creation
			submitting_date = result.submitting_date
			if creation and submitting_date:
				from datetime import timedelta
				if getdate(creation) == getdate(submitting_date):
					result.days = 0
				else:
					delta = submitting_date - creation
					# this case when delta is less than 24 hours
					if delta.days == 0:
						result.days = 1
					else:	
						days = delta.days
						current_fiscal_year = frappe.get_all("Fiscal Year")[0]
						holiday_list = frappe.db.sql(f"""SELECT holiday_date FROM `tabHoliday` WHERE parent = '{current_fiscal_year.name}'""")
						for i in range(1 , delta.days):
							day = creation + timedelta(days=i)					
							for j in holiday_list:						
								if j[0] == day.date():
									days = days - 1				
						result.days = days

	return results

def get_conditions(filters):
	conditions = ""

	if filters.get("from_date"):
		conditions += " AND creation >= %(from_date)s"

	if filters.get("to_date"):
		filters.update({"to_date":filters.get("to_date") + " 23:59:59"})
		conditions += " AND creation <= %(to_date)s"

	if filters.get("supplier") and filters.get("doctype") == 'Supplier Quotation':
		conditions += " AND supplier_name = %(supplier)s"	
	
	if filters.get("opportunity_owner") and filters.get("doctype") == 'Quotation':
		conditions += " AND opportunity_owner = %(opportunity_owner)s"

	return conditions
	

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_doctypes(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""
	SELECT `tabDocType`.name
	FROM `tabDocType` INNER JOIN `tabCustom Field` ON `tabDocType`.name = `tabCustom Field`.dt
	WHERE `tabCustom Field`.fieldname = 'submitting_date' AND `tabCustom Field`.dt like %(txt)s 
	""", {"txt": "%" + txt + "%"})
	

