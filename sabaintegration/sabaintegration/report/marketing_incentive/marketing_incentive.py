# Copyright (c) 2024, Ahmad and contributors
# For license information, please see license.txt
import json
import frappe
from frappe import _
from frappe.utils import flt

from sabaintegration.overrides.employee import get_leaders, get_employees
from sabaintegration.sabaintegration.report.quota import check_if_leader, get_employee, QuotaCalculations
from sabaintegration.sabaintegration.doctype.pre_sales_incentive_rule.pre_sales_incentive_rule import calculate_incentive, get_default_rule
from sabaintegration.sabaintegration.doctype.default_kpi.default_kpi import get_default_kpi

default_rule = get_default_rule()
ROLE, DOCTYPE = "0 Accounting - Marketing Incentive Report", "Product Manager"

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"label": _("Product Manager"),
			"fieldname": "product_manager",
			"fieldtype": "Link",
			"options": "Product Manager",
			"width": 100,
		},
		{
			"label": _("Brand"),
			"fieldname": "brand",
			"fieldtype": "Link",
			"options": "Brand",
			"width": 100,
		},
		{
			"label": _("Target Value"),
			"fieldname": "incentive_quota",
			"fieldtype": "Currency",
			"width": 150,
			"options": "Company:company:default_currency"
		},
		{
			"label": _("Direct Achievement Value"),
			"fieldname": "achievement_value",
			"fieldtype": "Currency",
			"width": 150,
			"options": "Company:company:default_currency"
		},
		{
			"label": _("Achievement Percentage"),
			"fieldname": "achieve_percent",
			"fieldtype": "Percent",
			"width": 180,
		},
		# {
		# 	"label": _("Default Incentive Value"),
		# 	"fieldname": "default_incentive_value",
		# 	"fieldtype": "Currency",
		# 	"width": 150,
		# 	"options": "Company:company:default_currency"
		# },
		{
			"label": _("Primary Supervision Incentive"),
			"fieldname": "primary_supervision_incentive",
			"fieldtype": "Currency",
			"width": 180,
			"options": "currency"
		},
		{
			"label": _("Secondary Supervision Incentive"),
			"fieldname": "secondary_supervision_incentive",
			"fieldtype": "Currency",
			"width": 180,
			"options": "currency"
		},
		{
			"label": _("Supervision Incentive"),
			"fieldname": "supervision_incentive",
			"fieldtype": "Currency",
			"width": 180,
			"options": "currency"
		},
		{
			"label": _("Incentive Value"),
			"fieldname": "incentive_value",
			"fieldtype": "Currency",
			"width": 180,
			"options": "currency"
		},
		{
			"label": _("KPI"),
			"fieldname": "kpi",
			"fieldtype": "Percent",
			"width": 100,
		},
		{
			"label": _("NET Incentive Value"),
			"fieldname": "net_incentive_value",
			"fieldtype": "Currency",
			"width": 180,
			"options": "currency"
		},
		{
			"label": _("Total NET Incentive"),
			"fieldname": "total",
			"fieldtype": "Currency",
			"width": 180,
			"options": "currency"
		},
	]
def get_conditions(filters):
	conditions = ""
	if filters.get("year"):
		conditions += " and EXTRACT(YEAR FROM so.submitting_date) = %(year)s"
	if filters.get("quarter"):
		conditions += " and CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.submitting_date) / 3.0)) = %(quarter)s"
	
	return conditions

def get_data(filters):
	results = []
	q = QuotaCalculations({
		"doctype": DOCTYPE,
		"filters": filters,
		"role": ROLE,
		"user": frappe.session.user,
		"rule": default_rule
	})

	incentives, msg = q.get_incentives()
		
	if filters.get("product_manager") and not filters.get("brand"):
		selected_values = {key: value for key, value in incentives.items() if key[0] == filters.get('product_manager')}
		if not selected_values: return
		incentives = selected_values
	
	elif not filters.get("product_manager") and filters.get("brand"):
		selected_values = {key: value for key, value in incentives.items() if key[1] == filters.get('brand')}
		if not selected_values: return
		incentives = selected_values
	
	elif filters.get("product_manager") and filters.get("brand"):
		if not incentives.get(filters['product_manager'], filters['brand']): return
		incentives = {(filters['product_manager'], filters['brand'])}

	if not incentives: return
	for product_manager, brand in incentives:
		results.append({
			"product_manager": product_manager,
			"brand": brand,
			"incentive_quota": incentives[(product_manager, brand)]['quota'],
			"achievement_value": flt(incentives[(product_manager, brand)].get('achieve_value', 0), 2),
			"achieve_percent": flt(incentives[(product_manager, brand)].get('achieve_percent', 0), 2),
			"incentive_value": flt(incentives[(product_manager, brand)].get('incentive_value', 0), 2),
			"primary_supervision_incentive": flt(incentives[(product_manager, brand)].get("primary_supervision_incentive",0), 2),
			"secondary_supervision_incentive": flt(incentives[(product_manager, brand)].get("secondary_supervision_incentive",0), 2),
			"supervision_incentive": flt(incentives[(product_manager, brand)].get("primary_supervision_incentive",0) + incentives[(product_manager, brand)].get("secondary_supervision_incentive",0) , 2),
			"kpi": incentives[(product_manager, brand)].get('kpi'),
			"net_incentive_value": flt(incentives[(product_manager, brand)].get('incentive_value', 0) * incentives[(product_manager, brand)].get('kpi') / 100),
			"total": flt((incentives[(product_manager, brand)].get('incentive_value', 0) * incentives[(product_manager, brand)].get('kpi') / 100) + ((incentives[(product_manager, brand)].get("primary_supervision_incentive",0) + incentives[(product_manager, brand)].get("secondary_supervision_incentive",0)) * incentives[(product_manager, brand)].get('kpi') / 100))
		})

		if msg:
			msg = "The following product_manager Don't Have a Quarter Quota Record for the Current Quarter: " + msg
			frappe.msgprint(msg)
	
	return results

