# Copyright (c) 2023, Ahmad and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate , get_datetime
from datetime import timedelta , datetime


def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_columns(filters):
	return  [
		{
			"label": _("Opportunity"),
			"fieldname": "opportunity",
			"fieldtype" : "Link",
			"options" : "Opportunity",
			"width": 100,
		},
		{
			"label": _("Option"),
			"fieldname": "opportunity_option_number",
			"fieldtype" : "Data",
			"width": 75,
		},
		{
			"label": _("Opportunity Owner"),
			"fieldname":  "opportunity_owner",
			"fieldtype": "Link",
			"options" : "User",
			"width": 175,
		},
		{
			"label": _("Request for Quotation"),
			"fieldname": "request_for_quotation",
			"fieldtype" : "Link",
			"options" : "Request for Quotation",
			"width": 220,
		},
		{
			"label": _("Supplier"),
			"fieldname":  "supplier",	
			"width": 200,
		},
		{
			"label": _("Option Submitting Date"),
			"fieldname": "op_submitting_date",
			"fieldtype": "Date",
			"width": 160,
		},				
		{
			"label": _("RFQ Submitting Date"),
			"fieldname": "rfq_submitting_date",
			"fieldtype": "Date",
			"width": 160,
		},						
		{
			"label": _("Number of Days"),
			"fieldname": "days",
			"fieldtype": "Data",
			"width": 100,
		}
	]

def get_data(filters):
	conditions = get_conditions(filters)
	results = frappe.db.sql(f"""
	SELECT  DISTINCT RFQ.name AS 'request_for_quotation' ,
        OP.name AS opportunity ,
        RFQItem.opportunity_option_number ,
        RFQ.submitting_date AS 'rfq_submitting_date',
        Option.submitting_date AS 'op_submitting_date',
		OP.opportunity_owner,
		RFQSupplier.supplier
        
	FROM `tabRequest for Quotation` AS RFQ INNER JOIN `tabOpportunity` AS OP ON RFQ.opportunity = OP.name
    INNER JOIN `tabRequest for Quotation Item` AS RFQItem ON RFQItem.parent = RFQ.name
    INNER JOIN `tabOpportunity Option` AS Option ON Option.parent = OP.name
	INNER JOIN `tabRequest for Quotation Supplier` AS RFQSupplier ON RFQSupplier.parent = RFQ.name
    
	WHERE RFQ.docstatus = 1  
	{conditions}
	GROUP BY RFQ.name
	ORDER BY opportunity_owner
	
	""" , filters , as_dict = True)
	if results:		
		for result in results:			
			op_submitting_date = result.op_submitting_date
			rfq_submitting_date = result.rfq_submitting_date
			if op_submitting_date and rfq_submitting_date:				
				if getdate(op_submitting_date) == getdate(rfq_submitting_date):
					result.days = 0
				else:
					delta = rfq_submitting_date - op_submitting_date
					# this case when delta is less than 24 hours
					if delta.days == 0:
						result.days = 1
					else:	
						days = delta.days
						current_fiscal_year = frappe.get_all("Fiscal Year")[0]
						holiday_list = frappe.db.sql(f"""SELECT holiday_date FROM `tabHoliday` WHERE parent = '{current_fiscal_year.name}'""")
						for i in range(1 , delta.days):
							day = op_submitting_date + timedelta(days=i)					
							for j in holiday_list:						
								if j[0] == day.date():
									days = days - 1				
						result.days = days

	return results

def get_conditions(filters):
	conditions = ""

	if filters.get("from_date"):		
		conditions += " AND Option.submitting_date >= %(from_date)s"

	if filters.get("to_date"):
		filters.update({"to_date":filters.get("to_date") + " 23:59:59"})
		conditions += " AND Option.submitting_date <= %(to_date)s"	
	
	if filters.get("opportunity_owner"):
		conditions += " AND opportunity_owner = %(opportunity_owner)s"

	return conditions



