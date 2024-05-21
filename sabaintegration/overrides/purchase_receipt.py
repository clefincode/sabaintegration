import json
import frappe
from frappe.utils import flt
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt

class CustomPurchaseReceipt(PurchaseReceipt):
    def on_submit(self):
        super(CustomPurchaseReceipt, self).on_submit()
        self.set_reserved_qtys()

    def on_cancel(self):
        super(CustomPurchaseReceipt, self).on_cancel()
        self.return_reserved_qtys()

    def set_reserved_qtys(self):
        for item in self.items:
            if item.purchase_order:
                sales_order = frappe.db.get_value("Purchase Order Item", {
                    "item_code": item.item_code,
                    "parent": item.purchase_order
                }, "sales_order")

                set_reserved_qtys_of_item(item, sales_order, self.name)
            else:
                set_reserved_qtys_of_item(item, purchase_receipt = self.name) 
    
    def return_reserved_qtys(self):
        for item in self.items:
            if item.purchase_order:
                sales_order = frappe.db.get_value("Purchase Order Item", {
                    "item_code": item.item_code,
                    "parent": item.purchase_order
                }, "sales_order")

                return_reserved_qtys_of_item(item, sales_order, self.name)
            else:
                return_reserved_qtys_of_item(item, purchase_receipt = self.name) 



def set_reserved_qtys_of_item(item, sales_order = None, purchase_receipt = None):
    if sales_order:
        if frappe.db.exists("Sales Order Qtys", {
            "sales_order": sales_order,
            "is_cancelled": 0
            }):
            sales_order_qtys = frappe.get_doc("Sales Order Qtys", {
                "sales_order": sales_order, 
                "is_cancelled": 0
            })


            for row in sales_order_qtys.items:
                if row.item_code == item.item_code:
                    ordered_po = json.loads(row.ordered_purchase_orders).get("ordered_po")
                    for po in ordered_po:
                        if po["po"] == item.purchase_order:
                            pr = po.get("pr")
                            if not pr:
                                pr = []
                            if item.qty >= po["qty"]:
                                receipt_qty = po["qty"]
                                row.reserved_qty += po["qty"]
                                row.ordered_qty -= po["qty"]
                                po["qty"] = 0
                                ordered_po.remove(po)
                                pr.append({"name" : purchase_receipt , "qty" : receipt_qty})
                                ordered_po.append({"po" : item.purchase_order , "qty" : po["qty"] , "pr" : pr})
                            else:  
                                row.reserved_qty += item.qty
                                row.ordered_qty -= item.qty
                                po["qty"] -= item.qty
                                ordered_po.remove(po)
                                pr.append({"name" : purchase_receipt , "qty" : item.qty})
                                ordered_po.append({"po" : item.purchase_order , "qty" : po["qty"] , "pr" : pr})
                            row.ordered_purchase_orders = json.dumps({"ordered_po": ordered_po})

            sales_order_qtys.save(ignore_permissions=True)
    
    else:
        if item.purchase_order:
            docs = frappe.db.sql(f"""
                select soq.name
                from `tabSales Order Qtys` as soq
                inner join `tabSales Order Qtys Item` as soqi on soq.name = soqi.parent and soq.is_cancelled = 0
                where soqi.item_code = '{item.item_code}' and soqi.is_completed = 0
                and soqi.projected_qty > 0 and soqi.projected_purchase_orders like '%{item.purchase_order}%'
                order by soqi.projected_qty desc
            """, as_dict=1)

            if not docs or not len(docs): return

            # total_qty, is_zero = item.qty, False

            for doc in docs:
                sales_order_qtys = frappe.get_doc("Sales Order Qtys", doc.name)
                for row in sales_order_qtys.items:
                    if row.item_code == item.item_code:
                        projected_po = json.loads(row.projected_purchase_orders).get("projected_po")
                        for po in projected_po:                            
                            if po["po"] == item.purchase_order:
                                pr = po.get("pr")
                                if not pr:
                                    pr = []
                                if item.qty >= po["qty"]:
                                    receipt_qty = po["qty"]
                                    row.reserved_qty += po["qty"]
                                    row.projected_qty -= po["qty"]
                                    po["qty"] = 0
                                    projected_po.remove(po)
                                    pr.append({"name" : purchase_receipt , "qty" : receipt_qty})
                                    projected_po.append({"po" : item.purchase_order , "qty" : po["qty"] , "pr" : pr})
                                else:  
                                    row.reserved_qty += item.qty
                                    row.projected_qty -= item.qty
                                    po["qty"] -= item.qty
                                    projected_po.remove(po)
                                    pr.append({"name" : purchase_receipt , "qty" : item.qty})
                                    projected_po.append({"po" : item.purchase_order , "qty" : po["qty"] , "pr" : pr})
                                row.projected_purchase_orders = json.dumps({"projected_po": projected_po})

                sales_order_qtys.save(ignore_permissions=True)


def return_reserved_qtys_of_item(item, sales_order = None, purchase_receipt = None):
    if sales_order:
        if frappe.db.exists("Sales Order Qtys", {
            "sales_order": sales_order,
            "is_cancelled": 0
            }):

            sales_order_qtys = frappe.get_doc("Sales Order Qtys", {
                "sales_order": sales_order, 
                "is_cancelled": 0
            })

            for row in sales_order_qtys.items:
                if row.item_code == item.item_code:
                    ordered_po = json.loads(row.ordered_purchase_orders).get("ordered_po")
                    for po in ordered_po:
                        if item.purchase_order == po["po"]:
                            receipt = 0
                            for pr in po["pr"]:
                                if pr["name"] == purchase_receipt:
                                    receipt = pr["qty"]
                                    row.reserved_qty -= pr["qty"]
                                    row.ordered_qty += pr["qty"]
                                    po["pr"].remove(pr)
                            po["qty"] += receipt
                            row.ordered_purchase_orders = json.dumps({"ordered_po": ordered_po})
                            row.is_completed = 0

                    sales_order_qtys.save(ignore_permissions=True)
    
    else:
        if item.purchase_order:
            docs = frappe.db.sql(f"""
                select soq.name
                from `tabSales Order Qtys` as soq
                inner join `tabSales Order Qtys Item` as soqi on soq.name = soqi.parent and soq.is_cancelled = 0
                where soqi.item_code = '{item.item_code}' and soqi.projected_purchase_orders like '%{item.purchase_order}%'
                order by soqi.projected_qty desc
            """, as_dict=1)

            if not docs or not len(docs): return

            for doc in docs:
                sales_order_qtys = frappe.get_doc("Sales Order Qtys", doc.name)
                for row in sales_order_qtys.items:
                    if row.item_code == item.item_code:
                        projected_po = json.loads(row.projected_purchase_orders).get("projected_po")
                        for po in projected_po:
                            if item.purchase_order == po["po"]:
                                receipt = 0
                                if po.get("pr"):
                                    for pr in po["pr"]:
                                        if pr["name"] == purchase_receipt:
                                            receipt = pr["qty"]
                                            row.reserved_qty -= pr["qty"]
                                            row.projected_qty += pr["qty"]
                                            po["pr"].remove(pr)
                                        po["qty"] += receipt
                                        row.projected_purchase_orders = json.dumps({"projected_po": projected_po})
                                        row.is_completed = 0
                                        sales_order_qtys.save(ignore_permissions=True)


   