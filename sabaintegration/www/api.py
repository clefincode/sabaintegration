import frappe
import json
from six import string_types
from frappe.utils import flt, now
from frappe.model.mapper import get_mapped_doc
from frappe.model.naming import make_autoname
from erpnext.selling.doctype.sales_order.sales_order import is_product_bundle, set_delivery_date


@frappe.whitelist()
def product_bundle_check_sales_order(item):
    doc = frappe.db.get_list('Sales Order Item',
    filters={
        'item_code': item,
        "docstatus": ("!=", 2)
    },
    pluck='name'
    )
    
    if(doc):
        frappe.msgprint('This product Bundle is used in Sales Order and can not be edited.')
        return doc

@frappe.whitelist()
def product_bundle_prevents(item):
    doc = frappe.db.get_list('Product Bundle',
    filters={
        'new_item_code': item
    },
    pluck='name'
    )
    if(doc):
        frappe.msgprint('There is a product bundle for this item ')
        return doc
    doc1 = frappe.db.get_list('Product Bundle Item',
    filters={
        'item_code': item
    },
    pluck='name'
    )
    
    if(doc1):
        frappe.msgprint('There is a product bundle item that includes this one as a child')
        return doc1



@frappe.whitelist()
def product_bundle_item_prevents(item):
    doc = frappe.db.get_list('Product Bundle',
    filters={
        'new_item_code': item
    },
    pluck='name'
    )
    
    if(doc):
        frappe.msgprint('There is a product bundle for this item you selected as a child')
        return doc


###This method is overrided from erpnext's Sales Order
@frappe.whitelist()
def make_purchase_order(source_name, selected_items=None, target_doc=None):
    if not selected_items:
        return

    if isinstance(selected_items, string_types):
        selected_items = json.loads(selected_items)

    items_to_map = [
        item.get("item_code")
        for item in selected_items
        if item.get("item_code") and item.get("item_code")
    ]
    items_to_map = list(set(items_to_map))

    def set_missing_values(source, target):
        target.supplier = ""
        target.apply_discount_on = ""
        target.additional_discount_percentage = 0.0
        target.discount_amount = 0.0
        target.inter_company_order_reference = ""
        target.customer = ""
        target.customer_name = ""
        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    def update_item(source, target, source_parent):
        target.schedule_date = source.delivery_date
        target.qty = flt(source.qty) - (flt(source.ordered_qty) / flt(source.conversion_factor))
        target.stock_qty = flt(source.stock_qty) - flt(source.ordered_qty)
        target.project = source_parent.project

    def update_item_for_packed_item(source, target, source_parent):
        target.qty = flt(source.qty) - flt(source.ordered_qty)

    # po = frappe.get_list("Purchase Order", filters={"sales_order":source_name, "supplier":supplier, "docstatus": ("<", "2")})
    doc = get_mapped_doc(
        "Sales Order",
        source_name,
        {
            "Sales Order": {
                "doctype": "Purchase Order",
                "field_no_map": [
                    "address_display",
                    "contact_display",
                    "contact_mobile",
                    "contact_email",
                    "contact_person",
                    "taxes_and_charges",
                    "shipping_address",
                    "terms",
                ],
                "validation": {"docstatus": ["=", 1]},
            },
            "Sales Order Item": {
                "doctype": "Purchase Order Item",
                "field_map": [
                    ["name", "sales_order_item"],
                    ["parent", "sales_order"],
                    ["stock_uom", "stock_uom"],
                    ["uom", "uom"],
                    ["conversion_factor", "conversion_factor"],
                    ["delivery_date", "schedule_date"],
                ],
                "field_no_map": [
                    "rate",
                    "price_list_rate",
                    "item_tax_template",
                    "discount_percentage",
                    "discount_amount",
                    "supplier",
                    "pricing_rules",
                ],
                "postprocess": update_item,
                "condition": lambda doc: doc.ordered_qty < doc.stock_qty
                and doc.item_code in items_to_map
                and not is_product_bundle(doc.item_code),
            },
            "Packed Item": {
                "doctype": "Purchase Order Item",
                "field_map": [
                    ["name", "sales_order_packed_item"],
                    ["parent", "sales_order"],
                    ["uom", "uom"],
                    ["conversion_factor", "conversion_factor"],
                    ["parent_item", "product_bundle"],
                    ["rate", "rate"],
                ],
                "field_no_map": [
                    "price_list_rate",
                    "item_tax_template",
                    "discount_percentage",
                    "discount_amount",
                    "supplier",
                    "pricing_rules",
                ],
                "postprocess": update_item_for_packed_item,
                "condition": lambda doc: doc.parent_item in items_to_map,
            },
        },
        target_doc,
        set_missing_values,
    )

    set_delivery_date(doc.items, source_name)
    group_similar_items(doc)

    return doc
