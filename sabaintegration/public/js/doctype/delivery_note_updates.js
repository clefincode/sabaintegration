// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt
//this file is updated copy of apps/erpnext/erpnext/stock/doctype/delivery_note/delivery_note.js to add Bundle Delivery Note button
{% include 'erpnext/stock/doctype/delivery_note/delivery_note.js' %};

frappe.ui.form.on("Delivery Note", {
	setup: function(frm) {
        frm.custom_make_buttons['Bundle Delivery Note'] = 'Bundle Delivery Note'
	},
})
	
erpnext.stock.CustomDeliveryNoteController = class CustomDeliveryNoteController extends erpnext.stock.DeliveryNoteController{
	refresh(doc, dt, dn) {
		var me = this;
		super.refresh(doc, dt, dn);
		
		if (!doc.is_return && doc.status!="Closed") {
			if(doc.docstatus==0 && doc.packed_items) {
				this.frm.add_custom_button(__('Bundle Delivery Note'), () => this.make_bundle_delivery_note(), __('Create'));
			}

		}
	}

	make_bundle_delivery_note(){
		var me = this;
		let doc_items = me.frm.doc.items
		let items = []
		for (let item in doc_items){
			items.push(doc_items[item]['item_code'])
		}
		var d = new frappe.ui.Dialog({
			title: __('Create New Bundle Delivery Note'),
			fields: [
				{
					"label" : "Parent Item",
					"fieldname": "parent_item",
					"fieldtype": "Link",
					"reqd": 1,
					"options": "Item",
					"get_query": function() {
						return {
							filters: { 'is_stock_item': 0, 'name': ["in", items] }
						}
					}

				}
			],
			primary_action: function() {
				var data = d.get_values();
				frappe.db.get_list("Bundle Delivery Note", {
					filters: {
						'item_parent': data.parent_item,
						'docstatus': 0
					},
					fields: ['name']
				}).then((res) => {
					if (!res[0]){
						frappe.new_doc("Bundle Delivery Note", {
							"item_parent": data.parent_item
						});
					}
					else {
						frappe.set_route("Form", "Bundle Delivery Note", res[0])
					}
				});				
			}
		})
		d.show();
	}
	
}

extend_cscript(cur_frm.cscript, new erpnext.stock.CustomDeliveryNoteController({frm: cur_frm}));
