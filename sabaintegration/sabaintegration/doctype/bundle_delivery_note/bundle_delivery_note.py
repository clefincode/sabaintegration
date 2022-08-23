# Copyright (c) 2022, Ahmad and contributors
# For license information, please see license.txt

import frappe
from frappe import _, msgprint
from frappe.model.document import Document
from frappe.utils import (getdate , nowtime, cint, cstr, flt)
from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
from erpnext.stock.stock_ledger import NegativeStockError, get_previous_sle

class BundleDeliveryNote(Document):

	def before_save(self):
		for item in self.stock_entries:
			self.check_bundle_items_qtys(item)
	
	def validate(self):
		self.validate_parent()
		self.validate_data()

	def before_submit(self):
		if not self.stock_entries:
			frappe.throw('No items have been added yet in {0}'.format(self.name))
		self.create_stock_entry()

	def on_submit(self):
		self.create_delivery_note()
		self.setting_packed_items_values()
		self.check_bundles()

	def check_bundle_items_qtys(self, item):
		bundle_child_qty = frappe.db.get_value('Packed Item', {'parent': self.sales_order, 'item_code': item.item_code, 'parent_item': self.item_parent}, 'qty')
		BDNs = frappe.db.get_all('Bundle Delivery Note', {'name': ('!=', self.name),'sales_order': self.sales_order, 'item_parent': self.item_parent ,'docstatus': ('!=', 2)}, 'name')
		total_qty =item.qty
		for BDN in BDNs:
			qty = frappe.db.get_value('Bundle Delivery Note Item', {'parent': BDN.name, 'item_code': item.item_code}, 'qty')
			if qty:
				total_qty += qty
		if bundle_child_qty < total_qty:
			frappe.throw("The quantity of item <b>{0}</b> is more than the required quantity. Required quantity is <b>{1}</b>. You Provided <b>{2}</b>".format(item.item_code, bundle_child_qty, total_qty))


	def validate_parent(self):
		if not frappe.db.exists("Sales Order Item", {'parent' :self.sales_order, 'item_code': self.item_parent}):
			frappe.throw("Item <b>{0}</b> is not found in the sales order".format(self.item_parent))

	def validate_data(self):
		def _get_msg(row_num, msg):
			return _("Row # {0}:").format(row_num + 1) + " " + msg

		self.validation_messages = []
		items = []
		for row_num, row in enumerate(self.stock_entries):
			# find duplicates
			key = [row.item_code]

			if key in items:
				self.validation_messages.append(_get_msg(row_num, _("Duplicate entry")))
			else:
				items.append(key)
			bundle_items = frappe.db.get_all('Product Bundle Item', {'parent': self.item_parent, 'parenttype': 'Product Bundle'}, ['item_code'])
			
			check_key = [key for item in bundle_items if item.item_code == key[0]]
			if not check_key:
				self.validation_messages.append(_get_msg(row_num, _("Item {0} doesn't exist in Product Bundle {1}".format(key[0], self.item_parent))))
			
			self.validate_qty(row)
			self.validate_batch_no(row.item_code, row)
			self.validate_serial_no(row.item_code, row)
			if flt(row.qty) < 0:
				self.validation_messages.append(_get_msg(row_num, _("Negative Quantity is not allowed")))

			# do not allow negative valuation
			if flt(row.rate) < 0:
				self.validation_messages.append(_get_msg(row_num, _("Negative Valuation Rate is not allowed")))

			if self.validation_messages:
				for msg in self.validation_messages:
					msgprint(msg)

				raise frappe.ValidationError(self.validation_messages)
		
	def validate_qty(self, row):
		previous_sle = get_previous_sle(
				{
					"item_code": row.item_code,
					"warehouse": row.warehouse,
					"posting_date": getdate(),
					"posting_time": nowtime(),
				}
			)
		actual_qty = previous_sle.get("qty_after_transaction")
		allow_negative_stock = cint(frappe.db.get_value("Stock Settings", None, "allow_negative_stock"))
		if (not allow_negative_stock and flt(actual_qty) < flt(row.qty)):
				frappe.throw(
					_(
						"Row {0}: Quantity not available for {1} in warehouse {2}"
					).format(row.idx, row.item_code, row.warehouse))

	def validate_batch_no(self, item_code, row):
		item = frappe.get_doc("Item", item_code)
		if item.has_batch_no and not row.batch_no:
				frappe.throw(_("Batch no is required for batched item {0}").format(item_code))
		
	def validate_serial_no(self, item_code, row):
		item = frappe.get_doc("Item", item_code)
		if item.has_serial_no and not row.serial_no:
			frappe.throw(
				_("Serial no(s) required for serialized item {0}").format(item_code))
		
	def create_stock_entry(self):
		stock_entries = frappe.db.get_all("Stock Entry", {'from_bundle_delivery_note': self.name, 'docstatus': ('!=', 2)}, ['name'])
		for item in self.stock_entries:
			self._create_stock_entry(item, stock_entries)

	def _create_stock_entry(self, item, stock_entries):
		qty = item.qty
		if not item.batch_no: batch_no = '' 
		else: batch_no = item.batch_no		

		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.company = frappe.db.get_value("Sales Order", self.sales_order, 'company')
		stock_entry.posting_date = getdate()
		stock_entry.posting_time = nowtime()
		stock_entry.purpose = "Material Issue"
		stock_entry.set_stock_entry_type()
		stock_entry.from_bundle_delivery_note = self.name

		stock_entry.append('items', {
			'item_code': item.item_code,
			'batch_no': item.batch_no,
			'serial_no': (item.serial_no) if item.serial_no else "",
			'qty': qty,
			'uom': item.uom,
			'basic_rate': item.rate,
			's_warehouse': item.warehouse,
			'conversion_factor': 1.0
		})
		stock_entry.save()
		stock_entry.submit()	

	def create_delivery_note(self):
		bundle_delivery_notes = frappe.db.get_all("Bundle Delivery Note", {"sales_order": self.sales_order, "name": ("!=", self.name), 'docstatus': 1}, 'delivery_note')
		#print(f"\033[94m {bundle_delivery_notes}")
		for bn in bundle_delivery_notes:
			if bn.delivery_note:
				self.delivery_note = bn.delivery_note
				frappe.db.set_value("Bundle Delivery Note", self.name, 'delivery_note', bn.delivery_note)
				frappe.msgprint("Delivery Note is {0}".format('<a href="/app/delivery-note/'+ self.delivery_note + '" class="strong">'+ self.delivery_note + '</a>'))
				return
		delivery_note = make_delivery_note(self.sales_order)
		delivery_note.save()
		self.delivery_note = delivery_note.name
		frappe.db.set_value("Bundle Delivery Note", self.name, 'delivery_note', delivery_note.name)
		frappe.db.commit()		

		for item in delivery_note.items:
			if not frappe.db.exists("Product Bundle", item.item_code):
				frappe.delete_doc("Delivery Note Item", item.name)
				frappe.db.commit()	

		for packed_item in delivery_note.packed_items:
			frappe.db.set_value("Packed Item", packed_item.name, 'qty', 0)
			frappe.db.set_value("Packed Item", packed_item.name, 'serial_no', '')
			frappe.db.set_value("Packed Item", packed_item.name, 'batch_no', '')
			frappe.db.commit()
		frappe.msgprint("Delivery Note {0} has been created succesfully".format('<a href="/app/delivery-note/'+ delivery_note.name + '" class="strong">'+ delivery_note.name + '</a>'))
		return				

	def setting_packed_items_values(self):
		BDNs = frappe.db.get_all("Bundle Delivery Note", {'sales_order': self.sales_order, 'item_parent': self.item_parent, 'docstatus': 1}, 'name')
		packed_items = frappe.db.get_all("Packed Item", {'parent': self.delivery_note, 'parent_item': self.item_parent}, ['name', 'item_code', 'warehouse'])
		for packed_item in packed_items:
			qty = 0
			serial_no = batch_no = ''
			warehouse = packed_item['warehouse']
			for BDN in BDNs:
				item_details = frappe.db.get_all("Bundle Delivery Note Item", {"parent": BDN.name, "item_code": packed_item.item_code}, ['batch_no', 'serial_no', 'qty', 'warehouse'])
				if item_details:
					qty += item_details[0]['qty']
					warehouse = item_details[0]['warehouse']
					if item_details[0]['serial_no']: serial_no += '\n' + item_details[0]['serial_no']
					if item_details[0]['batch_no']: batch_no = item_details[0]['batch_no']

			frappe.db.set_value("Packed Item", packed_item.name, 'qty', qty)
			frappe.db.set_value("Packed Item", packed_item.name, 'warehouse', warehouse)
			frappe.db.set_value("Packed Item", packed_item.name, 'batch_no', batch_no)
			frappe.db.set_value("Packed Item", packed_item.name, 'serial_no', serial_no)
			frappe.db.commit()
		
	def check_bundles(self):
		isDone = check_bundles_of_parent_item(self.item_parent, self.sales_order)
		messages = []
		if not isDone: messages.append("Item <b>{0}</b> is not fully delivered yet".format(self.item_parent))
		items = frappe.db.get_all("Sales Order Item", {'parent': self.sales_order}, 'item_code')
		for item in items:
			if frappe.db.exists('Product Bundle', item.item_code):
				isDone = check_bundles_of_parent_item(item.item_code, self.sales_order)
				if not isDone:
					messages.append("Item <b>{0}</b> is not fully delivered yet".format(item.item_code))
				
		if not messages:
			cancel_stock_entries(self.name)
			BDNs = frappe.db.get_all('Bundle Delivery Note', {'sales_order': self.sales_order, 'docstatus': 1}, 'name')
			for BDN in BDNs:
				cancel_stock_entries(BDN.name)
			self.submit_delivery_note()
			frappe.msgprint("All Bundle Items are delivered")
		else:
			frappe.msgprint("<br>".join(list(set(messages))))

	def submit_delivery_note(self):
		self.setting_packed_items_values()
		bundle_delivery_notes = frappe.db.get_list("Bundle Delivery Note", {
			"delivery_note": self.delivery_note, 
			"name": ("!=", self.name)
			},
			['docstatus'])
		for bdn in bundle_delivery_notes:
			if bdn.docstatus != 1:
				return
		delivery_note = frappe.get_doc("Delivery Note", self.delivery_note)
		delivery_note.submit()


