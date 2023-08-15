# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import copy
import frappe
from frappe import _
from frappe.utils import flt, now
from erpnext.selling.doctype.quotation.quotation import Quotation

class CustomQuotation(Quotation):
	def onload(self):
		if self.get("supplier_quotations"):
			self.supplier_quotations_table = self.set_table_html()

	def set_table_html(self):
		submittedSQs = unsubmittedSQs = []
		submittedSQs = copy.deepcopy(self.get("supplier_quotations"))
		if not submittedSQs: return

		elemtoadd = abs(len(unsubmittedSQs) - len(submittedSQs))
		
		unsubmittedSQs = get_unsubmitted_sq(self)
		if not unsubmittedSQs: return
		unsubmittedSQs = list(set(unsubmittedSQs))

		if elemtoadd:
			if len(submittedSQs) > len(unsubmittedSQs):
				for i in range(elemtoadd):
					unsubmittedSQs.append("")
			elif len(submittedSQs) < len(unsubmittedSQs):
				for i in range(elemtoadd):
					submittedSQs.append("")
		SQs = list(zip(submittedSQs, unsubmittedSQs))

		return frappe.render_template("templates/includes/supplier_quotations_table.html", {"SQs": SQs})

	def validate(self):
		super(Quotation, self).validate()
		self.set_status()
		self.validate_uom_is_integer("stock_uom", "qty")
		self.validate_valid_till()
		self.validate_shopping_cart_items()
		self.set_customer_name()
		if self.items:
			self.with_items = 1

		if self.get("_action") and self._action != 'submit': 
			if self.get("is_saved_from_ui"):
				self.validate_removed_items()
				self.is_saved_from_ui = 0

		self.add_item_name_in_packed()
		make_packing_list(self) 

		self.update_total_margin()
		self.update_costs()
		self.set_option_number()
		
		# sort quotation items as opportunity items
		if self.option_number_from_opportunity:
			self.sort_items(self.option_number_from_opportunity)	

		if self.is_new():
			self.set_title()	
		if self.get("_action") and self._action == 'submit':
			self.submitting_date = now()

	# def after_insert(self):
	# 	self.assign_quote()
	
	# def assign_quote(self):
	# 	if check_if_from_opportunity_option(self):
	# 		opportunity = self.supplier_quotations[0].get("opportunity")
	# 		if opportunity :
	# 			user = frappe.db.get_value("Opportunity", opportunity, "opportunity_owner")
	# 			from frappe.desk.form.assign_to import add
	# 			try:
	# 				add({"doctype": self.doctype, "name": self.name, "assign_to": [user]})
	# 			except Exception:
	# 				frappe.msgprint("Couldn't assign the quotation to its sales man")

	def add_item_name_in_packed(self):
		for item_row in self.get("items"):
			if frappe.db.exists("Product Bundle", {"new_item_code": item_row.item_code}) and item_row.opportunity:
				for i in range(len(self.get("packed_items"))):
					if not self.packed_items[i].parent_detail_docname and self.packed_items[i].parent_item == item_row.item_code and self.packed_items[i].get("section_title") == item_row.get("section_title"):
						self.packed_items[i].parent_detail_docname = item_row.name
	
	def update_items_table(self):
		itemslist = []
		i = 1
		for item in self.get("items"):
			if not frappe.db.exists("Product Bundle", {"new_item_code": item.item_code}): 
				item.idx = i
				itemslist.append(item)
				i += 1
				continue

			for packed_item in self.get("packed_items"):
				if item.item_code == packed_item.parent_item and packed_item.get("section_title") == item.get("section_title"):
					item.idx = i
					itemslist.append(item)
					i += 1
					break
		self.update({"items": itemslist})

	def update_total_margin(self):
		self.total = self.total_rate_without_margin = self.base_total_rate_without_margin = 0
		for item in self.items:
			item.base_rate_without_profit_margin = item.rate_without_profit_margin * self.conversion_rate
			self.total_rate_without_margin = self.total_rate_without_margin + flt(item.rate_without_profit_margin * item.qty, item.precision("rate_without_profit_margin"))
			self.total += flt(item.amount, item.precision("amount"))
		self.base_total_rate_without_markup = self.total_rate_without_margin * self.conversion_rate
		self.base_total = self.total * self.conversion_rate

		self.total_items_markup_value = (self.total - self.total_rate_without_margin)
		self.base_total_items_markup_value = self.total_items_markup_value * self.conversion_rate
		self.total_margin = self.total_items_markup_value / self.total_rate_without_margin * 100 if self.total_rate_without_margin else 0 

	def update_costs(self):
		total_costs = 0.00
		if self.get("costs"): 
			for row in self.costs:
				row.cost_value = self.net_total * row.cost_percentage / 100
				total_costs += row.cost_value
		self.total_costs = total_costs
		self.base_total_costs = self.total_costs * self.conversion_rate
		
		self.total_costs_with_material_costs = self.total_costs + self.total_rate_without_margin
		self.base_total_costs_with_material_costs = self.total_costs_with_material_costs * self.conversion_rate;

		self.expected_profit_loss_value = self.net_total - self.total_costs_with_material_costs 
		self.base_expected_profit_loss_value = self.expected_profit_loss_value * self.conversion_rate
		self.expected_profit_loss = (self.expected_profit_loss_value * 100) / self.net_total if self.net_total else 0

	def set_option_number(self):
		if self.option_number_from_opportunity: return

		for item in self.items:
			if item.opportunity_option_number:
				self.option_number_from_opportunity = item.opportunity_option_number
				break
		# opportunity_option = frappe.db.get_value("Quotation Item", {"parent": self.name}, "opportunity_option_number")
		# if opportunity_option:
		# 	self.option_number_from_opportunity =opportunity_option
	
	def set_title(self):
		if self.supplier_quotations:
			self.title = frappe.db.get_value("Supplier Quotation", self.supplier_quotations[0].supplier_quotation, "title")

	def validate_removed_items(self):
		if not self.get("supplier_quotations"): return
		doc_before_save = self.get_doc_before_save()

		if not doc_before_save: return
		items_before_save = [[item.item_code, item.section_title, item.opportunity] for item in doc_before_save.get("items")]
		items_after_save = [[item.item_code, item.section_title, item.opportunity] for item in self.get("items")]
		reset_table = items_before_save != items_after_save
		if not reset_table: return
		for item in items_before_save:
			found = False
			for curr_item in items_after_save:
				if curr_item[0] == item[0] and\
				curr_item[1] == item[1]:
					found = True
					break
			if not found:
				if item[2]:
					if not check_permission_remove_item(frappe.session.user):
						frappe.throw("You don't have enough permission to remove an item of the opportuity")
					else: frappe.msgprint("Be careful. You have removed item <b>{0}</b> which is from opportuity <b>{1}</b>".format(item[0], item[2]))

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
			precision = self.items[0].precision("qty")
			# iterate through items in the option to check if each item has been added to quotation
			for option_item in option_items:
				found = False
				i = 0
				notfounditem = option_item.item_code
				for item in itemslist:
						# if item is present with the same quantity and section title, then check its bundles
						if option_item.item_code == item.item_code and ((option_item.section_title and option_item.section_title == item.section_title) or (not option_item.section_title and not item.section_title) ):
							
							if flt(option_item.qty, precision) != flt(item.qty, precision) and not check_permission_qty(frappe.session.user):
								frappe.throw("Qty of item <b>{}</b> is not correct as in option".format(item.item_code))
							
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
					if not check_permission_remove_item(frappe.session.user):
						frappe.throw("""You can't submit this document now until you add
						all items of <b>{0}</b> from the opportunity <a href='/app/opportunity/{1}'><b>{1}</b></a>.<br>
						Item <b>{2} {3}</b> is not fully added to the quotation""".format("option" + str(opportunity_option) if opportunity_option else "items table", 
						opportunity_name, notfounditem, "with section "+ str(option_item.section_title) if option_item.get("section_title") else ""))
	
	def sort_items(self , opportunity_option_number):
		doc_before_save = self.get_doc_before_save()

		if doc_before_save:
			items_before_save = [[item.item_code, item.section_title] for item in doc_before_save.get("items")]
			items_after_save = [[item.item_code, item.section_title] for item in self.get("items")]
			reset_table = items_before_save != items_after_save
			if not reset_table: return

		opportunity_items = frappe.db.get_all("Opportunity Option", {"parent": self.opportunity, "parentfield": "option_"+str(opportunity_option_number)}, ["item_code", "qty", "section_title"] , order_by = "idx")
		quotation_items_new_list = []
		c = 0
		for item in opportunity_items:
			for i in self.items:
				if item.item_code == i.item_code and item.section_title == i.section_title:
					c = c+1
					i.update({"idx" : c})
					quotation_items_new_list.append(i)
		idx = len(quotation_items_new_list) + 1
		for i in self.items:
			found = False
			for item in quotation_items_new_list:
				if item.item_code == i.item_code and item.section_title == i.section_title:
					found = True
					break
			if not found:
				i.idx = idx
				quotation_items_new_list.append(i)
				idx += 1
		
		self.update({"items": quotation_items_new_list})

	def on_trash(self):
		remove_quote_from_copied_option(self.name)

	def before_cancel(self):
		remove_quote_from_copied_option(self.name)

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
		if item_row.opportunity and item_row.opportunity_option_number:
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
				pi_row.rate_before_margin = pi_row.rate if not pi_row.get("margin") else pi_row.rate / (pi_row.get('margin') - 1)

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
				precision = packed_item.precision("qty")
				if flt(packed_item.qty, precision) >= flt(bundle_item.qty * parent_item.qty, precision):
					found = True
					break
				#else: return False
		if not found:
			return False
	return True

