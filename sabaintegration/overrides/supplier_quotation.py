# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from copy import deepcopy
from frappe import _
from frappe.utils import flt
from frappe.model.mapper import get_mapped_doc
from frappe.utils import now

from erpnext.buying.doctype.supplier_quotation.supplier_quotation import SupplierQuotation
from erpnext.stock.doctype.packed_item.packed_item import get_product_bundle_items
from erpnext.accounts.party import get_party_account_currency
from erpnext.setup.utils import get_exchange_rate

class CustomSupplierQuotation(SupplierQuotation):
    def validate(self):
        super(CustomSupplierQuotation, self).validate()
        if self.is_new():
            self.set_title()
            self.set_rfq_status('Converted to Supplier Quotation')
        elif self.get("_action") and self._action == 'submit':
            self.submitting_date = now()

    def after_insert(self):
        self.reload()

    def set_rfq_status(self, status):
        for item in self.items:
            if item.request_for_quotation:
                doc = frappe.get_doc('Request for Quotation', item.request_for_quotation)
                if doc.docstatus == 2: return
                frappe.db.set_value('Request for Quotation', item.request_for_quotation, 'status', status)
                
                doc.reload()
                break

    def set_title(self):
        request_for_quotation = self.get_request_for_quotation()
        if not request_for_quotation: return

        opportunity, opportunity_option_number = frappe.db.get_value("Request for Quotation Item", {"parent": request_for_quotation, "docstatus": 1}, ["opportunity", "opportunity_option_number"]) 
        if not opportunity or not opportunity_option_number: return
        
        # opportunityTitle = frappe.db.get_value("Opportunity", opportunity, "title")
        # self.title = "{0}-Option{1}".format(opportunityTitle, opportunity_option_number)
        self.title = frappe.db.get_value("Request for Quotation", request_for_quotation, "title")
    
    def on_submit(self):
        super(CustomSupplierQuotation, self).on_submit()
        self.check_copied_option()
        self.create_quotation_automatically()
    
    def on_cancel(self):
        super(CustomSupplierQuotation, self).on_cancel()
        self.set_rfq_status("Submitted")
        self.update_quotation()

    def after_delete(self):
        if self.docstatus == 0:
            self.set_rfq_status("Submitted")

    def get_request_for_quotation(self):
        for item in self.items:
            if item.request_for_quotation:
                return item.request_for_quotation 

    def check_copied_option(self):
        """check if there is at least an copied option
         from the same opportunity with the same items in option"""
        request_for_quotation = self.get_request_for_quotation()
        if not request_for_quotation: return

        #Get the copied option doc
        copied_opportunity_option = frappe.db.get_all("Copied Opportunity Option", {
            "request_for_quotation": request_for_quotation
            }, "name")
        if not copied_opportunity_option: return

        doc = frappe.get_doc("Copied Opportunity Option", copied_opportunity_option[0]["name"])
        
        opportunity, opportunity_option_number = frappe.db.get_value("Request for Quotation Item", {"parent": request_for_quotation, "docstatus": 1}, ["opportunity", "opportunity_option_number"]) 
        if not opportunity and not opportunity_option_number: return

        #Get other copied option docs from the same opportunity and option number
        other_copied_opportunity_option = frappe.db.get_all("Copied Opportunity Option", {
            "opportunity": opportunity,
            "option_number": opportunity_option_number,
            "name": ("!=", copied_opportunity_option[0]["name"])
        }, ["name", "creation"], order_by = "creation")
        
        #iterate through copied option docs to check
        tosubmit = False
        for copied_option in other_copied_opportunity_option:
            #if the request copied option is before the other copied option then break
            if copied_option.creation > doc.creation:
                tosubmit = True
                break
            if not tosubmit:
                #check if other has at least one supplier quotation with draft status
                # if not, check the next copied option
                request_for_quotation = frappe.db.get_value("Copied Opportunity Option", copied_option.name, "request_for_quotation")
                
                copied_option_doc= frappe.get_doc("Copied Opportunity Option", copied_option.name)
                tosubmit = check_option_items(doc.opportunity_option, copied_option_doc)
                
                #if options are not equal to each other then don't submit this doc
                if not tosubmit:
                    if has_supplier_quotation_to_create(request_for_quotation):
                        frappe.throw("""You can't submit this supplier quotation. 
                            You have a request for quotation <a href='/app/request-for-quotation/{0}'><b>{0}</b></a> with no supplier quotation.
                            Creat supplier quotations from it and then submit them before submitting this one.""".format(request_for_quotation))
                    
                    supplier_quotation = check_supplier_quotations_status(request_for_quotation)
                    if not supplier_quotation:
                        continue

                    if supplier_quotation == True:
                        frappe.throw("""You can't submit this supplier quotation. 
                        You have a request for quotation <a href='/app/request-for-quotation/{0}'><b>{0}</b></a> with no supplier quotation.
                        Creat supplier quotations from it and then submit them before submitting this one.""".format(request_for_quotation))
                    else:
                        frappe.throw("""You can't submit this supplier quotation. 
                        You haven't submitted <a href='/app/supplier-quotation/{0}'><b>{0}</b></a> yet""".format(supplier_quotation))
    
    def update_quotation(self):
        """if the SQ is linked to a quotation 
        then remove items of sq in quotation"""

        request_for_quotation = self.get_request_for_quotation()
        if not request_for_quotation: return
        opportunity, opportunity_option_number = frappe.db.get_value("Request for Quotation Item", {"parent": request_for_quotation, "docstatus": 1}, ["opportunity", "opportunity_option_number"])
        quotation = frappe.db.get_value("Quotation Item", {
            "opportunity": opportunity,
            "opportunity_option_number": opportunity_option_number,
            "docstatus": 0},
            "parent")
        if not quotation: return

        quote_doc = frappe.get_doc("Quotation", quotation)   

        itemslist = []
        i = 1
        ## iteraten through items and packed items table in quote to remove items of canceled sq
        for quote_item in quote_doc.items:
            found = False
            for item in self.items:
                if item.name == quote_item.get("supplier_quotation_item"):
                    found = True
                    break
            if not found:
                quote_item.idx = i
                itemslist.append(quote_item)
                i += 1

        packinglist = []
        removedpackeds = []
        i = 1
        for packed_item in quote_doc.get("packed_items"):
            found = False
            for item in self.items:
                if item.name == packed_item.get("supplier_quotation_item"):
                    found = True
                    removedpackeds.append(packed_item)
                    break
            if not found:
                packed_item.idx = i
                packinglist.append(packed_item)
                i += 1
            
        quote_doc.update({"items": itemslist, "packed_items": packinglist})
        quote_doc.update_items_table() # remove items that has no packed items in quote
        # if no items has reminded in quotation then delete it
        if not quote_doc.get("items"):
            quote_doc.delete(ignore_permissions = True)
            frappe.db.commit()
            frappe.msgprint("Quotation <b>{0}</b> is deleted".format(quotation))
            return
        
        # update rate of items
        packed_items = deepcopy(quote_doc.get("packed_items"))
        for item in quote_doc.get("items"):
            if not frappe.db.exists("Product Bundle", {"new_item_code": item.item_code}): 
                continue
            rate = rate_without_margin = 0
            for packed_item in packed_items[:]:
                if packed_item.parent_item == item.item_code and packed_item.get("section_title") == item.get("section_title"):
                    rate += packed_item.rate * (packed_item.qty / item.qty)
                    rate_without_margin += packed_item.rate_before_margin * (packed_item.qty / item.qty) 
                    packed_items.remove(packed_item)
            item.rate = rate
            item.rate_without_profit_margin = rate_without_margin
            item.margin_from_supplier_quotation = (rate - rate_without_margin) / rate_without_margin * 100 if rate_without_margin else 0.00
            # to prevent assigning rate with price list rate when saving quote
            if item.price_list_rate > item.rate:
                item.margin_rate_or_amount = 0
                item.margin_type = ""
            else:
                if item.margin_type == "Amount":
                    item.margin_rate_or_amount = flt(item.rate - item.price_list_rate, item.precision("margin_rate_or_amount")) 

        sqlist = []
        for sq in quote_doc.supplier_quotations:
            if sq.supplier_quotation != self.name:
                sqlist.append(sq)
        
        quote_doc.update({"supplier_quotations": sqlist})
        
        if quote_doc.supplier_quotation == self.name: quote_doc.supplier_quotation = ""
        
        quote_doc.save(ignore_permissions = True)

        frappe.msgprint("Quotation <a href ='/app/quotation/{0}'><b>{0}</b></a> is updated".format(quotation))

    def create_quotation_automatically(self):
        if not self.get_request_for_quotation(): return
        make_quotation(self.name)

