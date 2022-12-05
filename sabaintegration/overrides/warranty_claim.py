import frappe
from erpnext.support.doctype.warranty_claim.warranty_claim import WarrantyClaim
from erpnext.utilities.transaction_base import TransactionBase
from frappe import _, session
from frappe.utils import now_datetime

class CustomWarrantyClaim(WarrantyClaim):       
    ##Custom Update
    def after_insert(self):
        self.change_issue_status()
    ##End Custom Update
    
    ##Custom Update
    def on_update(self):
        self.change_issue_status()       
    
    def change_issue_status(self):
        if self.issue and self.status != "Closed" and self.status != "Cancelled":
            if frappe.db.get_value("Issue", self.issue, "status") != "Hold (Warranty Claim)":
                frappe.db.set_value("Issue", self.issue, "status", "Hold (Warranty Claim)")
        elif self.issue and (self.status == "Closed" or self.status == "Cancelled"):
            if frappe.db.get_value("Issue", self.issue, "status") != "Open":
                frappe.db.set_value("Issue", self.issue, "status", "Open")
        frappe.db.commit()
    ##End Custom Update 
