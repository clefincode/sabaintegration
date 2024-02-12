# Copyright (c) 2023, Ahmad and contributors
# For license information, please see license.txt
import json
from copy import deepcopy

import frappe
from frappe import _

from erpnext import get_company_currency, get_default_company
from sabaintegration.sabaintegration.report.pre_sales_incentive_activity_details.pre_sales_incentive_activity_details import employees_query 
from sabaintegration.overrides.employee import get_leaders
from sabaintegration.sabaintegration.report.quota import is_admin, check_if_team_leader, get_employee
from sabaintegration.sabaintegration.doctype.pre_sales_incentive_rule.pre_sales_incentive_rule import calculate_incentive, get_default_rule

ROLE, DOCTYPE = "0 Accounting - Pre-Sales Activity Incentive Report", "Pre-Sales Engineer"
default_rule = get_default_rule()

def execute(filters=None):
	data, currencies = get_data(filters)
	columns = get_columns(currencies)
	return columns, data

def get_columns(curriences):
	columns = [
	{
		"label": _("Sales Order"),
		"fieldname": "sales_order",
		"fieldtype": "Link",
		"width": 100,
		"options": "Sales Order"
	},
	{
		"label": _("Sales Order Grand Total"),
		"fieldname": "base_grand_total",
		"fieldtype": "Currency",
		"width": 180,
		"options": "Company:company:default_currency"
	},
	{
		"label": _("Engineer"),
		"fieldname": "engineer",
		"fieldtype": "Link",
		"width": 100,
		"options": "Pre-Sales Engineer"
	},
	{
		"label": _("Reason"),
		"fieldname": "reason",
		"fieldtype": "Data",
		"width": 100,
	},
	{
		"label": _("Journal Entry"),
		"fieldname": "entry",
		"fieldtype": "Link",
		"width": 100,
		"options": "Journal Entry"
	},
	{
		"label": _("Incentive Value"),
		"fieldname": "base_net_incentive_value",
		"fieldtype": "Currency",
		"options": "Company:company:default_currency",
		"width": 150,
	},
	{
		"label": _("NET Incentive Percentage from Total Order%"),
		"fieldname": "net_incentive_percentage_from_to",
		"fieldtype": "Percent",
		"width": 120,
	},
	{
		"label": _("Previous Payment Amount"),
		"fieldname": "previous_payment",
		"fieldtype": "Currency",
		"options": "Company:company:default_currency",
		"width": 150,
	},
	{
		"label": _("Previous Incentive"),
		"fieldname": "previous_incentive",
		"fieldtype": "Currency",
		"options": "Company:company:default_currency",
		"width": 150,
	},
	]
	for curr in curriences:
		columns.extend([
			{
				"label": _("Current Payment in "+ curr + " Currency"),
				"fieldname": "current_payment_"+ curr + "_currency",
				"fieldtype": "Data",
				"width": 150,
			}
		])
	for curr in curriences:
		columns.extend([
			{
				"label": _("Current Incentive in "+ curr + " Currency"),
				"fieldname": "current_incentive_"+ curr + "_currency",
				"fieldtype": "Data",
				"width": 150,
			}
		])
	columns.extend([
		{
			"label": _("Exchange Rate"),
			"fieldname": "exchange_rate",
			"fieldtype": "Float",
			"width": 80,	
		},
		{
			"label": _("Additional Taxes"),
			"fieldname": "additional_taxes",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 150,	
		},
		{
			"label": _("Remaining Payment"),
			"fieldname": "remaining_payment",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 150,
		},
		{
			"label": _("Remaining Incentive"),
			"fieldname": "remaining_incentive",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 150,
		}
	])
	return columns

def get_conditions(filters):
	conditions = ""
	if filters.get("sales_order"):
		conditions += " and so.name = %(sales_order)s"
	if filters.get("year"):
		conditions += " and EXTRACT(YEAR FROM je.submitting_date) = %(year)s"
	if filters.get("quarter"):
		conditions += " and CONCAT('Q', CEILING(EXTRACT(MONTH FROM je.submitting_date) / 3.0)) = %(quarter)s"
	return conditions

def get_data(filters):

	co_results = get_payments_details(filters, True)
	
	return co_results

