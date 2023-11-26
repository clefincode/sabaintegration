# Copyright (c) 2022, Ahmad and contributors
# For license information, please see license.txt
import json
from six import string_types
from copy import deepcopy

import frappe
from frappe import _, msgprint
from frappe.model.document import Document
from frappe.utils import (getdate , nowtime, cint, cstr, flt)

from erpnext.stock.stock_ledger import get_previous_sle
from erpnext.stock.doctype.packed_item.packed_item import get_product_bundle_items

from sabaintegration.overrides.sales_order import make_delivery_note
from sabaintegration.stock.get_item_details import get_item_warehouse

class BundleDeliveryNote(Document):

	def __init__(self, *args, **kwargs):
		super(BundleDeliveryNote, self).__init__(*args, **kwargs)
		self.items = []
		if self.get("item_parent"):
			self.items = [self.get("item_parent")]
		elif self.get("parents_items"):
			self.items = [item.item_code for item in self.parents_items]

	def validate(self):
		if self.is_new():
			self.excluded_items = []
		self.validate_parent()
		self.validate_data()
		self.validate_excluded_items()

	def before_submit(self):
		if not self.stock_entries:
			frappe.throw('No items have been added yet in {0}'.format(self.name))
		self.create_stock_entry()

	def on_submit(self):
		state = self.create_delivery_note()
		self.setting_packed_items_values(state)
		if self.is_return:
			delete_dn(self.name, self.delivery_note)
		self.check_bundles()
		#frappe.db.commit()

	def before_cancel(self):
		self.remove_packed_items()
		remove_bdn(self.name, self.delivery_note)
		delete_dn(self.name, self.delivery_note)
		self.delivery_note = ''
		#frappe.db.commit()

	def validate_parent(self):
		notfound = ""
		if self.get("item_parent"):
			if not frappe.db.exists("Sales Order Item", {'parent' :self.sales_order, 'item_code': self.item_parent}):
				notfound = self.item_parent

		elif self.get("parents_items"):
			for item in self.parents_items:
				if not frappe.db.exists("Sales Order Item", {'parent' :self.sales_order, 'item_code': item.item_code}):
					notfound = item.item_code

		if notfound:
			frappe.throw("Item <b>{0}</b> is not found in the sales order".format(notfound))

	def validate_data(self):
		def _get_msg(row_num, msg):
			return _("Row # {0}:").format(row_num + 1) + " " + msg

		self.validation_messages = []
		accepted_items = get_items(**{"sales_order": self.sales_order, "parents": self.items})
		
		for row_num, row in enumerate(self.stock_entries):

			if not self.validate_packed_items(row, accepted_items):
					self.validation_messages.append(_get_msg(row_num, _("This item doesn't belonge to any parents in the BDN")))

			if self.get("_action") and self._action == "submit":
				self.validate_qty(row)
				self.validate_batch_no(row.item_code, row)
				self.validate_serial_no(row.item_code, row)
			if flt(row.qty) <= 0 and cint(self.is_return) == 0:
				self.validation_messages.append(_get_msg(row_num, _("Negative and Zero Quantitys is not allowed")))

			elif flt(row.qty) >= 0 and cint(self.is_return) == 1:
				self.validation_messages.append(_get_msg(row_num, _("Positive and Zero Quantitys is not allowed in Return BDN")))

			error = self.validate_returning_qty(row)
			if error:
				self.validation_messages.append(_get_msg(row_num, error))
			# do not allow negative valuation
			if flt(row.rate) < 0:
				self.validation_messages.append(_get_msg(row_num, _("Negative Valuation Rate is not allowed")))

			if self.validation_messages:
				for msg in self.validation_messages:
					msgprint(msg)

				raise frappe.ValidationError(self.validation_messages)

	def validate_packed_items(self, row, accepted_items):
		for item in accepted_items:
			if item.item_code == row.item_code:
				return True
		return False

	def validate_excluded_items(self):
		# excluded item of a bundle shouldn't be excluded more than once in the delivery note
		if not self.get("excluded_items"): return
		excluded_items = frappe.db.sql(f"""
		SELECT  parent_item , item_code
		FROM `tabBundle Delivery Note Excluded Item` AS ExcludedItem , `tabBundle Delivery Note` AS DN
		WHERE ExcludedItem.parent = DN.name AND DN.sales_order = '{self.sales_order}' AND DN.docstatus = 1 AND DN.name != '{self.name}'
		""" , as_dict = True)
		for item in self.excluded_items:
			if frappe.db.exists("Delivery Note Item", {"against_sales_order": self.sales_order, "docstatus": 0}):
				dn_name = frappe.db.get_value("Delivery Note Item", {"against_sales_order": self.sales_order, "docstatus": 0}, "parent")
				delivery_note = frappe.get_doc("Delivery Note", dn_name)
				for packed_item in delivery_note.get("packed_items"):
					if packed_item.item_code == item.item_code and packed_item.parent_item == item.parent_item and packed_item.qty > 0:
						frappe.throw(f"<b>{item.item_code}</b> in <b>{item.parent_item}</b> can't be excluded because it was delivered before")

			for i in excluded_items:
				if item.item_code == i.item_code and item.parent_item == i.parent_item:
					if frappe.db.get_value("Packed Item", {"item_code": item.item_code, "parent_item": item.parent_item}, "qty") > 0:
						frappe.throw(f"<b>{item.item_code}</b> in <b>{item.parent_item}</b> was excluded before")

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

	def validate_returning_qty(self, row):
		if not self.get("return_against"): return
		original_doc = frappe.get_doc("Bundle Delivery Note", self.return_against)
		for item in original_doc.stock_entries:
			if item.item_code == row.item_code and item.qty < abs(row.qty):
				return "Cannot return more than {0} for Item {1}".format(item.qty, row.item_code)

	def create_stock_entry(self):
		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.company = frappe.db.get_value("Sales Order", self.sales_order, 'company')
		stock_entry.posting_date = getdate()
		stock_entry.posting_time = nowtime()
		stock_entry.purpose = "Material Issue" if not self.is_return else "Material Receipt"
		stock_entry.set_stock_entry_type()
		stock_entry.from_bundle_delivery_note = self.name

		for item in self.stock_entries:
			qty = item.qty
			stock_entry.append('items', {
				'item_code': item.item_code,
				'batch_no': item.batch_no,
				'serial_no': (item.serial_no) if item.serial_no else "",
				'qty': abs(qty),
				'uom': item.uom,
				'basic_rate': item.rate,
				's_warehouse': item.warehouse if not self.is_return else "",
				't_warehouse': item.warehouse if self.is_return else "",
				'conversion_factor': 1.0
			})

		stock_entry.save()
		stock_entry.submit()

	def create_delivery_note(self):
		if frappe.db.exists("Delivery Note Item", {"against_sales_order": self.sales_order, "docstatus": 0}):
			dn_name = frappe.db.get_value("Delivery Note Item", {"against_sales_order": self.sales_order, "docstatus": 0}, "parent")

			delivery_note = frappe.get_doc("Delivery Note", dn_name)
			if delivery_note.get("bdns"):
				delivery_note.append("bdns", {"bundle_delivery_note": self.name, "status": 1})
				delivery_note.save(ignore_permissions = True)

				self.delivery_note = dn_name
				state = self.create_state()
				self.set_alt_excluded_items(state)

				frappe.db.set_value("Bundle Delivery Note", self.name, 'delivery_note', dn_name)
				frappe.msgprint("Delivery Note is {0}".format('<a href="/app/delivery-note/'+ self.delivery_note + '" class="strong">'+ self.delivery_note + '</a>'))
				#frappe.db.commit()
				return state

		if self.is_return:
			frappe.throw("There is no Delivery Note for the Sales Order")

		delivery_note = make_delivery_note(self.sales_order)
		delivery_note.project = self.project

		delivery_note.append("bdns", {"bundle_delivery_note": self.name, "status": 1})

		delivery_note.insert(ignore_permissions = True)

		self.delivery_note = delivery_note.name
		frappe.db.set_value("Bundle Delivery Note", self.name, 'delivery_note', delivery_note.name)

		state = self.create_state()

		for packed_item in delivery_note.packed_items:
			frappe.db.set_value("Packed Item", packed_item.name, {
				'qty': 0, 'serial_no': '', 'batch_no': '',
				})
			frappe.db.set_value("Delivery Note Item", packed_item.parent_detail_docname, "from_bundle_delivery_note", 1)

		#frappe.db.commit()
		frappe.msgprint("Delivery Note {0} has been created succesfully".format('<a href="/app/delivery-note/'+ delivery_note.name + '" class="strong">'+ delivery_note.name + '</a>'))
		return state

	def create_state(self):
		state = frappe.new_doc("Bundle Delivery Note State")
		state.bundle_delivery_note = self.name
		state.sales_order = self.sales_order
		state.delivery_note = self.delivery_note
		state.is_return = self.is_return
		state.return_against = self.return_against
		state.save(ignore_permissions = True)
		return state

	def set_alt_excluded_items(self, state):
		if not self.get("excluded_items"): return

		delivery_note = frappe.get_doc("Delivery Note", self.delivery_note)
		for excluded_item in self.excluded_items:
			for pi_row in delivery_note.get("packed_items"):
				if excluded_item.item_code == pi_row.item_code and\
				excluded_item.parent_item == pi_row.parent_item:
					if excluded_item.alt_item:
						pi_row.excluded_item = excluded_item.item_code
						pi_row.is_alternative = 1
						pi_row.item_code = excluded_item.alt_item
						pi_row.description = frappe.db.get_value("Item", pi_row.item_code, "stock_uom")
						pi_row.uom = frappe.db.get_value("Item", pi_row.item_code, "stock_uom")
						pi_row.rate = 0
						packed_item = deepcopy(pi_row)
						for item in delivery_note.items:
							if item.item_code == packed_item.parent_item:
								item_row = item
								break
						set_details(packed_item, item_row, pi_row, delivery_note)
					else:
						delivery_note.packed_items.remove(pi_row)
						state_item = {
						"parent_item": pi_row.parent_item,
						"item_code": excluded_item.item_code,
						"qty": 0,
						"warehouse": pi_row.warehouse,
						"serial_no": pi_row.get("serial_no"),
						"is_removed": 1
						}
						state.append("items", state_item)

					break
		delivery_note.save(ignore_permissions = True)
		state.save(ignore_permissions = True)


	def setting_packed_items_values(self, state):
		packed_items, serials = {}, {}
		for item in self.stock_entries:
			packed_items[item.item_code] = packed_items.get(item.item_code, 0) + abs(item.qty)

		if not self.is_return:
			so_packed_items = frappe.db.get_all('Packed Item', {'parent': self.sales_order, 'parent_item': ('in', self.items)
			}, ['parent_item', 'item_code', 'qty'], order_by = "idx")
			dn_packed_items = frappe.db.get_all('Packed Item', {'parent': self.delivery_note, 'parent_item': ('in', self.items), 'item_code': ('in', list(packed_items.keys()) )},
			['name','parent_item', 'item_code', 'excluded_item','qty'], order_by = "idx")
			for so_pi in so_packed_items:
				qty, i= 0, 0
				packed_name, packed_item_bdn = '', ''

				for dn_pi in dn_packed_items:
					if so_pi.parent_item == dn_pi.parent_item and ((so_pi.item_code == dn_pi.item_code) \
					or (so_pi.item_code == dn_pi.excluded_item)):
						qty = so_pi.qty - dn_pi.qty
						packed_item_bdn = dn_pi.item_code
						packed_name = dn_pi.name
						del dn_packed_items[i]
						break
					i += 1

				if not qty or qty < 0: continue
				qty_state = 0

				if packed_items[packed_item_bdn] >= qty:
					frappe.db.set_value("Packed Item", {'name': packed_name}, 'qty', so_pi.qty)
					packed_items[packed_item_bdn] -= qty
					qty_state = qty
				else:
					qty_state = packed_items[packed_item_bdn]
					qty = frappe.db.get_value('Packed Item', {'name': packed_name}, 'qty')
					packed_items[packed_item_bdn] = 0
					frappe.db.set_value("Packed Item", {'parent': self.delivery_note, 'parent_item': so_pi.parent_item, 'item_code': packed_item_bdn}, 'qty', qty + qty_state )

				item_details = frappe.db.get_all("Bundle Delivery Note Item", {"parent": self.name, "item_code": packed_item_bdn}, ['batch_no', 'serial_no', 'warehouse'])
				if item_details:
					batch, serial_no = frappe.db.get_value("Packed Item", {'name': packed_name}, ['batch_no', 'serial_no'])

					if item_details[0]["batch_no"]: frappe.db.set_value("Packed Item", {'name': packed_name}, "batch_no", batch + item_details[0]["batch_no"])
					else: frappe.db.set_value("Packed Item", {'name': packed_name}, "batch_no", "")
					
					if item_details[0]["serial_no"]:
						if serial_no: serial_no += '\n'
						s = item_details[0]["serial_no"].split()
						added_serial = ''
						for serial in s:
							if not serials.get(packed_item_bdn) or serial not in serials[packed_item_bdn]:
								added_serial = added_serial + serial + '\n'
								if serials.get(packed_item_bdn):
									serials[packed_item_bdn].append(serial)
								else: serials[packed_item_bdn] = [serial]
								if len(added_serial.split()) >= int(qty_state): break

						added_serial = serial_no + added_serial
						frappe.db.set_value("Packed Item", {'name': packed_name}, "serial_no", added_serial)

					frappe.db.set_value("Packed Item", {'name': packed_name}, "warehouse", item_details[0]["warehouse"])

				state_item = {
					"parent_item": so_pi.parent_item,
					"item_code": packed_item_bdn,
					"qty": qty_state,
					"original_item": so_pi.item_code if so_pi.item_code != packed_item_bdn else "",
					"warehouse": item_details[0]["warehouse"] if item_details else "",
					"serial_no": item_details[0]["serial_no"] if item_details and item_details[0]["serial_no"] else ""
				}
				for row in self.get("excluded_items"):
					if row.alt_item == packed_item_bdn and so_pi.parent_item == row.parent_item:
						state_item["is_excluded"] = 1

				state.append("items", state_item)

		else:
			delivery_note = frappe.get_doc("Delivery Note", self.delivery_note)
			if not delivery_note.get("packed_items"):
				frappe.throw("Nothing in the Delivery Note to Return")

			for item in packed_items:
				bdn_serials = []
				
				if frappe.db.get_value("Item", item, "has_serial_no"):
					for i in self.stock_entries:
						if i.item_code == item and i.serial_no:
							serial_no = i.serial_no.split('\n')
							bdn_serials += serial_no

				for row in delivery_note.packed_items:
					if packed_items[item] <= 0:
						break

					if row.item_code == item and row.parent_item in self.items:
						removed_serials = ''
						if row.serial_no:
							serial_nos = row.serial_no.split('\n')
							filtered_lines = []
							for line in serial_nos:
								if line not in bdn_serials: filtered_lines.append(line)
								else: 
									bdn_serials.remove(line)
									removed_serials += line + '\n'
							frappe.db.set_value("Packed Item", row.name, "serial_no", "\n".join(filtered_lines))

							qty = row.qty - len(filtered_lines)

						else:
							if packed_items[item] >= row.qty: qty = row.qty
							else: qty = packed_items[item]

						frappe.db.set_value("Packed Item", {'name': row.name}, 'qty', row.qty - qty)

						packed_items[item] -= qty

						state_item = {
							"parent_item": row.parent_item,
							"item_code": row.item_code,
							"qty": -1 * qty,
							"warehouse": row.warehouse,
							"serial_no": removed_serials
						}
						state.append("items", state_item)

				
				if len(bdn_serials) > 0:
					frappe.throw("You have provided <b>{0}</b> serial nos for item <b>{1}</b> that are not used in the Delivery Note".format((bdn_serials), item))

		state.save(ignore_permissions = True)

	def check_bundles(self):
		if self.is_return: return

		so_packed_items = frappe.db.get_all('Packed Item', {'parent': self.sales_order}, ['parent_item', 'item_code', 'qty'])
		dn_packed_items = frappe.db.get_all('Packed Item', {'parent': self.delivery_note}, ['parent_item', 'item_code', 'excluded_item','qty'])
		messages = []
		for so_pi in so_packed_items:
			i, exists = 0, False
			for dn_pi in dn_packed_items:
				if dn_pi.parent_item == so_pi.parent_item and (dn_pi.item_code == so_pi.item_code or dn_pi.excluded_item == so_pi.item_code):
					exists = True
					if dn_pi.qty < so_pi.qty:
						messages.append("Item <b>{0}</b> is not fully delivered yet".format(so_pi.parent_item))
					del dn_packed_items[i]
					break
				i += 1

		if not exists:
			if not is_excluded(so_pi, self.sales_order):
				messages.append("Item <b>{0}</b> is not fully delivered yet".format(so_pi.parent_item))

		if not messages:
			cancel_stock_entries(self.name)
			BDNs = frappe.db.get_all('Bundle Delivery Note', {'sales_order': self.sales_order, 'docstatus': 1}, 'name')
			for BDN in BDNs:
				cancel_stock_entries(BDN.name)
			self.submit_delivery_note()
			frappe.msgprint("All Bundle Items are delivered")
		else:
			frappe.msgprint("<br>".join(list(set(messages))))

	def remove_packed_items(self):
		if self.get("delivery_note") and frappe.db.exists("Bundle Delivery Note State", self.name):
			delivery_note = frappe.get_doc("Delivery Note", self.delivery_note)
			bdn_state = frappe.get_doc("Bundle Delivery Note State", self.name)
			idx_list = []
			for item in bdn_state.items:
				if item.is_removed:
					add_removed_item(item, delivery_note)
					continue
				for p_item in delivery_note.packed_items:
					if p_item.idx not in idx_list and (p_item.item_code == item.item_code or p_item.get("excluded_item") == item.item_code or p_item.item_code == item.get("original_item")) and p_item.parent_item == item.parent_item:
						p_item.qty -= item.qty
						idx_list.append(p_item.idx) # Prevent subtract qty from the same packed item
						
						if item.get("serial_no"):
							if self.is_return:
								p_item.serial_no += '\n' + item.serial_no
							else:
								p_item.serial_no = p_item.serial_no.replace(item.serial_no, "")
								serial = ""
								for line in p_item.serial_no.split('\n'):
									serial += line + "\n"
								p_item.serial_no = serial

						if p_item.get("excluded_item") == item.get("original_item") and item.get("is_excluded"):
							p_item.item_code = item.original_item
							p_item.excluded_item = ""
							p_item.is_alternative = 0
							p_item.description = frappe.db.get_value("Item", p_item.item_code, "description")
							p_item.uom = frappe.db.get_value("Item", p_item.item_code, "stock_uom")
							bundle_item = deepcopy(p_item)
							for item in delivery_note.items:
								if item.item_code == p_item.parent_item:
									item_row = item
									break
							set_details(bundle_item, item_row, p_item, delivery_note)
						break
			delivery_note.save(ignore_permissions = True)
			bdn_state.delete(ignore_permissions = True)


	def submit_delivery_note(self):
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

