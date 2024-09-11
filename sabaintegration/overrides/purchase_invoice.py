from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice
from frappe.utils import now

class CustomPurchaseInvoice(PurchaseInvoice):
    def validate(self):
        # Call the original validate method
        super(CustomPurchaseInvoice, self).validate()
        if self.get("_action") and self._action == 'submit':
            self.submitting_date = now()