# Copyright (c) 2023, Ahmad and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PreSalesIncentiveTemplate(Document):
	def validate(self):
		incentive_percentage_total = 0
		for row in self.pre_sales_incentive:
			incentive_percentage_total += row.contribution_percentage
		if incentive_percentage_total != 100:
			frappe.throw("The Total of Contribution Percentage in Pre-Sales Incentive not equal to 100%")