### Custom Update
def group_similar_items(doc):
    group_item_qty = {}
    group_item_amount = {}
    group_item_stock_qty = {}
    count = 0

    for item in doc.items:
        if not item.qty : item.qty = 0
        if not item.stock_qty : item.stock_qty = 0 
        if not item.amount : item.amount = 0.00 
        key = item.item_code + "_" + item.warehouse
        #key = item.item_code + "_" + item.warehouse if item.get("warehouse") else item.item_code
        group_item_qty[key] = group_item_qty.get(key, 0) + item.qty
        group_item_amount[key] = group_item_amount.get(key, 0) + item.amount
        group_item_stock_qty[key] = group_item_stock_qty.get(key, 0) + item.stock_qty


    duplicate_list = []
    for item in doc.items:
        key = item.item_code + "_" + item.warehouse
        #key = item.item_code + "_" + item.warehouse if item.get("warehouse") else item.item_code
        if key in group_item_qty:
            count += 1
            item.qty = group_item_qty[key]
            item.amount = group_item_amount[key]
            item.stock_qty = group_item_stock_qty[key]

            if item.qty:
                item.rate = flt(flt(item.amount) / flt(item.qty), item.precision("rate"))
            else:
                item.rate = 0
            
            if item.get("product_bundle"):
                item.product_bundle=""
            
            item.idx = count
            
            del group_item_qty[key]
        else:
            duplicate_list.append(item)

    for item in duplicate_list:
        doc.remove(item)

### End Custom Update  


###This method is overrided from erpnext's Sales Order
@frappe.whitelist()
def make_purchase_order_for_default_supplier(source_name, selected_items=None, target_doc=None):
    """Creates Purchase Order for each Supplier. Returns a list of doc objects."""
    if not selected_items:
        return

    if isinstance(selected_items, string_types):
        selected_items = json.loads(selected_items)

    def set_missing_values(source, target):
        target.supplier = supplier
        target.apply_discount_on = ""
        target.additional_discount_percentage = 0.0
        target.discount_amount = 0.0
        target.inter_company_order_reference = ""

        default_price_list = frappe.get_value("Supplier", supplier, "default_price_list")
        if default_price_list:
            target.buying_price_list = default_price_list

        if any(item.delivered_by_supplier == 1 for item in source.items):
            if source.shipping_address_name:
                target.shipping_address = source.shipping_address_name
                target.shipping_address_display = source.shipping_address
            else:
                target.shipping_address = source.customer_address
                target.shipping_address_display = source.address_display

            target.customer_contact_person = source.contact_person
            target.customer_contact_display = source.contact_display
            target.customer_contact_mobile = source.contact_mobile
            target.customer_contact_email = source.contact_email

        else:
            target.customer = ""
            target.customer_name = ""

        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    def update_item(source, target, source_parent):
        target.schedule_date = source.delivery_date
        target.qty = flt(source.qty) - (flt(source.ordered_qty) / flt(source.conversion_factor))
        target.stock_qty = flt(source.stock_qty) - flt(source.ordered_qty)
        target.project = source_parent.project

    suppliers = [item.get("supplier") for item in selected_items if item.get("supplier")]
    suppliers = list(dict.fromkeys(suppliers))  # remove duplicates while preserving order

    items_to_map = [item.get("item_code") for item in selected_items if item.get("item_code")]
    items_to_map = list(set(items_to_map))

    if not suppliers:
        frappe.throw(
            _("Please set a Supplier against the Items to be considered in the Purchase Order.")
        )

    purchase_orders = []
    for supplier in suppliers:
        doc = get_mapped_doc(
            "Sales Order",
            source_name,
            {
                "Sales Order": {
                    "doctype": "Purchase Order",
                    "field_no_map": [
                        "address_display",
                        "contact_display",
                        "contact_mobile",
                        "contact_email",
                        "contact_person",
                        "taxes_and_charges",
                        "shipping_address",
                        "terms",
                    ],
                    "validation": {"docstatus": ["=", 1]},
                },
                "Sales Order Item": {
                    "doctype": "Purchase Order Item",
                    "field_map": [
                        ["name", "sales_order_item"],
                        ["parent", "sales_order"],
                        ["stock_uom", "stock_uom"],
                        ["uom", "uom"],
                        ["conversion_factor", "conversion_factor"],
                        ["delivery_date", "schedule_date"],
                    ],
                    "field_no_map": [
                        "rate",
                        "price_list_rate",
                        "item_tax_template",
                        "discount_percentage",
                        "discount_amount",
                        "pricing_rules",
                    ],
                    "postprocess": update_item,
                    "condition": lambda doc: doc.ordered_qty < doc.stock_qty
                    and doc.supplier == supplier
                    and doc.item_code in items_to_map,
                },
            },
            target_doc,
            set_missing_values,
        )

        doc.insert()
        frappe.db.commit()
        purchase_orders.append(doc)

    return purchase_orders

