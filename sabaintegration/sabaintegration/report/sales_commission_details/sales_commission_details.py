# Copyright (c) 2023, Ahmad and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from sabaintegration.sabaintegration.doctype.commission_rule.commission_rule import calculate_commission, get_default_rule
from sabaintegration.overrides.employee import get_employees
from sabaintegration.sabaintegration.doctype.default_kpi.default_kpi import get_default_kpi
from sabaintegration.sabaintegration.report.quota import is_admin, get_employee, check_if_team_leader, QuotaCalculations

ROLE, DOCTYPE = "0 Accounting - Sales Persons Commission Report", "Sales Person"
default_rule = get_default_rule()

def execute(filters=None):
	data = get_data(filters)
	columns = get_columns(data)
	return columns, data

def get_columns(data):
	columns = [
		{
			"label": _("Sales Order"),
			"fieldname": "sales_order",
			"fieldtype": "Link",
			"width": 100,
			"options": "Sales Order"
		},
		{
			"label": _("Primary Sales Man"),
			"fieldname": "primary_sales_man",
			"fieldtype": "Link",
			"width": 100,
			"options": "Sales Person"
		},
		{
			"label": _("Team Primary Supervisior"),
			"fieldname": "team_primary_supervisior",
			"fieldtype": "Link",
			"width": 100,
			"options": "Sales Person"
		},
		{
			"label": _("Team Secondary Supervisior"),
			"fieldname": "team_secondary_supervisior",
			"fieldtype": "Link",
			"width": 100,
			"options": "Sales Person"
		},
		{
			"label": _("Expected Profit & Loss Value"),
			"fieldname": "base_expected_profit_loss_value",
			"fieldtype": "Currency",
			"width": 120,
			"options": "Company:company:default_currency"
		},
		{
			"label": _("Commission Percentage"),
			"fieldname": "commission_percentage",
			"fieldtype": "Percent",
			"width": 100,
		},
		{
			"label": _("Sales Man"),
			"fieldname": "sales_man",
			"fieldtype": "Link",
			"width": 100,
			"options": "Sales Person"
		},
		{
			"label": _("Stage Title"),
			"fieldname": "stage_title",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Stage Commission"),
			"fieldname": "stage_commission",
			"fieldtype": "Percent",
			"width": 100,
		},
		{
			"label": _("Sales Stage Expected P&L"),
			"fieldname": "sales_stage",
			"fieldtype": "Currency",
			"width": 100,
			"options": "Company:company:default_currency"
		},
		{
			"label": _("Default Achieving Percentage"),
			"fieldname": "default_achieving_percent",
			"fieldtype": "Currency",
			"width": 120,
			"options": "Company:company:default_currency"
		},
		{
			"label": _("Achievement Percentage"),
			"fieldname": "achieve_percent",
			"fieldtype": "Percent",
			"width": 100,
		},
		{
			"label": _("Commission Value"),
			"fieldname": "base_commission_value",
			"fieldtype": "Currency",
			"width": 120,
			"options": "Company:company:default_currency"
		},
		{
			"label": _("KPI"),
			"fieldname": "kpi",
			"fieldtype": "Percent",
			"width": 100,
		},
		{
			"label": _("NET Commission Value"),
			"fieldname": "base_net_commission_value",
			"fieldtype": "Currency",
			"width": 120,
			"options": "Company:company:default_currency"
		},
	]
	primary, secondary = False, False 
	if not data: return
	for d in data:
		if d.default_primary_supervision and not primary:
			columns.extend([
				{
					"label": _("Default Primary Supervision Achievement Value"),
					"fieldname": "default_primary_supervision",
					"fieldtype": "Currency",
					"width": 120,
					"options": "Company:company:default_currency"
				},
				{
					"label": _("Primary Supervision Achievement"),
					"fieldname": "default_primary_achievement",
					"fieldtype": "Percent",
					"width": 100,
				},
				{
					"label": _("Primary Supervision Commission Value"),
					"fieldname": "primary_supervision_commission",
					"fieldtype": "Currency",
					"width": 120,
					"options": "Company:company:default_currency"
				}]
			)
			primary = True
		if d.default_secondary_supervision and not secondary:
			columns.extend(
				[{
					"label": _("Default Secondary Supervision Achievement Value"),
					"fieldname": "default_secondary_supervision",
					"fieldtype": "Currency",
					"width": 120,
					"options": "Company:company:default_currency"
				},
				{
					"label": _("Secondary Supervision Achievement"),
					"fieldname": "default_secondary_achievement",
					"fieldtype": "Percent",
					"width": 100,
				},
				{
					"label": _("Secondary Supervision Commission Value"),
					"fieldname": "secondary_supervision_commission",
					"fieldtype": "Currency",
					"width": 120,
					"options": "Company:company:default_currency"
				}]
			)
			secondary = True
		if primary and secondary: break
	return columns

