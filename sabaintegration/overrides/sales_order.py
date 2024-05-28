import json
from copy import deepcopy
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
from erpnext.accounts.doctype.sales_invoice.sales_invoice import (
    validate_inter_company_party,
)
from sabaintegration.sabaintegration.doctype.sales_order_payment.sales_order_payment import get_quarter

class CustomSalesOrder(SalesOrder):
    def validate(self):
        super(SalesOrder, self).validate()
        self.validate_delivery_date()
        self.validate_proj_cust()
        self.validate_po()
        self.validate_uom_is_integer("stock_uom", "stock_qty")
        self.validate_uom_is_integer("uom", "qty")
        self.validate_for_items()
        self.validate_warehouse()
        self.validate_drop_ship()
        self.validate_serial_no_based_delivery()
        validate_inter_company_party(
            self.doctype, self.customer, self.company, self.inter_company_order_reference
        )

        if self.coupon_code:
            from erpnext.accounts.doctype.pricing_rule.utils import validate_coupon_code

            validate_coupon_code(self.coupon_code)

        make_packing_list(self)

        self.validate_with_previous_doc()
        self.set_status()

        if not self.billing_status:
            self.billing_status = "Not Billed"
        if not self.delivery_status:
            self.delivery_status = "Not Delivered"

        self.reset_default_field_value("set_warehouse", "items", "warehouse")
    
        self.custom_validate()

    def custom_validate(self):
        self.update_total_margin()
        self.update_costs()
        self.validate_commission()
        self.validate_sales_commission()
        self.validate_pre_sales_activities()
        self.set_brands()
        if self.get("_action") and self._action == 'submit':
            self.set_submitting_date()
        if self.get("_action") and self._action != 'update_after_submit':
            if not self.tc_name:
                frappe.throw("Terms is a mandatory field")
    
    def before_update_after_submit(self):
        super(CustomSalesOrder, self).before_update_after_submit()
        self.validate_sales_commission()
        self.validate_pre_sales_activities()
        
    def on_update_after_submit(self):
        self.update_total_margin()
        self.update_costs()

    def update_total_margin(self):
        self.total = self.total_rate_without_margin = self.base_total_rate_without_margin = 0
        margins = {}
        for item in self.items:
            item.base_rate_without_profit_margin = item.rate_without_profit_margin * self.conversion_rate
            self.total_rate_without_margin = self.total_rate_without_margin + flt(item.rate_without_profit_margin * item.qty, item.precision("rate_without_profit_margin"))
            self.total += flt(item.amount, item.precision("amount"))
            margins[item.name] = item.margin_from_supplier_quotation
        
        if self.get("packed_items"):
            for item in self.packed_items:
                item.rate_before_margin = item.rate_before_margin or 0
                if item.rate_before_margin:
                    item.rate = item.rate_before_margin * margins[item.parent_detail_docname] / 100 + item.rate_before_margin
                    item.margin = margins[item.parent_detail_docname]
        self.base_total_rate_without_markup = self.total_rate_without_margin * self.conversion_rate
        self.base_total = self.total * self.conversion_rate

        self.total_items_markup_value = (self.total - self.total_rate_without_margin)
        self.base_total_items_markup_value = self.total_items_markup_value * self.conversion_rate
        self.total_margin = self.total_items_markup_value / self.total_rate_without_margin * 100 if self.total_rate_without_margin else 0 

    def update_costs(self):
        total_costs = 0.00
        if self.get("costs"): 
            for row in self.costs:
                if row.cost_type == "Material Cost's VAT":
                    row.cost_value = self.total_rate_without_margin * row.cost_percentage / 100
                else:
                    row.cost_value = self.net_total * row.cost_percentage / 100
                total_costs += row.cost_value
        self.total_costs = total_costs
        self.base_total_costs = self.total_costs * self.conversion_rate
        
        self.total_costs_with_material_costs = self.total_costs + self.total_rate_without_margin
        self.base_total_costs_with_material_costs = self.total_costs_with_material_costs * self.conversion_rate

        self.expected_profit_loss_value = self.net_total - self.total_costs_with_material_costs 
        self.base_expected_profit_loss_value = self.expected_profit_loss_value * self.conversion_rate
        self.expected_profit_loss = (self.expected_profit_loss_value * 100) / self.net_total if self.net_total else 0

    def on_submit(self):
        super(CustomSalesOrder, self).on_submit()
        # self.create_project_automatically()
        create_sales_qtys(self)

    def on_cancel(self):
        self.cancel_soq()

    def cancel_soq(self):
        if frappe.db.exists("Sales Order Qtys", self.name):
            doc = frappe.get_doc("Sales Order Qtys", self.name)
            doc.is_cancelled = 1
            doc.save(ignore_permissions=True)

    def create_project_automatically(self):
        if self.project: return

        project = make_project(self.name)
        project.insert(ignore_permissions = True)
        frappe.msgprint("A new project <a href='/app/project/{project}'><b>{project}</b></a> has been created".format(project = project.name))
    
    def validate_commission(self):
        """Set Commission Details if There is an Assigned Sales Man for the SO
        and if There is a Missing Details"""
        if (not self.commission_percentage \
            or not self.primary_supervisor or not self.prm_sup_percentage or \
            not self.secondary_supervisor or not self.sec_sup_percentage) and \
            self.primary_sales_man:
            values = get_commission_percent(self.primary_sales_man)

            if not self.commission_percentage:
                self.commission_percentage = values["commission_percentage"]
            if not self.primary_supervisor:
                self.primary_supervisor = values["primary_supervisor"]
            if not self.secondary_supervisor:
                self.secondary_supervisor = values["secondary_supervisor"]
            if not self.prm_sup_percentage:
                self.prm_sup_percentage = values["prm_sup_percentage"]
            if not self.sec_sup_percentage == values["sec_sup_percentage"]:
                self.sec_sup_percentage = values["sec_sup_percentage"]

    def validate_sales_commission(self):
        if not self.primary_sales_man and not self.sales_commission:
            return

        if not self.primary_sales_man and self.sales_commission:
            frappe.throw("You Need to Set a Primary Sales Man for the Sales Order")

        commission_percentage_total = 0
        for row in self.sales_commission:
            commission_percentage_total += row.comm_percent
        if commission_percentage_total != 100:
            frappe.throw("The Total of Commission Percentages in Sales Commission is not equal to 100%")

    def validate_pre_sales_activities(self):
        "The Total of the Pre-Sales Activities Table Contribution Percentages has to Equal 100%"
        if not self.pre_sales_activities:
            return

        incentive_percentage_total = 0
        for row in self.pre_sales_activities:
            if row.contribution_percentage:
                incentive_percentage_total += row.contribution_percentage
        if incentive_percentage_total != 100:
            frappe.throw("The Total of Contribution Percentages in Pre-Sales Activities is not equal to 100%")

    def set_submitting_date(self):
        if not self.amended_from:
            self.submitting_date = now()
        elif frappe.db.exists("Sales Order", self.amended_from):
            submitting_date = frappe.db.get_value("Sales Order", self.amended_from, "submitting_date")
            if submitting_date: self.submitting_date = submitting_date

    def set_brands(self, quarter_args=None, update_table = False):
        "Set The Brands Table"

        toset = True
        if not quarter_args:
            # Get the Year and the Quarter of Today
            today_date = datetime.now()
            today_qq = (today_date.month, today_date.year)
        else:
            today_qq = quarter_args

        # If The Doc is not New, Then Compare it with the Previous State
        if self.get_doc_before_save() and update_table == False:
            # Get the Previous Modifiation Year and Quarter
            modified_dt = self.get_doc_before_save().modified
            before_save_qq = (modified_dt.month, modified_dt.year)
            
            # If the Year and The Quarter between Today and The Previous State are Equals
            # Then Check if the Table Needs to be Updated
            if before_save_qq == today_qq and \
            self.get_doc_before_save().conversion_rate == self.conversion_rate and \
            self.get_doc_before_save().currency == self.currency and \
            self.base_total_costs == self.get_doc_before_save().base_total_costs:
                items_before_save = [{"item_code": i.item_code, "base_amount": i.base_amount, "margin": i.margin_from_supplier_quotation} for i in self.get_doc_before_save().items]
                items_after_save = [{"item_code": i.item_code, "base_amount": i.base_amount, "margin": i.margin_from_supplier_quotation} for i in self.items]
                if items_before_save == items_after_save:
                    if self.get("packed_items"):
                        items_before_save = [{"item_code": i.item_code, "parent_item": i.parent_item, "rate": i.rate, "rate_before_margin": i.rate_before_margin} for i in self.get_doc_before_save().packed_items]
                        items_after_save = [{"item_code": i.item_code, "parent_item": i.parent_item, "rate": i.rate, "rate_before_margin": i.rate_before_margin} for i in self.packed_items]
                        if items_before_save == items_after_save:
                            toset = False
                    else:
                        toset = False
        
        if not toset: return

        self.brands, brands = [], {}
        # Get the Brands Set
        for item in self.items:
            if not frappe.db.get_value("Item", item.item_code, "is_stock_item") and frappe.db.get_value("Item", item.item_code, "is_a_parent_bundle"):
                continue
            brand = frappe.db.get_value("Item", item.item_code, "brand")
            if not brand: brand = "No Brand"
            if not brands.get(brand):
                brands[brand] = (
                    item.base_net_amount, 
                    item.net_amount)
            else: 
                brands[brand] = (
                    brands[brand][0] + item.base_net_amount, 
                    brands[brand][1] + item.net_amount)

        for item in self.get("packed_items"):
            brand = frappe.db.get_value("Item", item.item_code, "brand")
            item.margin = item.margin or 0
            item.rate_before_margin = item.rate_before_margin or 0
            if not brand: brand = "No Brand"
            if not brands.get(brand):
                brands[brand] = (
                    (item.rate * item.qty) * self.conversion_rate, 
                    item.rate * item.qty)
            else: 
                brands[brand] = (
                    brands[brand][0] + (item.rate * item.qty * self.conversion_rate),
                    brands[brand][1] + (item.rate * item.qty))

        quarter = "Q" + str(get_quarter(today_qq[0]))
        if frappe.db.exists("Marketing Quarter Quota", {"year": today_qq[1], "quarter": quarter, "docstatus": 1}):
            # Assign Each Brand with its Product Manager
            qq = frappe.get_doc("Marketing Quarter Quota", {"year": today_qq[1], "quarter": quarter, "docstatus": 1})   
            no_brand_row= None
            for row in qq.brands:
                if row.brand == "No Brand":
                    no_brand_row = row

            for brand in brands:
                found = False
                for row in qq.brands:
                    if brand == row.brand:
                        self.append("brands", frappe._dict({
                            "product_manager": row.product_manager,
                            "brand": brand,
                            "kpi": row.kpi,
                            "incentive_percentage": row.incentive_percentage,
                            # "selling_amount": brands[brand][0],
                            # "selling_amount_in_order_currency": brands[brand][2],
                            "total_quota": brands[brand][0] * self.expected_profit_loss / 100,
                            "total_quota_in_order_currency": brands[brand][1] * self.expected_profit_loss / 100
                        }))
                        found = True
                        qq.brands.remove(row)
                        break
                
                if not found:
                    if no_brand_row:
                        self.append("brands", frappe._dict({
                        "product_manager": no_brand_row.product_manager,
                        "brand": "No Brand",
                        "kpi": no_brand_row.kpi,
                        "incentive_percentage": no_brand_row.incentive_percentage,
                        # "selling_amount": brands[brand][0],
                        # "selling_amount_in_order_currency": brands[brand][2],
                        "total_quota": brands[brand][0] * self.expected_profit_loss / 100,
                        "total_quota_in_order_currency": brands[brand][1] * self.expected_profit_loss / 100
                    }))
                    else:
                        frappe.msgprint("Be Careful! Brand <b>{}</b> has no an associated Product Manager for it. So it's not added to the Marketing Table". format(brand))
        else:
            frappe.msgprint("Be Careful! Marketing Table can't be updated because there is no submitted Marketing Quarter Quota for the current Quarter")

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