@frappe.whitelist()
def make_material_request(source_name, target_doc=None):
    from erpnext.selling.doctype.sales_order.sales_order import get_requested_item_qty
    requested_item_qty = get_requested_item_qty(source_name)

    def update_item(source, target, source_parent):
        # qty is for packed items, because packed items don't have stock_qty field
        qty = source.get("qty")
        target.project = source_parent.project
        target.qty = qty - requested_item_qty.get(source.name, 0)
        target.stock_qty = flt(target.qty) * flt(target.conversion_factor)

    doc = get_mapped_doc(
        "Sales Order",
        source_name,
        {
            "Sales Order": {"doctype": "Material Request", "validation": {"docstatus": ["=", 1]}},
            "Packed Item": {
                "doctype": "Material Request Item",
                "field_map": {"parent": "sales_order", "uom": "stock_uom"},
                "postprocess": update_item,
            },
            "Sales Order Item": {
                "doctype": "Material Request Item",
                "field_map": {"name": "sales_order_item", "parent": "sales_order"},
                "condition": lambda doc: not frappe.db.exists("Product Bundle", doc.item_code)
                and doc.stock_qty > requested_item_qty.get(doc.name, 0),
                "postprocess": update_item,
            },
        },
        target_doc,
    )
    group_similar_items(doc) ###Custom Update

    return doc

@frappe.whitelist()
def add_items_to_option(opplist, process=False):
    from sabaintegration.overrides.opportunity import add_item_to_table
    if not process: return
    if isinstance(opplist, string_types):
        opplist = json.loads(opplist)

    opportunities = frappe.db.get_all("Opportunity", {"name": ("in", opplist)})
    added = []
    notadded = []
    validate_item_code("Opportunity Item")
    for opp in opportunities:
        opportunity = frappe.get_doc("Opportunity", opp)
        if opportunity.items:
            
            option = get_first_empty_option(opportunity)
            if not option: 
                notadded.append(opportunity.name) 
                

            else:
                selected_option = int(option[-1]) if option[-1] != '0' else 10  
                for item in opportunity.items:
                    fields = {
                        "option_number": selected_option,
                        "section_title": item.get("section_title") if hasattr(item, "section_title") else "",
                        "technical_comment": item.get("technical_comment") if hasattr(item, "technical_comment") else ""
                    }
                    add_item_to_table(item, option, opportunity, other_fields=fields)
                
                opportunity.update({"selected_option": selected_option})
                opportunity.save()

                added.append(opportunity.name)

    frappe.db.commit()

    return {"added": added, "not added": notadded}

def get_first_empty_option(opportunity):
    if not opportunity.option_1: return "option_1"
    if not opportunity.option_2: return "option_2"
    if not opportunity.option_3: return "option_3"
    if not opportunity.option_4: return "option_4"
    if not opportunity.option_5: return "option_5"
    if not opportunity.option_6: return "option_6"
    if not opportunity.option_7: return "option_7"
    if not opportunity.option_8: return "option_8"
    if not opportunity.option_9: return "option_9"
    if not opportunity.option_10: return "option_10"

