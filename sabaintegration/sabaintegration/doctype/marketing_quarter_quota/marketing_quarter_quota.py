# Copyright (c) 2023, Ahmad and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from sabaintegration.overrides.employee import get_leaders
from sabaintegration.sabaintegration.report.quota import check_if_team_leader

class MarketingQuarterQuota(Document):
	def validate(self):
		if frappe.db.exists("Marketing Quarter Quota", {"name": ("!=", self.name), "year": self.year, "quarter": self.quarter, "docstatus": ("!=", 2)}):
			frappe.throw("You've already had a marketing quarter quota in the same year and quarter")
		
		self.set_table_details()

	def on_update_after_submit(self):
		self.set_table_details()

	def set_table_details(self):
		"Set Default Incentive Percentage and Leaders"
		brands = []
		if self.get_doc_before_save():
			brands_before = [(d.product_manager, d.brand, d.total_quota) for d in self.get_doc_before_save().brands]
			brands_after = [(d.product_manager, d.brand, d.total_quota) for d in self.brands]
			if brands_before == brands_after:
				return
		
		self.leaders = []
		for row in self.brands:
			self.check_brands_duplications(row, brands)
			self.set_incentive_percentage(row)
			row.achievement_percentage = 0
			self.set_leaders(row)

	def check_brands_duplications(self, row, brands):
		if row.brand in brands:
			frappe.throw("Duplicated Brand <b>{}</b>".format(row.brand))
		else:
			brands.append(row.brand)

	def set_incentive_percentage(self, row):
		if not row.incentive_percentage:
			row.incentive_percentage = get_pm_details(row.product_manager)

	def set_leaders(self, row):
		"Set Leaders of a Product Manager"
		employee_name =  frappe.db.get_value("Product Manager", row.product_manager, "employee")
		if not employee_name: return

		team_leader_e, manager_e = "", ""

		employee = frappe.get_doc("Employee", employee_name)

		isLeader = check_if_team_leader(employee)
		position = employee.position

		# If the Product Manager is not a Leader, then Add the Primary and the Secondary Leaders
		if not isLeader:
			leaders = get_leaders(employee_name, "name", "reports_to")
			team_leader = frappe.db.get_value("Product Manager", {"employee": leaders[0]}, "name")
			manager = frappe.db.get_value("Product Manager", {"employee": leaders[1]}, "name")
			
			row.team_leader, row.manager = team_leader, manager
			team_leader_e, manager_e = leaders[0], leaders[1]

		elif position == "Senior" or position == "Team Leader":
			leaders = get_leaders(employee_name, "name", "reports_to")
			manager = frappe.db.get_value("Product Manager", {"employee": leaders[0]}, "name")
			
			row.team_leader, row.manager = row.product_manager, manager
			team_leader = row.team_leader
			team_leader_e, manager_e = employee_name, leaders[0]
					
		else:
			team_leader_e = manager_e = employee_name
			team_leader, manager = row.team_leader, row.manager = row.product_manager, row.product_manager
		
		if not team_leader: 
			frappe.throw(f"There is no Product Manager record for {team_leader_e}")

		if not manager: 
			frappe.throw(f"There is no Product Manager record for {manager_e}")

		row.leader_achievement_percentage = row.manager_achievement_percentage = row.leader_to_get_extra = row.manager_to_get_extra= 0
		self.set_leaders_quota(row)
	
	def set_leaders_quota(self, row):
		"Set the Total Quota of a Leader"

		for level in ["team_leader", "manager"]:
			Clevel = level.replace("_", " ")
			if not self.leaders:
				self.append("leaders", frappe._dict({
					"leading_product_manager": row.get(level),
					"title": Clevel.capitalize(),
					"total_margin_quota": row.total_quota or 0,
					#"extra": row.incentive_percentage
				}))
			else:
				found = False
				for leader in self.leaders:
					if leader.leading_product_manager == row.get(level):
						leader.total_margin_quota += row.total_quota
						found = True
						break
				if not found:
					self.append("leaders", frappe._dict({
						"leading_product_manager": row.get(level),
						"title": Clevel.capitalize(),
						"total_margin_quota": row.total_quota or 0,
						#"extra": row.incentive_percentage
					}))


@frappe.whitelist()
def get_pm_details(product_manager):
	return frappe.db.get_value("Product Manager", product_manager, "incentive_rate")