@frappe.whitelist()
def create_return_bdn(source_name, target_doc=None):
	from frappe.model.mapper import get_mapped_doc

	def update_item(source_doc, target_doc, source_parent):
		target_doc.qty = -1 * source_doc.qty

	def set_missing_values(source, target):
		doc = frappe.get_doc(target)
		doc.is_return = 1
		doc.return_against = source.name
		doc.excluded_items = []

	doclist = get_mapped_doc(
		"Bundle Delivery Note",
		source_name,
		{
			"Bundle Delivery Note": {
				"doctype": "Bundle Delivery Note",
				"validation": {
					"docstatus": ["=", 1],
				},
			},
			"Bundle Delivery Note Item": {
				"doctype": "Bundle Delivery Note Item",
				"postprocess": update_item,
			}
		},
		target_doc,
		set_missing_values
	)

	return doclist

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
			stock_entry.from_bundle_delivery_note = ''
			stock_entry.cancel()

def is_excluded(item, sales_order):
		bdns = frappe.db.get_all("Bundle Delivery Note", {"sales_order": sales_order, "docstatus": 1}, "name")
		for bdn in bdns:
			doc = frappe.get_doc("Bundle Delivery Note", bdn.name)
			if not doc.excluded_items: continue

			for excluded in doc.excluded_items:
				if excluded.item_code == item.item_code and\
				excluded.parent_item == item.parent_item and\
				not excluded.alt_item:
					return True

		return False

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_bundle_items(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""
		SELECT pbi.item_code FROM `tabProduct Bundle` as pb
		INNER JOIN `tabProduct Bundle Item` as pbi ON pb.new_item_code = pbi.parent
		WHERE pb.new_item_code = %(parent)s and pbi.name like %(txt)s
	""",{"parent": filters.get("parent"), "txt": "%" + txt + "%"})


@frappe.whitelist()
def get_items(**kwargs):
	if not kwargs.get("parents") or not kwargs.get("sales_order"):
		return

	delivery_note = ''
	sales_order = kwargs.get('sales_order')
	for bdn in frappe.db.get_all("Bundle Delivery Note", {"sales_order": sales_order, "docstatus": 1}, "delivery_note"):
		if bdn.delivery_note:
			delivery_note = bdn.delivery_note
			break

	parents_list = kwargs.get("parents")

	if isinstance(parents_list, string_types):
		parents_list = json.loads(parents_list)

	warehouses = {}
	parents = "("
	for item_parent in parents_list:
		parents += " '{}',".format(item_parent)
	parents = parents[:-1]
	parents += ")"

	if not delivery_note:
		return frappe.db.sql("""
			select item_code, item_name, sum(qty) as qty, warehouse, rate, uom
			from `tabPacked Item`
			where parent = '{0}' and parent_item in {1}
			group by item_code, warehouse, rate
		""".format(sales_order, parents), as_dict = 1)
	else:
		items = {}
		so_packed_items = frappe.db.get_all('Packed Item', {'parent': sales_order, "parent_item": ("in", parents_list)}, ['parent_item', 'item_code', 'qty'], order_by = "idx")
		dn_packed_items = frappe.db.get_all('Packed Item', {'parent': delivery_note, "parent_item": ("in", parents_list)}, ['parent_item', 'item_code', 'qty', 'excluded_item'], order_by = "idx")
		for so_pi in so_packed_items:
			i = 0
			for dn_pi in dn_packed_items:
				if dn_pi.parent_item == so_pi.parent_item and (dn_pi.item_code == so_pi.item_code or so_pi.item_code == dn_pi.excluded_item):
					if dn_pi.qty < so_pi.qty:
						qty = so_pi.qty - dn_pi.qty
						items[dn_pi.item_code] = items.get(dn_pi.item_code, 0) + qty
						del dn_packed_items[i]
						break
				i += 1

		itemslist = []
		for item in items.keys():
			items_details = frappe.db.get_value('Packed Item', {'parent': delivery_note, "item_code" : item}, ['item_code', 'item_name', 'warehouse', 'uom', 'rate'], as_dict = 1)
			items_details['qty'] = items[item]
			itemslist.append(items_details)
		return itemslist

def add_removed_item(bundle_item, delivery_note):
	pi_row = delivery_note.append("packed_items", {})
	for item in delivery_note.items:
		if item.item_code == bundle_item.parent_item:
			item_row = item
			break
	if not item_row: return
	bundle_item.description = frappe.db.get_value("Item", bundle_item.item_code, "description")
	bundle_item.uom = frappe.db.get_value("Item", bundle_item.item_code, "stock_uom")
	bundle_item.qty = 0

	set_details(bundle_item, item_row, pi_row, delivery_note)

	res = frappe.db.sql("""
	select sum(item.qty) from `tabBundle Delivery Note State Item` as item
	inner join `tabBundle Delivery Note State` as state on state.name = item.parent
	where state.delivery_note = '{0}' and item.item_code = '{1}' and item.parent_item = '{2}'
	group by item.item_code
	""".format(delivery_note.name, bundle_item.get("item_code"), bundle_item.get("parent_item")), as_list = 1)
	if res: pi_row.qty = res[0][0]

def set_details(bundle_item, item_row, pi_row, delivery_note):
	from erpnext.stock.doctype.packed_item.packed_item import (
		get_packed_item_details,
		update_packed_item_basic_data,
		update_packed_item_stock_data,
		update_packed_item_price_data,
		update_packed_item_from_cancelled_doc
	)
	item_data = get_packed_item_details(bundle_item.item_code, delivery_note.company)
	update_packed_item_basic_data(item_row, pi_row, bundle_item, item_data)
	update_packed_item_stock_data(item_row, pi_row, bundle_item, item_data, delivery_note)
	update_packed_item_price_data(pi_row, item_data, delivery_note)
	update_packed_item_from_cancelled_doc(item_row, bundle_item, pi_row, delivery_note)

def delete_dn(bdn, delivery_note):
	doc = frappe.get_doc("Delivery Note", delivery_note)
	if doc.get("packed_items"):
		for item in doc.get("packed_items"):
			if item.qty > 0: return
		frappe.db.set_value("Bundle Delivery Note", bdn, "delivery_note", "")
		if doc.docstatus == 0:
			doc.delete()

def remove_bdn(bdn, delivery_note):
	doc = frappe.get_doc("Delivery Note", delivery_note)
	bdnlist = []
	if doc.get("bdns"):
		i = 1
		for row in doc.bdns:
			if row.bundle_delivery_note != bdn:
				row.idx = i
				bdnlist.append(row)
				i += 1
		doc.update({"bdns": bdnlist})
		doc.save()


@frappe.whitelist()
def get_reminded_bundle_items(sales_order_name):
	if frappe.db.exists("Delivery Note Item", {"against_sales_order": sales_order_name, "docstatus": 0}):
		sales_order = frappe.get_doc("Sales Order", sales_order_name)
		delivery_note_name = frappe.db.get_value("Delivery Note Item", {"against_sales_order": sales_order_name, "docstatus": 0}, "parent")

		parent_items = []

		for sales_item in sales_order.items:
			if sales_item.delivered_qty >= sales_item.qty or sales_item.delivered_by_supplier == 1: continue
			so_packed_items = frappe.db.sql("""
				SELECT
					parent_item, item_code,
					SUM(qty) as qty
				FROM
					`tabPacked Item`
				WHERE
					parent = %s AND
					parent_item = %s
				GROUP BY
					item_code
			""", (sales_order_name, sales_item.item_code), as_dict=True)

			dn_packed_items = frappe.db.sql("""
				SELECT
					parent_item, item_code,
					SUM(qty) as qty , excluded_item
				FROM
					`tabPacked Item`
				WHERE
					parent = %s AND
					parent_item = %s
				GROUP BY
					item_code
			""", (delivery_note_name, sales_item.item_code), as_dict=True)
			#so_packed_items = frappe.db.get_all("Packed Item", {"parent": sales_order_name, "parent_item": sales_item.item_code}, ["*"])
			#dn_packed_items = frappe.db.get_all("Packed Item", {"parent": delivery_note_name, "parent_item": sales_item.item_code}, ["*"])
			toadd = True
			for so_pi in so_packed_items:
				for dn_pi in dn_packed_items:
					if so_pi.parent_item == dn_pi.parent_item and ((so_pi.item_code == dn_pi.item_code) \
					or (so_pi.item_code == dn_pi.excluded_item)):
						if so_pi.qty > dn_pi.qty:
							toadd = True
							break
				if toadd:
					parent_items.append({"item_code": sales_item.item_code})
					break
		return parent_items

	else:
		return frappe.db.sql(
			"""
			select distinct so_item.item_code
			from `tabSales Order Item` as so_item
			where so_item.parent = '{0}' and so_item.docstatus = 1
			and so_item.delivered_qty < so_item.qty and so_item.delivered_by_supplier != 1
			group by so_item.item_code
			""".format(sales_order_name),
		as_dict = 1)

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_parents_items(doctype, txt, searchfield, start, page_len, filters):
	if filters.get('item_parent'):
		result = (filters.get('item_parent'), )
		return (result, )

	strQuery = """
		SELECT bdnp.item_code 
		FROM `tabBundle Delivery Note Parent Item` as bdnp
	"""
	whereQuery = "WHERE bdnp.parent = %(parent)s and (bdnp.item_code like %(txt)s OR bdnp.item_code = %(item_parent)s)"
	
	if filters.get("child_item"):
		strQuery += """
		  inner join `tabProduct Bundle` as Pb on Pb.new_item_code = bdnp.item_code
		  inner join `tabProduct Bundle Item` as Pbi on Pbi.parent = Pb.name
		"""
		whereQuery += """ and Pbi.item_code = %(child_item)s """
	
	strQuery += whereQuery
	return frappe.db.sql(strQuery, {
		"parent": filters.get("parent"),
		"item_parent": filters.get("item_parent"),
		"child_item":filters.get("child_item"),
		"txt": "%" + txt + "%"})

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_packed_items(doctype, txt, searchfield, start, page_len, filters):
	query ="""
		SELECT bdni.item_code
		FROM `tabBundle Delivery Note Item` as bdni
		"""
	strwhere = """
		WHERE bdni.parent = %(parent)s and bdni.item_code like %(txt)s
		"""

	if filters.get("parent_item"):
		query += """
		  inner join `tabProduct Bundle Item` as Pbi on Pbi.item_code = bdni.item_code
		  inner join `tabProduct Bundle` as Pb on Pb.name = Pbi.parent
		"""
		strwhere += """
			and Pb.new_item_code = %(parent_item)s
		"""

	query += strwhere
	return frappe.db.sql(query, {
		"parent": filters.get("parent"), "txt": "%" + txt + "%", "parent_item": filters.get("parent_item")
		})

@frappe.whitelist()
def get_item_qty(item_code, parent_item, sales_order):
	if not frappe.db.exists("Delivery Note Item", {"against_sales_order": sales_order, "docstatus": 0}):
		return frappe.db.get_value("Packed Item", {"parent": sales_order, "parent_item": parent_item, "item_code": item_code}, "qty")

	delivery_note = frappe.db.get_value("Delivery Note Item", {"against_sales_order": sales_order, "docstatus": 0}, "parent")

	so_qty= frappe.db.get_value('Packed Item', {'parent': sales_order, "parent_item": parent_item,"item_code": item_code}, 'qty')
	
	if not so_qty:
		excluded_item = frappe.db.get_value('Packed Item', {'parent': delivery_note, "parent_item": parent_item, "item_code": item_code}, "excluded_item")
		so_qty= frappe.db.get_value('Packed Item', {'parent': sales_order, "parent_item": parent_item,"item_code": excluded_item}, 'qty')

	dn_qty = frappe.db.get_value('Packed Item', {'parent': delivery_note, "parent_item": parent_item, "item_code": item_code}, 'qty')

	if not dn_qty: return so_qty
	return so_qty - dn_qty

@frappe.whitelist()
def update_items(stock_entries, excluded_items , sales_order , price_list, company):
	# Handling excluded items
	stock_entries = json.loads(stock_entries)
	excluded_items = json.loads(excluded_items)
	stock_entries_new_items_list = []
	deleted_items_list = []
	items = deepcopy(stock_entries)
	for item in excluded_items:
		alt_item_found = False
		item['qty'] = get_item_qty(item["item_code"], item["parent_item"], sales_order)
		for i in items:

			if item["item_code"] == i["item_code"]:
				if not item["qty"] and not item.get('alt_item') or item.get('alt_item') == "":
					i["qty"] = 0
				i["qty"]  = i["qty"] - item["qty"]
				if i["qty"] <= 0:
					deleted_items_list.append(i["item_code"])

			if item.get('alt_item') and item.get('alt_item') == i["item_code"]:
				alt_item_found = True
				i["qty"] = i["qty"]  + item["qty"]

		if item.get('alt_item') and not alt_item_found:
			conversion_rate = frappe.db.get_value("Sales Order", sales_order ,"conversion_rate")
			price_list_rate = frappe.db.get_value("Item Price", {'item_code': item["alt_item"], 'price_list': price_list},"price_list_rate")
			items.append({
				"item_code" : item["alt_item"],
				"qty" : item["qty"],
				"warehouse" : item["warehouse"] if item.get("warehouse") else get_item_warehouse(frappe.get_doc("Item", item["alt_item"]), args = frappe._dict({"company": company}), overwrite_warehouse = True),
				"item_name" : frappe.db.get_value('Item' , i["item_code"] , 'item_name'),
				"uom" : frappe.db.get_value("Item", item["alt_item"], "stock_uom"),
				"rate" : price_list_rate / conversion_rate if price_list_rate else 0 ,
				"currency" : frappe.db.get_value("Sales Order", sales_order, "currency")
			})
	for i in items:
		if i["item_code"] not in deleted_items_list:
			values = {
				"doctype" : "Bundle Delivery Note Item",
				"item_code" : i["item_code"],
				"item_name" : i["item_name"],
				"qty" : i["qty"],
				"warehouse" : i["warehouse"],
				"uom" : i["uom"],
				"rate" : i["rate"],
				"currency" : i["currency"]
			}
			stock_entries_new_items_list.append(values)
	return {"stock_entries" : stock_entries_new_items_list }
	# self.update({"excluded_items" : []})

@frappe.whitelist()
def get_alt_details(item_code, sales_order, price_list, company, has_warehouse = False):
	message = {}
	conversion_rate, currency = frappe.db.get_value("Sales Order", sales_order, ["conversion_rate", "currency"])
	price_list_rate = frappe.db.get_value("Item Price", {
		'item_code': item_code, 'price_list': price_list},
			'price_list_rate')
	message['rate'] = price_list_rate / conversion_rate if price_list_rate else 0.00
	message['uom'] = frappe.db.get_value("Item", item_code, "stock_uom")
	message['currency'] = currency
	message['item_name'] = frappe.db.get_value("Item", item_code, "item_name")
	if not has_warehouse or has_warehouse == 'false':
		ware = get_item_warehouse(frappe.get_doc("Item", item_code), args = frappe._dict({"company": company}), overwrite_warehouse = True)
		message['warehouse'] = ware
	return message
