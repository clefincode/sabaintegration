# Copyright (c) 2023, Ahmad and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from sabaintegration.sabaintegration.doctype.pre_sales_incentive_rule.pre_sales_incentive_rule import calculate_incentive, get_default_rule
from sabaintegration.overrides.employee import get_employees
from sabaintegration.sabaintegration.doctype.default_kpi.default_kpi import get_default_kpi
from sabaintegration.sabaintegration.report.quota import is_admin, check_if_team_leader, get_employee, QuotaCalculations

ROLE, DOCTYPE = "0 Accounting - Pre-Sales Activity Incentive Report", "Pre-Sales Engineer"
default_rule = get_default_rule()

def execute(filters=None):
	data = get_data(filters)
	columns = get_columns()
	return columns, data

def get_columns():
	columns = [
		{
			"label": _("Sales Order"),
			"fieldname": "sales_order",
			"fieldtype": "Link",
			"width": 100,
			"options": "Sales Order"
		},
		{
			"label": _("Sales Order Title"),
			"fieldname": "title",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Total"),
			"fieldname": "base_grand_total",
			"fieldtype": "Currency",
			"width": 120,
			"options": "Company:company:default_currency"
		},
		{
			"label": _("Expected Profit & Loss Value"),
			"fieldname": "base_expected_profit_loss_value",
			"fieldtype": "Currency",
			"width": 120,
			"options": "Company:company:default_currency"
		},
		{
			"label": _("Pre-Sales Engineer"),
			"fieldname": "engineer_type",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": _("Team Primary Supervisior"),
			"fieldname": "team_primary_supervisior",
			"fieldtype": "Link",
			"width": 100,
			"options": "Pre-Sales Engineer"
		},
		{
			"label": _("Team Secondary Supervisior"),
			"fieldname": "team_secondary_supervisior",
			"fieldtype": "Link",
			"width": 100,
			"options": "Pre-Sales Engineer"
		},
		
		{
			"label": _("Contribution Percentage"),
			"fieldname": "contribution_percentage",
			"fieldtype": "Percent",
			"width": 100,
		},
		{
			"label": _("Contribution Value"),
			"fieldname": "contribution_value",
			"fieldtype": "Currency",
			"width": 100,
			"options": "Company:company:default_currency"
		},
		{
			"label": _("Member"),
			"fieldname": "member",
			"fieldtype": "Link",
			"width": 100,
			"options": "Pre-Sales Engineer"
		},
		{
			"label": _("Reason"),
			"fieldname": "reason",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Incentive Percentage"),
			"fieldname": "incentive_percentage",
			"fieldtype": "Percent",
			"width": 100,
		},
		{
			"label": _("Default Achieving Value"),
			"fieldname": "default_achieving_value",
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
		# {
		# 	"label": _("Incentive Value"),
		# 	"fieldname": "base_incentive_value",
		# 	"fieldtype": "Currency",
		# 	"width": 120,
		# 	"options": "Company:company:default_currency"
		# },
		{
			"label": _("KPI"),
			"fieldname": "kpi",
			"fieldtype": "Percent",
			"width": 100,
		},
		{
			"label": _("NET Incentive Value"),
			"fieldname": "base_net_incentive_value",
			"fieldtype": "Currency",
			"width": 120,
			"options": "Company:company:default_currency"
		},
		{
			"label": _("Incentive Value to NET Total"),
			"fieldname": "incentive_to_total",
			"fieldtype": "Percent",
			"width": 100,
		},
	]
	return columns

def get_conditions(filters):
	conditions = ""
	if filters.get("sales_order"):
		conditions += " and pre_sales.parent = %(sales_order)s"
	if filters.get("engineer"):
		conditions += " and pre_sales.engineer = %(engineer)s"
	if filters.get("year"):
		conditions += " and EXTRACT(YEAR FROM so.submitting_date) = %(year)s"
	if filters.get("quarter"):
		conditions += " and CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.submitting_date) / 3.0)) = %(quarter)s"
	if filters.get("supervisior"):
		query = ""
		admin, engineer = is_admin(frappe.session.user, ROLE, DOCTYPE)
		
		if not admin and engineer:
			engs = employees_query(engineer, filters["supervisior"])
			if engs:
				query = employees_query(filters["supervisior"])

		else:
			query = employees_query(filters["supervisior"])

		if query:
			conditions += f" and pre_sales.engineer in ({query})"
	return conditions

def employees_query(supervisior, engineer = None):
	def get_msg(engineer, recordtype):
		return "There is no {0} record for {1}.".format(recordtype, engineer)
	
	if engineer and engineer == supervisior:
		return engineer

	employee = get_employee(DOCTYPE ,supervisior)
	if not employee:
		frappe.throw(get_msg(supervisior, "Employee"))
	employees = get_employees(employee.name, "name", "reports_to")
	str_emps = ""
	if not employees: 
		if not engineer:
			return "'{}'".format(supervisior)
		if engineer and engineer == supervisior:
			return engineer
		else: return
	for emp in employees:
		eng = frappe.db.get_value("Pre-Sales Engineer", {"employee": emp}, "name")
		if not eng: continue

		if engineer and engineer == eng:
			return engineer
		elif not engineer:
			str_emps += " '{}',".format(eng)
	if engineer: 
		return
	return str_emps + " '{}'".format(supervisior)

def get_data(filters):
	conditions = get_conditions(filters)
	employees, employees_list = "", []

	admin, engineer = is_admin(frappe.session.user, ROLE, DOCTYPE)
		
	if not admin and engineer:

		if not filters.get("engineer"):
			emp = employees_query(engineer)
			employees_list = emp[2:-1].split("', '")
			employees = "and (pre_sales.engineer in ({0}) ) ".format(emp, engineer)
		else:
			eng = employees_query(engineer, filters.get("engineer", None))
			employees_list = eng.split("', '")
			if not eng: return

			employees = "and pre_sales.engineer = '{}' ".format(eng)
	
	strQuery = """
		select distinct so.name as sales_order, so.title, so.base_expected_profit_loss_value, so.base_grand_total,
			'Direct Contribution' as engineer_type, pre_sales.engineer, 'Pre-Sales Engineer' as reason,
			pre_sales.contribution_percentage,
			(so.base_expected_profit_loss_value * pre_sales.contribution_percentage / 100) as contribution_value,
			(so.base_expected_profit_loss_value * pre_sales.contribution_percentage / 100 * qq.incentive_percentage / 100) as default_achieving_value,
			qq.kpi,	pre_sales.base_net_incentive_value, pre_sales.base_incentive_value, qq.total_quota, qq.incentive_percentage,
			pre_sales.base_net_incentive_value / so.base_net_total * 100 as incentive_to_total 
		from `tabSales Order` as so
		inner join `tabPre-Sales Incentive` as pre_sales on so.name = pre_sales.parent
		left outer join `tabPre-Sales Quarter Quota` as qq on qq.engineer = pre_sales.engineer and qq.docstatus = 1 and qq.year = EXTRACT(YEAR FROM so.submitting_date) and qq.quarter = CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.submitting_date) / 3.0))
		where so.docstatus = 1
		{conditions}
		{employees}
		order by so.name, pre_sales.engineer
	""".format(conditions = conditions, employees = employees)

	res = frappe.db.sql(strQuery, filters, as_dict = 1)
	q = QuotaCalculations({
		"doctype": DOCTYPE,
		"filters": filters,
		"role": ROLE,
		"user": frappe.session.user,
		"rule": default_rule
	})
	engineers_comm = {}

	_, _, leaders = q.get_achievement_values()

	engineer, get_supervision = None, False
	if frappe.session.user == "Administrator" or\
	 ROLE in frappe.get_roles():
		get_supervision = True
	
	else:
		employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
			
		if not employee: return

		engineer = frappe.db.get_value("Pre-Sales Engineer", {"employee": employee}, "name")

	kpi_doc = False
	if frappe.db.exists("Default KPI", {
		"year": filters.get("year"),
		"quarter": filters.get("quarter"),
		"docstatus": 1
	}):
		kpi_doc = True
	total_results = []
	for row in res:
		row['member'] = row['engineer']	
		if not row['kpi']:
			if kpi_doc:
				row['kpi'] = get_default_kpi(
						doc = 'Pre-Sales Quarter Quota',
						person = row.engineer,
						year = filters['year'],
						quarter = filters['quarter']
					)
		if engineers_comm.get(row.engineer):
			row['achieve_percent'] = engineers_comm.get(row.engineer)
		else: row['achieve_percent'] = get_achieve_percent(row.engineer, filters)
			
		engineers_comm[row.engineer] = row['achieve_percent']

		total_results.append(row)
		new_rows = get_leaders_supervision_values(row, leaders, filters, engineer, employees_list, get_supervision)

		total_results.extend(new_rows)
	return total_results

def get_achieve_percent(engineer, filters):

	if not frappe.db.exists("Pre-Sales Quarter Quota", {"engineer": engineer, "year": filters.get("year"), "quarter": filters.get("quarter")}): 
		return 0

	return frappe.db.get_value("Pre-Sales Quarter Quota", {"engineer": engineer, "year": filters.get("year"), "quarter": filters.get("quarter")}, "achievement_percentage")

def get_leaders_supervision_values(row, leaders, filters, engineer, employees_list, get_supervision):		
	secondary = True
	
	if leaders.get(row.engineer):
		employee = frappe.db.get_value("Pre-Sales Engineer", row.engineer, "employee")
		if not employee: return

		doc = frappe.get_doc("Employee", employee)

		if doc.position == "Team Leader":
			row['team_primary_supervisior'] = row.engineer
			row['team_secondary_supervisior'] = leaders[row.engineer][0]

		elif doc.position == "Manager":
			row['team_primary_supervisior'] = row.engineer
			row['team_secondary_supervisior'] = row.engineer

		elif doc.position == "Senior":
			is_leader = check_if_team_leader(doc)
			if is_leader:
				
				row['team_primary_supervisior'] = row.engineer
				row['team_secondary_supervisior'] = leaders[row.engineer][0]
			else:
				row['team_primary_supervisior'] = leaders[row.engineer][0]
				if len(leaders[row.engineer]) > 1:
					row['team_secondary_supervisior'] = leaders[row.engineer][1]
				else:
					secondary = False
		else:
			row['team_primary_supervisior'] = leaders[row.engineer][0]
			
			if len(leaders[row.engineer]) > 1:
				row['team_secondary_supervisior'] = leaders[row.engineer][1]
			else:
				secondary = False
	else:
		row['team_primary_supervisior'] = row.engineer
		row['team_secondary_supervisior'] = row.engineer

	levels = []
	if get_supervision or row['team_primary_supervisior'] == engineer or row['team_primary_supervisior'] in employees_list:
		get_leader_supervision_values(row, filters, "primary")
		levels.append("primary")
	if secondary:
		if get_supervision or row['team_secondary_supervisior'] == engineer or row['team_secondary_supervisior'] in employees_list:		
			get_leader_supervision_values(row, filters, "secondary")
			levels.append("secondary")

	return set_supervisions_rows(row, levels)

def get_leader_supervision_values(row, filters, level):
	leader = row['team_'+level+'_supervisior']
	if not frappe.db.exists("Pre-Sales Quarter Quota", {
		"engineer": leader,
		"year": filters.get("year"),
		"quarter": filters.get("quarter"),
		"docstatus": 1
	}):
		frappe.throw("There is no Pre-Sales Quarter Quota for Pre-Sales Engineer {}".format(leader))
	doc = frappe.get_doc("Pre-Sales Quarter Quota", {
		"engineer": leader,
		"year": filters.get("year"),
		"quarter": filters.get("quarter"),
		"docstatus": 1
	})
	extra = doc.get(level+"_incentive_percentage")
	row["default_"+level+"_achievement"] = doc.achievement_percentage
	row[level+"_extra"] = extra
	
	if row["base_net_incentive_value"] == 0: return

	row["default_"+level+"_supervision"] = row['contribution_value'] * extra / 100
	
	comm = calculate_incentive(row["default_"+level+"_achievement"], default_rule)

	row[level+"_kpi"] = doc.kpi
	row[level+"_supervision_incentive"] = row["default_"+level+"_supervision"] * comm / 100 * doc.kpi / 100
	
def get_leader(leaders, filters):
	if not leaders: return
	for leader in leaders:
		to_get_extra = frappe.db.get_value("Pre-Sales Quarter Quota", {
			"engineer": leader,
			"year": filters.get("year"),
			"quarter": filters.get("quarter"),
			"docstatus": 1
		}, "to_get_extra")
		if to_get_extra:
			return leader

def set_supervisions_rows(row, levels):
	"Create Rows for Primary and Secondary Supervisiors"

	new_rows = []

	for level in levels:
		reason = "Team Leader" if level == "primary" else "Manager"
		new_row = {
			"sales_order": row['sales_order'],
			"title": row['title'],
			"base_grand_total": row['base_grand_total'],
			"base_expected_profit_loss_value": row['base_expected_profit_loss_value'],
			"engineer_type": level.capitalize() + " Supervision",
			# "contribution_percentage": row['contribution_percentage'],
			# "contribution_value": row['contribution_value'],
			"member": row['team_'+level+'_supervisior'],
			"reason": reason,
			"incentive_percentage": row.get(level+"_extra", 0),
			"default_achieving_value": row.get("default_"+level+"_supervision", 0),
			"achieve_percent": row.get("default_"+level+"_achievement", 0),
			#"base_incentive_value": row["default_"+level+"_supervision"] * row["default_"+level+"_achievement"],
			"kpi": row.get(level+"_kpi" ,0),
			"base_net_incentive_value": row.get(level+"_supervision_incentive", 0),
		}
		new_row["incentive_to_total"] = new_row["base_net_incentive_value"] / row["base_grand_total"] * 100
		new_rows.append(new_row)
	return new_rows