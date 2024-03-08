# Copyright (c) 2023, Ahmad and contributors
# For license information, please see license.txt

from datetime import datetime
from copy import deepcopy

import frappe
from frappe.model.document import Document

class SalesOrderPayment(Document):
	def validate(self):
		if frappe.db.exists("Sales Order Payment", {
               "name": ("!=", self.name),
               "sales_order": self.sales_order, 
               "quarter": self.quarter, 
               "year": self.year, 
               "docstatus": 1
               }):
			frappe.throw("There is another Sales Order Payment for this Sales Order in the same year and quarter")


def set_payment_for_quarter(): 
	current_month = datetime.now().month
    
	if current_month in [1, 4, 7, 10]:
		quarter = get_quarter(current_month)
		set_payment(quarter, datetime.now().year)

def get_quarter(month):
    if month in [1, 2, 3]:
        return 1
    elif month in [4, 5, 6]:
        return 2
    elif month in [7, 8, 9]:
        return 3
    elif month in [10, 11, 12]:
        return 4
    else:
        return "Invalid month"

@frappe.whitelist()
def set_payment(quarter, year):
    from sabaintegration.sabaintegration.report.sales_commission_to_be_paid.sales_commission_to_be_paid import get_payments_details

    results = get_payments_details(filters = {
            "year": year,
            "quarter": "Q"+str(quarter)
    })
    sales_orders = {}
    for row in results:
        sales_order = row['sales_order']

        if frappe.db.exists("Sales Order Payment", {
               "sales_order": sales_order, 
               "quarter": 'Q' + str(quarter), 
               "year": year, 
               "docstatus": 1
               }):
            continue
        
        sales_orders[sales_order] = sales_orders.get(sales_order, 0) + row['credit']
    
    for sales_order in sales_orders:
        sop = frappe.new_doc("Sales Order Payment")
        sop.sales_order = sales_order
        sop.year = year
        sop.quarter = 'Q' + str(quarter)
        sop.current_payment = sales_orders[sales_order]
        sop.insert(ignore_permissions = True)

    frappe.db.commit()
    return len(sales_orders)
            

    