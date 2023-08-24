# Copyright (c) 2023, Ahmad and contributors
# For license information, please see license.txt
import json
import datetime
import frappe
from frappe import _
from frappe.utils import flt

from sabaintegration.sabaintegration.doctype.commission_rule.commission_rule import calculate_commission, get_default_rule
from sabaintegration.sabaintegration.doctype.quarter_quota.quarter_quota import get_employee, check_if_team_leader
from sabaintegration.overrides.employee import get_leaders, get_employees
#from sabaintegration.sabaintegration.report.sales_commission_details.sales_commission_details import employees_query

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
		commissions, msg = get_commissions(filters)
		
		if not commissions: return
		
		if filters.get("sales_man"):
			if not commissions.get(filters.get('sales_man')): return
			commissions = {filters['sales_man'] : commissions[filters['sales_man']]}
		
		for comm in commissions:
			#if not commissions[comm].get('total'): continue

			results.append({
				"sales_man": comm,
				"comm_percent": flt(commissions[comm].get('avg_comm_percent', 0), 2),
				"quota": commissions[comm]['quota'],
				"achievement_value": flt(commissions[comm].get('achieve_value', 0), 2),
				"subordinates_commission": flt(commissions[comm].get('total_achieve_value', 0 ) - commissions[comm].get('achieve_value',0), 2),
				"total_achieve_value": flt(commissions[comm].get('total_achieve_value', 0 ), 2),
				"achiever_sub_pl": flt(commissions[comm].get("achiever_sub_pl",0), 2),				"achieve_percent": flt(commissions[comm].get('achieve_percent', 0), 2),
				"direct_sales_contribution": flt(commissions[comm].get('direct_sales_contribution', 0 ), 2),
				"commission_value": flt(commissions[comm].get('commission_value', 0), 2),
				"primary_supervision_commission": flt(commissions[comm].get("primary_supervision_commission",0), 2),
				"secondary_supervision_commission": flt(commissions[comm].get("secondary_supervision_commission",0), 2),
				"supervision_commission": flt(commissions[comm].get("primary_supervision_commission",0) + commissions[comm].get("secondary_supervision_commission",0) , 2),
				"kpi": commissions[comm].get('kpi', 100),
				"net_commission_value": flt(commissions[comm].get('commission_value', 0) + commissions[comm].get("primary_supervision_commission",0) + commissions[comm].get("secondary_supervision_commission",0), 2),
				"other_commission": flt(commissions[comm].get('other_commission', 0), 2),
				"total": flt(commissions[comm].get('commission_value', 0) + commissions[comm].get("primary_supervision_commission",0) + commissions[comm].get("secondary_supervision_commission",0) +  commissions[comm].get('other_commission', 0), 2)
			})

		if msg:
			msg = "The following Sales Men Don't Have a Quarter Quota Record for the Current Quarter: " + msg
			frappe.msgprint(msg)
	
	return results

