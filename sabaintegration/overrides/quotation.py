# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import copy
import frappe
from frappe import _

from erpnext.selling.doctype.quotation.quotation import Quotation

class CustomQuotation(Quotation):
	def validate(self):
		super(Quotation, self).validate()
		self.set_status()
		self.validate_uom_is_integer("stock_uom", "qty")
		self.validate_valid_till()
		self.validate_shopping_cart_items()
		self.set_customer_name()
		if self.items:
			self.with_items = 1

		self.add_item_name_in_packed()
		make_packing_list(self) 
		##self.validate_rates()
		self.update_total_margin()
		self.set_option_number()

	def add_item_name_in_packed(self):
		for item_row in self.get("items"):
			if frappe.db.exists("Product Bundle", {"new_item_code": item_row.item_code}) and item_row.opportunity:
				for i in range(len(self.get("packed_items"))):
					if not self.packed_items[i].parent_detail_docname and self.packed_items[i].parent_item == item_row.item_code:
						self.packed_items[i].parent_detail_docname = item_row.name
	
	# def validate_rates(self):
	# 	if self.has_value_changed("conversion_rate") and self.supplier_quotations:
	# 		for item in self.get("items"):
	# 			item.rate_without_profit_margin = item.rate_without_profit_margin / self.get("conversion_rate")
	# 			item.margin_from_supplier_quotation = (item.rate - item.rate_without_profit_margin) / item.rate_without_profit_margin * 100
	# 		for item in self.get("packed_items"):
	# 			item.rate = item.rate / self.get("conversion_rate")
	
	def update_total_margin(self):
		self.total_margin = 0
		for item in self.items:
			self.total_margin += item.margin_from_supplier_quotation

	def set_option_number(self):
		opportunity_option = frappe.db.get_value("Quotation Item", {"parent": self.name}, "opportunity_option_number")
		if opportunity_option:
			self.option_number_from_opportunity =opportunity_option
			
	def before_submit(self):
		if self.supplier_quotations: self.check_opportunity()

	def check_opportunity(self):
		"""Check if the quotations comes from an opportunity
		if yes, then check if all bundles are in the quotation"""

		opportunity_name = frappe.db.get_value("Quotation Item", {"parent": self.name}, "opportunity")
		opportunity_option = frappe.db.get_value("Quotation Item", {"parent": self.name}, "opportunity_option_number")
		if opportunity_name and opportunity_option > 0:
			# opportunity_name = [sub['opportunity'] for sub in opportunity_name ]
			# opportunity_name = list(set(opportunity_name))
			# if opportunity_option:
			# 	opportunity_option = [sub['opportunity_option_number'] for sub in opportunity_option ]
			# 	opportunity_option = list(set(opportunity_option))

			self.check_option_items_in_items_table(opportunity_name, opportunity_option)

	def check_option_items_in_items_table(self, opportunity_name, opportunity_option):
			# if quotation is from option in the opportunity, then get all items of the opportunity
			# if not, get all items from items table in the opportunity
			if opportunity_option:
				option_items = frappe.db.get_all("Opportunity Option", {"parent": opportunity_name, "parentfield": "option_"+str(opportunity_option)}, ["item_code", "qty", "section_title"])
			else: option_items = frappe.db.get_all("Opportunity Item", {"parent": opportunity_name}, ["item_code", "qty"])
			
			itemslist = copy.deepcopy(self.items)
			# iterate through items in the option to check if each item has been added to quotation
			for option_item in option_items:
				found = False
				i = 0
				notfounditem = option_item.item_code
				for item in itemslist:
						# if item is present with the same quantity and dection title, then check its bundles
						if option_item.item_code == item.item_code and option_item.qty == item.qty and ((option_item.section_title and option_item.section_title == item.section_title) or (not option_item.section_title and not item.section_title) ):
							if not frappe.db.exists("Product Bundle", {"new_item_code": item.item_code}):
								found = True
								del itemslist[i]
							else:
								found = check_bundle_items(item, self.packed_items)
								if found: del itemslist[i]
							break
					
						# elif option_item.item_code == item.item_code and option_item.qty > item.qty and option_item.section_title == item.section_title:
						# 	found = False
						# 	break
						i += 1
				if not found:
					frappe.throw("""You can't submit this document now until you add
					all items of <b>{0}</b> from the opportunity <b>{1}</b>.<br>
					Item <b>{2} {3}</b> is not fully added to the quotation""".format("option" + str(opportunity_option) if opportunity_option else "items table", 
					opportunity_name, notfounditem, "with section "+ str(option_item.section_title) if option_item.get("section_title") else ""))
	
###Custom Update the next methods are overrided from from erpnext packed_item.py
def make_packing_list(doc):
	"Make/Update packing list for Product Bundle Item."
	from erpnext.stock.doctype.packed_item.packed_item import (
		get_indexed_packed_items_table,
		add_packed_item_row,
		get_product_bundle_items,
		get_packed_item_details,
		set_product_bundle_rate_amount,
		update_product_bundle_rate,
		update_packed_item_from_cancelled_doc,
		update_packed_item_price_data,
		update_packed_item_stock_data,
		update_packed_item_basic_data
		)
			
	if doc.get("_action") and doc._action == "update_after_submit":
		return

	parent_items_price, reset = {}, False
	set_price_from_children = frappe.db.get_single_value(
		"Selling Settings", "editable_bundle_item_rates"
	)

	stale_packed_items_table = get_indexed_packed_items_table(doc)

	from_option = check_if_from_opportunity_option(doc)
	reset = reset_packing_list(doc, from_option)

	for item_row in doc.get("items"):
		if item_row.opportunity:
			continue
		if frappe.db.exists("Product Bundle", {"new_item_code": item_row.item_code}):
			for bundle_item in get_product_bundle_items(item_row.item_code):
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


def check_bundle_items(parent_item, packed_table):
	from erpnext.stock.doctype.packed_item.packed_item import get_product_bundle_items
	bundle_items = get_product_bundle_items(parent_item.item_code)
	for bundle_item in bundle_items:
		found = False
		for packed_item in packed_table:
			if packed_item.item_code == bundle_item.item_code and parent_item.item_code == packed_item.parent_item and parent_item.section_title == packed_item.section_title:
				if packed_item.qty >= bundle_item.qty * parent_item.qty:
					found = True
					break
				#else: return False
		if not found:
			return False
	return True

def check_if_from_opportunity_option(doc):
	if doc.supplier_quotations:
		return True

def reset_packing_list(doc, from_option):
	"Conditionally reset the table and return if it was reset or not."
	reset_table = False
	doc_before_save = doc.get_doc_before_save()

	if doc_before_save:
		# reset table if:
		# 1. items were deleted
		# 2. if bundle item replaced by another item (same no. of items but different items)
		# we maintain list to track recurring item rows as well
		items_before_save = [item.item_code for item in doc_before_save.get("items")]
		items_after_save = [item.item_code for item in doc.get("items")]
		reset_table = items_before_save != items_after_save
	else:
		# reset: if via Update Items OR
		# if new mapped doc with packed items set (SO -> DN)
		# (cannot determine action)
		reset_table = True

	if reset_table and not from_option:
		doc.set("packed_items", [])
	elif reset_table and from_option:
		packeditems = []
		i = 1
		for item in doc.get("packed_items"):
			for p_item in doc.get("items"):
				if item.parent_item == p_item.item_code:
					item.idx = i
					packeditems.append(item)
					i += 1
					break

		doc.set("packed_items", packeditems)
	return reset_table