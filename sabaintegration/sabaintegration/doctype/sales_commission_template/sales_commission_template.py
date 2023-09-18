# Copyright (c) 2023, Ahmad and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class SalesCommissionTemplate(Document):
	def validate(self):
		commission_percentage_total = 0
		for row in self.sales_commission:
			commission_percentage_total += row.comm_percent
		if commission_percentage_total != 100:
			frappe.throw("The Total of Commission Percentage in Sales Commission not equal to 100%")