def get_payments_details(filters, add_supervisior_row = False):
	conditions = get_conditions(filters)
	sos = ''
	employees, employees_list = '', []
	admin, engineer = is_admin(frappe.session.user, ROLE, DOCTYPE)
	
	if not admin and engineer:
		if not filters.get("engineer"):
			emp = employees_query(engineer)
			employees_list = emp[2:-1].split("', '")
			employees = "and pre_sales.engineer in ({}) ".format(emp)
		else:
			eng = employees_query(engineer, filters.get("product_manager", None))
			employees_list = eng.split("', '")
			if not eng: return

			employees = "and pre_sales.engineer = '{}' ".format(engineer)

	elif filters.get("engineer"):
		employees += " and pre_sales.engineer = %(engineer)s"

	filters["is_admin"] = admin
	if employees:
		soslist = frappe.db.sql("""
			select distinct so.name
			from `tabSales Order` as so
			inner join `tabPre-Sales Incentive` as pre_sales on pre_sales.parent = so.name
			where so.docstatus = 1
			{employees}
		""".format(employees = employees, conditions = conditions), filters, as_list = 1)
		if soslist:
			sos = " and so.name in ("
			for so in soslist:
				sos += " '{}',".format(so[0])
			sos = sos[:-1] + ")"
	strQuery = """
		select distinct so.name as sales_order, so.base_grand_total, so.base_expected_profit_loss_value,
		je.name as entry, jea.name as account_name, 
		jea.credit_in_account_currency as current_payment, jea.credit,
		jea.account_currency, jea.exchange_rate
		from `tabJournal Entry` as je
		inner join `tabJournal Entry Account` as jea on jea.parent = je.name
		inner join `tabSales Invoice` as si on jea.reference_name = si.name and si.docstatus = 1
		inner join `tabSales Invoice Item` as sii on sii.parent = si.name
		inner join `tabSales Order` as so on so.name = sii.sales_order and so.docstatus = 1
		where je.docstatus = 1
		{conditions}
		{sos}
		union

		select distinct so.name as sales_order, so.base_grand_total, so.base_expected_profit_loss_value,
		je.name as entry, jea.name as account_name,
		jea.credit_in_account_currency as current_payment, jea.credit,
		jea.account_currency, jea.exchange_rate
		from `tabJournal Entry` as je
		inner join `tabJournal Entry Account` as jea on jea.parent = je.name
		inner join `tabSales Order` as so on so.name = jea.reference_name and so.docstatus = 1
		
		where je.docstatus = 1
		{conditions}
		{sos}
		order by sales_order

	""".format(conditions = conditions, employees = employees, sos = sos)
	so_entries = frappe.db.sql(strQuery, filters, as_dict = 1)
	if not add_supervisior_row: 
		return so_entries

	results, sos, currencies = [], {}, []

	for entry in so_entries:
		sales_order = entry['sales_order']
		set_payment_in_debit_currency(entry)
		if not sos.get(entry['sales_order']):
			additional_taxes = get_additional_taxes(sales_order, filters)
			#sos.append(sales_order)

		sos[entry['sales_order']] = sos.get(entry['sales_order'], 0) + entry['credit']
		#sos[sales_order]['current_payment'] -= additional_taxes
		entry['additional_taxes'] = additional_taxes
		
		if entry.account_currency not in currencies:
			currencies.append(entry.account_currency)

		details = set_so_details(entry, sos, employees_list, filters)
		
		if details:
			results.extend(details)

	return results, currencies

def set_payment_in_debit_currency(entry):
	doc = frappe.get_doc("Journal Entry", entry["entry"])
	credit_currency, account_name = entry["account_currency"], entry["account_name"]
	company_currency = get_company_currency(get_default_company())
	
	for account in doc.accounts:
		if account_name != account.name and account.debit > 0:
			# Nothing to convert
			if credit_currency == account.account_currency:
				pass
			
			# Convert the credit (company currency) to debit currency
			elif credit_currency == company_currency:
				entry['current_payment'] = entry['current_payment'] / account.exchange_rate
				entry['exchange_rate'] = account.exchange_rate

			# Convert the credit currency to debit (company currency)
			elif account.account_currency == company_currency:
				entry['current_payment'] = entry['current_payment'] * entry["exchange_rate"]
				entry['exchange_rate'] = 1
			
			# Convert credit to company currency then convert company currency to debit currency
			else:
				base_payment = entry['current_payment'] * entry['exchange_rate']
				entry['current_payment'] = base_payment / account.exchange_rate
			
			entry["account_currency"] = account.account_currency
			return