def get_commissions(filters):
	"""Get the Commission Values for each sales man in a certaine quarter of a year
	
	Returns a dictonary of sales men with the following data:

	quota: required quota of the quarter
	achieve_value: the achievment value of the sales man on his direct SOs 
	achieve_percent:percentage of achievment
	total_achieve_value: the achievment value of the sales man on his direct SOs + his subordinates SOs
	achieved_target: the percentage of the commission he will take depending on his achievement percentage
	avg_comm_percent: the average of the commission percentage from his all SOs
	kpi: KPI of the sales man
	direct_sales_contribution: how much the sales man contribute in his direct SOs
	commission_value: the commission he should get from his direct SOs
	other_commission: the commission he should get from other SOs he contributed in
	extra_commission: the extra commission percentage
	primary_supervision_commission & secondary_supervision_commission: how much he will take as an extra commission from his subordinates SOs

	"""
	
	# get achievement values for each sales man
	if not filters.get('quarter') or not filters.get('year'): return None, None

	sales_orders = get_sales_orders(filters)
	total_achievement_values, achievement_values, leaders = get_achievement_values(sales_orders)
	list_filters = {}
	list_filters['year'] = filters['year']
	list_filters['quarter'] = filters['quarter']
	
	# get the rule that calculate the percentage of the commission percentage
	# that is depent on the achievement percentage for the quarter
	default_rule = get_default_rule()
	sales_men_comm = {}
	msg = ""
	for sales_man in total_achievement_values:
		list_filters['sales_man'] = sales_man
		
		if not frappe.db.exists("Quarter Quota", list_filters): 
			msg += "</br> {}".format(sales_man) 
			continue

		quarter_quota = frappe.get_doc("Quarter Quota", list_filters)
		
		# Calculate the achievement percentage depending on the quarter quota
		achievemnt_percent = total_achievement_values[sales_man] / quarter_quota.total_quota * 100 if quarter_quota.total_quota else 100
	
		# Calculate the commission milestone percentage depending on the rule
		comm = calculate_commission(achievemnt_percent, default_rule)
		if not sales_men_comm.get(sales_man):
			sales_men_comm[sales_man] = {}

		sales_men_comm[sales_man]['kpi'] = quarter_quota.kpi
		sales_men_comm[sales_man]['achieve_percent'] = achievemnt_percent
		sales_men_comm[sales_man]['quota'] = quarter_quota.total_quota
		sales_men_comm[sales_man]['achieve_value'] = achievement_values.get(sales_man, 0)
		sales_men_comm[sales_man]['total_achieve_value'] = total_achievement_values[sales_man]
		sales_men_comm[sales_man]['achieved_target'] = comm
		sales_men_comm[sales_man]['leaders'] = leaders.get(sales_man, [])

		if not comm: continue
		
		sales_orders = get_sales_orders(filters, sales_man)
		# Calculate commissions from all sales order of the quarter
		for so in sales_orders:
			calculate_commission_in_so(so.sales_order, sales_men_comm, comm, list_filters)
		sales_men_comm[sales_man]['avg_comm_percent'] = sales_men_comm[sales_man].get('avg_comm_percent') / len(sales_orders)
		#sales_men_comm[sales_man]['default_achieving_percent'] = total_achievement_values[sales_man] * sales_men_comm[sales_man]['avg_comm_percent'] / 100
		#sales_men_comm[sales_man]['total_achieve_value'] = total_achievement_values[sales_man]

	# msg is all of the sales men who don't have quarter quota
	set_leaders_extra(sales_men_comm, filters)
	sales_men_comm = get_permitted_rows(sales_men_comm)
	return sales_men_comm, msg

def get_achievement_values(sales_orders):
	total_achievement_values, achievement_values, emp_leaders = {}, {}, {}
	checked_sos = []
	for so in sales_orders:
		
		if so.sales_order in checked_sos: continue
		checked_sos.append(so.sales_order)


		achievement_values[so.primary_sales_man] = achievement_values.get(so.primary_sales_man, 0) + so.base_expected_profit_loss_value
		total_achievement_values[so.primary_sales_man] = total_achievement_values.get(so.primary_sales_man,0) + so.base_expected_profit_loss_value

		employee = get_employee(so.primary_sales_man)
		leaders = get_leaders(employee.name, "name", "reports_to", None)

		if leaders:
			for leader in leaders:
				leader_doc = frappe.get_doc("Employee", leader)
				if check_if_leader(leader_doc):
					sales_person = frappe.db.get_value("Sales Person", {"employee": leader}, "name")
					
					if not emp_leaders.get(so.primary_sales_man):
						emp_leaders[so.primary_sales_man] = [sales_person]
					elif sales_person not in emp_leaders[so.primary_sales_man]:
						emp_leaders[so.primary_sales_man].append(sales_person)

					if not sales_person: continue

					total_achievement_values[sales_person] = total_achievement_values.get(sales_person, 0) + so.base_expected_profit_loss_value
	
	return total_achievement_values, achievement_values, emp_leaders

def get_sales_orders(filters, sales_man = None):
	conditions = get_conditions(filters)
	
	strQuery= """
		select so.name as sales_order, so.base_expected_profit_loss_value as base_expected_profit_loss_value, so.primary_sales_man as primary_sales_man
		from `tabSales Order` as so
		where so.submitting_date != '' and so.submitting_date is not null and so.docstatus = 1
		and so.primary_sales_man != '' and so.primary_sales_man is not null
		and so.base_expected_profit_loss_value > 0
		{conditions}
		""".format(conditions = conditions)
	if sales_man:
		strQuery += " and so.primary_sales_man = '{primary_sales_man}'".format(primary_sales_man = sales_man)
	
	return frappe.db.sql(strQuery, filters, as_dict = 1)

