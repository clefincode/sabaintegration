# Copyright (c) 2024, Ahmad and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from sabaintegration.sabaintegration.report.quota import get_person

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
			"label": _("Product Manager"),
			"fieldname": "product_manager",
			"fieldtype": "Link",
			"width": 100,
			"options": "Product Manager"
		},
		{
			"label": _("Brand"),
			"fieldname": "brand",
			"fieldtype": "Link",
			"width": 100,
			"options": "Brand"
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
	if filters.get("brand"):
		conditions += " and brands.brand = %(brand)s"
	if filters.get("year"):
		conditions += " and EXTRACT(YEAR FROM so.submitting_date) = %(year)s"
	if filters.get("quarter"):
		conditions += " and CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.submitting_date) / 3.0)) = %(quarter)s"
	return conditions

def get_data(filters):
	conditions = get_conditions(filters)

	product_managers = ''
	if frappe.session.user == "Administrator" or "0 Accounting - Marketing Incentive Report" in frappe.get_roles():
		user = ''
		if filters.get("product_manager"):
			employee = frappe.db.get_value("Product Manager", filters["product_manager"], "employee")
			if employee:
				user = frappe.db.get_value("Employee", employee, "user_id")
		product_managers = get_person("Product Manager", user)
	else: product_managers = get_person("Product Manager", frappe.session.user)
	
	res = frappe.db.sql("""
		select distinct so.name as sales_order, brands.product_manager, brands.brand, EXTRACT(YEAR FROM so.submitting_date) as year, 
			CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.submitting_date) / 3.0)) AS quarter,  
			brands.total_quota as achievement_value, qu.total_quota
		from `tabBrand Details` as brands
		inner join `tabSales Order` as so on so.name = brands.parent
		inner join `tabBrand Details` as qu on qu.product_manager = brands.product_manager and brands.brand = qu.brand
		inner join `tabMarketing Quarter Quota` as qq on qq.name = qu.parent and qq.year = EXTRACT(YEAR FROM so.submitting_date) and qq.quarter = CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.submitting_date) / 3.0)) and qq.docstatus = 1

		where 
		brands.product_manager in ({product_managers}) 
		and	CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.submitting_date) / 3.0)) = qq.quarter 
		and EXTRACT(YEAR FROM so.submitting_date) = qq.year 
		and so.docstatus = 1 and qq.docstatus = 1
		{conditions}
		order by brands.product_manager, so.name
	""".format(product_managers = product_managers, conditions = conditions), filters, as_dict=1)
	chart_data = prepare_chart_data(res, filters)
	return res, chart_data

def prepare_chart_data(results, filters):
	labels = list(set((d.brand, d.product_manager) for d in results))
	values, i = {}, 0
	for label in labels:
		for res in results:
			if res.brand == label[0]:
				if values.get(res.brand):
					values[res.brand] = [values.get(res.brand)[0] + res.achievement_value, res.total_quota]
				else:
					values[res.brand] = [res.achievement_value, res.total_quota]

	achievement_values , quota_values = [], []

	labels = list(set([d.brand for d in results]))

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

