# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import json
from copy import deepcopy

import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import now

from erpnext.accounts.party import get_party_account_currency, get_party_details
from erpnext.stock.doctype.material_request.material_request import set_missing_values
from erpnext.buying.doctype.request_for_quotation.request_for_quotation import RequestforQuotation
from erpnext.stock.doctype.packed_item.packed_item import get_product_bundle_items

from sabaintegration.stock.get_item_details import get_item_warehouse
from sabaintegration.overrides.opportunity import add_item_to_table

class CustomRequestforQuotation(RequestforQuotation):
    def validate(self):
        super(CustomRequestforQuotation, self).validate()
        if self.is_new():
            self.create_copied_option()
            self.set_title()
        self.validate_bundle_items()
        if self.get("_action") and self._action == 'submit':
            self.submitting_date = now()
    
    def on_submit(self):
        frappe.db.set(self, "status", "Submitted")
        for supplier in self.suppliers:
            supplier.email_sent = 0
            supplier.quote_status = "Pending"
        if self.get("send_rfq_email"): self.send_to_supplier()
        self.create_sq_automatically()

    def create_sq_automatically(self):
        if len(self.suppliers) == 1:
            doc = first_supplier_quotation(self.name, for_supplier = self.suppliers[0].supplier, to_save = True)
            doc.save(ignore_permissions = True)
            #frappe.db.commit()
            self.reload()
            frappe.msgprint("A Supplier Quotation <a href='/app/supplier-quotation/{0}'><b>{0}</b></a> is created".format(doc.name))

    def on_cancel(self):
        super(CustomRequestforQuotation, self).on_cancel()
        self.delete_copied_option()
        self.delete_draft_sq()

    def before_insert(self):                    
        if self.opportunity:
            self.check_opportunity_option_number()
        
    def delete_draft_sq(self):
        supplier_quotation = frappe.db.get_all(
            "Supplier Quotation",
            {"supplier":self.suppliers[0].supplier , "opportunity" : self.opportunity , "docstatus" : 'Draft'},
            "name"
        )      
        if supplier_quotation:
            frappe.get_doc('Supplier Quotation' , supplier_quotation[0].name).delete()
            #frappe.db.commit()                    
    
    def after_delete(self):
        if self.docstatus == 0:
            self.delete_copied_option()

    def delete_copied_option(self):
        copied_option = frappe.db.get_all("Copied Opportunity Option", {"request_for_quotation":self.name}, "name")
        if copied_option:
            doc = frappe.get_doc("Copied Opportunity Option", copied_option[0]["name"])
            doc.delete()
            #frappe.db.commit()

    def validate_bundle_items(self):
        """Check if product bundle item that is in items table 
        has at least one packed item in packed items table
        if not, remove it"""
        
        if self.get_doc_before_save():
            items_before_save = [item.item_code for item in self.get_doc_before_save().get("packed_items")]
            items_after_save = [item.item_code for item in self.get("packed_items")]
            reset_table = items_before_save != items_after_save
            if not reset_table: return
        i = 1
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
                        item.idx = i
                        itemslist.append(item)
                        i += 1
                        break
            else: 
                item.idx = i
                itemslist.append(item)
                i += 1
        self.update({"items": itemslist})

    def create_copied_option(self):
        "Create Copied Opportunity Option if the rfq comes from an opportunity"
        if not self.opportunity:
            return

        option_number = 0
        for item in self.items:
            if item.opportunity_option_number:
                option_number = item.opportunity_option_number
                break

        if option_number:
            filters = {
                "parent": self.opportunity,
                "parentfield": "option_"+str(option_number)
            }
            copied_option = frappe.new_doc("Copied Opportunity Option")
            opportunity_option = frappe.db.get_all("Opportunity Option", filters, ['*'])
            optionlist = []
            for option in opportunity_option:
                add_item_to_table(option, optionlist, other_fields={
                    "section_title": option.get("section_title"),
                    "technical_comment": option.get("technical_comment")
                })
            copied_option.update({"opportunity_option": optionlist})
            copied_option.opportunity = self.opportunity
            copied_option.option_number = option_number
            copied_option.request_for_quotation = self.name
            copied_option.insert(ignore_permissions = True)
            #frappe.db.commit()

    # def autoname(self):
        ###If this rfq is coming from an opportunity option,
        ###then the name of rfq will include the opportunity name and option
        # is_from_opp = False
        # opportunityTitle = None
        # option_number = None
        # for item in self.get("items"):
        #     if item.opportunity and item.opportunity_option_number: 
        #         opportunityTitle = frappe.db.get_value("Opportunity", item.opportunity, "title") or item.opportunity
        #         option_number = item.opportunity_option_number
        #         is_from_opp = True
        #         break
        # if is_from_opp:
        #     from frappe.model.naming import make_autoname

        #     name = "{0}-Option{1}-".format(opportunityTitle, option_number)
        #     self.name= make_autoname(name+".####", "", self)

        # else:
        #     from frappe.model.naming import set_name_by_naming_series, make_autoname

        #     set_name_by_naming_series(self)
        
    def set_title(self):
        is_from_opp = False
        opportunityTitle = None
        option_number = None
        for item in self.get("items"):
            if item.opportunity and item.opportunity_option_number: 
                opportunityTitle = frappe.db.get_value("Opportunity", item.opportunity, "title") or item.opportunity
                option_number = item.opportunity_option_number
                is_from_opp = True
                break
        if is_from_opp:
            self.title = "{0}-Option{1}".format(opportunityTitle, option_number)

    def send_to_supplier(self):
        """Sends RFQ mail to involved suppliers."""
        if not self.get("send_rfq_email"): return
        for rfq_supplier in self.suppliers:
            if rfq_supplier.email_id is not None and rfq_supplier.send_email:
                self.validate_email_id(rfq_supplier)

                # make new user if required
                update_password_link, contact = self.update_supplier_contact(rfq_supplier, self.get_link())

                self.update_supplier_part_no(rfq_supplier.supplier)
                self.supplier_rfq_mail(rfq_supplier, update_password_link, self.get_link())
                rfq_supplier.email_sent = 1
                if not rfq_supplier.contact:
                    rfq_supplier.contact = contact
                rfq_supplier.save()
    
    # def update_sqs_rates(self, sqs):
    #     from sabaintegration.overrides.supplier_quotation import set_rates
    #     supplier_quotation = frappe.db.get_all('Supplier Quotation Item', {'request_for_quotation': self.name, "docstatus": 0}, 'parent', distinct = 1)
    #     if supplier_quotation:
    #         supplier_quotation = supplier_quotation[0].parent
    #         not_updated_items = updated_items = []
    #         if not self.get("amended_from"): return
    #         sqs = sqs.get(self.amended_from)
    #         print(f"\033[93m {sqs}")
    #         if not sqs: return
    #         for sq in sqs:
    #             items = set_rates(sq, supplier_quotation)
    #             for i in items[0]['updated_items']:
    #                 updated_items.append(i)
    #             for i in items[1]['not_updated_items']:
    #                 not_updated_items.append(i)
    #         print(f"\033[94m {updated_items}")
    #         print(f"\033[94m {not_updated_items}")
    #         doc = frappe.get_doc("Supplier Quotation", supplier_quotation)
    #         doc.items = []
    #         doc.append("items", not_updated_items)
    #         doc.append("items", updated_items)
    #         doc.save(ignore_permissions = True)
    #         if not not_updated_items:
    #             doc.submit(ignore_permissions = True)

    def check_opportunity_option_number(self):
        opportunity_option_number = None
        for item in self.items:
            opportunity_option_number = item.opportunity_option_number
            break
        
        if opportunity_option_number == 0:
            frappe.throw("You must back to Opportunity and recreate the Request for Quotation") 

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
def delete_by_brand(items, packed_items, brands):
    messages = {}
    if brands: brands = json.loads(brands)
    if len(items) > 0:
        itemslist = []
        items = json.loads(items)
        #i = 1
        for item in items:
            # found = False
            if not frappe.db.exists("Product Bundle", {"new_item_code": item["item_code"]}):
                for brand in brands:
                    if (item["brand"] == brand["brand"]):
                        # found = True
                        newitem = deepcopy(item)
                        fields = {
                            "stock_uom": newitem.get("uom") or newitem.get("stock_uom") or frappe.db.get_value("Item", newitem.get("item_code"), "stock_uom"),
                            "conversion_factor": 1.00,
                            "image": newitem.get("image") or frappe.db.get_value("Item", newitem.get("item_code"), "image"),
                            "opportunity": newitem.get("opportunity"),
                            "opportunity_option_number": newitem.get("opportunity_option_number"),
                            "opportunity_item": newitem.get("opportunity_item")
                        }
                        add_item_to_table(newitem, itemslist, doc = None, other_fields= fields)
                        #itemslist.append(item)
                        #i += 1
                        break
            else: 
                #item["idx"] = i
                newitem = deepcopy(item)
                fields = {
                    "stock_uom": newitem.get("uom") or newitem.get("stock_uom") or frappe.db.get_value("Item", newitem.get("item_code"), "stock_uom"),
                    "conversion_factor": 1.00,
                    "image": newitem.get("image") or frappe.db.get_value("Item", newitem.get("item_code"), "image"),
                    "opportunity": newitem.get("opportunity"),
                    "opportunity_option_number": newitem.get("opportunity_option_number"),
                    "opportunity_item": newitem.get("opportunity_item")
                }
                add_item_to_table(newitem, itemslist, doc = None, other_fields= fields)
                #itemslist.append(item)
                #i += 1
            # if not found:
            #     item["idx"] = item["idx"] - i
            #     itemslist.append(item)

        messages["items"] = itemslist

    if len(packed_items) > 0:
        itemslist = []
        packed_items = json.loads(packed_items)
        #i = 1
        for item in packed_items:
            # found = False
            for brand in brands:
                if (item["brand"] == brand["brand"]):
                    # found = True
                    #item["idx"] = i
                    newitem = deepcopy(item)
                    add_item_to_table(newitem, itemslist)
                    #itemslist.append(item)
                    #i += 1
                    break
            # if not found:
            #     item["idx"] = item["idx"] - i
            #     itemslist.append(item)

        messages["packed_items"] = itemslist

    return messages