def get_primary_sales_man_leaders(sales_man):
    "Get The Primary and The Secondary Supervisors of The Primary Sales Man"
    from sabaintegration.sabaintegration.report.quota import get_employee, check_if_leader
    from sabaintegration.overrides.employee import get_leaders
    leaders = []
    employee = get_employee("Sales Person", sales_man)
    if check_if_leader(employee, "Sales Person"):
        if employee.position == "Manager":
            leaders.extend([sales_man, sales_man])
        else:
            leadersList = get_leaders(employee.name, "name", "reports_to")

            if leadersList:
              sales_leader = frappe.db.get_value("Sales Person", {"employee": leadersList[0]}, "name")
              leaders.extend([sales_man, sales_leader])  
    else: 
        leadersList = get_leaders(employee.name, "name", "reports_to")
        if leadersList:
            sales_leader_1 = frappe.db.get_value("Sales Person", {"employee": leadersList[0]}, "name")
            sales_leader_2 = frappe.db.get_value("Sales Person", {"employee": leadersList[1]}, "name")
              
            leaders.extend([sales_leader_1, sales_leader_2])
           
    return leaders

@frappe.whitelist()
def get_commission_percent(sales_man):
    "Get the Commission Percentages"
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

    leaders = get_primary_sales_man_leaders(sales_man)
    commission_percentage = frappe.db.get_value("Quarter Quota", {
        "sales_man": sales_man, 
        "quarter": "Q"+ str(quarter), 
        "year": year, 
        "docstatus": 1}, "commission_percentage")

    primary_commission = frappe.db.get_value("Quarter Quota", {
        "sales_man": leaders[0] if leaders else None, 
        "quarter": "Q"+ str(quarter), 
        "year": year, 
        "docstatus": 1}, "primary_commission_percentage")

    secondary_commission = frappe.db.get_value("Quarter Quota", {
        "sales_man": leaders[1] if leaders else None, 
        "quarter": "Q"+ str(quarter), 
        "year": year, 
        "docstatus": 1}, "secondary_commission_percentage")

    return {"commission_percentage": commission_percentage, 
            "primary_supervisor": leaders[0] if leaders else None,
            "secondary_supervisor": leaders[1] if leaders else None,
            "prm_sup_percentage": primary_commission,
            "sec_sup_percentage": secondary_commission}