def check_bundles_of_parent_item(parent_item, sales_order):
	# print(f"\033[92m {parent_item}")
	packed_items = frappe.db.get_all("Packed Item", {'parent': sales_order, 'parent_item': parent_item}, ['item_code', 'qty'])
	BDNs = frappe.db.get_all('Bundle Delivery Note', {'sales_order': sales_order, 'item_parent': parent_item ,'docstatus': 1}, 'name')
	BDN_items = []
	for BDN in BDNs:
		BDN_items.append(frappe.get_doc('Bundle Delivery Note', BDN.name).stock_entries)
	for packed_item in packed_items:
		# print(f"\033[94m {packed_item}")
		qty = 0
		for items in BDN_items:
			for item in items:
				if item.item_code == packed_item.item_code:
					qty += item.qty
					break
		# print(f"\033[94m {str(qty) + ' ' + str(packed_item.qty)}")
		if flt(qty) < packed_item.qty:
			return False
	return True

def cancel_stock_entries(bundle_delivery_note):
	stock_entries = frappe.db.get_all("Stock Entry", {'from_bundle_delivery_note': bundle_delivery_note, 'docstatus': ('!=', 2)}, ['name'])
	if stock_entries:
		for st in stock_entries:
			stock_entry = frappe.get_doc("Stock Entry", st['name'])
			stock_entry.cancel()


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_bundle_items(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""
		SELECT pbi.item_code FROM `tabProduct Bundle` as pb 
		INNER JOIN `tabProduct Bundle Item` as pbi ON pb.new_item_code = pbi.parent
		WHERE pb.new_item_code = %(parent)s
	""",{"parent": filters.get("parent")})


@frappe.whitelist()
def get_items(sales_order = None, item_parent = None, item_code = None):
	if not item_parent and not item_code:
		return
	if not item_parent and item_code:
		return [{'item_code': item_code, 'qty':0}]

	if not sales_order: return

	delivery_note = ''
	for bdn in frappe.db.get_all("Bundle Delivery Note", {"sales_order": sales_order, "docstatus": 1}, "delivery_note"):
		if bdn.delivery_note:
			delivery_note = bdn.delivery_note
			break
	if item_code:
		if not delivery_note:
			details = frappe.db.get_all("Packed Item", {'parent': sales_order, 'parent_item': item_parent, 'item_code': item_code}, ['item_name','qty', 'warehouse', 'rate', 'uom'])
			return [{'item_code': item_code, 'qty':details[0]['qty'], 'item_name': details[0]['item_name'], 'warehouse': details[0]['warehouse'], 'rate': details[0]['rate'], 'uom': details[0]['uom']}]

		q1 = frappe.db.get_value("Packed Item", {'parent': sales_order, 'parent_item': item_parent, 'item_code': item_code}, 'qty') 
		q2 = frappe.db.get_value("Packed Item", {'parent': delivery_note, 'parent_item': item_parent, 'item_code': item_code}, 'qty')
		qty = q1 - q2
		if qty == 0: return
		details = frappe.db.get_all("Packed Item", {'parent': sales_order, 'parent_item': item_parent, 'item_code': item_code}, ['item_name', 'warehouse', 'rate', 'uom'])
		return [{'item_code': item_code, 'qty':qty ,'item_name': details[0]['item_name'], 'warehouse': details[0]['warehouse'], 'rate': details[0]['rate'], 'uom': details[0]['uom']}]
	else:
		packed_items_so = frappe.db.get_all("Packed Item", {'parent': sales_order, 'parent_item': item_parent}, ['item_code', 'qty', 'item_name', 'warehouse', 'rate', 'uom'])
		if not delivery_note: return packed_items_so
		items = []
		packed_items_dn = frappe.db.get_all("Packed Item", {'parent': delivery_note, 'parent_item': item_parent}, ['item_code', 'qty'])
		for packed_item_dn in packed_items_dn:
			for packed_item_so in packed_items_so:
				if packed_item_dn.item_code == packed_item_so.item_code:
					qty = packed_item_so.qty - packed_item_dn.qty
					if qty > 0:
						items.append({'item_code': packed_item_so.item_code, 'qty': qty, 'item_name': packed_item_so.item_name, 'warehouse': packed_item_so.warehouse, 'rate': packed_item_so.rate, 'uom': packed_item_so.uom})
					break
		return items

					
