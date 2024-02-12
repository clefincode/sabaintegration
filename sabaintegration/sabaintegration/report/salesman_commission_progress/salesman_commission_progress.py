# Copyright (c) 2023, Ahmad and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from sabaintegration.overrides.employee import get_leaders
from sabaintegration.sabaintegration.report.quota import get_person, get_employee

def execute(filters=None):
	columns = get_columns()
	data, chart_data = get_data(filters)
	return columns, data, None, chart_data

def get_columns():
	return [
		{
			"label": _("Sales Order"),
			"fieldname": "sales_order",
			"fieldtype": "Link",
			"width": 100,
			"options": "Sales Order"
		},
		{
			"label": _("Sales Man"),
			"fieldname": "sales_man",
			"fieldtype": "Link",
			"width": 100,
			"options": "Sales Person"
		},
		{
			"label": _("Year"),
			"fieldname": "year",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Quarter"),
			"fieldname": "quarter",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Achievemnt Value"),
			"fieldname": "base_expected_profit_loss_value",
			"fieldtype": "currency",
			"width": 150,
			"options": "Company:company:default_currency"
		},
		{
			"label": _("Quarter Quota"),
			"fieldname": "total_quota",
			"fieldtype": "currency",
			"width": 180,
			"options": "Company:company:default_currency"
		},
	]

def get_conditions(filters):
	conditions = ""
	if filters.get("sales_order"):
		conditions += " and comm.parent = %(sales_order)s"
	# if filters.get("sales_man"):
	# 	conditions += " and comm.sales_person = %(sales_man)s"
	if filters.get("year"):
		conditions += " and EXTRACT(YEAR FROM so.submitting_date) = %(year)s"
	if filters.get("quarter"):
		conditions += " and CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.submitting_date) / 3.0)) = %(quarter)s"
	return conditions

def get_data(filters):
	conditions = get_conditions(filters)

	sales_men = ''
	if frappe.session.user == "Administrator" or "0 Accounting - Sales Persons Commission Report" in frappe.get_roles():
		user = ''
		if filters.get("sales_man"):
			employee = frappe.db.get_value("Sales Person", filters["sales_man"], "employee")
			if employee:
				user = frappe.db.get_value("Employee", employee, "user_id")
		sales_men = get_person("Sales Person", user)
	else: sales_men = get_person("Sales Person", frappe.session.user)
	
	res = frappe.db.sql("""
		select distinct so.name as sales_order, comm.sales_person, EXTRACT(YEAR FROM so.submitting_date) as year, 
			CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.submitting_date) / 3.0)) AS quarter,  
			so.base_expected_profit_loss_value, qu.total_quota as total_quota, qu.sales_man
		from `tabSales Commission` as comm
		inner join `tabSales Order` as so on so.name = comm.parent
		inner join `tabSales Person` as sp on sp.name = comm.sales_person
		inner join `tabQuarter Quota` as qu on qu.sales_man = comm.sales_person
		where 
		sp.name in ({sales_men}) 
		and sp.name = so.primary_sales_man
		and	CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.submitting_date) / 3.0)) = qu.quarter 
		and EXTRACT(YEAR FROM so.submitting_date) = qu.year 
		and so.docstatus = 1 and qu.docstatus = 1
		{conditions}
		order by comm.sales_person, so.name
	""".format(sales_men = sales_men, conditions = conditions), filters, as_dict=1)
	chart_data = prepare_chart_data(res, filters)
	return res , chart_data

def prepare_chart_data(results, filters):
	labels = list(set([d.sales_person for d in results]))
	values, i = {}, 0
	for label in labels:
		for res in results:
			if res.sales_person == label:
				if values.get(res.sales_person):
					values[res.sales_person] = [values.get(res.sales_person)[0] + res.base_expected_profit_loss_value, res.total_quota]
				else:
					values[res.sales_person] = [res.base_expected_profit_loss_value, res.total_quota]
				
				employee = get_employee("Sales Person", label)
				if not employee: continue

				leaders = get_leaders(employee.name, "name", "reports_to", None)
				if not leaders: continue
				
				for leader in leaders:
					sales_person = frappe.db.get_value("Sales Person", {"employee": leader}, "name")
					if not sales_person: continue
					
					total_quota = frappe.db.get_value("Quarter Quota", {
						"sales_man": sales_person,
						"year": filters.get("year"),
						"quarter": filters.get("quarter"),
						"docstatus": 1
						}, "total_quota")
					if values.get(sales_person):
						values[sales_person] = [values.get(sales_person)[0] + res.base_expected_profit_loss_value, total_quota]
					else:
						values[sales_person] = [res.base_expected_profit_loss_value, total_quota]

	achievement_values , quota_values = [], []
	for label in labels:
		achievement_values.append(values[label][0])
		quota_values.append(values[label][1])

	datasets = [
        {
			"name": "Quarter Quota",
			"values": quota_values,
		},
		{
			"name": "Achievement Value",
			"values": achievement_values,
		},
	]
	return {
		"data": {"labels": labels, "datasets": datasets},
		"type": "bar",
		"height": 300,
	}

