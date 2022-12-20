# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from copy import deepcopy
from frappe import _
from frappe.model.mapper import get_mapped_doc

from erpnext.buying.doctype.supplier_quotation.supplier_quotation import SupplierQuotation
from erpnext.stock.doctype.packed_item.packed_item import get_product_bundle_items
from erpnext.accounts.party import get_party_account_currency

from sabaintegration.overrides.opportunity import add_item_to_table
class CustomSupplierQuotation(SupplierQuotation):
    pass


@frappe.whitelist()
def make_quotation(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.quotation_to = frappe.db.get_value("Opportunity", opportunity, "opportunity_from")
        target.party_name = frappe.db.get_value("Opportunity", opportunity, "party_name")
        target.opportunity = opportunity

        target.currency = get_party_account_currency(target.quotation_to, target.party_name, target.company)
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
                "field_map": {
                    "name": "supplier_quotation",
                },
            },
            "Supplier Quotation Item": {
				"doctype": "Quotation Item",
				"condition": lambda doc: frappe.db.get_value("Item", doc.item_code, "is_sales_item") == 1,
				"add_if_empty": True,
			},
            "Purchase Taxes and Charges": {
                "doctype": "Purchase Taxes and Charges",
            }
        },
        target_doc,
        )
    
    else:
        # Get opportunity and option number linked to the request for quotation
        # if there is quotation linked to the opportunity, 
        # open the quotation to add the supplier quotatiuon items to it
        opportunity, opportunity_option_number = frappe.db.get_value("Request for Quotation Item", {"parent": request_for_quotation, "docstatus": 1}, ["opportunity", "opportunity_option_number"])
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
                    "Purchase Taxes and Charges": {
                        "doctype": "Sales Taxes and Charges",
                    }
                },
                target_doc,
                set_missing_values,
                )

        rfq_doc = frappe.get_doc("Request for Quotation", request_for_quotation)
        opportunity_option_items = frappe.db.get_all("Opportunity Option", {
            "parent": opportunity,
            "parentfield": "option_"+str(opportunity_option_number)
            }, ["*"])
        quotation_items = [[item.item_code, item.section_title] for item in doclist.get("items")] or []
        packed_items = [[item.item_code, item.parent_item, item.section_title] for item in doclist.get("packed_items")] or []
        
        # for conversion rate pupose
        if quotation and doclist.conversion_rate: 
            conversion_rate = doclist.conversion_rate
        else:
            conversion_rate = 1.00
        
        # iterate through items in request for quotation items
        for opp_row in opportunity_option_items:
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
                                if item.item_code == product_bundle_item.item_code and\
                                    (not [row.item_code, opp_row.section_title] in quotation_items or\
                                    not [item.item_code, row.item_code, opp_row.section_title] in packed_items):
                                    found = True
                                    packed_item = deepcopy(item)
                                    packed_item.qty = product_bundle_item.qty * opp_row.qty
                                    rate = (item.base_rate + (item.base_rate * item.profit_margin / 100)) / conversion_rate # rate of the item is with respect to its margin
                                    
                                    fields = {
                                        "parent_item": row.item_code,
                                        "rate": rate,
                                        "conversion_factor": 1.00,
                                        "section_title": opp_row.section_title
                                    }
                                    add_item_to_table(packed_item, "packed_items", doclist, fields)

                                    # calculate the total rate of the product bundle
                                    total_rate += item.base_rate * product_bundle_item.qty / conversion_rate
                                    total_rate_with_margin += rate * product_bundle_item.qty 
                                    break
                        # if there is at least one packed item that has added 
                        # and the product bundle is not in the quotation items, then add the item
                        # margin_from_supplier_quotation is the overall margine for this item
                        
                        if found and not [row.item_code, opp_row.section_title] in quotation_items:
                            fields = {
                                "rate": total_rate_with_margin,
                                "rate_without_profit_margin": total_rate,
                                "price_list_rate": total_rate_with_margin,
                                "margin_from_supplier_quotation": (total_rate_with_margin - total_rate) / total_rate * 100,
                                "opportunity_option_number": row.opportunity_option_number,
                                "opportunity": row.opportunity,
                                "section_title": opp_row.section_title
                            }
                            add_item_to_table(opp_row, "items", doclist, fields)
                        
                        # if it's already in the items table then update the rates only
                        elif found and [row.item_code, opp_row.section_title] in quotation_items:
                            for item in doclist.get("items"):
                                if item.item_code == row.item_code:
                                    item.rate += total_rate_with_margin
                                    item.rate_without_profit_margin += total_rate
                                    item.price_list_rate += total_rate_with_margin
                                    if item.rate_without_profit_margin: 
                                        item.margin_from_supplier_quotation = (item.rate - item.rate_without_profit_margin) / item.rate_without_profit_margin * 100
                    
                    # if item is not a product bundle then add it to items table
                    # and it's present in the supplier quotation
                    elif frappe.db.exists("Supplier Quotation Item", {"parent": source_name, "item_code": row.item_code})\
                        and not [row.item_code, opp_row.section_title] in quotation_items:
                        
                        rate, profit_margin = frappe.db.get_value("Supplier Quotation Item", {"parent": source_name, "item_code": row.item_code}, ["base_rate", "profit_margin"])
                        rate_with_profit_margin = (rate + (rate * profit_margin / 100)) / conversion_rate
                        rate_without_profit_margin = rate / conversion_rate
                        fields = {
                            "rate": rate_with_profit_margin,
                            "price_list_rate": rate_with_profit_margin,
                            "rate_without_profit_margin": rate_without_profit_margin,
                            "margin_from_supplier_quotation": profit_margin,
                            "opportunity_option_number": row.opportunity_option_number,
                            "opportunity": row.opportunity,
                            "section_title": opp_row.section_title
                        }
                        add_item_to_table(opp_row, "items", doclist, fields)
                    break
        add_supplier_quotation_row(source_name, opportunity, opportunity_option_number, doclist)
        
        if quotation: 
            frappe.msgprint("Items are added")
            doclist.save()

        return doclist

def add_supplier_quotation_row(supplier_quotation, opportunity, opportunity_option_number, doc):
    "add record of the supplier quotation in the quotation"
    from_sq = frappe.new_doc("From Supplier Quotation")
    from_sq.supplier_quotation = supplier_quotation
    from_sq.opportunity = opportunity
    from_sq.opportunity_option_number = opportunity_option_number
    doc.append("supplier_quotations", from_sq)

