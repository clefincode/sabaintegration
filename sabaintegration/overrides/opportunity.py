import json

import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cint

from erpnext.stock.doctype.packed_item.packed_item import get_product_bundle_items
from erpnext.crm.doctype.opportunity.opportunity import Opportunity
from frappe.utils import nowdate

from sabaintegration.stock.get_item_details import get_item_warehouse

class CustomOpportunity(Opportunity):
    @frappe.whitelist()
    def group_similar_bundle_items(self):
        """group packed items with the same item code in one row
        with the sum of the quatities"""
        import copy
        group_items= {}
        brand_list = {}
        #parent_items= {}
        count = 0
        bundles = []
        for item in self.parent_items:
            if not item.qty : item.qty = 0
            group_items[item.item_code] = group_items.get(item.item_code, 0) + item.qty
            brand_list[item.item_code] = frappe.db.get_value("Item", item.item_code, "brand")
            #parent_items[item.item_code] =parent_items.get(item.item_code, '') + "<a href='/app/item/"+item.parent_item+"' data-doctype='Item' target='_blank' data-name='"+item.parent_item+"' data-original-title='' title=''>"+item.parent_item+"</a> <br>"  

        brand_list = sorted(brand_list.items(), key=lambda x:x[1]) 
        for item in brand_list:
            bundles.append({
                "item_code": item[0],
                "qty": group_items[item[0]],
                "uom": frappe.db.get_value("Item", item[0], "stock_uom"),
                "description": frappe.db.get_value("Item", item[0], "description"),
                "brand": item[1],
                "warehouse": get_item_warehouse(frappe.get_doc("Item", item[0]), args = frappe._dict({"company": self.company}), overwrite_warehouse = True)
            })
        # duplicate_list = []
        # for item in bundles:
        #     key = item.item_code
        #     if key in group_items:
        #         count += 1
        #         item.qty = group_items[key]                
        #         item.idx = count
        #         del group_items[key]
        #     else:
        #         duplicate_list.append(item)
                
        # for item in duplicate_list:
        #     bundles.remove(item)
        #print(f"\033[92m {bundles}")
        return bundles

    def validate(self):
        self._prev = frappe._dict(
            {
                "contact_date": frappe.db.get_value("Opportunity", self.name, "contact_date")
                if (not cint(self.get("__islocal")))
                else None,
                "contact_by": frappe.db.get_value("Opportunity", self.name, "contact_by")
                if (not cint(self.get("__islocal")))
                else None,
            }
        )

        self.make_new_lead_if_required()

        self.validate_item_details()
        self.validate_uom_is_integer("uom", "qty")
        self.validate_cust_name()
        self.map_fields()

        if not self.title:
            self.title = self.customer_name

        if not self.with_items:
            self.items = []

        #self.validate_items() ###Custom Update
        self.set_option_number() ###Custmo Update

    def validate_items(self):
        def _get_msg(row_num, msg):
            return _("Row # {0}:").format(row_num + 1) + " " + msg
        
        self.validation_messages = []
        items = []
        for row_num, row in enumerate(self.items):
            # find duplicates
            key = [row.item_code]

            if key in items:
                self.validation_messages.append(_get_msg(row_num, _("Duplicate entry")))
            else:
                items.append(key)
        errmsg = ""
        if self.validation_messages:
            for msg in self.validation_messages:
                errmsg += msg + "<br>"
        if errmsg: 
            frappe.msgprint(errmsg)
            raise frappe.ValidationError(self.validation_messages)

    def set_option_number(self):
        "set the option field in each option if it's null"
        if self.option_1:
            for op in self.option_1:
                if not op.option_number: op.option_number = 1
        if self.option_2:
            for op in self.option_2:
                if not op.option_number: op.option_number = 2 
        if self.option_3:
            for op in self.option_3:
                if not op.option_number: op.option_number = 3
        if self.option_4:
            for op in self.option_4:
                if not op.option_number: op.option_number = 4
        if self.option_5:
            for op in self.option_5:
                if not op.option_number: op.option_number = 5
        if self.option_6:
            for op in self.option_6:
                if not op.option_number: op.option_number = 6
        if self.option_7:
            for op in self.option_7:
                if not op.option_number: op.option_number = 7
        if self.option_8:
            for op in self.option_8:
                if not op.option_number: op.option_number = 8
        if self.option_9:
            for op in self.option_9:
                if not op.option_number: op.option_number = 9
        if self.option_10:
            for op in self.option_10:
                if not op.option_number: op.option_number = 10
    
@frappe.whitelist()
def get_item_details(item_code, company = None):
    """get item_name, uom, description, image, item_group,
     brand and warehouse of the item"""
    item = frappe.db.sql(
        """select item_name, stock_uom, image, description, item_group, brand
        from `tabItem` where name = %s""",
        item_code,
        as_dict=1,
    )
    warehouse = ""
    if company: warehouse = get_item_warehouse(frappe.get_doc("Item", item_code), args = frappe._dict({"company": company}), overwrite_warehouse = True)
    return {
        "item_name": item and item[0]["item_name"] or "",
        "uom": item and item[0]["stock_uom"] or "",
        "description": item and item[0]["description"] or "",
        "image": item and item[0]["image"] or "",
        "item_group": item and item[0]["item_group"] or "",
        "brand": item and item[0]["brand"] or "",
        "warehouse": warehouse or ""
    }

