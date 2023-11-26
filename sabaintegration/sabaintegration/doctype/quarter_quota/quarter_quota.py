# Copyright (c) 2023, Ahmad and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from sabaintegration.overrides.employee import get_employees, get_leaders

class QuarterQuota(Document):
	def validate(self):
		if frappe.db.exists("Quarter Quota", {"name": ("!=", self.name), "sales_man": self.sales_man, "year": self.year, "quarter": self.quarter, "docstatus": ("!=", 2)}):
			frappe.throw("You've already had a quarter quota for the same sales man in the same year and quarter")
		
		self.set_position()
		self.set_commission_values()
			
	def on_submit(self):
		self.set_leader_commission_values()

	def on_cancel(self):
		self.set_leader_commission_values()

	def on_update_after_submit(self):
		is_leader, leader_id = check_if_team_leader(self.sales_man)
		self.set_total_quota(is_leader, leader_id)
		self.set_leader_commission_values()
		frappe.db.set_value("Quarter Quota", self.name, "total_quota", self.total_quota)

	def set_position(self):
		employee = get_employee(self.sales_man)
		if employee:
			self.position = employee.position

	def set_commission_values(self):
		is_leader, leader_id = self.check_position()
		self.set_total_quota(is_leader, leader_id)

	def check_position(self):	
		position = self.position
		leader_id = ""
		if self.position == "Senior":
			is_leader, leader_id = check_if_team_leader(self.sales_man)
			if is_leader: position = "Team Leader"

		if position != "Team Leader" and position != "Manager": return False, None

		return True, leader_id

	def set_total_quota(self, is_leader=True, leader_id = ""):
		self.total_quota = self.quota or 0
		if not is_leader: return
		if not leader_id:
			employee = get_employee(self.sales_man)
			if not employee: return
			leader_id = employee.name
		
		team = get_employees(leader_id, "name", "reports_to")

		if not team: return

		for member in team:
			employee_name = frappe.db.get_value("Employee", {"name": member, "status": "Active"})
			if not employee_name: continue
			sales_person = frappe.db.get_value("Sales Person", {"employee": employee_name}, "name")
			if not sales_person: continue
			quarter_quota = frappe.db.get_value("Quarter Quota", {
				"sales_man": sales_person,
				"year": self.year,
				"quarter": self.quarter,
				"docstatus": 1
			}, "quota")
			if not quarter_quota: continue
			self.total_quota += quarter_quota

	def set_leader_commission_values(self):
		doc_before_save = self.get_doc_before_save()
		if doc_before_save and self.get("_action") and self._action == 'update_after_submit':
			if doc_before_save.quota == self.quota and\
			doc_before_save.year == self.year and\
			doc_before_save.quarter == self.quarter and\
			doc_before_save.sales_man == self.sales_man and\
			doc_before_save.position == self.position:
				return

		employee = get_employee(self.sales_man)
		if employee:
			leaders = get_leaders(employee.name, "name", "reports_to")

			if not leaders: return

			for leader in leaders:
				sales_person = frappe.db.get_value("Sales Person", {"employee": leader}, "name")
				if not sales_person: continue
				qq = frappe.db.get_all("Quarter Quota", {"sales_man": sales_person, "year": self.year, "quarter": self.quarter, "docstatus": 1}, "name")
				if qq and qq[0].name:
					doc = frappe.get_doc("Quarter Quota", qq[0].name)
					doc.set_total_quota()
					doc.save()
					doc.reload()

def check_if_team_leader(sales_man):
	employee = get_employee(sales_man)
	if employee:
		if employee.get("reports_to"):
			reports_to = employee.reports_to
			position = frappe.db.get_value("Employee", reports_to, "position")
			if position and position == "Manager":
				return True, employee.name
		if employee.position == "Manager" or employee.position == "Team Leader":
			return True, employee.name

	return False, None
		
		

def get_employee(sales_man):
	employee = frappe.db.get_all("Sales Person", {"name": sales_man}, "employee")
	if employee and employee[0].employee:
		return frappe.get_doc("Employee", employee[0].employee)
	return