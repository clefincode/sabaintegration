# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import json

import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc

from erpnext.accounts.party import get_party_account_currency, get_party_details
from erpnext.buying.utils import validate_for_items
from erpnext.stock.doctype.material_request.material_request import set_missing_values
from erpnext.buying.doctype.request_for_quotation.request_for_quotation import RequestforQuotation
from sabaintegration.stock.get_item_details import get_item_warehouse
from erpnext.stock.doctype.packed_item.packed_item import get_product_bundle_items


class CustomRequestforQuotation(RequestforQuotation):
    def validate(self):
        self.validate_duplicate_supplier()
        self.validate_supplier_list()
        validate_for_items(self)
        super(CustomRequestforQuotation, self).set_qty_as_per_stock_uom()
        self.update_email_id()

        if self.docstatus < 1:
            # after amend and save, status still shows as cancelled, until submit
            frappe.db.set(self, "status", "Draft")
        self.validate_bundle_items() ###Custom Update

    def validate_bundle_items(self):
        """Check if product bundle item that is in items table 
        has at least one packed item in packed items table
        if not, remove it"""
        
        if self.get_doc_before_save():
            items_before_save = [item.item_code for item in self.get_doc_before_save().get("packed_items")]
            items_after_save = [item.item_code for item in self.get("packed_items")]
            reset_table = items_before_save != items_after_save
            if not reset_table: return
        i = 0
        itemslist = []
        for item in self.items:
            if frappe.db.exists("Product Bundle", {"new_item_code": item.item_code}):
                found = False
                for bundle_item in get_product_bundle_items(item.item_code):
                    for packed_item in self.packed_items:
                        if packed_item.item_code == bundle_item.item_code:
                            found = True
                            break
                    if found:
                        itemslist.append(item)
                        break
            else: itemslist.append(item)
        self.update({"items": itemslist})

    def autoname(self):
        ###If this rfq is coming from an opportunity option,
        ###then the name of rfq will include the opportunity name and option
        is_from_opp = False
        opportunity = None
        option_number = None
        for item in self.get("items"):
            if item.opportunity and item.opportunity_option_number: 
                opportunity = item.opportunity
                option_number = item.opportunity_option_number
                is_from_opp = True
                break
        if is_from_opp:
            from frappe.model.naming import make_autoname

            name = "PUR-RFQ-{0}-OP{1}-".format(opportunity, option_number)
            self.name= make_autoname(name+".####", "", self)

        else:
            from frappe.model.naming import set_name_by_naming_series, make_autoname

            set_name_by_naming_series(self)

    @frappe.whitelist()
    def make_packing_list(self):
        from copy import deepcopy
        doc = deepcopy(self)
        packing_list = {}
        brand_list = {}
        for item_row in doc.get("items"):
            if frappe.db.exists("Product Bundle", {"new_item_code": item_row.item_code}):
                for bundle_item in get_product_bundle_items(item_row.item_code):
                    packing_list[bundle_item.item_code] = packing_list.get(bundle_item.item_code, 0) + (bundle_item.qty * float(item_row.qty)) 
                    brand_list[bundle_item.item_code] = frappe.db.get_value("Item", bundle_item.item_code, "brand")
        
        table = []
        table = _order_by_brand(table, packing_list, brand_list, doc.company)
        if not self.is_new(): doc.append("packed_items", table)
        else: doc.update({"packed_items": table})

        return doc.get("packed_items")

    @frappe.whitelist()
    def update_packing_list(self):
        from copy import deepcopy
        doc = deepcopy(self)
        packing_list = {}
        brand_list = {}
        for item in doc.get("packed_items"):
            packing_list[item.item_code] = item.qty
            brand_list[item.item_code] = frappe.db.get_value("Item", item.item_code, "brand")

        table = []
        table = _order_by_brand(table, packing_list, brand_list, doc.company)
        
        doc.update({"packed_items": table})
        
        return doc.get("packed_items")

    @frappe.whitelist()
    def remove_from_packing_list(self):
        from copy import deepcopy
        doc = deepcopy(self)
        packed_items = deepcopy(doc.packed_items)
        todelete = []
        i = 0
        for packed_item in packed_items:
            packed_item.qty = 0
            for item in self.items:
                if frappe.db.exists("Product Bundle", {"new_item_code": item.item_code}):
                    for bundle_item in get_product_bundle_items(item.item_code):
                        if bundle_item.item_code == packed_item.item_code:
                            packed_item.qty += bundle_item.qty * item.qty
                            break
            if packed_item.qty == 0:
                todelete.append(i)
            i += 1
        for index in sorted(todelete, reverse=True):
            del packed_items[index]

        doc.update({"packed_items": packed_items})
        return doc.get("packed_items")