def check_if_from_opportunity_option(doc):
	if doc.supplier_quotations:
		for item in doc.items:
			if item.opportunity and item.opportunity_option_number:
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
	elif from_option:
		if not reset_table:
			items_before_save = [(item.item_code, item.qty) for item in doc_before_save.get("items")]
			items_after_save = [(item.item_code, item.qty) for item in doc.get("items")]
			reset_qty = items_before_save != items_after_save
			
			if not reset_qty: return reset_table
		# check every packed item if its parent exists
		from erpnext.stock.doctype.packed_item.packed_item import get_product_bundle_items
		packeditems = []
		i = 1
		for item in doc.get("packed_items"):
			for p_item in doc.get("items"):
				#if exists then check the qty
				if item.parent_item == p_item.item_code and item.section_title == p_item.section_title:
					if not p_item.opportunity and not p_item.opportunity_option_number:
						break
					for packed in get_product_bundle_items(p_item.item_code):
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

def get_unsubmitted_sq(doc):
	opportunity = option_number = None
	for item in doc.items:
		if item.get("opportunity"):
			opportunity = item.opportunity
			if item.get("opportunity_option_number"):
				option_number = item.opportunity_option_number
			break
	if not opportunity: return
	if not option_number: option_number = 0
	unsubmitted_sq = []
	rfqs = frappe.db.get_all("Request for Quotation Item", {"opportunity": opportunity, "opportunity_option_number": option_number, "docstatus": 1}, "parent", distinct = 1)

	for rfq in rfqs:
		sqs = frappe.db.get_all("Supplier Quotation Item", {"request_for_quotation": rfq.parent, "docstatus": 0}, "parent")
		if sqs:
			for sq in sqs:
				unsubmitted_sq.append(sq.parent)

	return unsubmitted_sq