def validate_item_code(doctype):
    items = frappe.db.get_all(doctype, {"item_code": "", "item_name": ("!=", "")}, ["name", "item_name"])
    for item in items:
        item_code = frappe.db.get_value("Item", {"item_name": item.item_name}, "item_code")
        if item_code: frappe.db.set_value(doctype, {"item_name": item.item_name, "name": item.name}, "item_code", item_code)
        else:
            
            itemdoc = frappe.new_doc("Item")
            itemdoc.item_code = item.item_name if not frappe.db.exists("Item", item.item_name) else make_autoname(item.item_name+".###", "", itemdoc)
            itemdoc.item_name = item.item_name
            itemdoc.item_group = "All Item Groups"
            if not frappe.db.exists("Brand", "unknown"): 
                brand = frappe.new_doc("Brand")
                brand.brand = "unknown"
                brand.save()
            
            itemdoc.brand = "unknown"
            itemdoc.save()
            frappe.db.set_value(doctype, {"item_name": item.item_name, "name": item.name}, "item_code", itemdoc.item_code)
    #frappe.db.commit()

@frappe.whitelist()
def get_clients(project):
    strquery = """
    select distinct role.parent 
    from `tabHas Role` as role,
    `tabUser Permission` as perm
    where role.parenttype = 'User' and role.role = 'Client'
    and perm.user = role.parent and allow = 'Project' and for_value = '{0}'
    """.format(project)
    res = frappe.db.sql(strquery, as_list = 1)
    users = []
    for r in res:
        for i in r:
            users.append(i)
    return users

@frappe.whitelist()
def send_updates():
    from frappe.desk.form.document_follow import send_hourly_updates
    send_hourly_updates()


@frappe.whitelist()
def update_party_details():
    from erpnext.accounts.party import get_party_details
    quotations = frappe.db.get_all("Quotation", {"docstatus": 0}, ["name", "contact_person", "party_name"])
    for quote in quotations:
        contacts = frappe.db.get_all("Dynamic Link", {
            "link_name" : quote.party_name,
            "parenttype": "Contact"
        }, "parent")
        found = False
        for contact in contacts:
            found = False
            if quote.contact_person == contact.parent:
                found = True
                break
        if not found and contacts:
            doc = frappe.get_doc("Quotation", quote.name)

            details = get_party_details(
                party = doc.party_name, 
                party_type = doc.quotation_to, 
                currency = doc.currency,
                price_list = doc.selling_price_list,
                posting_date = doc.transaction_date,
                company = doc.company
                )
                
            for d in details.keys():
                setattr(doc, d, details[d])
            doc.save()
    frappe.db.commit()

@frappe.whitelist()
def opp_sales_man_to_opp_owner():
    opps = frappe.db.sql("""
    select name, sales_man
    from `tabOpportunity`
    where sales_man IS NOT NULL and sales_man != "" 
    order by creation
    """, as_dict = 1)  

    for opp in opps:
        frappe.db.set_value("Opportunity", opp.name, "opportunity_owner", opp.sales_man)
        frappe.db.set_value("Opportunity", opp.name, "sales_man", "")
    frappe.db.commit()

    opps = frappe.db.sql("""
    select name, sales_man
    from `tabOpportunity`
    where sales_man != ""
    """, as_dict = 1)  
    return opps

def amend_rfq(doc):
    newdoc = frappe.copy_doc(doc)
    if doc.docstatus == 0:
        doc.delete(ignore_permissions = True)
    else:
        # if frappe.db.exists('Supplier Quotation Item', {'request_for_quotation': doc.name, 'docstatus': 1}):
        # 	SQs = frappe.db.get_all('Supplier Quotation Item', {'request_for_quotation': doc.name, 'docstatus': 1}, 'parent', distinct = 1)
        # 	for sq in SQs:
        # 		sq_doc = frappe.get_doc('Supplier Quotation', sq.parent)
        # 		sq_doc.cancel()
        newdoc.amended_from = doc.name
        doc.cancel()
    return newdoc

