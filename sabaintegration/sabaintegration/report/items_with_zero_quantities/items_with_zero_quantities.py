# Copyright (c) 2022, Ahmad and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = get_columns()
	data = get_data()
	return columns, data

def get_columns():
	return [
		{
			"label": ("idx"),
			"fieldtype": "Data",
			"fieldname": "idx",
		},
		{
			"label": ("Opportunity"),
			"fieldtype": "Link",
			"fieldname": "opportunity",
			"options":"Opportunity",
			"width": 100,
		},
		{
			"label": ("Item Code"),
			"fieldtype": "Link",
			"fieldname": "item_code",
			"options":"Item",
			"width": 150,
		},
		
		{
			"label": ("Item Name"),
			"fieldtype": "Data",
			"fieldname": "item_name",
			"width": 200,
		},
	]

def get_data():
	return frappe.db.sql("""
		select idx, parent as opportunity, item_code, item_name
		from `tabOpportunity Item` 
		where qty = 0
		union
		select idx, parent as opportunity, item_code, item_name
		from `tabOpportunity Option` 
		where qty = 0 order by opportunity, idx
	""", as_dict = 1)