@frappe.whitelist()
def make_supplier_quotation_from_rfq(source_name, target_doc=None, for_supplier=None):
    from frappe.utils import now, today, add_months
    if not frappe.db.exists("Supplier Quotation Item", {"request_for_quotation": source_name, "docstatus": ("!=", 2)}):
        doclist = first_supplier_quotation(source_name, target_doc, for_supplier)
        
    else:
        doclist = not_first_supplier_quotation(source_name, target_doc, for_supplier)
    
    from frappe.utils import now, today, add_months
    doclist.transaction_date = now()
    doclist.valid_till = add_months(today(), 1)
    return doclist

def first_supplier_quotation(source_name, target_doc=None, for_supplier=None, to_save = None):
    def postprocess(source, target_doc):
        if for_supplier:
            target_doc.supplier = for_supplier
            args = get_party_details(for_supplier, party_type="Supplier", ignore_permissions=True)
            target_doc.currency = args.currency or get_party_account_currency(
                "Supplier", for_supplier, source.company
            )
            target_doc.selling_price_list = target_doc.buying_price_list = ''
            if source.opportunity: target_doc.opportunity = source.opportunity
            target_doc.supplier_group = frappe.db.get_value("Supplier", for_supplier, "supplier_group")
            target_doc.flags.ignore_permissions = True
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
            ignore_permissions = True
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
                    if to_save and not doclist.items[i].warehouse: doclist.items[i].warehouse = "General - S"
                    break
                i += 1
                    
            if not found:
                sqi = frappe.new_doc("Supplier Quotation Item")
                sqi.item_code = item.item_code
                sqi.qty = item.qty
                sqi.item_name = frappe.db.get_value("Item", item.item_code, "item_name")
                sqi.description = item.description
                sqi.uom = item.uom
                sqi.request_for_quotation = item.parent
                sqi.warehouse = item.get("warehouse") or ""
                if to_save and not sqi.warehouse: sqi.warehouse = "General - S"
                newitems.append(sqi)
    if to_save:
        for item in newitems:
            if not item.warehouse:
                item.warehouse = "General - S"

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
            target_doc.selling_price_list = target_doc.buying_price_list = ''
        if source.opportunity: target_doc.opportunity = source.opportunity
        target_doc.supplier_group = frappe.db.get_value("Supplier", for_supplier, "supplier_group")
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
            ignore_permissions = True
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
                sqi.warehouse = item.get("warehouse") or ""
                newitems.append(sqi)
                item_list.append(sqi)
    doclist.update({
        "items": newitems
    })
    return doclist

@frappe.whitelist(allow_guest = True)
def get_quotations_related_to_rfq(doc_name):
    quotations = frappe.db.sql(f"""
    SELECT DISTINCT `tabQuotation`.name
    FROM `tabQuotation` INNER JOIN `tabFrom Supplier Quotation` ON `tabFrom Supplier Quotation`.parent = `tabQuotation`.name
    INNER JOIN `tabRequest for Quotation` ON `tabRequest for Quotation`.name = `tabFrom Supplier Quotation`.request_for_quotation
    WHERE `tabFrom Supplier Quotation`.request_for_quotation = '{doc_name}'
    """ , as_dict = True)

    return {"quotations" : quotations}
