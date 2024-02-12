# Copyright (c) 2023, Ahmad and contributors
# For license information, please see license.txt
import json
import frappe
from frappe import _
from frappe.utils import flt

from sabaintegration.sabaintegration.doctype.commission_rule.commission_rule import calculate_commission, get_default_rule
from sabaintegration.overrides.employee import get_leaders, get_employees
#from sabaintegration.sabaintegration.report.sales_commission_details.sales_commission_details import employees_query
from sabaintegration.sabaintegration.report.quota import is_admin, QuotaCalculations

default_rule = get_default_rule()
ROLE, DOCTYPE = "0 Accounting - Sales Persons Commission Report", "Sales Person"

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	if filters.get("annual"):
		return [
			{
				"label": _("Sales Man"),
				"fieldname": "sales_man",
				"fieldtype": "Link",
				"options": "Sales Person",
				"width": 100,
			},
			{
				"label": _("Year"),
				"fieldname": "year",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Annual Quota"),
				"fieldname": "annual_quota",
				"fieldtype": "Currency",
				"width": 100,
				"options": "currency"
			},
			{
				"label": _("Total Achievement Value"),
				"fieldname": "achieve_value",
				"fieldtype": "Currency",
				"width": 100,
				"options": "currency"
			},
			{
				"label": _("Paid Annual Commission"),
				"fieldname": "paid_annual_commission",
				"fieldtype": "Currency",
				"width": 100,
				"options": "currency"
			},
			{
				"label": _("Average KPI"),
				"fieldname": "avg_kpi",
				"fieldtype": "Percent",
				"width": 100,
			},
			{
			"label": _("Additional Annual Commission Value"),
			"fieldname": "additional_annual_comm",
			"fieldtype": "Currency",
			"width": 100,
			"options": "currency"
		},
				
		]
	else: return [
		{
			"label": _("Sales Man"),
			"fieldname": "sales_man",
			"fieldtype": "Link",
			"options": "Sales Person",
			"width": 100,
		},
		{
			"label": _("Commission Percentage"),
			"fieldname": "comm_percent",
			"fieldtype": "Percent",
			"width": 130,
		},
		{
			"label": _("Direct Sales P&L"),
			"fieldname": "achievement_value",
			"fieldtype": "Currency",
			"width": 150,
			"options": "Company:company:default_currency"
		},
		{
			"label": _("Subordinates Sales P&L"),
			"fieldname": "subordinates_commission",
			"fieldtype": "Currency",
			"width": 150,
			"options": "Company:company:default_currency"
		},
		{
			"label": _("Total Sales P&L"),
			"fieldname": "total_achieve_value",
			"fieldtype": "Currency",
			"width": 150,
			"options": "Company:company:default_currency"
		},
		{
			"label": _("Quarter Quota"),
			"fieldname": "quota",
			"fieldtype": "Currency",
			"width": 160,
			"options": "Company:company:default_currency"
		},
		{
			"label": _("Achievement Percentage"),
			"fieldname": "achieve_percent",
			"fieldtype": "Percent",
			"width": 180,
		},
		{
			"label": _("Direct Sales (Sales Stage Contribution"),
			"fieldname": "direct_sales_contribution",
			"fieldtype": "Currency",
			"width": 150,
			"options": "currency"
		},
		{
			"label": _("Direct Sales Contribution Commission Value"),
			"fieldname": "commission_value",
			"fieldtype": "Currency",
			"width": 150,
			"options": "currency"
		},
		{
			"label": _("Achiever Subordinates P&L"),
			"fieldname": "achiever_sub_pl",
			"fieldtype": "Currency",
			"width": 160,
			"options": "Company:company:default_currency"
		},
		{
			"label": _("Primary Supervision Commission"),
			"fieldname": "primary_supervision_commission",
			"fieldtype": "Currency",
			"width": 180,
			"options": "currency"
		},
		{
			"label": _("Secondary Supervision Commission"),
			"fieldname": "secondary_supervision_commission",
			"fieldtype": "Currency",
			"width": 180,
			"options": "currency"
		},
		{
			"label": _("Supervision Commission"),
			"fieldname": "supervision_commission",
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
			"label": _("NET Commission Value"),
			"fieldname": "net_commission_value",
			"fieldtype": "Currency",
			"width": 180,
			"options": "currency"
		},
		{
			"label": _("Commission From Others"),
			"fieldname": "other_commission",
			"fieldtype": "Currency",
			"width": 180,
			"options": "Company:company:default_currency"
		},
		{
			"label": _("Total NET Commission"),
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
	if filters.get("annual"):
		commissions, msgs = get_annual_commission(filters)
		
		if filters.get("sales_man"):
			if not commissions.get(filters.get('sales_man')): return
			commissions = {filters['sales_man'] : commissions[filters['sales_man']]}
		
		for sales_man in commissions:
			results.append({
				"sales_man": sales_man,
				"year": filters.get("year"),
				"additional_annual_comm": commissions[sales_man]['additional_annual_comm'], 
				"avg_kpi": commissions[sales_man]['avg_kpi'],
				"achieve_value": commissions[sales_man]['achieve_value'],
				"paid_annual_commission": commissions[sales_man]['paid_annual_commission'],
				"annual_quota": commissions[sales_man]['annual_quota']
			})
		if msgs:
			frappe.msgprint("Missing records in Quarter Quota:" + msgs)
	else:
		q = QuotaCalculations({
				"doctype": DOCTYPE,
				"filters": filters,
				"role": ROLE,
				"user": frappe.session.user,
				"rule": default_rule
		})
		commissions, msg = q.get_incentives()

		if not commissions: return
		
		if filters.get("sales_man"):
			if not commissions.get(filters.get('sales_man')): return
			commissions = {filters['sales_man'] : commissions[filters['sales_man']]}
		
		for comm in commissions:
			#if not commissions[comm].get('total'): continue
			kpi = commissions[comm].get('kpi') or 0
			subordinates_commission = flt(commissions[comm].get('total_achieve_value', 0 ) - commissions[comm].get('achieve_value',0), 2)
			supervision_commission = flt(commissions[comm].get("primary_supervision_incentive",0) + commissions[comm].get("secondary_supervision_incentive",0) , 2)
			results.append({
				"sales_man": comm,
				"comm_percent": flt(commissions[comm].get('incentive_percentage', 0), 2),
				"quota": commissions[comm]['quota'],
				"achievement_value": flt(commissions[comm].get('achieve_value', 0), 2),
				"subordinates_commission": subordinates_commission,
				"total_achieve_value": flt(commissions[comm].get('total_achieve_value', 0 ), 2),
				"achiever_sub_pl": flt(commissions[comm].get("achiever_sub_pl",0), 2),				"achieve_percent": flt(commissions[comm].get('achieve_percent', 0), 2),
				"direct_sales_contribution": flt(commissions[comm].get('direct_sales_contribution', 0 ), 2),
				"commission_value": flt(commissions[comm].get('commission_value', 0), 2),
				"primary_supervision_commission": flt(commissions[comm].get("primary_supervision_incentive",0), 2),
				"secondary_supervision_commission": flt(commissions[comm].get("secondary_supervision_incentive",0), 2),
				"supervision_commission": supervision_commission,
				"kpi": kpi,
				"net_commission_value": flt((commissions[comm].get('commission_value', 0) + supervision_commission) * kpi / 100, 2),
				"other_commission": flt(commissions[comm].get('other_commission', 0), 2),
				"total": flt((commissions[comm].get('commission_value', 0) * kpi / 100) + (supervision_commission * kpi / 100) + commissions[comm].get('other_commission', 0), 2)
			})

		if msg:
			msg = "The following Sales Men Don't Have a Quarter Quota Record for the Current Quarter: " + msg
			frappe.msgprint(msg)
	
	return results

def get_annual_commission(filters):
	"Get the Additional Annual Commission"

	annual_commission, msgs = {}, ''
	results = {}
	# Iterate through quarters to get the total achievement
	for q in ["Q1", "Q2", "Q3", "Q4"]:
		filters['quarter'] = q

		# Get the commission and the achievement for the sales men during the quarter
		q = QuotaCalculations({
		"doctype": DOCTYPE,
		"filters": filters,
		"role": ROLE,
		"user": frappe.session.user,
		"rule": default_rule
		})
		commissions, msg = q.get_incentives()
		for sales_man in commissions:
			total, kpi, msg = get_quarter_quota(sales_man, filters.get("year"), q)
			if annual_commission.get(sales_man):
				annual_commission[sales_man][0] += total # The Profit Quota of the year
				annual_commission[sales_man][1] += kpi # Average KPI 
				annual_commission[sales_man][2] += commissions[sales_man]['achieve_value'] # The total achievement of the year
				annual_commission[sales_man][3] += commissions[sales_man].get('commission_value', 0) # Commission he got during the year
				
			else:
				annual_commission[sales_man] = [total, kpi, commissions[sales_man]['achieve_value'], commissions[sales_man].get('commission_value', 0)]
				
			if q == "Q4": 
				annual_commission[sales_man][1] = annual_commission[sales_man][1] / 4
				# if the sales man achieves the annual quota then what he gets in addition
				# additional commission = total achievement * kpi * commission percentage
				if annual_commission[sales_man][2] >= annual_commission[sales_man][0]:
					commission = (annual_commission[sales_man][2] * annual_commission[sales_man][1] / 100 * 0.06) - annual_commission[sales_man][3]
					results[sales_man] = {
						"additional_annual_comm": commission,
						"avg_kpi": annual_commission[sales_man][1],
						"achieve_value": commissions[sales_man]['achieve_value'],
						"paid_annual_commission": annual_commission[sales_man][3],
						"annual_quota": annual_commission[sales_man][0]
					}

			if msg: msgs += "<br>" + msg

	return results, msgs

	

def get_quarter_quota(sales_man, year, quarter):
	quotas = frappe.db.get_all("Quarter Quota", {"sales_man": sales_man, "docstatus": 1, "year": year, "quarter": quarter}, ["quota", "kpi"])
	msg = ""
	total, kpi = 0.00 , 0.00
	if not quotas:
		if msg: msg += "<br>"
		msg += "<b>{0}</b>: Quarter {1} - {2}".format(sales_man, quarter, year)
	else:
		total = quotas[0].quota
		kpi = quotas[0].kpi
		
	return total, kpi, msg

@frappe.whitelist()
def apply_comm_on_so(args):
	args = json.loads(args)
	if not args.get("year") or not args.get("quarter"):
		frappe.throw("Select Year and Quarter to Apply Commissions")

	q = QuotaCalculations({
		"doctype": DOCTYPE,
		"filters": args,
		"role": ROLE,
		"user": frappe.session.user,
		"rule": default_rule
	})
	commissions, msg = q.get_incentives()
	if msg:
		msg = "The following Sales men don't have a Quarter Quota record for the current Quarter: " + msg
		frappe.throw(msg)
	if commissions:
		conditions = get_conditions(args)
		sales_men = ""
		for sales_man in commissions:
			if commissions[sales_man].get("primary_supervision_commission") or commissions[sales_man].get("secondary_supervision_commission"):
				frappe.db.set_value("Quarter Quota", {
					"sales_man": sales_man,
					"year": args["year"],
					"quarter": args["quarter"],
					"docstatus": 1
					}, "to_get_extra", 1)
			
			frappe.db.set_value("Quarter Quota", {
				"sales_man": sales_man,
				"year": args["year"],
				"quarter": args["quarter"],
				"docstatus": 1
				}, "achievement_percentage", commissions[sales_man].get("achieve_percent", 0))
			sales_men += "'{sales_man}',".format(sales_man = sales_man)
		sales_men = sales_men[:-1]
		strQuery = """
			select so.name
			from `tabSales Order` as so
			where so.primary_sales_man != '' and so.primary_sales_man is not null
			and so.docstatus = 1
			and so.primary_sales_man in ({sales_men})
			{conditions}
		""".format(conditions = conditions, sales_men = sales_men)
		sales_orders = frappe.db.sql(strQuery, args, as_dict = 1)
		so_number = 0
		for sales_order in sales_orders:
			doc = frappe.get_doc("Sales Order", sales_order.name)

			if not commissions.get(doc.primary_sales_man): continue

			achieved_target = commissions[doc.primary_sales_man].get('achieved_target', 0) or 0
			#if achieved_target <= 0: continue

			employee = frappe.db.get_value("Sales Person", doc.primary_sales_man, "employee")
			
			# Set Primary and Secondary Supervisor in the SO, in Addition to the Supervision Commissions
			if commissions[doc.primary_sales_man].get("primary_supervision_commission") or not get_leaders(employee, "name", "reports_to"):
				doc.primary_supervisor = doc.primary_sales_man

			else: 
				
				leader = get_leaders(employee, "name", "reports_to", None, direct_leader = True)

				if leader:
					sales_person = frappe.db.get_value("Sales Person", {"employee": leader}, "name")

					doc.primary_supervisor = sales_person

			if commissions.get(doc.primary_supervisor) and achieved_target > 0:
				comm = calculate_commission(commissions[doc.primary_supervisor].get('achieved_target', 0), default_rule)
				if comm: doc.primary_supervision_value = doc.prm_sup_percentage / 100 * doc.base_expected_profit_loss_value * comm / 100
			elif achieved_target <= 0:
				doc.primary_supervision_value = 0

			if commissions[doc.primary_sales_man].get("secondary_supervision_commission") or not get_leaders(employee, "name", "reports_to"):
				doc.secondary_supervisor = doc.primary_sales_man
				
			else:
				employee = frappe.db.get_value("Sales Person", doc.primary_sales_man, "employee")
				
				leaders = get_leaders(employee, "name", "reports_to")

				if leaders:
					sales_person = frappe.db.get_value("Sales Person", {"employee": leaders[0]}, "name")

					if sales_person == doc.primary_supervisor and len(leaders) > 1:
						sales_person = frappe.db.get_value("Sales Person", {"employee": leaders[1]}, "name")

						if sales_person: doc.secondary_supervisor = sales_person
					
					elif sales_person == doc.primary_supervisor and not len(leaders) > 1:
						doc.secondary_supervisor = doc.primary_supervisor

					elif sales_person != doc.primary_supervisor:
						
						doc.secondary_supervisor = sales_person

			if commissions.get(doc.secondary_supervisor) and achieved_target > 0:
				comm = calculate_commission(commissions[doc.secondary_supervisor].get('achieved_target', 0), default_rule)
				if comm: doc.secondary_supervision_value = doc.sec_sup_percentage / 100 * doc.base_expected_profit_loss_value * comm / 100
			elif achieved_target <= 0:
				doc.secondary_supervision_value  = 0

			commission = doc.base_expected_profit_loss_value * doc.commission_percentage / 100 * achieved_target / 100
			
			# Set Regular Commission for every Contributed Sales Man
			for row in doc.get("sales_commission"):
				row.base_commission_value = commission * row.comm_percent / 100
				row.commission_value = row.base_commission_value / doc.conversion_rate 
				if not commissions.get(row.sales_person): continue
				if not commissions[row.sales_person].get('kpi'):
					kpi = frappe.db.get_value('Quarter Quota', {'sales_man': row.sales_person, 'quarter': args['quarter'], 'year': args['year'], 'docstatus': 1}, 'kpi')
					if not kpi:
						kpi = 100
				else:
					kpi = commissions[row.sales_person]['kpi']

				row.base_net_commission_value = row.base_commission_value * kpi / 100
				row.net_commission_value = row.base_net_commission_value / doc.conversion_rate
			doc.save(ignore_permissions = True)
			so_number += 1

		return so_number


	