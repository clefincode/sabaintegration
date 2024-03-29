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

from sabaintegration.sabaintegration.doctype.sales_order_payment.sales_order_payment import get_quarter

class CustomSalesOrder(SalesOrder):
    def validate(self):
        super(CustomSalesOrder, self).validate()
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
                if row.cost_type == "Material Cost's VAT":
                    row.cost_value = self.total_rate_without_margin * row.cost_percentage / 100
                else:
                    row.cost_value = self.net_total * row.cost_percentage / 100
                total_costs += row.cost_value
        self.total_costs = total_costs
        self.base_total_costs = self.total_costs * self.conversion_rate
        
        self.total_costs_with_material_costs = self.total_costs + self.total_rate_without_margin
        self.base_total_costs_with_material_costs = self.total_costs_with_material_costs * self.conversion_rate;

        self.expected_profit_loss_value = self.net_total - self.total_costs_with_material_costs 
        self.base_expected_profit_loss_value = self.expected_profit_loss_value * self.conversion_rate
        self.expected_profit_loss = (self.expected_profit_loss_value * 100) / self.net_total if self.net_total else 0

    # def on_submit(self):
    #     super(CustomSalesOrder, self).on_submit()
    #     self.create_project_automatically()

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
            self.get_doc_before_save().currency == self.currency:
                items_before_save = [{"item_code": i.item_code, "base_amount": i.base_amount, "margin": i.margin_from_supplier_quotation} for i in self.get_doc_before_save().items]
                items_after_save = [{"item_code": i.item_code, "base_amount": i.base_amount, "margin": i.margin_from_supplier_quotation} for i in self.items]
                if items_before_save == items_after_save:
                    toset = False
        
        if not toset: return

        self.brands, brands = [], {}
        # Get the Brands Set
        for item in self.items:
            # if frappe.db.get_value("Item", item.item_code, "is_stock_item"):
            #     continue
            brand = frappe.db.get_value("Item", item.item_code, "brand")
            if not brand: brand = "Unknown"
            if not brands.get(brand):
                if item.base_rate_without_profit_margin == 0 and item.base_rate > 0:
                    brands[brand] = (item.base_amount, item.base_rate, item.amount, item.rate)
                else: brands[brand] = (item.base_amount, item.margin_from_supplier_quotation / 100 * item.base_rate_without_profit_margin * item.qty, item.amount, item.margin_from_supplier_quotation / 100 * item.rate_without_profit_margin * item.qty)
            else: 
                if item.base_rate_without_profit_margin == 0 and item.base_rate > 0:
                    brands[brand] = (brands[brand][0] + item.base_amount, brands[brand][1] + item.base_rate, brands[brand][2] + item.amount, brands[brand][3] + item.rate)
                else: brands[brand] = (brands[brand][0] + item.base_amount, brands[brand][1] + (item.margin_from_supplier_quotation / 100 * item.base_rate_without_profit_margin * item.qty), brands[brand][2] + item.amount, brands[brand][3] + (item.margin_from_supplier_quotation / 100 * item.rate_without_profit_margin * item.qty))

        # for p_item in self.get("packed_items"):
        #     brand = p_item.brand or frappe.db.get_value("Item", p_item.item_code, "brand")
        #     if not brand: brand = "Unknown"
        #     if not brands.get(brand):
        #         if p_item.base_rate_without_profit_margin == 0 and item.base_rate > 0:
        #             brands[brand] = (item.base_amount, item.base_rate, item.amount, item.rate)
        #         else: brands[brand] = (item.base_amount, item.margin_from_supplier_quotation / 100 * item.base_rate_without_profit_margin * item.qty, item.amount, item.margin_from_supplier_quotation / 100 * item.rate_without_profit_margin * item.qty)
        #     else: 
        #         if item.base_rate_without_profit_margin == 0 and item.base_rate > 0:
        #             brands[brand] = (brands[brand][0] + item.base_amount, brands[brand][1] + item.base_rate, brands[brand][2] + item.amount, brands[brand][3] + item.rate)
        #         else: brands[brand] = (brands[brand][0] + item.base_amount, brands[brand][1] + (item.margin_from_supplier_quotation / 100 * item.base_rate_without_profit_margin * item.qty), brands[brand][2] + item.amount, brands[brand][3] + (item.margin_from_supplier_quotation / 100 * item.rate_without_profit_margin * item.qty))

        quarter = "Q" + str(get_quarter(today_qq[0]))
        if frappe.db.exists("Marketing Quarter Quota", {"year": today_qq[1], "quarter": quarter, "docstatus": 1}):
            # Assign Each Brand with its Product Manager
            qq = frappe.get_doc("Marketing Quarter Quota", {"year": today_qq[1], "quarter": quarter, "docstatus": 1})   
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
                            "total_quota": brands[brand][1],
                            "total_quota_in_order_currency": brands[brand][3]
                        }))
                        found = True
                        qq.brands.remove(row)
                        break
                
                if not found:
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
        "docstatus": 1}, "commission_percentage") or 5

    primary_commission = frappe.db.get_value("Quarter Quota", {
        "sales_man": leaders[0], 
        "quarter": "Q"+ str(quarter), 
        "year": year, 
        "docstatus": 1}, "primary_commission_percentage") or 1.5

    secondary_commission = frappe.db.get_value("Quarter Quota", {
        "sales_man": leaders[1], 
        "quarter": "Q"+ str(quarter), 
        "year": year, 
        "docstatus": 1}, "secondary_commission_percentage") or 0.75

    return {"commission_percentage": commission_percentage, 
            "primary_supervisor": leaders[0],
            "secondary_supervisor": leaders[1],
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