@frappe.whitelist()
def make_request_for_quotation(source_name, target_doc=None):
    def update_item(obj, target, source_parent):
        target.conversion_factor = 1.0

    op_num = frappe.db.get_value("Opportunity Item", {"parent": source_name}, "option_number")
    if not frappe.db.exists("Request for Quotation Item", {"opportunity": source_name, "opportunity_option_number": op_num, "docstatus": ("!=", 2)}):
        doclist = get_mapped_doc(
            "Opportunity",
            source_name,
            {
                "Opportunity": {
                    "doctype": "Request for Quotation",
                    },
                "Opportunity Item":{
                    "doctype": "Request for Quotation Item",
                    "field_map": [ ["parent", "opportunity"], ["uom", "uom"], ["option_number", "opportunity_option_number"]],
                    "postprocess": update_item,
                }
            },
            target_doc,
        )
        doclist.update({"packed_items" : doclist.make_packing_list()})
    else:
        
        doclist = get_mapped_doc(
            "Opportunity",
            source_name,
            {
                "Opportunity": {
                    "doctype": "Request for Quotation",
                    },
            }
        )
        req_packed_items = frappe.db.sql("""
        select packed_item.item_code, packed_item.qty, rfg.name as parent
        from `tabRequest for Quotation Item` as item
        inner join `tabRequest for Quotation` as rfg on rfg.name = item.parent
        inner join `tabRequest for Quotation Packed Item` as packed_item on packed_item.parent = rfg.name 
        where item.opportunity = '{0}' and item.opportunity_option_number = {1} and item.docstatus != 2
        group by packed_item.item_code, packed_item.qty
        """.format(source_name, op_num), as_dict = 1)

        opportunity = frappe.get_doc("Opportunity", source_name)
        bundles = opportunity.group_similar_bundle_items()
        for bundle in bundles:
            found = False
            existsitems = []
            for packed_item in req_packed_items:
                if packed_item.item_code == bundle.get("item_code") and packed_item.qty == bundle.get("qty"):
                    found = True
                    break
                elif packed_item.item_code == bundle.get("item_code") and packed_item.qty < bundle.get("qty"):
                    bundle["qty"] -= packed_item.qty
                    if bundle.get("qty") == 0:
                        found = True
                        break
                    items = frappe.db.get_all("Request for Quotation Item", {"parent" : packed_item.parent}, ["item_code"])
                    for item in items:
                        if frappe.db.exists("Product Bundle", {"new_item_code": item.item_code}):
                            for bundle_item in get_product_bundle_items(item.item_code):
                                if bundle_item.item_code == packed_item.item_code:
                                    existsitems.append(item.item_code)
                                    break
                    
                    
            #print(f"\033[93m {bundle.get('item_code')}")
            
            if not found:
                add_item_to_table(bundle, "packed_items", doclist)

                items = frappe.db.get_all("Opportunity Packed Parent Item", {"parent":source_name, "item_code": bundle.get("item_code")}, ["parent_item"])
                for item in items:
                    if (item.parent_item in existsitems): continue
                    
                    item = frappe.get_doc("Opportunity Item", {"parent": source_name, "item_code":item.parent_item})
                    toadd = True
                    for ritem in doclist.get("items"):
                        if ritem.item_code == item.item_code:
                            toadd = False
                            break
                    if toadd:
                        fields = {
                            "stock_uom": item.uom or item.get("stock_uom") or frappe.db.get_value("Item", item.get("item_code"), "stock_uom"),
                            "conversion_factor": 1.00,
                            "image": item.image or frappe.db.get_value("Item", item.item_code, "image"),
                            "opportunity": item.parent,
                            "opportunity_option_number": item.option_number
                        }
                        add_item_to_table(item, "items", doclist, fields)

        items = frappe.db.sql("""
        select item.item_code, item.item_name, item.qty, item.uom, item.warehouse,
        item.description, item.brand, item.image, item.parent, item.option_number
        from `tabItem`
        inner join `tabOpportunity Item` as item on item.item_code = `tabItem`.item_code
        left outer join `tabRequest for Quotation Item` as rfqi on item.item_code = rfqi.item_code and rfqi.opportunity = item.parent and rfqi.opportunity_option_number = item.option_number
        where  `tabItem`.is_stock_item = 1 and item.parent = '{}' and rfqi.item_code is null 
        """.format(source_name), as_dict = 1)

        for item in items:
            fields = {
                "stock_uom": item.uom or item.get("stock_uom") or frappe.db.get_value("Item", item.get("item_code"), "stock_uom"),
                "conversion_factor": 1.00,
                "image": item.image or frappe.db.get_value("Item", item.item_code, "image"),
                "opportunity": item.parent,
                "opportunity_option_number": item.option_number
            }
            add_item_to_table(item, "items", doclist, fields)
        
    return doclist

def add_item_to_table(item, table = None, doc = None, other_fields = None):
    """add item to table in a doctype
    the default fields are item_code, item_name, qty, uom, warehouse,
    description and brand. to add other fields, you can send a dict
    with the other_fields paremater"""
    fields = {
            "item_code":item.get("item_code"),
            "item_name":item.get("item_name"),
            "qty": item.get("qty"),
            "uom":item.get("uom") or item.get("stock_uom") or frappe.db.get_value("Item", item.get("item_code"), "stock_uom"),
            "warehouse":item.get("warehouse") or frappe.db.get_value("Item Default", {"parent" : item.get("item_code")}, "default_warehouse"),
            "description":item.get("description") or frappe.db.get_value("Item", item.get("item_code"), "description"),
            "brand": item.get("brand") or frappe.db.get_value("Item", item.get("item_code"), "brand"),
            }
    if other_fields:
        for field_name in other_fields:
            fields[field_name] = other_fields[field_name]
    
    if doc and table: doc.append(table, fields) # If doctype has table
    elif doc and not table: doc.append(fields) # If doctype is child table
    else: table.append(fields) # if it's not a doctype (just a list)