def get_conditions(filters):
	conditions = ""
	if filters.get("primary_sales_man"):
		conditions += " and so.primary_sales_man = %(primary_sales_man)s"
	if filters.get("sales_order"):
		conditions += " and comm.parent = %(sales_order)s"
	if filters.get("sales_man"):
		conditions += " and comm.sales_person = %(sales_man)s"
	if filters.get("year"):
		conditions += " and EXTRACT(YEAR FROM so.submitting_date) = %(year)s"
	if filters.get("quarter"):
		conditions += " and CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.submitting_date) / 3.0)) = %(quarter)s"
	if filters.get("supervisior"):
		query = ""
		admin, sales_person = is_admin(frappe.session.user, ROLE, DOCTYPE)
		
		if not admin and sales_person:

			sales_man = employees_query(sales_person, filters["supervisior"])
			if sales_man:
				query = employees_query(filters["supervisior"])

		else:
			query = employees_query(filters["supervisior"])

		if query:
			conditions += f" and so.primary_sales_man in ({query})"
	return conditions

def employees_query(supervisior, sales_man = None):
	def get_msg(sales_man, recordtype):
		return "There is no {0} record for {1}.".format(recordtype, sales_man)
	
	if sales_man and sales_man == supervisior:
		return sales_man

	employee = get_employee(DOCTYPE, supervisior)
	if not employee:
		frappe.throw(get_msg(supervisior, "Employee"))
	employees = get_employees(employee.name, "name", "reports_to")
	str_emps = ""
	if not employees: 
		if not sales_man:
			return "'{}'".format(supervisior)
		if sales_man and sales_man == supervisior:
			return sales_man
		else: return
	for emp in employees:
		sales_person = frappe.db.get_value("Sales Person", {"employee": emp}, "name")
		if not sales_person: continue

		if sales_man and sales_man == sales_person:
			return sales_man
		elif not sales_man:
			str_emps += " '{}',".format(sales_person)
	if sales_man: 
		return
	return str_emps + " '{}'".format(supervisior)

def get_data(filters):
	conditions = get_conditions(filters)
	employees, employees_list = "", []
	admin, sales_person = is_admin(frappe.session.user, ROLE, DOCTYPE)
		
	if not admin and sales_person:
		if not filters.get("sales_man"):
			emp = employees_query(sales_person)
			employees_list = emp[2:-1].split("', '")
			employees = "and (so.primary_sales_man in ({0}) or comm.sales_person = '{1}' ) ".format(emp, sales_person)
		else:
			sales_man = employees_query(sales_person, filters.get("sales_man", None))
			employees_list = sales_man.split("', '")
			if not sales_man: return

			employees = "and comm.sales_person = '{}' ".format(sales_man)
	
	strQuery = """
		select distinct so.name as sales_order, so.primary_sales_man, so.base_expected_profit_loss_value, 
			so.commission_percentage, so.prm_sup_percentage, so.sec_sup_percentage,
			(so.base_expected_profit_loss_value * comm.comm_percent / 100) as sales_stage,
			(so.base_expected_profit_loss_value * so.commission_percentage / 100 * comm.comm_percent / 100) as default_achieving_percent,
			comm.sales_person as sales_man, comm.stage_title, comm.comm_percent as stage_commission, comm.base_commission_value,
			qq.kpi, comm.base_net_commission_value, qq.total_quota
		from `tabSales Order` as so
		inner join `tabSales Commission` as comm on so.name = comm.parent
		left outer join `tabQuarter Quota` as qq on qq.sales_man = comm.sales_person and qq.docstatus = 1 and qq.year = EXTRACT(YEAR FROM so.submitting_date) and qq.quarter = CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.submitting_date) / 3.0)) 
    	where so.docstatus = 1	and so.primary_sales_man != '' and so.primary_sales_man is not null	
		{conditions}
		{employees}
		order by so.name, comm.sales_person
	""".format(conditions = conditions, employees = employees)

	res = frappe.db.sql(strQuery, filters, as_dict = 1)
	
	sales_men_comm = {}

	q = QuotaCalculations({
		"doctype": DOCTYPE,
		"filters": filters,
		"role": ROLE,
		"user": frappe.session.user,
		"rule": default_rule
	})

	_, _, leaders = q.get_achievement_values()

	sales_person, get_supervision = None, False
	if frappe.session.user == "Administrator" or\
	 ROLE in frappe.get_roles():
		get_supervision = True
	
	else:
		employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
			
		if not employee: return

		sales_person = frappe.db.get_value("Sales Person", {"employee": employee}, "name")
	
	kpi_doc = False
	if frappe.db.exists("Default KPI", {
		"year": filters.get("year"),
		"quarter": filters.get("quarter"),
		"docstatus": 1
	}):
		kpi_doc = True
	
	for row in res:	
		if not row['kpi']:
			if kpi_doc:
				row['kpi'] = get_default_kpi(
						doc = 'Quarter Quota',
						person = row.engineer,
						year = filters['year'],
						quarter = filters['quarter']
					)
		if sales_men_comm.get(row.primary_sales_man):
			row['achieve_percent'] = sales_men_comm.get(row.primary_sales_man)
		else: row['achieve_percent'] = get_achieve_percent(row.primary_sales_man, filters)
		sales_men_comm[row.primary_sales_man] = row['achieve_percent']

		get_leaders_supervision_values(row, leaders, filters, sales_person, employees_list, get_supervision)

	return res

