import json
import frappe
from erpnext.buying.doctype.purchase_order.purchase_order import PurchaseOrder
from frappe.utils import now

class CustomPurchaseOrder(PurchaseOrder):
    def validate(self):
        # Call the original validate method
        super(CustomPurchaseOrder, self).validate()
        if self.get("_action") and self._action == 'submit':
            self.submitting_date = now()


    def on_submit(self):
        super(CustomPurchaseOrder, self).on_submit()
        self.set_ordered_qtys()

    def set_ordered_qtys(self):
        for item in self.items:
            set_ordered_qtys_of_item(item)

    def on_cancel(self):
        super(CustomPurchaseOrder, self).on_cancel()
        self.update_qtys()

    def update_qtys(self):
        sales_order = None
        for item in self.items:
            if item.sales_order:
                sales_order = item.sales_order
                break

        if sales_order:
            if frappe.db.exists("Sales Order Qtys", sales_order):
                doc = frappe.get_doc("Sales Order Qtys", sales_order)
                for item in self.items:
                    for row in doc.items:
                        if row.item_code == item.item_code:                            
                            ordered_po = json.loads(row.ordered_purchase_orders).get("ordered_po")
                            if ordered_po:
                                for po in ordered_po:
                                    if po["po"] == self.name:
                                        row.ordered_qty -= po["qty"] 
                                        ordered_po.remove(po) 
                                        row.ordered_purchase_orders = json.dumps({"ordered_po": ordered_po})
                                        doc.save(ignore_permissions=True)
                                
        else:
            for item in self.items:
                item_soqs = frappe.db.sql(f"""
                    select soq.name
                    from `tabSales Order Qtys` as soq
                    inner join `tabSales Order Qtys Item` as soqi on soq.name = soqi.parent and soq.is_cancelled = 0
                    where soqi.is_completed = 0 and soqi.is_delivered = 0
                    and soqi.projected_qty > 0 and soqi.item_code = '{item.item_code}'
                    order by soqi.projected_qty desc
                """, as_dict=1)

                for soq in item_soqs:
                    soq_doc = frappe.get_doc("Sales Order Qtys", soq.name)
                    for row in soq_doc.items:
                        projected_po = json.loads(row.projected_purchase_orders).get("projected_po")
                        if projected_po:
                            for po in projected_po:
                                if po["po"] == self.name:
                                    row.projected_qty -= po["qty"]  
                                    projected_po.remove(po)                                  
                                    row.projected_purchase_orders = json.dumps({"projected_po": projected_po})
                                    soq_doc.save(ignore_permissions=True)           

def set_ordered_qtys_of_item(item):
    if item.sales_order:
        if frappe.db.exists("Sales Order Qtys", {"sales_order": item.sales_order, "is_cancelled": 0}):
            sales_order_qtys = frappe.get_doc("Sales Order Qtys", {"sales_order": item.sales_order, "is_cancelled": 0})
            for row in sales_order_qtys.items:
                if item.item_code == row.item_code and row.remained_qty > 0:
                    ordered_qty = 0
                    if item.qty <= row.remained_qty:
                        ordered_qty = item.qty
                        row.ordered_qty += item.qty
                    else:
                        ordered_qty = row.remained_qty
                        row.ordered_qty += row.remained_qty                  

                    ordered_po = json.loads(row.ordered_purchase_orders).get("ordered_po")
                    if not ordered_po:
                        ordered_po = []
                    ordered_po.append({"po" : item.parent , "qty" : ordered_qty})
                    row.ordered_purchase_orders = json.dumps({"ordered_po": ordered_po})

            sales_order_qtys.save(ignore_permissions = True)
    
    else:
        docs = frappe.db.sql(f"""
            select soq.name
            from `tabSales Order Qtys` as soq
            inner join `tabSales Order Qtys Item` as soqi on soq.name = soqi.parent and soq.is_cancelled = 0
            where soqi.item_code = '{item.item_code}' and soqi.is_completed = 0
            and soqi.remained_qty > 0
        """, as_dict=1)

        if not docs or not len(docs): return

        total_qty, is_zero = item.qty, False

        for doc in docs:
            sales_order_qtys = frappe.get_doc("Sales Order Qtys", doc.name)
            for row in sales_order_qtys.items:
                if row.item_code == item.item_code:
                    if row.remained_qty > 0:
                        if row.remained_qty >= total_qty:
                            row.projected_qty += total_qty
                            projected_po = json.loads(row.projected_purchase_orders).get("projected_po")
                            if not projected_po:
                                projected_po = []
                            projected_po.append({"po" : item.parent , "qty" : total_qty})
                            row.projected_purchase_orders = json.dumps({"projected_po": projected_po})

                            total_qty = 0

                        else:
                            row.projected_qty += row.remained_qty
                            projected_po = json.loads(row.projected_purchase_orders).get("projected_po")
                            if not projected_po:
                                projected_po = []
                            projected_po.append({"po" : item.parent , "qty" : row.remained_qty})
                            row.projected_purchase_orders = json.dumps({"projected_po": projected_po})
                            total_qty -= row.remained_qty

                
                if total_qty <= 0: 
                    is_zero = True
                    break         
 
            sales_order_qtys.save(ignore_permissions=True)
            if is_zero:
                break
