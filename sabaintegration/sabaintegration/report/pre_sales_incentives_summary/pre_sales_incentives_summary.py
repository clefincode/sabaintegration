# Copyright (c) 2023, Ahmad and contributors
# For license information, please see license.txt

import json
import frappe
from frappe import _
from frappe.utils import flt

from sabaintegration.sabaintegration.doctype.pre_sales_incentive_rule.pre_sales_incentive_rule import get_default_rule
from sabaintegration.sabaintegration.doctype.default_kpi.default_kpi import get_default_kpi
from sabaintegration.sabaintegration.report.quota import QuotaCalculations

default_rule = get_default_rule()
ROLE, DOCTYPE = "0 Accounting - Pre-Sales Activity Incentive Report", "Pre-Sales Engineer"

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"label": _("Engineer"),
			"fieldname": "engineer",
			"fieldtype": "Link",
			"options": "Pre-Sales Engineer",
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

	if filters.get("engineer"):
		if not incentives.get(filters.get('engineer')): return
		incentives = {filters['engineer'] : incentives[filters['engineer']]}

	if not incentives: return

	for engineer in incentives:

		results.append({
			"engineer": engineer,
			"incentive_quota": incentives[engineer]['quota'],
			"achievement_value": flt(incentives[engineer].get('achieve_value', 0), 2),
			"achieve_percent": flt(incentives[engineer].get('achieve_percent', 0), 2),
			"incentive_value": flt(incentives[engineer].get('incentive_value', 0), 2),
			"primary_supervision_incentive": flt(incentives[engineer].get("primary_supervision_incentive",0), 2),
			"secondary_supervision_incentive": flt(incentives[engineer].get("secondary_supervision_incentive",0), 2),
			"supervision_incentive": flt(incentives[engineer].get("primary_supervision_incentive",0) + incentives[engineer].get("secondary_supervision_incentive",0) , 2),
			"kpi": incentives[engineer].get('kpi'),
			"net_incentive_value": flt(incentives[engineer].get('incentive_value', 0) * incentives[engineer].get('kpi') / 100),
			"total": flt((incentives[engineer].get('incentive_value', 0) * incentives[engineer].get('kpi') / 100) + incentives[engineer].get("primary_supervision_incentive",0) + incentives[engineer].get("secondary_supervision_incentive",0))
		})

		if msg:
			msg = "The following Engineer Don't Have a Quarter Quota Record for the Current Quarter: " + msg
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
	if msg:
		msg = "The following Engineers don't have a Quarter Quota record for the current Quarter: " + msg
		frappe.throw(msg)
	if incentives:
		conditions = q.get_conditions()
		engineers = ""
		for engineer in incentives:
			if incentives[engineer].get("primary_supervision_incentive") or incentives[engineer].get("secondary_supervision_incentive"):
				frappe.db.set_value("Pre-Sales Quarter Quota", {
					"engineer": engineer,
					"year": args["year"],
					"quarter": args["quarter"],
					"docstatus": 1
					}, "to_get_extra", 1)
			
			frappe.db.set_value("Pre-Sales Quarter Quota", {
				"engineer": engineer,
				"year": args["year"],
				"quarter": args["quarter"],
				"docstatus": 1
				}, "achievement_percentage", incentives[engineer].get("achieve_percent", 0))
			engineers += "'{engineer}',".format(engineer = engineer)
		engineers = engineers[:-1]
		strQuery = """
			select distinct so.name
			from `tabSales Order` as so
			inner join `tabPre-Sales Incentive` as pre_sales on pre_sales.parent = so.name
			where so.docstatus = 1
			and pre_sales.engineer in ({engineers})
			{conditions}
		""".format(conditions = conditions, engineers = engineers)
		sales_orders = frappe.db.sql(strQuery, args, as_dict = 1)
		so_number = 0

		for sales_order in sales_orders:
			doc = frappe.get_doc("Sales Order", sales_order.name)
			for row in doc.get("pre_sales_activities"):
				if incentives.get(row.engineer):
					achieved_target = incentives[row.engineer].get('achieved_target', 0 ) * incentives[row.engineer].get('incentive_percentage', 0) / 100
					row.base_incentive_value = doc.base_expected_profit_loss_value * row.contribution_percentage / 100 * achieved_target / 100
					row.incentive_value = row.base_incentive_value / doc.conversion_rate 
					
					if not incentives[row.engineer].get('kpi'):
						kpi = frappe.db.get_value('Pre-Sales Quarter Quota', {'engineer': row.engineer, 'quarter': args['quarter'], 'year': args['year'], 'docstatus': 1}, 'kpi')
						if not kpi:
							kpi = get_default_kpi(
								doc = 'Pre-Sales Quarter Quota',
								person = row.engineer,
								year = args['year'],
								quarter = args['quarter']
							)
							if not kpi:
								kpi = 100
					else:
						kpi = incentives[row.engineer]['kpi']

					row.base_net_incentive_value = row.base_incentive_value * kpi / 100
					row.net_incentive_value = row.base_net_incentive_value / doc.conversion_rate

			doc.save(ignore_permissions = True)
			so_number += 1

		return so_number