def calculate_commission_in_so(sales_order, sales_men_comm, achievement_commission, filters, sales_man = None):
	
	doc = frappe.get_doc("Sales Order", sales_order)
	
	profit_loss_value = doc.base_expected_profit_loss_value * achievement_commission / 100 * doc.commission_percentage / 100
	
	sales_men_comm[doc.primary_sales_man]['avg_comm_percent'] = sales_men_comm[doc.primary_sales_man].get('avg_comm_percent', 0) + doc.commission_percentage
	
	for row in doc.get("sales_commission"):
		
		if sales_man and sales_man != row.sales_person: continue
		
		new_comm = profit_loss_value * (row.comm_percent / 100)
		
		if not sales_men_comm.get(row.sales_person):
			sales_men_comm[row.sales_person] = {}

		if sales_men_comm[row.sales_person].get('kpi'):
			kpi = sales_men_comm[row.sales_person]['kpi']
		else:
			kpi = frappe.db.get_value('Quarter Quota', {'sales_man': row.sales_person, 'quarter': filters['quarter'], 'year': filters['year'], 'docstatus': 1}, 'kpi')
			if not kpi:
				kpi = 100
		if not sales_men_comm[row.sales_person].get('quota'):
			sales_men_comm[row.sales_person]['quota'] = frappe.db.get_value('Quarter Quota', {'sales_man': row.sales_person, 'quarter': filters['quarter'], 'year': filters['year'], 'docstatus': 1}, 'quota')
		
		
		if row.sales_person == doc.primary_sales_man:
			sales_men_comm[row.sales_person]['direct_sales_contribution'] = sales_men_comm.get(row.sales_person).get('direct_sales_contribution', 0) + doc.base_expected_profit_loss_value * (row.comm_percent / 100)
			sales_men_comm[row.sales_person]['commission_value'] = sales_men_comm.get(row.sales_person).get('commission_value', 0) + new_comm
		else:
			sales_men_comm[row.sales_person]['other_commission'] = sales_men_comm[row.sales_person].get('other_commission', 0) + new_comm * kpi / 100
		
def set_leaders_extra(sales_men_comm, filters):
	conditions = get_conditions(filters)

	for sales_man in sales_men_comm:
		comm = sales_men_comm[sales_man].get('achieved_target', 0)
		if  comm <= 0: continue
		res = frappe.db.sql("""
			 select name, base_expected_profit_loss_value as total, prm_sup_percentage, sec_sup_percentage
			 from `tabSales Order` as so
			 where primary_sales_man = '{sales_man}' 
			 and docstatus = 1 and so.base_expected_profit_loss_value > 0
			 {conditions}
			""".format(sales_man = sales_man, conditions = conditions), filters, as_dict = 1)
		
		if not res or len(res[0])<= 0: continue

		for so in res:			
			own_level = set_extra_on_direct_so(sales_men_comm, sales_man, so)

			if own_level == "primary": set_extra_on_indirect_so(sales_men_comm, sales_man, so, "secondary")
			else: set_extra_on_indirect_so(sales_men_comm, sales_man, so)


def set_extra_on_direct_so(sales_men_comm, sales_man, sales_order):
	employee = get_employee(sales_man)

	if not check_if_leader(employee): return

	prm_extra = sales_order.prm_sup_percentage or 1.5

	comm = sales_men_comm[sales_man].get('achieved_target', 0)

	if comm:
		sales_men_comm[sales_man]['primary_supervision_commission'] = sales_men_comm[sales_man].get('primary_supervision_commission', 0) + (sales_order.total * prm_extra / 100 * comm / 100)
		return "primary"
	
def set_extra_on_indirect_so(sales_men_comm, sales_man, sales_order, leader_level = None):
	employee = get_employee(sales_man)
	set_employee = False
	if sales_men_comm[sales_man].get("leaders"):
		leaders = sales_men_comm[sales_man]["leaders"]
		set_employee = True
	else:
		leaders = get_leaders(employee.name, "name", "reports_to", None)

	own_so = False

	if not leaders: 
		leaders = [employee.name]
		leader_level = "secondary"
		own_so = True

	if leader_level == "secondary":
		level = 'secondary'
		extra = sales_order.sec_sup_percentage or 0.75

	else:
		level = 'primary'
		extra = sales_order.prm_sup_percentage or 1.5


	for leader in leaders:
		
		if set_employee:
			leader_doc = get_employee(leader)
			if leader_doc:
				leader = leader_doc.name
			else: frappe.throw("There is no Employee record for sales man: "+ leader)
		leader = frappe.get_doc("Employee", leader)

		if not check_if_leader(leader) : return

		sales_person = frappe.db.get_value("Sales Person", {"employee": leader.name}, "name")
		
		if not sales_person or not sales_person in sales_men_comm: return
		
		comm = sales_men_comm[sales_person].get('achieved_target', 0)

		if comm:			
			sales_men_comm[sales_person][level+'_supervision_commission'] = sales_men_comm[sales_person].get(level+'_supervision_commission', 0) + sales_order.total * extra / 100 * comm / 100

			if not own_so:
				sales_men_comm[sales_person]["achiever_sub_pl"] = sales_men_comm[sales_person].get("achiever_sub_pl", 0) + sales_order.total
		
		if level == "secondary":
			return
		else:
			level = "secondary"
			extra = sales_order.sec_sup_percentage or 0.75