def set_so_details(entry, sos, employees_list, filters):
	sales_order = entry["sales_order"]
	doc = frappe.get_doc("Sales Order", sales_order)
	
	if not doc.get("pre_sales_activities"): return
	
	total_details = []
	for row in doc.pre_sales_activities:
		if filters.get("engineer") and filters["engineer"] != row.engineer: continue

		details = deepcopy(entry)
		details['engineer'] = row.engineer
		details['reason'] = "Pre-Sales Engineer"
		details['achievement_percentage'] = frappe.db.get_value("Pre-Sales Quarter Quota", {
			"engineer": row.engineer,
			"year": filters['year'],
			"quarter": filters['quarter'],
			"docstatus": 1
			}, "achievement_percentage")

		rule = get_default_rule()
		details['achieve_target'] = calculate_incentive(details['achievement_percentage'], rule)
 	
		details['base_net_incentive_value'] = row.base_net_incentive_value
		details['net_incentive_percentage_from_to'] = row.base_net_incentive_value / entry['base_grand_total'] * 100
		
		formatted_number = "{:,.2f}".format(entry['current_payment'])
		details['current_payment_'+ entry['account_currency'] + '_currency'] = entry['account_currency'] + " " + formatted_number
		entry['current_payment_'+ entry['account_currency'] + '_currency'] = details['current_payment_'+ entry['account_currency'] + '_currency']

		formatted_number = "{:,.2f}".format(details['net_incentive_percentage_from_to'] * details['current_payment'] / 100)
		details['current_incentive_'+ entry['account_currency'] + '_currency'] = entry['account_currency'] + " " + formatted_number
		
		previous_payment = frappe.db.sql("""
			select sum(current_payment) as payment
			from `tabSales Order Payment` 
			where sales_order = '{sales_order}' and docstatus = 1 and (
			(year =  %(year)s and quarter < %(quarter)s) or
			(year < %(year)s)			
			) group by sales_order
		""".format(sales_order = sales_order), filters, as_list = 1)

		if previous_payment and previous_payment[0]:
			details['previous_payment'] = previous_payment[0][0]
		else: details['previous_payment'] = 0
		entry['previous_payment'] = details['previous_payment']
		

		details['previous_incentive'] = details['net_incentive_percentage_from_to'] * details['previous_payment'] / 100
		details['remaining_payment'] = details['base_grand_total'] - (details['previous_payment'] + (sos[sales_order]))
		details['remaining_incentive'] = details['net_incentive_percentage_from_to'] * details['remaining_payment'] / 100
		entry['remaining_payment'] = details['remaining_payment']
		

		total_details.append(details)
		add_supervision_rows(total_details, details, entry, employees_list, filters)
	return total_details

def add_supervision_rows(total_details, row, entry, employees_list, filters):
	engineer = row['engineer']
	new_row_primary, new_row_secondary = deepcopy(entry), deepcopy(entry)
	employee = get_employee(DOCTYPE, engineer)
	if not employee:
		frappe.throw("There is no Employee record for Engineer {}".format(engineer))
	
	leaders = get_leaders(employee.name, "name", "reports_to")

	secondary = True
	if leaders:
		if employee.position == "Team Leader":
			new_row_primary['engineer'] = engineer
			leader_engineer = frappe.db.get_value("Pre-Sales Engineer", {"employee": leaders[0]}, "name")
			if leader_engineer: new_row_secondary['engineer'] = leader_engineer
			else: secondary = False

		elif employee.position == "Manager":
			new_row_primary['team_primary_supervisior'] = engineer
			new_row_secondary['team_secondary_supervisior'] = engineer

		elif employee.position == "Senior":
			is_leader= check_if_team_leader(employee)
			if is_leader:
				
				new_row_primary['engineer'] = engineer
				leader_engineer = frappe.db.get_value("Pre-Sales Engineer", {"employee": leaders[0]}, "name")
				if leader_engineer: new_row_secondary['engineer'] = leader_engineer
				else: secondary = False
			else:
				leader_engineer = frappe.db.get_value("Pre-Sales Engineer", {"employee": leaders[0]}, "name")
				if leader_engineer: new_row_primary['engineer'] = leader_engineer

				if len(leaders) > 1:
					leader_engineer = frappe.db.get_value("Pre-Sales Engineer", {"employee": leaders[1]}, "name")
					if leader_engineer: new_row_secondary['engineer'] = leader_engineer
					else: secondary = False
				else:
					secondary = False
		else:
			leader_engineer = frappe.db.get_value("Pre-Sales Engineer", {"employee": leaders[0]}, "name")
			if leader_engineer: new_row_primary['engineer'] = leader_engineer
			
			if len(leaders) > 1:
				leader_engineer = frappe.db.get_value("Pre-Sales Engineer", {"employee": leaders[1]}, "name")
				if leader_engineer: new_row_secondary['engineer'] = leader_engineer
				else: secondary = False
			else:
				secondary = False
	else:
		new_row_primary['engineer'] = engineer
		new_row_secondary['engineer'] = engineer

	if new_row_primary.get("engineer") and (new_row_primary["engineer"] in employees_list or filters.get("is_admin", 0) == 1):
		get_leader_supervision_values(new_row_primary, filters, "primary")
		total_details.append(new_row_primary)
	if secondary and new_row_secondary.get("engineer") and (new_row_secondary["engineer"] in employees_list or filters.get("is_admin", 0) == 1):		
		get_leader_supervision_values(new_row_secondary, filters, "secondary")
		total_details.append(new_row_secondary)

