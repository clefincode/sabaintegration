import frappe
from frappe.utils import cint
from erpnext.stock.doctype.delivery_note.delivery_note import DeliveryNote
# from erpnext.stock.doctype.batch.batch import set_batch_nos

from sabaintegration.sabaintegration.doctype.sales_order_qtys.sales_order_qtys import get_actual_qty, get_total_reserved_qty
from frappe.utils import now

class CustomDeliveryNote(DeliveryNote):
    def validate(self):
        self.validate_posting_time()
        super(DeliveryNote, self).validate()
        self.set_status()
        self.so_required()
        self.validate_proj_cust()
        self.check_sales_order_on_hold_or_close("against_sales_order")
        self.validate_warehouse()
        self.validate_uom_is_integer("stock_uom", "stock_qty")
        self.validate_uom_is_integer("uom", "qty")
        self.validate_with_previous_doc()
        self.set_serial_and_batch_bundle_from_pick_list()

        make_packing_list(self)

        # if self._action != "submit" and not self.is_return:
        #     set_batch_nos(self, "warehouse", throw=True)
        #     set_batch_nos(self, "warehouse", throw=True, child_table="packed_items")

        self.update_current_stock()

        if not self.installation_status:
            self.installation_status = "Not Installed"
        self.reset_default_field_value("set_warehouse", "items", "warehouse")

        if self.get("_action") and self._action == 'submit':
            self.submitting_date = now()

    def on_submit(self):
        super(CustomDeliveryNote, self).on_submit()
        self.on_submit_delivery_note()



    def before_submit(self):
        self.check_if_qtys_are_reserved()

    def on_cancel(self):
        super(CustomDeliveryNote, self).on_cancel()
        self.update_qtys()

    def on_submit_delivery_note(self):
        customer = self.customer  

        for item in self.items:
            if item.serial_no:
                serial_nos = item.serial_no.split("\n")
                for serial in serial_nos:
                    self.update_serial_custom_customer(serial, customer)
            else:
                if item.serial_and_batch_bundle:
                    serial_and_batch = frappe.get_doc("Serial and Batch Bundle", item.serial_and_batch_bundle)
                    for row in serial_and_batch.entries:
                        self.update_serial_custom_customer(row.serial_no, customer)


    def update_serial_custom_customer(self, serial_no, customer):
        serial_doc = frappe.get_doc("Serial No", serial_no)
        
        if not serial_doc.custom_customer:
            serial_doc.custom_customer = customer
            serial_doc.save()


    def check_if_qtys_are_reserved(self):
        if self.ignore_unreserved_qty: return

        sales_order = None
        for item in self.items:
            if item.against_sales_order:
                sales_order = item.against_sales_order
                break
        
        linked_so = False
        if sales_order:
            if frappe.db.exists("Sales Order Qtys", {"sales_order": sales_order, "is_cancelled": 0}):
                linked_so = True
                sales_order_qtys = frappe.get_doc("Sales Order Qtys", {"sales_order": sales_order, "is_cancelled": 0})
                for item in self.items:
                    for row in sales_order_qtys.items:
                        if row.so_detail == item.so_detail:
                            if row.reserved_qty < item.qty:
                                frappe.throw("Can't deliver the doc. There are {} unreserved qtys".format(item.qty - row.reserved_qty))
                            
                            row.delivered_qty += item.qty
                            row.reserved_qty -= item.qty

                sales_order_qtys.save(ignore_permissions=True)

        if not linked_so:
            for item in self.items:
                actual_qty = get_actual_qty(item.item_code)
                reserved_qty = get_total_reserved_qty(item.item_code)

                remained_reserved_qty = actual_qty - reserved_qty

                if remained_reserved_qty < item.qty:
                    frappe.throw("Can't deliver the doc. There are {} unreserved qtys".format(item.qty - remained_reserved_qty))

    def update_qtys(self):
        if self.ignore_unreserved_qty: return

        sales_order = None
        for item in self.items:
            if item.against_sales_order:
                sales_order = item.against_sales_order
                break
        
        if sales_order:
            if frappe.db.exists("Sales Order Qtys", {"sales_order": sales_order, "is_cancelled": 0}):
                sales_order_qtys = frappe.get_doc("Sales Order Qtys", {"sales_order": sales_order, "is_cancelled": 0})
                for item in self.items:
                    for row in sales_order_qtys.items:
                        if row.so_detail == item.so_detail:
                            row.delivered_qty -= item.qty
                            row.reserved_qty += item.qty
                
                sales_order_qtys.save(ignore_permissions=True)