def check_option_items(doc_option, copied_option):
    copied_option_items = copied_option.opportunity_option
    items = deepcopy(copied_option_items)
    for row in doc_option:
        found = False
        for sec_row in items:
            if row.item_code == sec_row.item_code and row.section_title == sec_row.section_title:
                if row.qty <= sec_row.qty:
                    found = True
                items.remove(sec_row)
                break
        if not found:
            return False
    return True

def check_supplier_quotations_status(request_for_quotation):
    "Get Supplier Quotation of the Request with draft status"
    if frappe.db.exists("Supplier Quotation Item", {"request_for_quotation": request_for_quotation, "docstatus": 0}):
        return frappe.db.get_value("Supplier Quotation Item", {"request_for_quotation": request_for_quotation, "docstatus": 0}, "parent")
    else: 
        if frappe.db.exists("Supplier Quotation Item", {"request_for_quotation": request_for_quotation, "docstatus":1}):
            return
        else: return True 

def has_supplier_quotation_to_create(request_for_quotation):
    from sabaintegration.overrides.request_for_quotation import make_supplier_quotation_from_rfq
    if frappe.db.get_value("Request for Quotation", request_for_quotation, "docstatus") < 1: return True
    doc = make_supplier_quotation_from_rfq(request_for_quotation)
    if doc.get("items"):
        return True

