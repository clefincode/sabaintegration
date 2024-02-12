# Copyright (c) 2023, Ahmad and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PreSalesEngineer(Document):
	def validate(self):
		self.set_position()

	def set_position(self):
		employee = get_employee(self)
		if employee:
			self.position = employee.position

def get_employee(engineer):
	if not engineer.employee: return
	return frappe.get_doc("Employee", engineer.employee)