def make_packing_list(doc):
    "Make/Update packing list for Product Bundle Item."
    from erpnext.stock.doctype.packed_item.packed_item import (
        get_indexed_packed_items_table,
        is_product_bundle,
        add_packed_item_row,
        get_packed_item_details,
        set_product_bundle_rate_amount,
        update_product_bundle_rate,
        update_packed_item_from_cancelled_doc,
        update_packed_item_price_data,
        update_packed_item_stock_data
        )
            
    if doc.get("_action") and doc._action == "update_after_submit":
        return

    parent_items_price, reset = {}, False
    set_price_from_children = frappe.db.get_single_value(
        "Selling Settings", "editable_bundle_item_rates"
    )

    stale_packed_items_table = get_indexed_packed_items_table(doc)

    reset = reset_packing_list(doc)

    for item_row in doc.get("items"):
        if item_row.get("from_bundle_delivery_note"): continue
        if is_product_bundle(item_row.item_code):
            for bundle_item in get_product_bundle_items(item_row.item_code, doc):
                pi_row = add_packed_item_row(
                    doc=doc,
                    packing_item=bundle_item,
                    main_item_row=item_row,
                    packed_items_table=stale_packed_items_table,
                    reset=reset,
                )
                item_data = get_packed_item_details(bundle_item.item_code, doc.company)
                update_packed_item_basic_data(item_row, pi_row, bundle_item, item_data)
                update_packed_item_stock_data(item_row, pi_row, bundle_item, item_data, doc)
                update_packed_item_price_data(pi_row, item_data, doc)
                update_packed_item_from_cancelled_doc(item_row, bundle_item, pi_row, doc)

                if set_price_from_children:  # create/update bundle item wise price dict
                    update_product_bundle_rate(parent_items_price, pi_row)

    if parent_items_price:
        set_product_bundle_rate_amount(doc, parent_items_price)  # set price in bundle item

def reset_packing_list(doc):
    "Conditionally reset the table and return if it was reset or not."
    reset_table = False
    doc_before_save = doc.get_doc_before_save()

    if doc_before_save:
        items_before_save = [(item.item_code, item.qty) for item in doc_before_save.get("items")]
        items_after_save = [(item.item_code, item.qty) for item in doc.get("items")]
        reset_table = items_before_save != items_after_save
    else:
        reset_table = True

    if not reset_table: return reset_table
            
    packeditems = []
    i = 1
    for item in doc.get("packed_items"):
        for p_item in doc.get("items"):
            #if exists then check the qty
            if item.parent_item == p_item.item_code:
                if not p_item.get("from_bundle_delivery_note"):
                    break

                for packed in get_product_bundle_items(p_item.item_code, doc):
                    if packed.item_code == item.item_code:
                        # if the packed qty is greater than the required then reset it
                        # if the qty is less than the required then it means that the remainder qty hasn't yet received
                        if packed.qty * p_item.qty < item.qty:
                            item.qty = packed.qty * p_item.qty
                        break
                if reset_table:
                    item.idx = i
                    packeditems.append(item)
                    i += 1
                break

    if reset_table: doc.set("packed_items", packeditems)

    return reset_table

def get_product_bundle_items(item_code, doc):
    from erpnext.stock.doctype.packed_item.packed_item import get_product_bundle_items

    packed_items = get_product_bundle_items(item_code)

    if not doc.get("bdns"): return packed_items

    bdns = [row.bundle_delivery_note for row in doc.bdns if cint(row.status) != 2]

    if not bdns: return packed_items
        
    for bdn in bdns:
        bdn_doc = frappe.get_doc("Bundle Delivery Note", bdn)
        if not bdn_doc.get("excluded_items"): continue

        if bdn_doc.get("multiple_items") == 0 and bdn_doc.get("item_parent") and bdn_doc.item_parent != item_code: continue

        elif bdn_doc.get("multiple_items") == 1 :
            found = False
            for item in bdn_doc.parents_items:
                if item.item_code == item_code:
                    found = True
                    break
            if not found: continue
        
        for row in bdn_doc.excluded_items:
            if row.parent_item == item_code:
                excluded_item = row.item_code
                alt_item = row.alt_item if row.get("alt_item") else ""
                #qty = row.qty
                for packed in packed_items:
                    if packed.item_code == excluded_item:
                        if alt_item: 
                            packed["excluded_item"] = packed.item_code
                            packed.item_code = alt_item
                            packed["is_alternative"] = 1
                            #packed.qty = qty
                        else:
                            packed_items.remove(packed)
    return packed_items

def update_packed_item_basic_data(main_item_row, pi_row, packing_item, item_data):
    from erpnext.stock.doctype.packed_item.packed_item import update_packed_item_basic_data

    update_packed_item_basic_data(main_item_row, pi_row, packing_item, item_data)
    pi_row.description = frappe.db.get_value("Item", pi_row.item_code, "description")
    pi_row.excluded_item = packing_item.get("excluded_item") if  packing_item.get("excluded_item") else ""
    pi_row.is_alternative = 1 if packing_item.get("is_alternative") else 0