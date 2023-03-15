import frappe
import json
from six import string_types
from frappe.utils import flt
from frappe.model.mapper import get_mapped_doc
from frappe.model.naming import make_autoname
from erpnext.selling.doctype.sales_order.sales_order import is_product_bundle, set_delivery_date

from sabaintegration.overrides.opportunity import group_similar_items, add_item_to_table

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
				price_list = doc.selling_price_list,
				posting_date = doc.transaction_date,
				company = doc.company
				)
				
			for d in details.keys():
				setattr(doc, d, details[d])
			doc.save()
	frappe.db.commit()

@frappe.whitelist()
def update_opp_owner():
	opps = frappe.db.sql("""
	select name, opportunity_owner
	from `tabOpportunity`
	where opportunity_owner IS NOT NULL and opportunity_owner != "" 
	order by creation
	""", as_dict = 1)  

	for opp in opps:
		frappe.db.set_value("Opportunity", opp.name, "sales_man", opp.opportunity_owner)
		frappe.db.set_value("Opportunity", opp.name, "opportunity_owner", "")
	frappe.db.commit()

	opps = frappe.db.sql("""
	select name, opportunity_owner
	from `tabOpportunity`
	where opportunity_owner != ""
	""", as_dict = 1)  
	return opps