@frappe.whitelist()
def get_incentive_percent(engineer):
    "Get the Incentive Percentagr of an Engineer in The Current Quarter"
    if not engineer: return
    from datetime import datetime

    # Get the current date
    now_date = frappe.utils.nowdate()

    # Convert it to a datetime object
    today_date = datetime.strptime(now_date, '%Y-%m-%d')
    month = today_date.month
    year = today_date.year
    quarter = (month - 1) // 3 + 1
    
    if not quarter: return

    incentive_percentage = frappe.db.get_value("Pre-Sales Quarter Quota", {"engineer": engineer, "quarter": "Q"+ str(quarter), "year": year, "docstatus": 1}, "incentive_percentage")

    if incentive_percentage: return incentive_percentage

@frappe.whitelist()
def get_pre_sales_activities(pre_sales_incentive_template):
    "Fill the Pre-Sales Activity Table with a Specific Template"
    from frappe.model import child_table_fields, default_fields

    template = frappe.get_doc("Pre-Sales Incentive Template", pre_sales_incentive_template)

    template_list = []
    for i, comm in enumerate(template.get("pre_sales_incentive")):
        comm = comm.as_dict()

        for fieldname in default_fields + child_table_fields:
            if fieldname in comm:
                del comm[fieldname]

        template_list.append(comm)

    return template_list