def check_if_leader(employee):
	if employee.position != "Senior" and\
		employee.position != "Team Leader" and\
		employee.position != "Manager" : 
		return False
	
	if employee.position == "Senior":
		sales_person = frappe.db.get_value("Sales Person", {"employee": employee.name}, "name")
		if sales_person:
			is_leader, _ = check_if_team_leader(sales_person)
			if not is_leader: return
		else: return False
	return True

def get_permitted_rows(sales_men_comm):
	if frappe.session.user != "Administrator" and "0 Accounting - Sales Persons Commission Report" not in frappe.get_roles():		
		employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
		
		if not employee: return

		sales_person = frappe.db.get_value("Sales Person", {"employee": employee}, "name")
		
		if not sales_person: return

		dict_sm = {}
		
		if sales_men_comm.get(sales_person):
			dict_sm = {sales_person : sales_men_comm[sales_person]}
		employees = get_employees(employee, "name", "reports_to")
		if not employees: return dict_sm
		for emp in employees:
			sp = frappe.db.get_value("Sales Person", {"employee": emp}, "name")
			if not sp or not sales_men_comm.get(sp): continue
			
			dict_sm[sp] = sales_men_comm[sp]
		return dict_sm
	
	else: return sales_men_comm

def get_annual_commission(filters):
	"Get the Additional Annual Commission"

	annual_commission, msgs = {}, ''
	results = {}
	# Iterate through quarters to get the total achievement
	for q in ["Q1", "Q2", "Q3", "Q4"]:
		filters['quarter'] = q

		# Get the commission and the achievement for the sales men during the quarter
		commissions = get_commissions(filters)[0]
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
def create_journal_entry(args):
	args = json.loads(args)
	if not args.get("year") or not args.get("quarter") and not args.get("annual"):
		frappe.throw("Select Year and Quarter to create the journal entry")
	
	if args.get("annual"):
		commissions, msg = get_annual_commission(args)
	else:
		commissions, msg = get_commissions(args)
	
	if msg:
		msg = "Missing records in Quarter Quota: " + msg
		frappe.throw(msg)
	if commissions:
		doc = frappe.new_doc("Journal Entry")
		doc.is_quarter_commission = 1
		doc.year = args.get("year")
		doc.quarter = args.get("quarter") if args.get("quarter") else ''
		accounts = []
		for comm in commissions:
			emp = frappe.db.get_value("Sales Person", comm, "employee")
			if emp:
				accounts.append({
					'doctype':'Journal Entry Account',
					'party_type': 'Employee',
					'party': emp,
					'debit_in_account_currency': commissions[comm].get("total") or commissions[comm].get("additional_annual_comm"),
					'debit': commissions[comm].get("total") or commissions[comm].get("additional_annual_comm")
				})
			else:
				accounts.append({
					'debit_in_account_currency': commissions[comm].get("total") or commissions[comm].get("additional_annual_comm"),
					'debit': commissions[comm].get("total") or commissions[comm].get("additional_annual_comm")
				})
			accounts.append({
				'account': '11001002 - Cash EGP - S',
				'credit_in_account_currency': commissions[comm].get("total") or commissions[comm].get("additional_annual_comm"),
				'credit': commissions[comm].get("total") or commissions[comm].get("additional_annual_comm")
			})
		doc.set("accounts", accounts)
		return doc

@frappe.whitelist()
def apply_comm_on_so(args):
	args = json.loads(args)
	if not args.get("year") or not args.get("quarter"):
		frappe.throw("Select Year and Quarter to Apply Commissions")

	commissions, msg = get_commissions(args)
	if msg:
		msg = "The following Sales men don't have a Quarter Quota record for the current Quarter: " + msg
		frappe.throw(msg)
	if commissions:
		conditions = get_conditions(args)
		sales_men = ""
		for sales_man in commissions:
			if commissions[sales_man].get("supervision_commission"):
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

			achieved_target = commissions[doc.primary_sales_man].get('achieved_target', 0)
			if achieved_target <= 0: continue

			commission = doc.base_expected_profit_loss_value * doc.commission_percentage / 100 * achieved_target / 100
			
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


	