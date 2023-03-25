import frappe
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry

class CustomStockEntry(StockEntry):
    def before_cancel(self):
        if self.get('from_bundle_delivery_note'):
            self.from_bundle_delivery_note = ''