@frappe.whitelist()
def apply_incentive_on_so(args):
	args = json.loads(args)
	if not args.get("year") or not args.get("quarter"):
		frappe.throw("Select Year and Quarter to Apply Incetnives")

	q = QuotaCalculations({
		"doctype": DOCTYPE,
		"filters": args,
		"role": ROLE,
		"user": frappe.session.user,
		"rule": default_rule
	})
	incentives, msg = q.get_incentives()
	doc = frappe.get_doc('Marketing Quarter Quota', {'quarter': args['quarter'], 'year': args['year'], 'docstatus': 1})

	if msg:
		msg = "The following Product Managers don't have a Quarter Quota record for the current Quarter: " + msg
		frappe.throw(msg)
	if incentives:
		conditions = q.get_conditions()
		pms, bs = "", ""
		qq = frappe.get_doc("Marketing Quarter Quota", {
			"year": args["year"],
			"quarter": args["quarter"],
			"docstatus": 1
		})

		for row in qq.brands:
			achievement_percentage = 0
			leader_achievement_percentage , leader_to_get_extra = 0, 0
			manager_achievement_percentage , manager_to_get_extra = 0, 0

			if incentives.get((row.product_manager, row.brand)):
				pms += "'{pm}',".format(pm = row.product_manager)
				bs += "'{b}',".format(b = row.brand)
				
				achievement_percentage = incentives[(row.product_manager, row.brand)].get("achieve_percent", 0)
				
				if not incentives[(row.product_manager, row.brand)].get('kpi'):
					kpi = row.kpi
					if not kpi:
						incentives[(row.product_manager, row.brand)]['kpi'] = get_kpi(row.product_manager, args)
				
				# Supervisiors achievements
				if incentives.get((row.team_leader, row.brand)):
					if not incentives[(row.team_leader, row.brand)].get('kpi'):
						incentives[(row.team_leader, row.brand)]['kpi'] = get_kpi(row.team_leader, args)
					
					leader_achievement_percentage = incentives[(row.team_leader, row.brand)].get("achieve_percent", 0)

					if incentives[(row.team_leader, row.brand)].get("primary_supervision_incentive"):
						leader_to_get_extra = 1
				
				if incentives.get((row.manager, row.brand)):
					if not incentives[(row.manager, row.brand)].get('kpi'):
						incentives[(row.manager, row.brand)]['kpi'] = get_kpi(row.manager, args)
					
					manager_achievement_percentage = incentives[(row.manager, row.brand)].get("achieve_percent", 0)

					if incentives[(row.manager, row.brand)].get("secondary_supervision_incentive"):
						manager_to_get_extra = 1


			frappe.db.set_value("Brand Details", {
				"parent": qq.name,
				"product_manager":row.product_manager,
				"brand": row.brand
				}, "achievement_percentage", achievement_percentage)
			
			frappe.db.set_value("Brand Details", {
				"parent": qq.name,
				"product_manager":row.product_manager,
				"brand": row.brand
				}, "leader_achievement_percentage", leader_achievement_percentage)

			frappe.db.set_value("Brand Details", {
					"parent": qq.name,
					"product_manager":row.product_manager,
					"brand": row.brand
					}, "leader_to_get_extra", leader_to_get_extra)

			frappe.db.set_value("Brand Details", {
				"parent": qq.name,
				"product_manager":row.product_manager,
				"brand": row.brand
				}, "manager_achievement_percentage", manager_achievement_percentage)

			frappe.db.set_value("Brand Details", {
					"parent": qq.name,
					"product_manager":row.product_manager,
					"brand": row.brand
					}, "manager_to_get_extra", manager_to_get_extra)

	
		pms, bs = pms[:-1], bs[:-1]
		strQuery = """
			select distinct so.name
			from `tabSales Order` as so
			inner join `tabBrand Details` as bd on bd.parent = so.name
			where so.docstatus = 1
			and bd.product_manager in ({pms}) and bd.brand in ({bs})
			{conditions}
		""".format(conditions = conditions, pms = pms, bs = bs)
		sales_orders = frappe.db.sql(strQuery, args, as_dict = 1)
		so_number = 0

		for sales_order in sales_orders:
			doc = frappe.get_doc("Sales Order", sales_order.name)
			for row in doc.get("brands"):
				if incentives.get((row.product_manager, row.brand)):
					achieved_target = incentives[(row.product_manager, row.brand)].get('achieved_target', 0 ) * row.incentive_percentage / 100
					row.base_incentive_value = row.total_quota * achieved_target / 100
					row.incentive_value = row.base_incentive_value / doc.conversion_rate 
					
					
					kpi = incentives[(row.product_manager, row.brand)]['kpi']
					
					row.base_net_incentive_value = row.base_incentive_value * kpi / 100
					row.net_incentive_value = row.base_net_incentive_value / doc.conversion_rate

			doc.save(ignore_permissions = True)
			so_number += 1

		return so_number


def get_kpi(product_manager, args):
	kpi = get_default_kpi(
			doc = 'Marketing Quarter Quota',
			person = product_manager,
			year = args['year'],
			quarter = args['quarter']
	)
	if not kpi:
		kpi = 100
	return kpi