@frappe.whitelist()
def make_quotation(source_name, target_doc=None):   
    from sabaintegration.overrides.opportunity import add_item_to_table
    def set_missing_values(source, target):
        from erpnext.controllers.accounts_controller import get_default_taxes_and_charges
        from erpnext import get_company_currency
        from sabaintegration.overrides.quotation import get_costs

        target.quotation_to = frappe.db.get_value("Opportunity", opportunity, "opportunity_from")
        target.party_name = frappe.db.get_value("Opportunity", opportunity, "party_name")
        target.opportunity = opportunity
        target.opportunity_owner = frappe.db.get_value("Opportunity", opportunity, "opportunity_owner")

        target.currency = get_party_account_currency(target.quotation_to, target.party_name, target.company) or get_company_currency(target.company)

        target.conversion_rate = get_exchange_rate(target.currency, "USD")
        taxes = get_default_taxes_and_charges(
            "Sales Taxes and Charges Template", company=target.company
        )
        if taxes.get("taxes"):
            target.update(taxes)

        target.update({
            "costs_template": "Projects Indirect Cost Analysis",
            "costs": get_costs("Projects Indirect Cost Analysis")
        })

        target.flags.ignore_permissions = True
        set_party_details(source, target)

    def set_party_details(source, target):
        from erpnext.accounts.party import get_party_details

        details = get_party_details(
            party = target.party_name, 
            party_type = target.quotation_to, 
            currency = target.currency,
            price_list = target.selling_price_list,
            posting_date = target.transaction_date,
            company = target.company
            )
        for d in details.keys():
            setattr(target, d, details[d])

    # If there is no request for quotation linked to this supplier quotation,
    # then map supplier quotation fields and items to quotation
    request_for_quotation = frappe.db.get_value("Supplier Quotation Item", {"parent" : source_name}, "request_for_quotation")
    if not request_for_quotation:
        return get_mapped_doc(
        "Supplier Quotation",
        source_name,
        {
            "Supplier Quotation": {
                "doctype": "Quotation",
                # "field_map": {
                #     "name": "supplier_quotation",
                # },
            },
            "Supplier Quotation Item": {
                "doctype": "Quotation Item",
                "condition": lambda doc: frappe.db.get_value("Item", doc.item_code, "is_sales_item") == 1,
                "add_if_empty": True,
                "field_map": {
                    "name": "supplier_quotation_item",
                },
            },
        },
        target_doc,
        )
    
    else:
        # Get opportunity and option number linked to the request for quotation
        # if there is quotation linked to the opportunity, 
        # open the quotation to add the supplier quotatiuon items to it
        opportunity, opportunity_option_number = frappe.db.get_value("Request for Quotation Item", {"parent": request_for_quotation, "docstatus": 1}, ["opportunity", "opportunity_option_number"])
        if not opportunity:
            return get_mapped_doc(
            "Supplier Quotation",
            source_name,
            {
                "Supplier Quotation": {
                    "doctype": "Quotation",
                },
                "Supplier Quotation Item": {
                    "doctype": "Quotation Item",
                    "condition": lambda doc: frappe.db.get_value("Item", doc.item_code, "is_sales_item") == 1,
                    "add_if_empty": True,
                    "field_map": {
                        "name": "supplier_quotation_item",
                        #"request_for_quotation": request_for_quotation
                    },
                },
            },
            target_doc,
            )
        quotation = frappe.db.get_value("Quotation Item", {
            "opportunity": opportunity,
            "opportunity_option_number": opportunity_option_number,
            "docstatus": 0},
            "parent")
        if quotation and opportunity:
            doclist =  frappe.get_doc("Quotation", quotation)

            # if there is an already quotation from this supplier quotation, return quotation
            if frappe.db.exists("From Supplier Quotation", {"parent": quotation, "supplier_quotation": source_name}):
                return doclist
        else: 
            doclist = get_mapped_doc(
                "Supplier Quotation",
                source_name,
                {
                    "Supplier Quotation": {
                        "doctype": "Quotation",
                    },
                },
                target_doc,
                set_missing_values,
                ignore_permissions = True
                )

        rfq_doc = frappe.get_doc("Request for Quotation", request_for_quotation)
        copied_opportunity_option = frappe.db.get_all("Copied Opportunity Option", {
            "opportunity": opportunity,
            "option_number": opportunity_option_number,
            "request_for_quotation": request_for_quotation
            }, "name")
        if copied_opportunity_option:
            opportunity_option_items = frappe.db.get_all("Opportunity Option", {"parent":copied_opportunity_option[0]["name"]}, ['*'])
        elif opportunity_option_number: 
            opportunity_option_items = frappe.db.get_all("Opportunity Option",{
                "parent": opportunity,
                "parentfield": "option_"+str(opportunity_option_number)
            }, ["*"])
        else:
            opportunity_option_items = frappe.db.get_all("Opportunity Item",{
                "parent": opportunity,
                "parentfield": "items"
            }, ["*"])
        quotation_items = [[item.item_code, item.section_title] for item in doclist.get("items")] or []
        packed_items = [[item.item_code, item.parent_item, item.section_title] for item in doclist.get("packed_items")] or []
        packed_rfg = [item.item_code for item in rfq_doc.packed_items]
        # for conversion rate pupose
        if not quotation:
            conversion_rate = get_exchange_rate(doclist.currency, "USD")
        else: conversion_rate = doclist.get("conversion_rate", 1)

        # iterate through items in request for quotation items
        for opp_row in opportunity_option_items:
            #toupdate = False
            for row in rfq_doc.items:
                if (opp_row.item_code == row.item_code):
                    # if the item is a product bundle item,
                    # iterate through supplier quotation items to add its items in the quotation
                    if frappe.db.exists("Product Bundle", {"new_item_code": row.item_code}):
                        total_rate = total_rate_with_margin = 0
                        sq_items = frappe.get_doc("Supplier Quotation", source_name).items
                        found = False

                        # for each packed item, if the item is in the supplier quotation items,
                        # add it to the packed_items table in the quotation
                        for product_bundle_item in get_product_bundle_items(row.item_code):
                            for item in sq_items:
                                #if item or its parent is not in the quotation then add the item
                                if item.item_code == product_bundle_item.item_code and\
                                item.item_code in packed_rfg and\
                                (not [row.item_code, opp_row.section_title] in quotation_items or\
                                not [item.item_code, row.item_code, opp_row.section_title] in packed_items):
                                    found = True
                                    qty = product_bundle_item.qty * opp_row.qty
                                    rate = add_packed_item(item, qty, opp_row, conversion_rate, doclist)
                                    
                                    # calculate the total rate of the product bundle
                                    #if not toupdate:
                                    total_rate += item.base_rate * product_bundle_item.qty / conversion_rate
                                    total_rate_with_margin += rate * product_bundle_item.qty 
                                    break
                                # if packed item is exists then update its rate and qty
                                elif item.item_code == product_bundle_item.item_code and\
                                item.item_code in packed_rfg and\
                                ([row.item_code, opp_row.section_title] in quotation_items and\
                                [item.item_code, row.item_code, opp_row.section_title] in packed_items):
                                    found = True
                                    qty = product_bundle_item.qty * opp_row.qty
                                    # rate = (item.base_rate + (item.base_rate * item.profit_margin / 100)) / conversion_rate
                                    # rate_before_margin = item.base_rate / conversion_rate
                                    for pi in doclist.get("packed_items"):
                                        if (opp_row.item_code == pi.parent_item and opp_row.section_title == pi.section_title and\
                                        pi.item_code == item.item_code): 
                                            precision = pi.precision("qty")
                                            if (flt(pi.qty, precision) < flt(qty,precision)):
                                                # #if the new rate is not equal the old one, then add a new row for this item
                                                # if (pi.rate != rate or pi.rate_before_margin != rate_before_margin):
                                                #     qty = (product_bundle_item.qty * opp_row.qty) - pi.qty 
                                                #     if qty >= 1:
                                                #         add_packed_item(item, qty, opp_row, conversion_rate, doclist)
                                                #         toupdate = True  
                                                #else, update the qty only
                                                #else:
                                                pi.qty = flt(qty,precision)
                                            break
                        # if there at least a new row for an existing packed item with different rate
                        # then recalcualate product bundle rates
                        # if toupdate:
                        #     total_rate_with_margin = total_rate = 0
                        #     for pi in doclist.get("packed_items"):
                        #         if opp_row.item_code == pi.parent_item and opp_row.section_title == pi.section_title:
                        #             total_rate_with_margin += pi.rate * (pi.qty / opp_row.qty) if pi.qty >= opp_row.qty else pi.rate 
                        #             total_rate += pi.rate_before_margin *  (pi.qty / opp_row.qty)

                        # if there is at least one packed item that has added 
                        # and the product bundle is not in the quotation items, then add the item
                        # margin_from_supplier_quotation is the overall margine for this item
                        #print(f"\033[93m {opp_row.item_code}")
                        if found and not [row.item_code, opp_row.section_title] in quotation_items:
                            fields = {
                                "rate": total_rate_with_margin,
                                "rate_without_profit_margin": total_rate,
                                "base_without_profit_margin": total_rate * conversion_rate,
                                #"price_list_rate": total_rate_with_margin,
                                "margin_from_supplier_quotation": (total_rate_with_margin - total_rate) / total_rate * 100 if total_rate else 0,
                                "opportunity_option_number": row.opportunity_option_number,
                                "opportunity": row.opportunity,
                                #"request_for_quotation": request_for_quotation,
                                "section_title": opp_row.section_title
                            }
                            if total_rate_with_margin == 0:
                                fields['discount_percentage'] = 100
                            add_item_to_table(opp_row, "items", doclist, fields)
                        
                        # if it's already in the items table then update the rates only
                        elif found and [row.item_code, opp_row.section_title] in quotation_items:
                            for item in doclist.get("items"):
                                if item.item_code == row.item_code and opp_row.section_title == item.section_title:
                                    precision = item.precision("qty")
                                    if (flt(item.qty, precision) < flt(opp_row.qty, precision)):
                                        item.qty = flt(opp_row.qty, precision)
                                    # if (toupdate):
                                    #     item.rate = total_rate_with_margin
                                    #     item.rate_without_profit_margin = total_rate
                                    else:
                                        item.rate += total_rate_with_margin
                                        item.rate_without_profit_margin += total_rate
                                        item.base_without_profit_margin = item.rate_without_profit_margin * conversion_rate,
                                    #item.price_list_rate += total_rate_with_margin
                                    if item.rate_without_profit_margin: 
                                        item.margin_from_supplier_quotation = (item.rate - item.rate_without_profit_margin) / item.rate_without_profit_margin * 100
                    
                    # if item is not a product bundle then add it to items table
                    # and it's present in the supplier quotation
                    elif frappe.db.exists("Supplier Quotation Item", {"parent": source_name, "item_code": row.item_code}):
                        if not [row.item_code, opp_row.section_title] in quotation_items:
                            name, rate, profit_margin = frappe.db.get_value("Supplier Quotation Item", {"parent": source_name, "item_code": row.item_code}, ["name", "base_rate", "profit_margin"])
                            rate_with_profit_margin = (rate + (rate * profit_margin / 100)) / conversion_rate
                            rate_without_profit_margin = rate / conversion_rate
                            fields = {
                                "rate": rate_with_profit_margin,
                                #"price_list_rate": rate_with_profit_margin,
                                "rate_without_profit_margin": rate_without_profit_margin,
                                "base_without_profit_margin": rate_without_profit_margin * conversion_rate,
                                "margin_from_supplier_quotation": profit_margin,
                                "opportunity_option_number": row.opportunity_option_number,
                                "opportunity": row.opportunity,
                                #"request_for_quotation": request_for_quotation,
                                "section_title": opp_row.section_title,
                                "supplier_quotation_item": name
                            }
                            if rate == 0:
                                fields['discount_percentage'] = 100
                            add_item_to_table(opp_row, "items", doclist, fields)
                        elif [row.item_code, opp_row.section_title] in quotation_items and quotation:
                            for item in doclist.items:
                                if item.item_code == opp_row.item_code and item.section_title == opp_row.section_title:
                                    # item.rate = rate_with_profit_margin
                                    # item.rate_without_profit_margin = rate_without_profit_margin
                                    # item.margin_from_supplier_quotation = profit_margin
                                    precision = item.precision("qty")
                                    item.qty += flt(opp_row.qty, precision) - flt(item.qty, precision)
                                    break
                    break
        add_supplier_quotation_row(source_name, request_for_quotation, opportunity, opportunity_option_number, doclist)
        
        #if quotation: 
        #doclist.save(ignore_permissions = True)
        
        if copied_opportunity_option:
            frappe.db.set_value("Copied Opportunity Option", copied_opportunity_option[0]["name"], "in_quotation", 1)
            frappe.db.set_value("Copied Opportunity Option", copied_opportunity_option[0]["name"], "quotation", doclist.name)

        # sort quotation items as opportunity items
        if opportunity_option_number:
            doclist.option_number_from_opportunity = opportunity_option_number
            doclist.sort_items(opportunity_option_number)
        doclist.save(ignore_permissions = True)
        msg = ""
        if not quotation:
            msg = "Quotation <a href ='/app/quotation/{0}'><b>{0}</b></a> is created".format(doclist.name)
        else:
            msg = "Quotation <a href ='/app/quotation/{0}'><b>{0}</b></a> is updated".format(doclist.name)
        frappe.msgprint(msg)
        return doclist