@frappe.whitelist()
def get_sales_person(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql(
        f"""SELECT name , employee
            FROM `tabSales Person` 
            WHERE enabled = 1 AND (name like '%{txt}%' or employee like '%{txt}%')
            order by name
            """)

@frappe.whitelist()
def get_engineer(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql(
        f"""SELECT name , employee
            FROM `tabPre-Sales Engineer` 
            WHERE enabled = 1 AND (name like '%{txt}%' or employee like '%{txt}%')
            order by name
            """)

def make_packing_list(doc):
    "Make/Update packing list for Product Bundle Item."
    from erpnext.stock.doctype.packed_item.packed_item import (
        is_product_bundle,
        get_indexed_packed_items_table,
        reset_packing_list,
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

    packed_items = deepcopy(doc.get("packed_items"))

    reset = reset_packing_list(doc)

    for item_row in doc.get("items"):
        if is_product_bundle(item_row.item_code):
            for bundle_item in get_product_bundle_items(item_row.item_code):
                pi_row = add_packed_item_row(
                    doc=doc,
                    packing_item=bundle_item,
                    main_item_row=item_row,
                    packed_items_table=stale_packed_items_table,
                    reset=reset,
                    packed_items = packed_items
                )
                item_data = get_packed_item_details(bundle_item.item_code, doc.company)
                update_packed_item_basic_data(item_row, pi_row, bundle_item, item_data)
                update_packed_item_stock_data(item_row, pi_row, bundle_item, item_data, doc)
                update_packed_item_price_data(pi_row, item_data, doc)
                update_packed_item_from_cancelled_doc(item_row, bundle_item, pi_row, doc)

                if set_price_from_children:  # create/update bundle item wise price dict
                    update_product_bundle_rate(parent_items_price, pi_row, item_row)

    if parent_items_price:
        set_product_bundle_rate_amount(doc, parent_items_price)  # set price in bundle item


def add_packed_item_row(doc, packing_item, main_item_row, packed_items_table, reset, packed_items):
    """Add and return packed item row.
    doc: Transaction document
    packing_item (dict): Packed Item details
    main_item_row (dict): Items table row corresponding to packed item
    packed_items_table (dict): Packed Items table before save (indexed)
    reset (bool): State if table is reset or preserved as is
    """
    exists, pi_row = False, {}

    # check if row already exists in packed items table
    key = (main_item_row.item_code, packing_item.item_code, main_item_row.name)
    if packed_items_table.get(key):
        pi_row, exists = packed_items_table.get(key), True

    if not exists:
        if packed_items:
            for packed_item in packed_items:
                if packed_item.parent_item == main_item_row.item_code and\
                packed_item.item_code == packing_item.item_code and\
                packed_item.section_title == main_item_row.section_title:
                    pi_row, exists = packed_item, True
                    exists = True
                    break

    if not exists:
        pi_row = doc.append("packed_items", {})
    elif reset:  # add row if row exists but table is reset
        pi_row.idx, pi_row.name = None, None
        pi_row = doc.append("packed_items", pi_row)

    return pi_row

@frappe.whitelist()
def make_sales_order(sales_order, items):
    if frappe.db.exists("Delivery Note Item", {"against_sales_order": sales_order, "docstatus": 1}):
        frappe.throw("You can't update the qtys after creating a Delivery Note")

    if isinstance(items, string_types):
        items = json.loads(items)

    old_doc = frappe.get_doc("Sales Order", sales_order)
    new_doc = frappe.copy_doc(old_doc)
    new_doc.amended_from = old_doc.name

    for item in items:
        for row in new_doc.items:
            if not row.get("section_title"):
                row.section_title = ""

            if not item.get("section_title"):
                item["section_title"] = ""

            if row.item_code == item["item_code"] and row.get("section_title") == item.get("section_title"):

                row.qty = item["qty"]
                row.amount = row.qty * row.rate
                break  
    
    old_doc.cancel()
    new_doc.insert()
    frappe.db.commit()
    return new_doc


def create_sales_qtys(doc):
    """Create a Sales Order Qtys document for recording 
    the details of items qty in each sales order"""

    soq = frappe.new_doc("Sales Order Qtys")

    # Add stock items to the new doc table
    for item in doc.items:
        if not frappe.db.get_value("Item", item.item_code, "is_stock_item"):
            continue

        soq.append("items", {
            "item_code": item.item_code,
            "so_detail": item.name,
            "required_qty": item.qty
        })

    # Add packed items to the new doc table if exists
    if doc.get("packed_items"):
        for item in doc.items:
            soq.append("items", {
                "item_code": item.item_code,
                "pi_detail": item.name,
                "required_qty": item.qty,
                "parent_item": item.parent_item,
                "so_detail": item.parent_detail_docname
            })

    soq.update({
        "sales_order": doc.name,
        "project": doc.get("project")
    })

    soq.insert(ignore_permissions = True)