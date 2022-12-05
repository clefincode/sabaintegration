import frappe
from erpnext.support.doctype.issue.issue import Issue

from frappe import _


class CustomIssue(Issue):
    ##Custom Update 
    def before_save(self):
        if frappe.db.get_value("Warranty Claim", {"issue": self.name}, "status") == "Open" and self.status != "Hold (Warranty Claim)":
            self.status = "Hold (Warranty Claim)"
        elif frappe.db.get_value("Warranty Claim", {"issue": self.name}, "status") == "Closed" and self.status != "Open":
            self.status = "Open"
    ##End Custom Update 