def get_leader_supervision_values(row, filters, level):
	row["reason"] = level +" Supervision"
	percents = frappe.db.get_value("Pre-Sales Quarter Quota", {
			"engineer": row.engineer,
			"year": filters['year'],
			"quarter": filters['quarter'],
			"docstatus": 1
			}, [level+"incentive_percentage", "achievement_percentage", "kpi"])
	
	rule = get_default_rule()
	achieved_target = calculate_incentive(percents[1], rule)
 	
	row['incentive_value'] = row['base_expected_profit_loss_value'] * percents[0] / 100 * achieved_target / 100 # * original_row['achieve_target'] / 100
	row['base_net_incentive_value'] = row['incentive_value'] * percents[2] / 100
	row['net_incentive_percentage_from_to'] = row['base_net_incentive_value'] / row['base_grand_total'] * 100

	formatted_number = "{:,.2f}".format(row['net_incentive_percentage_from_to'] * row['current_payment'] / 100)
	row['current_incentive_'+ row['account_currency'] + '_currency'] = row['account_currency'] + " " + formatted_number
	
	row['previous_incentive'] = row['net_incentive_percentage_from_to'] * row['previous_payment'] / 100
	row['remaining_incentive'] = row['net_incentive_percentage_from_to'] * row['remaining_payment'] / 100


def get_additional_taxes(sales_order, filters):
	sales_order = frappe.get_doc("Sales Order", sales_order)

	query = """
		select distinct si.name as sales_invoice
		from `tabSales Invoice` as si
		inner join `tabSales Invoice Item` as sii on sii.parent = si.name
		inner join `tabJournal Entry Account` as jea on jea.reference_name = si.name
		inner join `tabJournal Entry` as je on je.name = jea.parent
		where je.docstatus = 1 and si.docstatus = 1
		and sii.sales_order = '{sales_order}'
		and EXTRACT(YEAR FROM je.submitting_date) = %(year)s
		and CONCAT('Q', CEILING(EXTRACT(MONTH FROM je.submitting_date) / 3.0)) = %(quarter)s
		""".format(sales_order = sales_order.name)
	
	sis = frappe.db.sql(query, filters, as_dict = 1)

	additional_taxes = 0
	for res in sis:
		doc = frappe.get_doc("Sales Invoice", res.sales_invoice)
		taxes = deepcopy(sales_order.get("taxes"))

		for si_tax in doc.taxes:
			found = False

			for tax in taxes:
				if tax.account_head == si_tax.account_head and tax.rate == si_tax.rate:
					found = True
					taxes.remove(tax)
					break
			if not found:
				additional_taxes += si_tax.base_tax_amount
	
	return additional_taxes

@frappe.whitelist()
def create_journal_entry(args):
	args = json.loads(args)
	if not args.get("year") or not args.get("quarter") and not args.get("annual"):
		frappe.throw("Select Year and Quarter to create the journal entry")
	
	if not args.get("annual"):
		commissions = get_payments_details(args, add_supervisior_row=True)
	
	if commissions:
		sales_men = {}
		for row in commissions:
			sales_men[row["sales_person"]] = sales_men.get(row["sales_person"], 0) + row["current_commission"]
		
		doc = frappe.new_doc("Journal Entry")
		doc.is_quarter_commission = 1
		doc.year = args.get("year")
		doc.quarter = args.get("quarter") if args.get("quarter") else ''
		accounts = []
		for sales_man in sales_men:
			emp = frappe.db.get_value("Sales Person", sales_man, "employee")
			if emp:
				accounts.append({
					'doctype':'Journal Entry Account',
					'party_type': 'Employee',
					'party': emp,
					'debit_in_account_currency': sales_men[sales_man],
					'debit': sales_men[sales_man],
				})

				accounts.append({
					'account': '11001002 - Cash EGP - S',
					'credit_in_account_currency': sales_men[sales_man],
					'credit': sales_men[sales_man]
				})
		doc.set("accounts", accounts)
		return doc