def replace_item_with_item(doc, item_code, new_item_code, option_number, added_packed):
    from erpnext.stock.doctype.packed_item.packed_item import is_product_bundle, get_product_bundle_items

    itemslist, replaced_item = [], None
    item_code_bundle = is_product_bundle(item_code)
    new_item_code_bundle = is_product_bundle(new_item_code)
    for item in doc.items:
        if item.item_code != item_code:
            itemslist.append(item)
        elif item.item_code == item_code:
            replaced_item = item
            if not new_item_code_bundle and new_item_code == added_packed: continue
            qty = None
            if not new_item_code_bundle and item_code_bundle:
                qty = frappe.db.sql("""
                select sum(qty)
                from `tabOpportunity Option` 
                where parent = '{0}' and parentfield = 'option_{1}' 
                and item_code = '{2}'
                group by item_code
                """.format(doc.opportunity, option_number, new_item_code))
            rfqitem = frappe.new_doc("Request for Quotation Item")
            fields = {
            "item_code":new_item_code,
            "item_name":frappe.db.get_value("Item", new_item_code, "item_name"),
            "qty": qty[0][0] if qty else item.get("qty"),
            "uom":frappe.db.get_value("Item", new_item_code, "stock_uom"),
            "warehouse":frappe.db.get_value("Item Default", {"parent" : new_item_code}, "default_warehouse") or item.get('warehouse'),
            "description":frappe.db.get_value("Item", new_item_code, "description"),
            "brand": frappe.db.get_value("Item", new_item_code, "brand"),
            "opportunity": item.get("opportunity"),
            "opportunity_option_number": item.get("opportunity_option_number"),
            "conversion_factor": 1
            }
            rfqitem.update(fields)
            itemslist.append(rfqitem)
            if new_item_code_bundle and not item_code_bundle: added_packed = new_item_code
    
    doc.update({"items": itemslist})

    if not item_code_bundle and not new_item_code_bundle: 
        return 

    if not doc.get("packed_items") and not item_code_bundle and new_item_code_bundle:
        packed_items = get_product_bundle_items(new_item_code)
        packinglist = []
        for p_item in packed_items:
            packinglist.append({
                "item_code": p_item.item_code,
                "qty": p_item.qty * replaced_item.qty,
                "description": p_item.description,
                "uom": p_item.uom,
                "warehouse": frappe.db.get_value("Item Default", {"parent" : item.get("item_code")}, "default_warehouse"),
                "brand": frappe.db.get_value("Item", p_item.item_code, "brand")
            })
        doc.update({"packed_items": packinglist})
        return
    elif doc.get("packed_items") and not item_code_bundle and new_item_code_bundle:
        packed_items = get_product_bundle_items(new_item_code)
        for p_item in packed_items:
            found = False
            for packed in doc.packed_items:
                if packed.item_code == p_item.item_code:
                    packed.qty += p_item.qty * replaced_item.qty
                    found = True
                    break
            if not found:
                doc.append("packed_items", {
                "item_code": p_item.item_code,
                "qty": p_item.qty * replaced_item.qty,
                "description": p_item.description,
                "uom": p_item.uom,
                "warehouse": frappe.db.get_value("Item Default", {"parent" : item.get("item_code")}, "default_warehouse"),
                "brand": frappe.db.get_value("Item", p_item.item_code, "brand")
            })

    elif doc.get("packed_items") and item_code_bundle:
        packed_items = get_product_bundle_items(item_code)
        new_packed_items = None
        if new_item_code_bundle:
            new_packed_items = get_product_bundle_items(new_item_code)
        
        packinglist = []
        for packed in doc.packed_items:
            for p_item in packed_items:
                if p_item.item_code == packed.item_code:
                    packed.qty -= p_item.qty * replaced_item.qty
                    break
            if not new_packed_items and packed.qty > 0: packinglist.append(packed)
            else: packinglist.append(packed)
        packinglist_update = []
        if new_packed_items:
            for packed in packinglist:
                for np_item in new_packed_items:
                    if np_item.item_code == packed.item_code:
                        packed.qty += np_item.qty * replaced_item.qty
                        added_packed.append(np_item.item_code)
                        break
                if packed.qty > 0:
                    packinglist_update.append(packed)
        else: packinglist_update = packinglist
        doc.update({"packed_items": packinglist_update})
        return added_packed

