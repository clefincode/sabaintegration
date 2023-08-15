import json
import frappe
from datetime import datetime
from six import string_types
from frappe.utils import  cstr, flt, now
from frappe.model.utils import get_fetch_values
from frappe.model.mapper import get_mapped_doc
from frappe.contacts.doctype.address.address import get_company_address

from erpnext.stock.doctype.item.item import get_item_defaults
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.selling.doctype.sales_order.sales_order import SalesOrder, make_project

class CustomSalesOrder(SalesOrder):
    def validate(self):
        super(CustomSalesOrder, self).validate()
        self.update_total_margin()
        self.update_costs()
        self.validate_commission()
        if self.get("_action") and self._action == 'submit':
            self.submitting_date = now()
        if self.get("_action") and self._action != 'update_after_submit':
            if not self.tc_name:
                frappe.throw("Terms is a mandatory field")

    def update_total_margin(self):
        self.total = self.total_rate_without_margin = self.base_total_rate_without_margin = 0
        for item in self.items:
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

    def on_submit(self):
        super(CustomSalesOrder, self).on_submit()
        self.create_project_automatically()

    def create_project_automatically(self):
        if self.project: return

        project = make_project(self.name)
        project.insert(ignore_permissions = True)
        frappe.msgprint("A new project <a href='/app/project/{project}'><b>{project}</b></a> has been created".format(project = project.name))
    
    def validate_commission(self):
        if not self.primary_sales_man and self.sales_commission:
            frappe.throw("You Need to Set a Primary Sales Man for the Sales Order")
        if not self.commission_percentage and self.primary_sales_man:
            comm = get_commission_percent(self.primary_sales_man)
            if not comm:
                comm = 5
            self.commission_percentage = comm

@frappe.whitelist()
def make_bdn(sales_order, parents_items):
    from sabaintegration.sabaintegration.doctype.bundle_delivery_note.bundle_delivery_note import get_items
    
    if isinstance(parents_items, string_types):
        parents_items = json.loads(parents_items)

    doc = get_bdn(sales_order, parents_items)
    if doc: return doc

    from erpnext import get_default_company

    doc = frappe.new_doc("Bundle Delivery Note") 
    sales_order_doc = frappe.get_doc("Sales Order", sales_order)
    fields= {
        "sales_order": sales_order,
        "project": sales_order_doc.get("project") or "",
        "price_list": sales_order_doc.get("selling_price_list") or "",
        "company": sales_order_doc.get("company") or get_default_company()
    }
    itemcodes = []
    if len(parents_items) == 1:
        fields["item_parent"] = parents_items[0]["item_code"]
        itemcodes.append(parents_items[0]["item_code"])

    else:
        itemslist = []
        for item in parents_items:
            row = frappe.new_doc("Bundle Delivery Note Parent Item")
            row.item_code = item["item_code"]
            row.item_name = frappe.db.get_value("Item", row.item_code, "item_name")
            row.qty = frappe.db.get_value("Sales Order Item", {"parent": sales_order, "item_code": row.item_code}, "qty")
            row.uom = frappe.db.get_value("Sales Order Item", {"parent": sales_order, "item_code": row.item_code}, "uom")
            row.warehouse = frappe.db.get_value("Sales Order Item", {"parent": sales_order, "item_code": row.item_code}, "warehouse")
            itemslist.append(row)
            itemcodes.append(row.item_code)

        fields["parents_items"] = itemslist
        fields["multiple_items"] = 1

    packed_items = get_items(sales_order = sales_order, parents = itemcodes)
    fields["stock_entries"] = packed_items
    doc.update(fields)
    return doc

