# Copyright (c) 2023, Ahmad and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class CommissionRule(Document):
	def validate(self):
		if self.is_default and frappe.db.exists("Commission Rule", {"name": ("!=", self.name) , "is_default" : 1}):
			frappe.throw("Only one Rule can be a default rule")

def calculate_commission(achieve_percent, rule):
	conditions = frappe.db.get_all("Commission Rule Condition", {"parent": rule}, '*', order_by = "idx")
	for condition in conditions:
		
		comm = condition_istrue(achieve_percent, condition)
		if comm != "False":
			return comm
	return

def condition_istrue(achieve_percent, condition_row):
	if condition_row.condition == 'less than':
		if achieve_percent < condition_row.milestone:
			return commission_precent_calcualation(condition_row, achieve_percent)
		else: return "False"
	elif condition_row.condition == 'less than or equals':
		if achieve_percent <= condition_row.milestone:
			return commission_precent_calcualation(condition_row, achieve_percent)
		else: return "False"
	elif condition_row.condition == 'greater than':
		if achieve_percent > condition_row.milestone:
			return commission_precent_calcualation(condition_row, achieve_percent)
		else: return "False"
	elif condition_row.condition == 'greater than or equals':
		if achieve_percent > condition_row.milestone:
			return commission_precent_calcualation(condition_row, achieve_percent)
		else: return "False"
	elif condition_row.condition == 'equals':
		if achieve_percent == condition_row.milestone:
			return commission_precent_calcualation(condition_row, achieve_percent)
		else: return "False"
	elif condition_row.condition == 'not equals':
		if achieve_percent != condition_row.milestone:
			return commission_precent_calcualation(condition_row, achieve_percent)
		else: return "False"

def commission_precent_calcualation(condition_row, achieve_percent):
	if condition_row.get("calculation") and condition_row.get("calculation") == "Zero":
		return 0
	if condition_row.get("calculation") and condition_row.get("calculation") == "As Milestone":
		return achieve_percent
	if condition_row.get("comm_percent"):
		return condition_row.comm_percent
	else: return 0

@frappe.whitelist()
def get_default_rule():
	if frappe.db.exists("Commission Rule", {"is_default" : 1}):
		return frappe.db.get_value("Commission Rule", {"is_default" : 1}, "name")


	
