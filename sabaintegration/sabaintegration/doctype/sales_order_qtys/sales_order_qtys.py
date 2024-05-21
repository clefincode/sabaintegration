# Copyright (c) 2024, Ahmad and contributors
# For license information, please see license.txt
import json
import frappe
from frappe.model.document import Document

class SalesOrderQtys(Document):
	def before_insert(self):
		self.set_items_qty()

	def validate(self):
		for item in self.items:
			self.set_remained_qty(item)
			self.check_is_completed(item)
			self.check_is_delivered(item)

	def set_items_qty(self):
		for item in self.items:
			self.set_reserved_qty(item)
			self.set_ordered_qty(item)
			self.set_projected_qty(item)


	def set_reserved_qty(self, item):
		actual_qty = get_actual_qty(item.item_code)
		reserved_qty = get_total_reserved_qty(item.item_code)

		remained_reserved_qty = actual_qty - reserved_qty

		if remained_reserved_qty < 0:
			remained_reserved_qty = 0

		if remained_reserved_qty >= item.required_qty:
			item.reserved_qty = item.required_qty
		else:
			item.reserved_qty = remained_reserved_qty


	def set_ordered_qty(self, item):
		if item.is_completed or item.is_delivered or item.reserved_qty == item.required_qty: 
			item.ordered_qty = 0
			return

		if not item.get("projected_qty"): item.projected_qty = 0

		remained_qty = item.required_qty - (item.reserved_qty + item.projected_qty)

		results = get_ordered_item_qty(item.item_code, remained_qty, self.sales_order)
		item.ordered_qty = results[0]

		if results[1]:
			ordered_po = json.loads(item.ordered_purchase_orders).get("ordered_po")
			if not ordered_po:
				ordered_po = []
			for res in results[1]:
				ordered_po.append({"po" : res.purchase_order, "qty" : res.qty})
			item.ordered_purchase_orders = json.dumps({"ordered_po": ordered_po})

	def set_projected_qty(self, item):
		if item.is_completed or item.is_delivered or item.reserved_qty + item.ordered_qty == item.required_qty: 
			item.projected_qty = 0
			return

		if not item.get("ordered_qty"): item.ordered_qty = 0

		remained_qty = item.required_qty - (item.get("reserved_qty", 0) + item.get("ordered_qty", 0))
		results = get_ordered_item_qty(item.item_code, remained_qty)
		item.projected_qty = results[0]

		if results[1]:
			projected_po = json.loads(item.projected_purchase_orders).get("projected_po")
			if not projected_po:
				projected_po = []
			for res in results[1]:
				projected_po.append({"po" : res.purchase_order , "qty" : res.qty})
			item.projected_purchase_orders = json.dumps({"projected_po": projected_po})

	def set_remained_qty(self, item):
		if not item.get("delivered_qty", 0):
			item.delivered_qty = 0
		item.remained_qty = item.required_qty - (item.get("reserved_qty", 0) + item.get("projected_qty", 0) + item.get("ordered_qty", 0) + item.get("delivered_qty", 0)) 

	def check_is_completed(self, item):
		if item.required_qty == item.reserved_qty:
			item.is_completed = 1

	def check_is_delivered(self, item):
		if item.required_qty == item.delivered_qty:
			item.is_delivered = 1

def get_actual_qty(item_code):
	bin_qty = frappe.db.sql(
		"""select sum(actual_qty) from `tabBin`
		where item_code = %s
		group by item_code""",
		(item_code),
		as_list=1,
	)
	if not bin_qty or not bin_qty[0]: bin_qty = 0
	else: bin_qty = bin_qty[0][0]

	return bin_qty

def get_total_reserved_qty(item_code):
	reserved_qty = frappe.db.sql("""
		select sum(reserved_qty)
		from `tabSales Order Qtys` as soq, `tabSales Order Qtys Item` as soqi
		where soq.name = soqi.parent 
		and soq.is_cancelled = 0 and soqi.item_code = %s
		group by soqi.item_code
	""", item_code, as_list=1)

	if not reserved_qty or not reserved_qty[0]: reserved_qty = 0
	else:
		reserved_qty = reserved_qty[0][0]

	return reserved_qty

def get_ordered_item_qty(item_code, remained_qty, sales_order = None):
	strQuery = f"""
		select poi.qty, po.name as purchase_order
		from `tabPurchase Order` as po
		inner join `tabPurchase Order Item` as poi on po.name = poi.parent and po.docstatus = 1
		where 
		po.status not in ('Completed', 'To Bill', 'Closed', 'Delivered')
		and poi.item_code = '{item_code}'
	"""

	if sales_order:
		strQuery += f" and poi.sales_order = '{sales_order}'"
	else: 
		strQuery += " and (poi.sales_order = '' or poi.sales_order is null)"

	strQuery += " order by poi.qty desc "

	details = frappe.db.sql(strQuery, as_dict = 1)
	
	if not details or not details[0]: return 0, None

	ordered_qty = 0

	results = []

	if not sales_order:
		get_total_projected_qtys(item_code, details)

	for res in details:
		res.qty = res.qty - get_receipt_qty(item_code, res.purchase_order)

		if res.qty <= 0: continue
		if remained_qty >= res.qty:
			ordered_qty += res.qty

		else:
			ordered_qty = (remained_qty - ordered_qty) + ordered_qty
			res.qty = remained_qty
		results.append(res)

		if ordered_qty >= remained_qty: break		

	return ordered_qty, results

def get_receipt_qty(item_code, purchase_order):
	total = 0
	qtys = frappe.db.get_all("Purchase Receipt Item", {'purchase_order': purchase_order, 'item_code': item_code, 'docstatus': 1}, 'qty')
	for qty in qtys:
		total += qty.qty
	
	return total

def get_total_projected_qtys(item_code, purchase_orders):
	itemqtys = frappe.db.get_all("Sales Order Qtys Item", {
		"item_code": item_code,
		"is_completed": 0,
		"is_delivered": 0,
		"projected_qty": ('>', 0)
		}, '*')
	
	for doc in purchase_orders:
		for row in itemqtys:
			projected_po = json.loads(row.projected_purchase_orders).get("projected_po")
			if projected_po:
				for po in projected_po:
					if po["po"] == doc.purchase_order:
						doc.qty = doc.qty - po["qty"]