def get_bdn(sales_order, parents_items):
    filters = {
        "docstatus": 0,
        "sales_order": sales_order
    }

    if len(parents_items) == 1:
        filters["item_parent"] = parents_items[0]["item_code"]
        bdn = frappe.db.get_all("Bundle Delivery Note", filters)
        if bdn: return frappe.get_doc("Bundle Delivery Note", bdn[0])
    
    if "item_parent" in filters.keys(): del filters["item_parent"]
    bdns = frappe.db.get_all("Bundle Delivery Note", filters, "name")
    for bdn in bdns:
        skipBDN = False
        doc = frappe.get_doc("Bundle Delivery Note", bdn.name)
        for data_item in parents_items:
            found = False
            for item in doc.parents_items:
                if item.item_code == data_item["item_code"]:
                    found = True
                    break
            if not found:
                skipBDN = True
                break
        if not skipBDN: return doc

def make_delivery_note(source_name, target_doc=None, skip_item_mapping=False):
    def set_missing_values(source, target):
        target.run_method("set_missing_values")
        target.run_method("set_po_nos")
        target.run_method("calculate_taxes_and_totals")

        if source.company_address:
            target.update({"company_address": source.company_address})
        else:
            # set company address
            target.update(get_company_address(target.company))

        if target.company_address:
            target.update(get_fetch_values("Delivery Note", "company_address", target.company_address))

    def update_item(source, target, source_parent):
        target.base_amount = (flt(source.qty) - flt(source.delivered_qty)) * flt(source.base_rate)
        target.amount = (flt(source.qty) - flt(source.delivered_qty)) * flt(source.rate)
        target.qty = flt(source.qty) - flt(source.delivered_qty)

        item = get_item_defaults(target.item_code, source_parent.company)
        item_group = get_item_group_defaults(target.item_code, source_parent.company)

        if item:
            target.cost_center = (
                frappe.db.get_value("Project", source_parent.project, "cost_center")
                or item.get("buying_cost_center")
                or item_group.get("buying_cost_center")
            )

    mapper = {
        "Sales Order": {"doctype": "Delivery Note", "validation": {"docstatus": ["=", 1]}},
        "Sales Taxes and Charges": {"doctype": "Sales Taxes and Charges", "add_if_empty": True},
        "Sales Team": {"doctype": "Sales Team", "add_if_empty": True},
    }

    if not skip_item_mapping:

        def condition(doc):
            # make_mapped_doc sets js `args` into `frappe.flags.args`
            if frappe.flags.args and frappe.flags.args.delivery_dates:
                if cstr(doc.delivery_date) not in frappe.flags.args.delivery_dates:
                    return False          
            if frappe.db.exists("Product Bundle", {"new_item_code": doc.item_code}):
                ex = True
            else: ex = False
            return abs(doc.delivered_qty) < abs(doc.qty) and doc.delivered_by_supplier != 1 and ex

        mapper["Sales Order Item"] = {
            "doctype": "Delivery Note Item",
            "field_map": {
                "rate": "rate",
                "name": "so_detail",
                "parent": "against_sales_order",
            },
            "postprocess": update_item,
            "condition": condition,
        }

    target_doc = get_mapped_doc("Sales Order", source_name, mapper, target_doc, set_missing_values)

    target_doc.set_onload("ignore_price_list", True)

    return target_doc

@frappe.whitelist()
def get_commission(commission_template):

	from frappe.model import child_table_fields, default_fields

	template = frappe.get_doc("Sales Commission Template", commission_template)

	template_list = []
	for i, comm in enumerate(template.get("sales_commission")):
		comm = comm.as_dict()

		for fieldname in default_fields + child_table_fields:
			if fieldname in comm:
				del comm[fieldname]

		template_list.append(comm)

	return template_list

@frappe.whitelist()
def get_commission_percent(sales_man):
    if not sales_man: return
    from datetime import datetime

    # Get the current date
    now_date = frappe.utils.nowdate()

    # Convert it to a datetime object
    today_date = datetime.strptime(now_date, '%Y-%m-%d')
    month = today_date.month
    year = today_date.year
    quarter = (month - 1) // 3 + 1
    
    if not quarter: return
    
    commission_percentage = frappe.db.get_value("Quarter Quota", {"sales_man": sales_man, "quarter": "Q"+ str(quarter), "year": year, "docstatus": 1}, "commission_percentage")

    if commission_percentage: return commission_percentage