def create_rfq_if_necessary(new_item_code, item_code, added_packed, opportunity, option_number):
    from erpnext.stock.doctype.packed_item.packed_item import is_product_bundle, get_product_bundle_items
    from sabaintegration.overrides.opportunity import make_request_for_quotation

    selected_option = frappe.db.get_value("Opportunity", opportunity, "selected_option")
    if str(selected_option) == option_number and is_product_bundle(new_item_code):
        added_packed = list(set(added_packed))
        packed_items = get_product_bundle_items(new_item_code)
        if len(packed_items) > len(added_packed):
            return make_request_for_quotation(opportunity)
    return None

def create_sqs_if_necessary(new_s_rfqs, cancelled_sqs):
    for rfq in new_s_rfqs:
        if not frappe.db.exists("Supplier Quotation Item", {"request_for_quotation": rfq.name}):
            rfq.create_sq_automatically()
        rfq.update_sqs_rates(cancelled_sqs)

def custom_validate_je(self, *args, **kwargs):
    from dateutil.relativedelta import relativedelta
    from frappe.utils import now_datetime
    if self.get("_action") and self._action == 'submit':

            # Get the current date and time as a datetime object
            now = now_datetime()

            # Add 3 months to it
            new_date = now
            #new_date = now + relativedelta(months=-8)

            # If needed, convert it back to string
            self.submitting_date = new_date.strftime("%Y-%m-%d %H:%M:%S")

@frappe.whitelist()
def move_field_to_field(field, new_field, doctype):
    all_docs = frappe.db.get_all(doctype, {field: ("!=", "")}, ["name", field])
    for doc in all_docs:
        new_value = convert_to_float(doc.get(field))
        frappe.db.set_value(doctype, doc.name, new_field, new_value)
    frappe.db.commit()
    return all_docs

def convert_to_float(s):
    import re
    # Remove commas and any non-numeric characters except for the decimal point
    cleaned_string = re.sub(r"[^\d.]", "", s.replace(",", ""))
    # Convert the cleaned string to float
    try:
        return float(cleaned_string)
    except ValueError:
        # Handle the case where the string cannot be converted to float
        return None

@frappe.whitelist()
def update_sales_orders_brands(year, quarter):
    strQuery = f"""
        select name from `tabSales Order` as so
        where so.docstatus = 1 and so.submitting_date != '' and so.submitting_date is not null
        and EXTRACT(YEAR FROM so.submitting_date) = '{year}'
        and CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.submitting_date) / 3.0)) = '{quarter}'
        
        UNION
        
        select name from `tabSales Order` as so
        where so.docstatus = 0  and EXTRACT(YEAR FROM so.modified) = '{year}'
        and CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.modified) / 3.0)) = '{quarter}'
    """
    
    docs = frappe.db.sql(strQuery, as_list = 1)
    for d in docs:
        doc = frappe.get_doc("Sales Order", d[0])
        doc.update_total_margin()
        if doc.submitting_date:
            doc.set_brands((doc.submitting_date.month, doc.submitting_date.year), True)
        else:
            doc.set_brands((doc.modified.month, doc.modified.year), True)
        doc.save()

    frappe.db.commit()

    return len(docs)

def indexing_after_migrate():
    if not frappe.db.has_index('tabNotification Log', 'idx_for_user_modified'):
        frappe.db.sql_ddl("""
            CREATE INDEX idx_for_user_modified 
            ON `tabNotification Log`(for_user, modified DESC);
        """)

        frappe.db.commit()

@frappe.whitelist()
def update_sales_man_incentive_percentage(sales_man, commission_percentage, year, quarter):
    strQuery = f"""
        select so.name 
        from `tabSales Order` as so        
        where so.docstatus = 0 and so.primary_sales_man = '{sales_man}' and EXTRACT(YEAR FROM so.modified) = '{year}'
        and CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.modified) / 3.0)) = '{quarter}'
        
        UNION
        
        select so.name 
        from `tabSales Order` as so        
        where so.docstatus = 0 and so.primary_sales_man = '{sales_man}' and EXTRACT(YEAR FROM so.submitting_date) = '{year}'
        and CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.submitting_date) / 3.0)) = '{quarter}'
    """
    docs = frappe.db.sql(strQuery, as_dict = 1)
    updated_so = []
    for d in docs:
        prev_commission_percentage = frappe.db.get_value("Sales Order", {"name" : d.name}, "commission_percentage")        
        if flt(prev_commission_percentage) != flt(commission_percentage):
            updated_so.append(d.name)
            frappe.db.set_value("Sales Order", {"name" : d.name}, "commission_percentage" , commission_percentage)
    frappe.db.commit()

    return updated_so

