# # Copyright (c) 2024, Ahmad and contributors
# # For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    columns, data = get_columns(filters), get_data(filters)
    return columns, data

def get_columns(filters):
    columns =  [
        {
            "label": _("Project"),
            "fieldname": "project",
            "fieldtype" : "Link",
            "options": "Project",
            "width": 100,
        },
        # {
        #     "label": _("First Sales Order"),
        #     "fieldname": "first_sales_order",
        #     "fieldtype" : "Link",
        #     "options": "Sales Order",
        #     "width": 100,
        # },
        # {
        #     "label": _("Sales Order"),
        #     "fieldname": "sales_order",
        #     "fieldtype" : "Link",
        #     "options": "Sales Order",
        #     "width": 100,
        # },
        {
            "label": _("Section Title"),
            "fieldname": "section_title",
            "fieldtype" : "Data",
            "width": 100,
        },	        	
        {
            "label": _("Parent Item"),
            "fieldname": "parent_item",
            "fieldtype" : "Link",
            "options": "Item",
            "width": 100,
        },
        {
            "label": _("Original Quantity"),
            "fieldname": "original_parent_qty",
            "fieldtype" : "Int",
            "width": 75,
        },
        {
            "label": _("Updated Qty"),
            "fieldname": "updated_qty",
            "fieldtype" : "Int",
            "width": 75,
        },
        {
            "label": _("Last Update Date"),
            "fieldname": "last_update_date",
            "fieldtype" : "Date",
            "width": 150,
        },
        {
            "label": _("New SOs"),
            "fieldname": "new_so",
            "fieldtype" : "Data",
            "width": 75,
        },
        {
            "label": _("Change Percentage"),
            "fieldname": "change_percentage",
            "fieldtype" : "Float",
            "precision": 2,
            "width": 100,
        },
        {
            "label": _("Child Item"),
            "fieldname": "child_item",
            "fieldtype" : "Link",
            "options": "Item",
            "width": 100,
        },
        {
            "label": _("Quantity"),
            "fieldname": "child_qty",
            "fieldtype" : "Int",
            "width": 100,
        },
        {
            "label": _("Reserved Quantity"),
            "fieldname": "reserved_qty",
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("Projected Quantity"),
            "fieldname": "projected_qty",
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("Ordered Quantity"),
            "fieldname": "ordered_qty",
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("Remained Quantity"),
            "fieldname": "remained_qty",
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("Consultant Approval"),
            "fieldname": "consultant_approval",
            "fieldtype": "Data",
            "width": 50
        }
        
    ]

    return columns

def get_data(filters):	
    condition = ""
    if filters.get("project"):
        condition += f" AND project = '{filters.get('project')}'" 
    
    if filters.get("parent_item"):
        condition += f" AND project = '{filters.get('parent_item')}'"    
    
    results = frappe.db.sql(f"""
    SELECT
        soq.project,
        soq.sales_order,
        soqi.section_title,
        soqi.parent_item,
        NULL AS original_parent_qty,
        NULL AS updated_qty,
        soq.creation AS last_update_date,
        NULL AS new_so,
        NULL AS change_percentage,
        soqi.item_code AS child_item,
        soqi.required_qty AS child_qty,
        soqi.reserved_qty,
        soqi.projected_qty,
        soqi.ordered_qty,
        soqi.remained_qty,
        NULL AS consultant_approval,
        project.sales_order AS first_sales_order
    
    FROM `tabSales Order Qtys` AS soq 
        INNER JOIN `tabSales Order Qtys Item` AS soqi  ON soqi.parent = soq.name
        INNER JOIN `tabProject` AS project ON project.name = soq.project
    WHERE soq.is_cancelled = 0 AND soq.project IS NOT NULL {condition}
    """ , as_dict = True)

    prev_project = None
    prev_section_title = None
    prev_parent_item = None
    
    for row in results:              
        if row.first_sales_order and row.parent_item:            
            row.original_parent_qty = frappe.db.get_value("Sales Order Item" , {"parent": row.first_sales_order, "section_title" : row.section_title , "item_code" : row.parent_item} , "qty")
            row.updated_qty = frappe.db.get_value("Sales Order Item" , {"parent": row.sales_order, "section_title" : row.section_title , "item_code" : row.parent_item} , "qty")
            
            if row.original_parent_qty != 0:
                row.change_percentage = ((row.updated_qty / row.original_parent_qty) * 100) - 100

            new_so = frappe.get_all('Sales Order',
                filters={
                    'project': row.project,
                    'name': ['!=', row.first_sales_order]
                },
                fields=['name'])
            
            row.new_so = ' , '.join([f'<u>{frappe.utils.get_link_to_form("Sales Order", so["name"])}</u>' for so in new_so])


        if row.section_title == prev_section_title and row.parent_item == prev_parent_item:
            row.section_title = None
            row.parent_item = None
        else:
            prev_section_title = row.section_title
            prev_parent_item = row.parent_item

        if row.project == prev_project:
            row.project = ""
        else:
            prev_project = row.project
           
    return results