def _order_by_brand(table, items_list, brand_list = None, company = None):
    if not brand_list:
        brand_list = []
    if brand_list:
        brand_list = sorted(brand_list.items(), key=lambda x:x[1])
        for item in brand_list:
            table.append({
                "item_code": item[0],
                "qty": items_list[item[0]],
                "uom": frappe.db.get_value("Item", item[0], "stock_uom"),
                "description": frappe.db.get_value("Item", item[0], "description"),
                "brand": item[1],
                "warehouse": get_item_warehouse(frappe.get_doc("Item", item[0]), args = frappe._dict({"company": company}), overwrite_warehouse = True) if company else ""
            })
    return table


@frappe.whitelist()
def make_supplier_quotation_from_rfq(source_name, target_doc=None, for_supplier=None):
    if not frappe.db.exists("Supplier Quotation Item", {"request_for_quotation": source_name, "docstatus": ("!=", 2)}):
        doclist = first_supplier_quotation(source_name, target_doc, for_supplier)
        
    else:
        doclist = not_first_supplier_quotation(source_name, target_doc, for_supplier)

    return doclist

def first_supplier_quotation(source_name, target_doc=None, for_supplier=None):
    def postprocess(source, target_doc):
        if for_supplier:
            target_doc.supplier = for_supplier
            args = get_party_details(for_supplier, party_type="Supplier", ignore_permissions=True)
            target_doc.currency = args.currency or get_party_account_currency(
                "Supplier", for_supplier, source.company
            )
            target_doc.buying_price_list = args.buying_price_list or frappe.db.get_value(
                "Buying Settings", None, "buying_price_list"
            )
        set_missing_values(source, target_doc)

    doclist = get_mapped_doc(
            "Request for Quotation",
            source_name,
            {
                "Request for Quotation": {
                    "doctype": "Supplier Quotation",
                    "validation": {"docstatus": ["=", 1]},
                },
                "Request for Quotation Packed Item": {
                    "doctype": "Supplier Quotation Item",
                    "field_map": {"name": "request_for_quotation_item", "parent": "request_for_quotation"},
                },
            },
            target_doc,
            postprocess,
        )
    newitems = doclist.items
    items = frappe.get_doc("Request for Quotation", source_name).items
    for item in items:
        if not frappe.db.exists("Product Bundle", {"new_item_code": item.item_code}):
            found = False
            i = 0
            for s_item in doclist.items:
                if s_item.item_code == item.item_code:
                    found = True
                    doclist.items[i].qty += item.qty
                    newitems = doclist.items
                    break
                    
            if not found:
                sqi = frappe.new_doc("Supplier Quotation Item")
                sqi.item_code = item.item_code
                sqi.qty = item.qty
                sqi.item_name = frappe.db.get_value("Item", item.item_code, "item_name")
                sqi.description = item.description
                sqi.uom = item.uom
                sqi.request_for_quotation = item.parent
                newitems.append(sqi)
    doclist.update({
        "items": newitems
    })
    return doclist

def not_first_supplier_quotation(source_name, target_doc=None, for_supplier=None):
    def postprocess(source, target_doc):
        if for_supplier:
            target_doc.supplier = for_supplier
            args = get_party_details(for_supplier, party_type="Supplier", ignore_permissions=True)
            target_doc.currency = args.currency or get_party_account_currency(
                "Supplier", for_supplier, source.company
            )
            target_doc.buying_price_list = args.buying_price_list or frappe.db.get_value(
                "Buying Settings", None, "buying_price_list"
            )
        set_missing_values(source, target_doc)

    doclist = get_mapped_doc(
            "Request for Quotation",
            source_name,
            {
                "Request for Quotation": {
                    "doctype": "Supplier Quotation",
                    "validation": {"docstatus": ["=", 1]},
                },
            },
            target_doc,
            postprocess,
        )
    items = frappe.get_doc("Request for Quotation", source_name).packed_items
    items += frappe.get_doc("Request for Quotation", source_name).items
    
    item_list = frappe.db.get_all("Supplier Quotation Item", {"request_for_quotation": source_name, "docstatus": ("!=", 2)}, ["item_code", "qty"])
    newitems = []
    for item in items:
        if not frappe.db.exists("Product Bundle", {"new_item_code": item.item_code}):
            found = False

            for s_item in item_list:
                if s_item.item_code == item.item_code:
                    found = True
                    for newitem in newitems:
                        if newitem.item_code == item.item_code: newitem.qty += item.qty
                    break
                
                    
            if not found:
                sqi = frappe.new_doc("Supplier Quotation Item")
                sqi.item_code = item.item_code
                sqi.qty = item.qty
                sqi.item_name = frappe.db.get_value("Item", item.item_code, "item_name")
                sqi.description = item.description
                sqi.uom = item.uom
                sqi.request_for_quotation = item.parent
                newitems.append(sqi)
                item_list.append(sqi)
    doclist.update({
        "items": newitems
    })
    return doclist