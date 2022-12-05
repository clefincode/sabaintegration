# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, getdate, nowdate

from erpnext.controllers.selling_controller import SellingController

form_grid_templates = {"items": "templates/form_grid/item_grid.html"}


class CustomQuotation(SellingController):
	def set_indicator(self):
		if self.docstatus == 1:
			self.indicator_color = "blue"
			self.indicator_title = "Submitted"
		if self.valid_till and getdate(self.valid_till) < getdate(nowdate()):
			self.indicator_color = "gray"
			self.indicator_title = "Expired"

	def validate(self):
		super(CustomQuotation, self).validate()
		self.set_status()
		self.validate_uom_is_integer("stock_uom", "qty")
		self.validate_valid_till()
		self.validate_shopping_cart_items()
		self.set_customer_name()
		if self.items:
			self.with_items = 1

		self.add_item_name_in_packed()
		make_packing_list(self) 

	def validate_valid_till(self):
		if self.valid_till and getdate(self.valid_till) < getdate(self.transaction_date):
			frappe.throw(_("Valid till date cannot be before transaction date"))

	def validate_shopping_cart_items(self):
		if self.order_type != "Shopping Cart":
			return

		for item in self.items:
			has_web_item = frappe.db.exists("Website Item", {"item_code": item.item_code})

			# If variant is unpublished but template is published: valid
			template = frappe.get_cached_value("Item", item.item_code, "variant_of")
			if template and not has_web_item:
				has_web_item = frappe.db.exists("Website Item", {"item_code": template})

			if not has_web_item:
				frappe.throw(
					_("Row #{0}: Item {1} must have a Website Item for Shopping Cart Quotations").format(
						item.idx, frappe.bold(item.item_code)
					),
					title=_("Unpublished Item"),
				)

	def get_ordered_status(self):
		ordered_items = frappe._dict(
			frappe.db.get_all(
				"Sales Order Item",
				{"prevdoc_docname": self.name, "docstatus": 1},
				["item_code", "sum(qty)"],
				group_by="item_code",
				as_list=1,
			)
		)

		status = "Open"
		if ordered_items:
			status = "Ordered"

			for item in self.get("items"):
				if item.qty > ordered_items.get(item.item_code, 0.0):
					status = "Partially Ordered"

		return status

	def is_fully_ordered(self):
		return self.get_ordered_status() == "Ordered"

	def is_partially_ordered(self):
		return self.get_ordered_status() == "Partially Ordered"

	def update_lead(self):
		if self.quotation_to == "Lead" and self.party_name:
			frappe.get_doc("Lead", self.party_name).set_status(update=True)

	def set_customer_name(self):
		if self.party_name and self.quotation_to == "Customer":
			self.customer_name = frappe.db.get_value("Customer", self.party_name, "customer_name")
		elif self.party_name and self.quotation_to == "Lead":
			lead_name, company_name = frappe.db.get_value(
				"Lead", self.party_name, ["lead_name", "company_name"]
			)
			self.customer_name = company_name or lead_name
	
	###Custom Update
	def add_item_name_in_packed(self):
		for item_row in self.get("items"):
			if frappe.db.exists("Product Bundle", {"new_item_code": item_row.item_code}) and item_row.opportunity:
				for i in range(len(self.get("packed_items"))):
					if not self.packed_items[i].parent_detail_docname and self.packed_items[i].parent_item == item_row.item_code:
						self.packed_items[i].parent_detail_docname = item_row.name
	###End Custom Update

	def update_opportunity(self, status):
		for opportunity in set(d.prevdoc_docname for d in self.get("items")):
			if opportunity:
				self.update_opportunity_status(status, opportunity)

		if self.opportunity:
			self.update_opportunity_status(status)

	def update_opportunity_status(self, status, opportunity=None):
		if not opportunity:
			opportunity = self.opportunity

		opp = frappe.get_doc("Opportunity", opportunity)
		opp.set_status(status=status, update=True)

	@frappe.whitelist()
	def declare_enquiry_lost(self, lost_reasons_list, detailed_reason=None):
		if not (self.is_fully_ordered() or self.is_partially_ordered()):
			get_lost_reasons = frappe.get_list("Quotation Lost Reason", fields=["name"])
			lost_reasons_lst = [reason.get("name") for reason in get_lost_reasons]
			frappe.db.set(self, "status", "Lost")

			if detailed_reason:
				frappe.db.set(self, "order_lost_reason", detailed_reason)

			for reason in lost_reasons_list:
				if reason.get("lost_reason") in lost_reasons_lst:
					self.append("lost_reasons", reason)
				else:
					frappe.throw(
						_("Invalid lost reason {0}, please create a new lost reason").format(
							frappe.bold(reason.get("lost_reason"))
						)
					)

			self.update_opportunity("Lost")
			self.update_lead()
			self.save()

		else:
			frappe.throw(_("Cannot set as Lost as Sales Order is made."))

	###Custom Update
	def before_submit(self):
		self.check_opportunity()

	def check_opportunity(self):
		"""Check if the quotations comes from an opportunity
		if yes, then check if all bundles are in the quotation"""

		opportunity_name = frappe.db.get_all("Quotation Item", {"parent": self.name}, "opportunity")
		opportunity_option = frappe.db.get_all("Quotation Item", {"parent": self.name}, "opportunity_option_number")
		if opportunity_name[0]['opportunity']:
			opportunity_name = [sub['opportunity'] for sub in opportunity_name ]
			opportunity_name = list(set(opportunity_name))
			if opportunity_option:
				opportunity_option = [sub['opportunity_option_number'] for sub in opportunity_option ]
				opportunity_option = list(set(opportunity_option))

			self.check_option_items_in_items_table(opportunity_name[0], opportunity_option[0])

	def check_option_items_in_items_table(self, opportunity_name, opportunity_option):
			if opportunity_option:
				option_items = frappe.db.get_all("Opportunity Option", {"parent": opportunity_name, "parentfield": "option_"+str(opportunity_option)}, ["item_code", "qty"])
			else: option_items = frappe.db.get_all("Opportunity Item", {"parent": opportunity_name}, ["item_code", "qty"])
			
			for option_item in option_items:
				found = False
				notfounditem = option_item.item_code
				for item in self.items:
					# if (item.opportunity and item.opportunity_option_number and\
					# item.opportunity == opportunity_name and item.opportunity_option_number == opportunity_option) or\
					# (not opportunity_option and item.opportunity and item.opportunity == opportunity_name):
						if option_item.item_code == item.item_code and option_item.qty == item.qty:
							if not frappe.db.exists("Product Bundle", {"new_item_code": item.item_code}):
								found = True
							else:
								found = check_bundle_items(item, self.packed_items)
							break
					
						elif option_item.item_code == item.item_code and option_item.qty > item.qty:
							found = False
							break
				if not found:
					frappe.throw("""You can't submit this document now until you add
					all items of <b>{0}</b> of the opportunity <b>{1}</b>.<br>
					Item <b>{2}</b> is not fully added to the quotation""".format("option" + str(opportunity_option) if opportunity_option else "items table", opportunity_name, notfounditem))

	# ###End Custom Update

	def on_submit(self):
		# Check for Approving Authority
		frappe.get_doc("Authorization Control").validate_approving_authority(
			self.doctype, self.company, self.base_grand_total, self
		)

		# update enquiry status
		self.update_opportunity("Quotation")
		self.update_lead()

	def on_cancel(self):
		if self.lost_reasons:
			self.lost_reasons = []
		super(CustomQuotation, self).on_cancel()

		# update enquiry status
		self.set_status(update=True)
		self.update_opportunity("Open")
		self.update_lead()

	def print_other_charges(self, docname):
		print_lst = []
		for d in self.get("taxes"):
			lst1 = []
			lst1.append(d.description)
			lst1.append(d.total)
			print_lst.append(lst1)
		return print_lst

	def on_recurring(self, reference_doc, auto_repeat_doc):
		self.valid_till = None