def add_packed_item(item, qty, opp_row, conversion_rate, doclist):
    from sabaintegration.overrides.opportunity import add_item_to_table
    packed_item = deepcopy(item)
    precision = item.precision("qty")
    packed_item.qty = flt(qty, precision)
    rate = (item.base_rate + (item.base_rate * item.profit_margin / 100)) / conversion_rate # rate of the item is with respect to its margin
    rate_before_margin = item.base_rate / conversion_rate
    fields = {
        "parent_item": opp_row.item_code,
        "rate": rate,
        "margin":item.profit_margin,
        "rate_before_margin":rate_before_margin,
        "conversion_factor": 1.00,
        "section_title": opp_row.section_title,
        "supplier_quotation_item": item.name
    }

    add_item_to_table(packed_item, "packed_items", doclist, fields)
    return rate

def add_supplier_quotation_row(supplier_quotation, request_for_quotation, opportunity, opportunity_option_number, doc):
    "add record of the supplier quotation in the quotation"
    from_sq = frappe.new_doc("From Supplier Quotation")
    from_sq.supplier_quotation = supplier_quotation
    from_sq.request_for_quotation = request_for_quotation
    from_sq.opportunity = opportunity
    from_sq.opportunity_option_number = opportunity_option_number
    doc.append("supplier_quotations", from_sq)

