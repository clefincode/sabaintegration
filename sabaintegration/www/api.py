import frappe

@frappe.whitelist()
def product_bundle_prevents(item):
    doc = frappe.db.get_list('Product Bundle',
    filters={
        'new_item_code': item
    },
    pluck='name'
    )
    if(doc):
        # print(doc[0])
        frappe.msgprint('There is a product bundle for this item ')
        return doc
    doc1 = frappe.db.get_list('Product Bundle Item',
    filters={
        'item_code': item
    },
    pluck='name'
    )
    
    if(doc1):
        # print(doc1[0])
        frappe.msgprint('There is a product bundle item that include this one as child')
        return doc1



@frappe.whitelist()
def product_bundle_item_prevents(item):
    doc = frappe.db.get_list('Product Bundle',
    filters={
        'new_item_code': item
    },
    pluck='name'
    )
    
    if(doc):
        # print(doc[0])
        frappe.msgprint('There is a product bundle for this item you selected as a child')
        return doc