def remove_quote_from_copied_option(quote):
	docs = frappe.db.get_all("Copied Opportunity Option", {"quotation" : quote}, "name")
	for doc in docs:
		frappe.db.set_value("Copied Opportunity Option", doc.name, "quotation", "")
		frappe.db.set_value("Copied Opportunity Option", doc.name, "in_quotation", 0)

@frappe.whitelist()
def check_permission_qty(user):
	if "0 Selling - Quotation edit qty" in frappe.get_roles():
		return True
	return False

@frappe.whitelist()
def check_permission_remove_item(user):
	if "0 Selling - Quotation Remove Item" in frappe.get_roles():
		return True
	return False

@frappe.whitelist()
def check_qty(opportunity, option_number, item_code, qty, section_title = None):
	strquery = """
		select qty from `tabOpportunity Option`
		where parent = '{0}' and parentfield = 'option_{1}' and item_code = '{2}' 
	""".format(opportunity, option_number, item_code)

	if (section_title == None):
		strquery += "and section_title is null"
	else: 
		strquery += "and section_title = '{}'".format(section_title)

	option_qty = frappe.db.sql(strquery, as_list = 1)
	if option_qty: return flt(option_qty[0][0]) == flt(qty)
	else: return 


@frappe.whitelist()
def get_costs(costs_template):

	from frappe.model import child_table_fields, default_fields

	template = frappe.get_doc("Costs Template", costs_template)

	template_list = []
	for i, cost in enumerate(template.get("costs")):
		cost = cost.as_dict()

		for fieldname in default_fields + child_table_fields:
			if fieldname in cost:
				del cost[fieldname]

		template_list.append(cost)

	return template_list

@frappe.whitelist()
def get_rfq_related_to_quotation(doc_name):
	rfq = frappe.db.sql(f"""
	SELECT DISTINCT request_for_quotation
	FROM `tabFrom Supplier Quotation`
	WHERE parent = '{doc_name}'
	""" , as_dict = True)

	return {"rfq" : rfq}