@frappe.whitelist()
def set_rates(source_name, target_name, itemslist = None):
    source_doc = frappe.get_doc("Supplier Quotation", source_name)
    target_doc = frappe.get_doc("Supplier Quotation", target_name)
    if not itemslist:
        itemslist = deepcopy(target_doc.items)
    conversion_rate = get_exchange_rate(source_doc.currency, target_doc.currency)    
    items = []
    not_updated_items = [] 
    for item in itemslist[:]:
        item_exists = False     
        for source_item in source_doc.items:
            if item.item_code == source_item.item_code:
                item_exists = True
                if item.rate != source_item.rate:
                    item.profit_margin = source_item.profit_margin
                    item.rate = source_item.rate / conversion_rate
                    item.amount = item.rate * item.qty if item.qty > 0 else 0
                    item.base_rate = source_item.get("base_rate")
                    item.net_rate = source_item.get("net_rate") / conversion_rate
                    item.base_net_rate = source_item.get("base_net_rate")
                    item.base_amount = item.get("base_rate") * item.qty if item.qty > 0 else 0
                    item.net_amount = item.get("net_rate") * item.qty if item.qty > 0 else 0
                    item.base_net_amount = item.get("base_net_rate") * item.qty if item.qty > 0 else 0
                    item.discount_percentage = flt((1 - item.rate / item.price_list_rate) * 100.0, item.precision("discount_percentage")) if item.price_list_rate > 0 else 0
                    item.discount_amount = flt(item.rate - item.price_list_rate)
                break
        if not item_exists:
            itemslist.remove(item)
            not_updated_items.append(item)                                           
   
    items.append({"updated_items" : itemslist})
    items.append({"not_updated_items" : not_updated_items})
                
    return items

