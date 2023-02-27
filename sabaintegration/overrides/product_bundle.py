import frappe

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_new_item_code(doctype, txt, searchfield, start, page_len, filters):
	from erpnext.controllers.queries import get_match_cond

	return frappe.db.sql(
		"""select name, item_name, description, is_a_parent_bundle from tabItem
		where is_a_parent_bundle=1 and is_stock_item=0 and name not in (select name from `tabProduct Bundle`)
		and %s like %s %s limit %s, %s"""
		% (searchfield, "%s", get_match_cond(doctype), "%s", "%s"),
		("%%%s%%" % txt, start, page_len),
	)##orginal code located in apps/erpnext/erpnext/selling/doctype/product_bundle/product_bundle.py starting from line 73