def get_list_context(context=None):
	from erpnext.controllers.website_list_for_contact import get_list_context

	list_context = get_list_context(context)
	list_context.update(
		{
			"show_sidebar": True,
			"show_search": True,
			"no_breadcrumbs": True,
			"title": _("Quotations"),
		}
	)

	return list_context


@frappe.whitelist()
def make_sales_order(source_name, target_doc=None):
	quotation = frappe.db.get_value(
		"Quotation", source_name, ["transaction_date", "valid_till"], as_dict=1
	)
	if quotation.valid_till and (
		quotation.valid_till < quotation.transaction_date or quotation.valid_till < getdate(nowdate())
	):
		frappe.throw(_("Validity period of this quotation has ended."))
	return _make_sales_order(source_name, target_doc)


def _make_sales_order(source_name, target_doc=None, ignore_permissions=False):
	customer = _make_customer(source_name, ignore_permissions)
	ordered_items = frappe._dict(
		frappe.db.get_all(
			"Sales Order Item",
			{"prevdoc_docname": source_name, "docstatus": 1},
			["item_code", "sum(qty)"],
			group_by="item_code",
			as_list=1,
		)
	)

	def set_missing_values(source, target):
		if customer:
			target.customer = customer.name
			target.customer_name = customer.customer_name
		if source.referral_sales_partner:
			target.sales_partner = source.referral_sales_partner
			target.commission_rate = frappe.get_value(
				"Sales Partner", source.referral_sales_partner, "commission_rate"
			)
		target.flags.ignore_permissions = ignore_permissions
		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")

	def update_item(obj, target, source_parent):
		balance_qty = obj.qty - ordered_items.get(obj.item_code, 0.0)
		target.qty = balance_qty if balance_qty > 0 else 0
		target.stock_qty = flt(target.qty) * flt(obj.conversion_factor)

		if obj.against_blanket_order:
			target.against_blanket_order = obj.against_blanket_order
			target.blanket_order = obj.blanket_order
			target.blanket_order_rate = obj.blanket_order_rate

	doclist = get_mapped_doc(
		"Quotation",
		source_name,
		{
			"Quotation": {"doctype": "Sales Order", "validation": {"docstatus": ["=", 1]}},
			"Quotation Item": {
				"doctype": "Sales Order Item",
				"field_map": {"parent": "prevdoc_docname"},
				"postprocess": update_item,
				"condition": lambda doc: doc.qty > 0,
			},
			"Sales Taxes and Charges": {"doctype": "Sales Taxes and Charges", "add_if_empty": True},
			"Sales Team": {"doctype": "Sales Team", "add_if_empty": True},
			"Payment Schedule": {"doctype": "Payment Schedule", "add_if_empty": True},
		},
		target_doc,
		set_missing_values,
		ignore_permissions=ignore_permissions,
	)

	# postprocess: fetch shipping address, set missing values
	doclist.set_onload("ignore_price_list", True)

	return doclist