@frappe.whitelist()
def update_engineer_incentive_percentage(engineer, incentive_percentage, year, quarter):
    strQuery = f"""
        select so.name from `tabSales Order` as so
        INNER JOIN `tabPre-Sales Incentive` AS ps ON ps.parent = so.name AND ps.engineer = '{engineer}'
        where so.docstatus = 0 and EXTRACT(YEAR FROM so.modified) = '{year}'
        and CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.modified) / 3.0)) = '{quarter}'
        
        UNION
        
        select so.name from `tabSales Order` as so
        INNER JOIN `tabPre-Sales Incentive` AS ps ON ps.parent = so.name AND ps.engineer = '{engineer}'
        where so.docstatus = 1 and EXTRACT(YEAR FROM so.submitting_date) = '{year}'
        and CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.submitting_date) / 3.0)) = '{quarter}'
    """
    docs = frappe.db.sql(strQuery, as_dict = 1)
    updated_so = []
    for d in docs:
        prev_incentive_percentage = frappe.db.get_value("Pre-Sales Incentive", {"parent" : d.name , "engineer" : engineer}, "incentive_percentage")
        if flt(prev_incentive_percentage) != flt(incentive_percentage):
            updated_so.append(d.name)
            frappe.db.set_value("Pre-Sales Incentive", {"parent" : d.name , "engineer" : engineer}, "incentive_percentage" , incentive_percentage)
    frappe.db.commit()

    return updated_so

@frappe.whitelist()
def update_product_manager_incentive_percentage(brands, year, quarter):
    brands = json.loads(brands)
    if len(brands) > 0:
        updated_so = []
        for b in brands:
            strQuery = f"""
                select so.name from `tabSales Order` as so
                INNER JOIN `tabBrand Details` AS b ON b.parent = so.name AND b.product_manager = '{b["product_manager"]}'
                where so.docstatus = 0 and EXTRACT(YEAR FROM so.modified) = '{year}'
                and CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.modified) / 3.0)) = '{quarter}'
                
                UNION
                
                select so.name from `tabSales Order` as so
                INNER JOIN `tabBrand Details` AS b ON b.parent = so.name AND b.product_manager = '{b["product_manager"]}'
                where so.docstatus = 1 and EXTRACT(YEAR FROM so.submitting_date) = '{year}'
                and CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.submitting_date) / 3.0)) = '{quarter}'
                
            """
            sales_orders = frappe.db.sql(strQuery, as_dict = 1)
            for so in sales_orders:
                prev_incentive_percentage = frappe.db.get_value("Brand Details", {"parent" : so.name , "product_manager" : b["product_manager"]}, "incentive_percentage")
                if flt(prev_incentive_percentage) != flt(b["incentive_percentage"]):
                    updated_so.append(so.name)
                    frappe.db.set_value("Brand Details", {"parent" : so.name , "product_manager" : b["product_manager"]}, "incentive_percentage" , b["incentive_percentage"])                        
            frappe.db.commit()
        return updated_so


@frappe.whitelist()
def get_sales_order_invoices(sales_order):

    query = """
        SELECT SUM(si.billing_percentage) AS total_billing_percentage
        FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
        WHERE sii.sales_order = %s
        AND si.docstatus = 1
    """
    
    result = frappe.db.sql(query, sales_order, as_dict=True)
    return result[0].total_billing_percentage 



@frappe.whitelist()

def check_linked_documents(sales_order_name):
    linked_invoices = frappe.get_all('Sales Invoice Item', filters={'sales_order': sales_order_name, 'docstatus': 1}, fields=['parent'])

    linked_journal_entries = frappe.get_all('Journal Entry Account', filters={'reference_name': sales_order_name, 'reference_type': 'Sales Order','docstatus': 1}, fields=['parent'])

    linked_delivery_notes = frappe.get_all('Delivery Note Item',filters={'against_sales_order': sales_order_name,'docstatus': 1  },
        fields=['parent']
    )


    if linked_invoices or linked_journal_entries or linked_delivery_notes:
        return {
            'has_linked_documents': True,

        }
    
    return {
        'has_linked_documents': False,
    }