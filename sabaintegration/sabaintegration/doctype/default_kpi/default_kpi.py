# Copyright (c) 2023, Ahmad and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DefaultKPI(Document):
	def validate(self):
		if frappe.db.exists("Default KPI", {"name": ("!=", self.name), "year": self.year, "quarter": self.quarter, "docstatus": ("!=", 2)}):
			frappe.throw("You've already had a Default KPI in the same year and quarter")
		self.validate_details()

	def on_update_after_submit(self):
		self.validate_details()

	def validate_details(self):
		if not self.get("kpi_details"): return
		employees = []
		for row_num, row in enumerate(self.kpi_details):
			if row.employee in employees:
				frappe.throw("Row # {}: Duplicated Row".format(row_num + 1))
			if not row.employee_name:
				row.employee_name = frappe.db.get_value("Employee", row.employee, "employee_name")
			if not row.department:
				row.department = frappe.db.get_value("Employee", row.employee, "department")
			employees.append(row.employee)

@frappe.whitelist()
def get_default_kpi(**kwargs):
	"""
	kwargs has the following args: 
	1- doc = 'Quarter Quota' or 'Marketing Quarter Quota' or 'Pre-Sales Quarter Quota'
	2- person = name of the sales man or the product manager or the engineer
	3- year
	4- quarter
	"""
	kwargs=frappe._dict(kwargs)
	person_type = ""
	if not kwargs.person or not kwargs.year or not kwargs.quarter: return

	if kwargs.doc == "Quarter Quota":
		person_type = "Sales Person"
	elif kwargs.doc == "Marketing Quarter Quota":
		person_type = "Product Manager"
	elif kwargs.doc == "Pre-Sales Quarter Quota":
		person_type = "Pre-Sales Engineer"
	else: return

	employee = frappe.db.get_value(person_type, kwargs.person, "employee")
	
	kpi = 0
	if not frappe.db.exists("Default KPI", {"year": kwargs.year, "quarter": kwargs.quarter, "docstatus": 1}): return kpi
	
	kpi_default = frappe.get_doc("Default KPI", {"year": kwargs.year, "quarter": kwargs.quarter, "docstatus": 1})
	for row in kpi_default.kpi_details:
		if row.employee == employee:
			kpi = row.kpi
			return kpi
	return kpi

@frappe.whitelist()
def get_all_employees(department = None):
	filters = {"status": "Active"}
	if department:
		filters["department"] = department	
	
	return frappe.db.get_all("Employee", filters, ["name", "employee_name", "department"], order_by = "employee_name")