def set_expired_status():
	# filter out submitted non expired quotations whose validity has been ended
	cond = "qo.docstatus = 1 and qo.status NOT IN ('Expired', 'Lost') and qo.valid_till < %s"
	# check if those QUO have SO against it
	so_against_quo = """
		SELECT
			so.name FROM `tabSales Order` so, `tabSales Order Item` so_item
		WHERE
			so_item.docstatus = 1 and so.docstatus = 1
			and so_item.parent = so.name
			and so_item.prevdoc_docname = qo.name"""

	# if not exists any SO, set status as Expired
	frappe.db.sql(
		"""UPDATE `tabQuotation` qo SET qo.status = 'Expired' WHERE {cond} and not exists({so_against_quo})""".format(
			cond=cond, so_against_quo=so_against_quo
		),
		(nowdate()),
	)


@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
	return _make_sales_invoice(source_name, target_doc)


def _make_sales_invoice(source_name, target_doc=None, ignore_permissions=False):
	customer = _make_customer(source_name, ignore_permissions)

	def set_missing_values(source, target):
		if customer:
			target.customer = customer.name
			target.customer_name = customer.customer_name

		target.flags.ignore_permissions = ignore_permissions
		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")

	def update_item(obj, target, source_parent):
		target.cost_center = None
		target.stock_qty = flt(obj.qty) * flt(obj.conversion_factor)

	doclist = get_mapped_doc(
		"Quotation",
		source_name,
		{
			"Quotation": {"doctype": "Sales Invoice", "validation": {"docstatus": ["=", 1]}},
			"Quotation Item": {"doctype": "Sales Invoice Item", "postprocess": update_item},
			"Sales Taxes and Charges": {"doctype": "Sales Taxes and Charges", "add_if_empty": True},
			"Sales Team": {"doctype": "Sales Team", "add_if_empty": True},
		},
		target_doc,
		set_missing_values,
		ignore_permissions=ignore_permissions,
	)

	doclist.set_onload("ignore_price_list", True)

	return doclist


def _make_customer(source_name, ignore_permissions=False):
	quotation = frappe.db.get_value(
		"Quotation", source_name, ["order_type", "party_name", "customer_name"], as_dict=1
	)

	if quotation and quotation.get("party_name"):
		if not frappe.db.exists("Customer", quotation.get("party_name")):
			lead_name = quotation.get("party_name")
			customer_name = frappe.db.get_value(
				"Customer", {"lead_name": lead_name}, ["name", "customer_name"], as_dict=True
			)
			if not customer_name:
				from erpnext.crm.doctype.lead.lead import _make_customer

				customer_doclist = _make_customer(lead_name, ignore_permissions=ignore_permissions)
				customer = frappe.get_doc(customer_doclist)
				customer.flags.ignore_permissions = ignore_permissions
				if quotation.get("party_name") == "Shopping Cart":
					customer.customer_group = frappe.db.get_value(
						"E Commerce Settings", None, "default_customer_group"
					)

				try:
					customer.insert()
					return customer
				except frappe.NameError:
					if frappe.defaults.get_global_default("cust_master_name") == "Customer Name":
						customer.run_method("autoname")
						customer.name += "-" + lead_name
						customer.insert()
						return customer
					else:
						raise
				except frappe.MandatoryError as e:
					mandatory_fields = e.args[0].split(":")[1].split(",")
					mandatory_fields = [customer.meta.get_label(field.strip()) for field in mandatory_fields]

					frappe.local.message_log = []
					lead_link = frappe.utils.get_link_to_form("Lead", lead_name)
					message = (
						_("Could not auto create Customer due to the following missing mandatory field(s):") + "<br>"
					)
					message += "<br><ul><li>" + "</li><li>".join(mandatory_fields) + "</li></ul>"
					message += _("Please create Customer from Lead {0}.").format(lead_link)

					frappe.throw(message, title=_("Mandatory Missing"))
			else:
				return customer_name
		else:
			return frappe.get_doc("Customer", quotation.get("party_name"))

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
			if packed_item.item_code == bundle_item.item_code and parent_item.item_code == packed_item.parent_item:
				if packed_item.qty >= bundle_item.qty * parent_item.qty:
					found = True
					break
				else: return False
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
		for item in doc.get("packed_items"):
			for p_item in doc.get("items"):
				if item.parent_item == p_item.item_code:
					packeditems.append(item)
					break

		doc.set("packed_items", packeditems)
	return reset_table