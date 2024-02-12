# Copyright (c) 2024, Ahmad and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from sabaintegration.sabaintegration.report.quota import get_person, get_employee
from sabaintegration.overrides.employee import get_leaders

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
			"label": _("Engineer"),
			"fieldname": "engineer",
			"fieldtype": "Link",
			"width": 100,
			"options": "Pre-Sales Engineer"
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
			"fieldname": "achievement_value",
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
		conditions += " and so.name = %(sales_order)s"
	if filters.get("year"):
		conditions += " and EXTRACT(YEAR FROM so.submitting_date) = %(year)s"
	if filters.get("quarter"):
		conditions += " and CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.submitting_date) / 3.0)) = %(quarter)s"
	return conditions

def get_data(filters):
	conditions = get_conditions(filters)

	engineers = ''
	if frappe.session.user == "Administrator" or "0 Accounting - Pre-Sales Activity Incentive Report" in frappe.get_roles():
		user = ''
		if filters.get("engineer"):
			employee = frappe.db.get_value("Pre-Sales Engineer", filters["engineer"], "employee")
			if employee:
				user = frappe.db.get_value("Employee", employee, "user_id")
		engineers = get_person("Pre-Sales Engineer", user)
	else: engineers = get_person("Pre-Sales Engineer", frappe.session.user)
	
	res = frappe.db.sql("""
		select distinct so.name as sales_order, inc.engineer, EXTRACT(YEAR FROM so.submitting_date) as year, 
			CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.submitting_date) / 3.0)) AS quarter,  
			so.base_expected_profit_loss_value * inc.contribution_percentage / 100 as achievement_value, qu.total_quota as total_quota, qu.engineer
		from `tabPre-Sales Incentive` as inc
		inner join `tabSales Order` as so on so.name = inc.parent
		inner join `tabPre-Sales Engineer` as engineer on engineer.name = inc.engineer
		inner join `tabPre-Sales Quarter Quota` as qu on qu.engineer = inc.engineer
		where 
		engineer.name in ({engineers}) 
		and engineer.name = inc.engineer
		and	CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.submitting_date) / 3.0)) = qu.quarter 
		and EXTRACT(YEAR FROM so.submitting_date) = qu.year 
		and so.docstatus = 1 and qu.docstatus = 1
		{conditions}
		order by inc.engineer, so.name
	""".format(engineers = engineers, conditions = conditions), filters, as_dict=1)
	chart_data = prepare_chart_data(res, filters)
	return res, chart_data

def prepare_chart_data(results, filters):
	labels = list(set([d.engineer for d in results]))
	values, i = {}, 0
	for label in labels:
		for res in results:
			if res.engineer == label:
				if values.get(res.engineer):
					values[res.engineer] = [values.get(res.engineer)[0] + res.achievement_value, res.total_quota]
				else:
					values[res.engineer] = [res.achievement_value, res.total_quota]

				employee = get_employee("Pre-Sales Engineer", label)
				if not employee: continue

				leaders = get_leaders(employee.name, "name", "reports_to", None)
				if not leaders: continue
				
				for leader in leaders:
					engineer = frappe.db.get_value("Pre-Sales Engineer", {"employee": leader}, "name")
					if not engineer: continue
					
					total_quota = frappe.db.get_value("Pre-Sales Quarter Quota", {
						"engineer": engineer,
						"year": filters.get("year"),
						"quarter": filters.get("quarter"),
						"docstatus": 1
						}, "total_quota")
					if values.get(engineer):
						values[engineer] = [values.get(engineer)[0] + res.achievement_value, total_quota]
					else:
						values[engineer] = [res.achievement_value, total_quota]

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

