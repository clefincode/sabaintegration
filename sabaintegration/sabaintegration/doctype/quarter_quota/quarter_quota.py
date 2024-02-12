# Copyright (c) 2023, Ahmad and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from sabaintegration.overrides.employee import get_employees, get_leaders
from sabaintegration.sabaintegration.report.quota import check_if_team_leader, get_employee

class QuarterQuota(Document):
	def __init__(self, *args, **kwargs):
		super(QuarterQuota, self).__init__(*args, **kwargs)
		self.employee_doc = None
		if self.sales_man:
			self.employee_doc = get_employee("Sales Person", self.sales_man)

	def validate(self):
		if frappe.db.exists("Quarter Quota", {"name": ("!=", self.name), "sales_man": self.sales_man, "year": self.year, "quarter": self.quarter, "docstatus": ("!=", 2)}):
			frappe.throw("You've already had a quarter quota for the same sales man in the same year and quarter")
		
		if not self.get("employee_doc"):
			self.employee_doc = get_employee("Sales Person", self.sales_man)

		self.set_position()
		self.set_commission_values()
			
	def on_submit(self):
		self.set_leader_commission_values()

	def on_cancel(self):
		self.set_leader_commission_values()

	def on_update_after_submit(self):
		is_leader = check_if_team_leader(self.employee_doc)
		self.set_total_quota(is_leader, self.employee_doc.name)
		self.set_leader_commission_values()
		frappe.db.set_value("Quarter Quota", self.name, "total_quota", self.total_quota)

	def set_position(self):
		if self.employee_doc:
			self.position = self.employee_doc.position

	def set_commission_values(self):
		is_leader = self.check_position()
		self.set_total_quota(is_leader, self.employee_doc.name)

	def check_position(self):	
		position = self.position
		if self.position == "Senior":
			is_leader = check_if_team_leader(self.employee_doc)
			if is_leader: position = "Team Leader"

		if position != "Team Leader" and position != "Manager": return False

		return True

	def set_total_quota(self, is_leader=True, leader_id = ""):
		self.total_quota = self.quota or 0
		if not is_leader: return
		if not leader_id:
			if not self.employee_doc:
				self.employee_doc = get_employee("Sales Person", self.sales_man)
				if  not self.employee_doc: return
			leader_id = self.employee_doc.name
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

		if self.employee_doc:
			leaders = get_leaders(self.employee_doc.name, "name", "reports_to")

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