@frappe.whitelist()
def get_supplier_quotations(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql(
        f"""SELECT name , opportunity
            FROM `tabSupplier Quotation` 
            WHERE docstatus = 1 AND opportunity is not null AND opportunity = '{filters.get("opportunity")}' AND name like '%{txt}%'
            group by name , opportunity
            UNION 
            SELECT name , opportunity
            FROM `tabSupplier Quotation` 
            WHERE docstatus = 1 AND opportunity is not null AND name like '%{txt}%'
            group by name , opportunity            
            """)

@frappe.whitelist()
def validate_supplier(doc_name , new_supplier):
    if doc_name and doc_name != '':
        sq_doc = frappe.get_doc("Supplier Quotation" , doc_name)
        rfq = frappe.get_all(
                "Supplier Quotation Item",
                filters={"parent": doc_name},
                fields=["request_for_quotation"],
            )
        if rfq:
            rfq = rfq[0].request_for_quotation
            doc = frappe.get_doc("Request for Quotation", rfq)
            doc_sup = frappe.get_all(
                "Request for Quotation Supplier",
                filters={"parent": doc.name, "supplier": new_supplier},
                fields=["name"],
            )                
            doc_sup = doc_sup[0] if doc_sup else None
            if not doc_sup:
                return {"supplier_exists": 0 , "request_for_quotation" : rfq}        

@frappe.whitelist()
def handle_changed_supplier(doc_name , new_supplier , rfq):
    rfq_doc = frappe.get_doc("Request for Quotation" , rfq)    
    rfq_doc.cancel()

    amended_doc = frappe.copy_doc(rfq_doc)
    amended_doc.docstatus = 0
    amended_doc.amended_from = rfq_doc.name
    new_suppliers_list = []
    for supplier in amended_doc.suppliers: 
        doctype = frappe.new_doc("Request for Quotation Supplier")       
        values = {
            "doctype" : "Request for Quotation Supplier" ,
            "supplier" : new_supplier
        }
        doctype.update(values)
        new_suppliers_list.append(values)    
    amended_doc.save()
    amended_doc.update({"suppliers" : new_suppliers_list})
    amended_doc.submit()