def get_achieve_percent(sales_man, filters):

	if not frappe.db.exists("Quarter Quota", {"sales_man": sales_man, "year": filters.get("year"), "quarter": filters.get("quarter")}): 
		return 0

	return frappe.db.get_value("Quarter Quota", {"sales_man": sales_man, "year": filters.get("year"), "quarter": filters.get("quarter")}, "achievement_percentage")

def get_leaders_supervision_values(row, leaders, filters, sales_person, employees_list, get_supervision):		
	secondary = True
	
	if leaders.get(row.primary_sales_man):
		employee = frappe.db.get_value("Sales Person", row.primary_sales_man, "employee")
		if not employee: return

		doc = frappe.get_doc("Employee", employee)

		if doc.position == "Team Leader":
			row['team_primary_supervisior'] = row.primary_sales_man
			row['team_secondary_supervisior'] = leaders[row.primary_sales_man][0]

		elif doc.position == "Manager":
			row['team_primary_supervisior'] = row.primary_sales_man
			row['team_secondary_supervisior'] = row.primary_sales_man

		elif doc.position == "Senior":
			is_leader = check_if_team_leader(doc)
			if is_leader:
				
				row['team_primary_supervisior'] = row.primary_sales_man
				row['team_secondary_supervisior'] = leaders[row.primary_sales_man][0]
			else:
				row['team_primary_supervisior'] = leaders[row.primary_sales_man][0]
				if len(leaders[row.primary_sales_man]) > 1:
					row['team_secondary_supervisior'] = leaders[row.primary_sales_man][1]
				else:
					secondary = False
		else:
			row['team_primary_supervisior'] = leaders[row.primary_sales_man][0]
			
			if len(leaders[row.primary_sales_man]) > 1:
				row['team_secondary_supervisior'] = leaders[row.primary_sales_man][1]
			else:
				secondary = False
	else:
		row['team_primary_supervisior'] = row.primary_sales_man
		row['team_secondary_supervisior'] = row.primary_sales_man

	if get_supervision or row['team_primary_supervisior'] == sales_person or row['team_primary_supervisior'] in employees_list:	
		get_leader_supervision_values(row, filters, "primary")
	if secondary:
		if get_supervision or row['team_secondary_supervisior'] == sales_person or row['team_secondary_supervisior'] in employees_list:		
			get_leader_supervision_values(row, filters, "secondary")

def get_leader_supervision_values(row, filters, level):
	leader = row['team_'+level+'_supervisior']
	if not frappe.db.exists("Quarter Quota", {
		"sales_man": leader,
		"year": filters.get("year"),
		"quarter": filters.get("quarter"),
		"docstatus": 1
	}):
		frappe.throw("There is no Quarter Quota for Sales Person {}".format(leader))
	doc = frappe.get_doc("Quarter Quota", {
		"sales_man": leader,
		"year": filters.get("year"),
		"quarter": filters.get("quarter"),
		"docstatus": 1
	})
	if level == "primary": extra = row.prm_sup_percentage
	else: extra = row.sec_sup_percentage
	row["default_"+level+"_achievement"] = doc.achievement_percentage

	
	if row["base_net_commission_value"] == 0: return

	row["default_"+level+"_supervision"] = extra * row["sales_stage"] / 100
	
	comm = calculate_commission(row["default_"+level+"_achievement"], default_rule)
	if comm:
		row[level+"_supervision_commission"] = row["default_"+level+"_supervision"] * comm / 100
	
def get_leader(leaders, filters):
	if not leaders: return
	for leader in leaders:
		to_get_extra = frappe.db.get_value("Quarter Quota", {
			"sales_man": leader,
			"year": filters.get("year"),
			"quarter": filters.get("quarter"),
			"docstatus": 1
		}, "to_get_extra")
		if to_get_extra:
			return leader
	