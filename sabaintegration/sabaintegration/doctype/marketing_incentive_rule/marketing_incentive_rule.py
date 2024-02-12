# Copyright (c) 2024, Ahmad and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from sabaintegration.sabaintegration.doctype.commission_rule.commission_rule import calculate_commission

class MarketingIncentiveRule(Document):
	def validate(self):
		if self.is_default and frappe.db.exists("Marketing Incentive Rule", {"name": ("!=", self.name) , "is_default" : 1}):
			frappe.throw("Only one Rule can be a default rule")

def calculate_incentive(achieve_percent, rule):
	return calculate_commission(achieve_percent, rule)
	
@frappe.whitelist()
def get_default_rule():
	if frappe.db.exists("Marketing Incentive Rule", {"is_default" : 1}):
		return frappe.db.get_value("Marketing Incentive Rule", {"is_default" : 1}, "name")


	

