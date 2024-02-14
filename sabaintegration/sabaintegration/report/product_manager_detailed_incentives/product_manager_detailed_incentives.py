# Copyright (c) 2024, Ahmad and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from sabaintegration.sabaintegration.doctype.marketing_incentive_rule.marketing_incentive_rule import calculate_incentive, get_default_rule
from sabaintegration.overrides.employee import get_employees
from sabaintegration.sabaintegration.doctype.default_kpi.default_kpi import get_default_kpi
from sabaintegration.sabaintegration.report.quota import is_admin, get_employee

ROLE, DOCTYPE = "0 Accounting - Marketing Incentive Report", "Product Manager"
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
			"label": _("Brand"),
			"fieldname": "brand",
			"fieldtype": "Link",
			"width": 100,
			"options": "Brand"
		},
		{
			"label": _("Brand Contribution Percentage"),
			"fieldname": "brand_contribution_percentage",
			"fieldtype": "Percent",
			"width": 100,
		},
		{
			"label": _("Brand Contribution Value"),
			"fieldname": "brand_contribution_value",
			"fieldtype": "Currency",
			"width": 100,
			"options": "Company:company:default_currency"
		},
		{
			"label": _("Team Leader"),
			"fieldname": "team_leader",
			"fieldtype": "Link",
			"width": 100,
			"options": "Product Manager"
		},
		{
			"label": _("Manager"),
			"fieldname": "manager",
			"fieldtype": "Link",
			"width": 100,
			"options": "Product Manager"
		},
		
		{
			"label": _("Member"),
			"fieldname": "member",
			"fieldtype": "Link",
			"width": 100,
			"options": "Product Manager"
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
		# {
		# 	"label": _("Brand Achievement Percentage"),
		# 	"fieldname": "brand_achieve_percent",
		# 	"fieldtype": "Percent",
		# 	"width": 100,
		# },
		{
			"label": _("Member Default Achieving Value"),
			"fieldname": "default_achieving_value",
			"fieldtype": "Currency",
			"width": 120,
			"options": "Company:company:default_currency"
		},
		{
			"label": _("Member Achievement Percentage"),
			"fieldname": "member_achieve_percent",
			"fieldtype": "Percent",
			"width": 100,
		},
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
		conditions += " and so.name = %(sales_order)s"
	if filters.get("product_manager"):
		conditions += " and brands.product_manager = %(product_manager)s"
	if filters.get("brand"):
		conditions += " and brands.brand = %(brand)s"
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
			conditions += f" and brands.product_manager in ({query})"
	return conditions

def employees_query(supervisior, product_manager = None):
	def get_msg(product_manager, recordtype):
		return "There is no {0} record for {1}.".format(recordtype, product_manager)
	
	if product_manager and product_manager == supervisior:
		return product_manager

	employee = get_employee(DOCTYPE ,supervisior)
	if not employee:
		frappe.throw(get_msg(supervisior, "Employee"))
	employees = get_employees(employee.name, "name", "reports_to")
	str_emps = ""
	if not employees: 
		if not product_manager:
			return "'{}'".format(supervisior)
		if product_manager and product_manager == supervisior:
			return product_manager
		else: return
	for emp in employees:
		eng = frappe.db.get_value("Product Manager", {"employee": emp}, "name")
		if not eng: continue

		if product_manager and product_manager == eng:
			return product_manager
		elif not product_manager:
			str_emps += " '{}',".format(eng)
	if product_manager: 
		return
	return str_emps + " '{}'".format(supervisior)

def get_data(filters):
	conditions = get_conditions(filters)
	employees, employees_list = "", []

	admin, product_manager = is_admin(frappe.session.user, ROLE, DOCTYPE)
		
	if not admin and product_manager:

		if not filters.get("product_manager"):
			emp = employees_query(product_manager)
			employees_list = emp[2:-1].split("', '")
			employees = "and (brands.product_manager in ({0}) ) ".format(emp, product_manager)
		else:
			eng = employees_query(product_manager, filters.get("product_manager", None))
			employees_list = eng.split("', '")
			if not eng: return

			employees = "and brands.product_manager = '{}' ".format(eng)
		

	strQuery = """
		select distinct so.name as sales_order, so.title, so.base_expected_profit_loss_value, so.base_grand_total,
			'Product Manager' as reason, brands.brand, brands.product_manager as member,
			qq_row.team_leader, qq_row.manager,
			qq_row.leader_achievement_percentage as team_leader_achievement_percentage, qq_row.manager_achievement_percentage,
			brands.total_quota as brand_contribution_value, qq_row.achievement_percentage as member_achieve_percent,
			(brands.total_quota / so.base_expected_profit_loss_value * 100) as brand_contribution_percentage,
			(brands.total_quota * brands.incentive_percentage / 100) as default_achieving_value,
			qq_row.parent as qq_name, qq_row.kpi,	brands.base_net_incentive_value, brands.base_incentive_value, qq_row.total_quota, brands.incentive_percentage,
			brands.base_net_incentive_value / so.base_net_total * 100 as incentive_to_total 
		from `tabSales Order` as so
		inner join `tabBrand Details` as brands on so.name = brands.parent
		left outer join `tabBrand Details` as qq_row on qq_row.product_manager = brands.product_manager and qq_row.brand = brands.brand
		inner join `tabMarketing Quarter Quota` as qq on qq.name = qq_row.parent and qq.year = EXTRACT(YEAR FROM so.submitting_date) and qq.quarter = CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.submitting_date) / 3.0)) and qq.docstatus = 1
		where so.docstatus = 1
		{conditions}
		{employees}
		order by so.name, brands.product_manager, brands.brand
	""".format(conditions = conditions, employees = employees)

	res = frappe.db.sql(strQuery, filters, as_dict = 1)

	product_manager, get_supervision = None, False
	if frappe.session.user == "Administrator" or\
	 ROLE in frappe.get_roles():
		get_supervision = True
	
	else:
		employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
			
		if not employee: return

		product_manager = frappe.db.get_value("Product Manager", {"employee": employee}, "name")

	kpi_doc = False
	if frappe.db.exists("Default KPI", {
		"year": filters.get("year"),
		"quarter": filters.get("quarter"),
		"docstatus": 1
	}):
		kpi_doc = True
	total_results = []
	for row in res:
		if kpi_doc:
			for level in ['team_leader', 'manager']:
				row[level+'_kpi'] = get_default_kpi(
						doc = 'Marketing Quarter Quota',
						person = row[level],
						year = filters['year'],
						quarter = filters['quarter']
					)

		if not row['kpi']:
			if kpi_doc:
				row['kpi'] = get_default_kpi(
						doc = 'Marketing Quarter Quota',
						person = row.product_manager,
						year = filters['year'],
						quarter = filters['quarter']
					)

		total_results.append(row)
		new_rows = get_leaders_supervision_values(row, employees_list, get_supervision)

		total_results.extend(new_rows)
	return total_results

def get_leaders_supervision_values(row, employees_list, get_supervision):
	new_rows = []

	for level in ["team_leader", "manager"]:
		if not get_supervision and row[level] != row["member"] and row[level] not in employees_list: continue
		
		total_margin_quota, incentive_percentage = frappe.db.get_value("Marketing Leader Quota", {"parent": row['qq_name'], "leading_product_manager": row[level]}, ["total_margin_quota", "extra"])

		if row["base_net_incentive_value"] == 0: 
			base_net_incentive_value = 0
		else:
			comm = calculate_incentive(row[level+"_achievement_percentage"], default_rule)
			base_net_incentive_value = row["brand_contribution_value"] * incentive_percentage / 100 *row.get(level+"_kpi", 0) / 100 * comm / 100

		
		new_row = {
			"sales_order": row['sales_order'],
			"title": row['title'],
			"base_grand_total": row['base_grand_total'],
			"base_expected_profit_loss_value": row['base_expected_profit_loss_value'],
			"brand": row['brand'],
			"member": row[level],
			"reason": level.replace("_", " ").capitalize(),
			"member_achieve_percent": row[level+ "_achievement_percentage"], 
			"brand_contribution_value": row['brand_contribution_value'],
			"brand_contribution_percentage": row['brand_contribution_percentage'],
			"incentive_percentage": incentive_percentage,
			"default_achieving_value": total_margin_quota * incentive_percentage / 100,
			"kpi": row.get(level+"_kpi", 0),
			"base_net_incentive_value": base_net_incentive_value,
			
		}
		new_row["incentive_to_total"] = new_row["base_net_incentive_value"] / row["base_grand_total"] * 100
		
		new_rows.append(new_row)
	return new_rows