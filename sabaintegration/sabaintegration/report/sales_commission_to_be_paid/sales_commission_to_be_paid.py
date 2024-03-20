# Copyright (c) 2023, Ahmad and contributors
# For license information, please see license.txt
import json
from copy import deepcopy

import frappe
from frappe import _
from frappe.utils import flt

from erpnext import get_company_currency, get_default_company
from sabaintegration.sabaintegration.report.sales_commission_details.sales_commission_details import employees_query 

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
		"label": _("Sales Man"),
		"fieldname": "sales_person",
		"fieldtype": "Link",
		"width": 100,
		"options": "Sales Person"
	},
	{
		"label": _("Journal Entry"),
		"fieldname": "entry",
		"fieldtype": "Link",
		"width": 100,
		"options": "Journal Entry"
	},
	{
		"label": _("Reason"),
		"fieldname": "stage_title",
		"fieldtype": "Data",
		"width": 100,
	},
	{
		"label": _("Commission Value"),
		"fieldname": "base_net_commission_value",
		"fieldtype": "Currency",
		"options": "Company:company:default_currency",
		"width": 150,
	},
	{
		"label": _("NET Commission Percentage from Total Order%"),
		"fieldname": "net_commission_percentage_from_to",
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
		"label": _("Previous Commission"),
		"fieldname": "previous_commission",
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
				"label": _("Current Commission in "+ curr + " Currency"),
				"fieldname": "current_commission_"+ curr + "_currency",
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
			"label": _("Remaining Commission"),
			"fieldname": "remaining_commission",
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
	employees = ''
	if frappe.session.user != "Administrator" and "0 Accounting - Sales Persons Commission Report" not in frappe.get_roles():		
		employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
		
		if not employee: return

		sales_person = frappe.db.get_value("Sales Person", {"employee": employee}, "name")
		
		if not sales_person: return

		if not filters.get("sales_man"):
			employees = "and comm.sales_person in ({}) ".format(employees_query(sales_person))
		else:
			sales_man = employees_query(sales_person, filters.get("sales_man", None))
			if not sales_man: return

			employees = "and comm.sales_person = '{}' ".format(sales_man)

	co_results = get_payments_details(filters, employees, True)
	
	return co_results

def get_payments_details(filters, employees = '', add_supervisior_row = False):
	conditions = get_conditions(filters)
	sos = ''
	if employees:
		soslist = frappe.db.sql("""
			select distinct so.name
			from `tabSales Order` as so
			inner join `taSales Commission` as comm on comm.parent = so.name
			where so.docstatus = 1
			{employees}
		""".format(employees = employees), as_list = 1)
		if soslist:
			sos = " and so.name in ("
			for so in soslist:
				sos += " '{}',".format(so[0])
			sos = sos[:-1] + ")"
	
	strQuery = """
		select distinct so.name as sales_order, so.base_grand_total,
		je.name as entry, jea.name as account_name, 
		jea.credit_in_account_currency as current_payment, jea.credit,
		jea.account_currency, jea.exchange_rate, je.creation as creation_date
		from `tabJournal Entry` as je
		inner join `tabJournal Entry Account` as jea on jea.parent = je.name
		inner join `tabSales Invoice` as si on jea.reference_name = si.name and si.docstatus = 1
		inner join `tabSales Invoice Item` as sii on sii.parent = si.name
		inner join `tabSales Order` as so on so.name = sii.sales_order and so.docstatus = 1
		where je.docstatus = 1
		{sos}
		{conditions}

		union

		select distinct so.name as sales_order, so.base_grand_total,
		je.name as entry, jea.name as account_name,
		jea.credit_in_account_currency as current_payment, jea.credit,
		jea.account_currency, jea.exchange_rate, je.creation as creation_date
		from `tabJournal Entry` as je
		inner join `tabJournal Entry Account` as jea on jea.parent = je.name
		inner join `tabSales Order` as so on so.name = jea.reference_name and so.docstatus = 1
		where je.docstatus = 1
		{sos}
		{conditions}
		order by sales_order, creation_date

	""".format(conditions = conditions, sos = sos)
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

		details = set_so_details(sales_order, entry, sos, filters)
		
		if details:
			results.extend(details)

			results = add_supervision_row(results, "Primary")
			#print(results)
			results = add_supervision_row(results,  "Secondary")

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



def set_so_details(sales_order, entry, sos, filters):
	doc = frappe.get_doc("Sales Order", sales_order)
	
	if not doc.get("sales_commission"): return
	
	total_details = []
	for row in doc.sales_commission:
		if filters.get("sales_man") and filters["sales_man"] != row.sales_person: continue

		details = deepcopy(entry)
		details['sales_person'] = row.sales_person
		details['stage_title'] = row.stage_title
		details['base_net_commission_value'] = row.base_net_commission_value
		details['net_commission_percentage_from_to'] = row.base_net_commission_value / entry['base_grand_total'] * 100
		
		formatted_number = "{:,.2f}".format(entry['current_payment'])
		details['current_payment_'+ entry['account_currency'] + '_currency'] = entry['account_currency'] + " " + formatted_number
		
		formatted_number = "{:,.2f}".format(details['net_commission_percentage_from_to'] * details['current_payment'] / 100)
		details['current_commission_'+ entry['account_currency'] + '_currency'] = entry['account_currency'] + " " + formatted_number
		
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

		details['previous_commission'] = details['net_commission_percentage_from_to'] * details['previous_payment'] / 100
		details['remaining_payment'] = details['base_grand_total'] - (details['previous_payment'] + (sos[sales_order]))
		details['remaining_commission'] = details['net_commission_percentage_from_to'] * details['remaining_payment'] / 100

		total_details.append(details)

	return total_details

def add_supervision_row(rows, reason):
	commission_value = frappe.db.get_value('Sales Order', rows[-1]['sales_order'], reason+'_supervision_value') or 0
	commission_percentage_from_to = commission_value / rows[-1]['base_grand_total'] * 100
	account_currency_str = rows[-1]['account_currency'] + '_currency'

	payment = rows[-1]['current_payment_' + account_currency_str]
	commission = "{:,.2f}".format((rows[-1]['current_payment'] if rows[-1]['current_payment'] else 0) * commission_percentage_from_to / 100)
	supervisor_row = [{
					'sales_order': rows[-1]['sales_order'],
					'base_grand_total': rows[-1]['base_grand_total'],
					'sales_person': frappe.db.get_value('Sales Order', rows[-1]['sales_order'], reason+'_supervisor') or '',
					'stage_title': reason + " Supervision",
					'base_net_commission_value': commission_value,
					'net_commission_percentage_from_to': commission_percentage_from_to,
					'previous_payment': rows[-1]['previous_payment'],
					'previous_commission': (rows[-1]['previous_payment'] if rows[-1]['previous_payment'] else 0) * commission_percentage_from_to / 100,
					'current_payment': rows[-1]['current_payment'],
					'current_payment_' + account_currency_str : payment,
					'current_commission_' + account_currency_str: rows[-1]['account_currency'] + " " + commission,
					'remaining_payment': rows[-1]['remaining_payment'],
					'remaining_commission': (rows[-1]['remaining_payment'] if rows[-1]['remaining_payment'] else 0) * commission_percentage_from_to / 100,
					'account_currency': rows[-1]['account_currency'],
					'exchange_rate': rows[-1]['exchange_rate'],
					'entry': rows[-1]['entry'],
					'additional_taxes': rows[-1]['additional_taxes']
				}]
	return rows + supervisor_row
	 

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