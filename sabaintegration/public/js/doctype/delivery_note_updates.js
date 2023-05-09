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
		let sales_order = "";
		for (let i = 0; i < me.frm.doc.items.length; i++){
			if (me.frm.doc.items[i].against_sales_order !== undefined) {
				sales_order = me.frm.doc.items[i].against_sales_order
				break
			}
		}
		if (!sales_order) return
		me.setup_items(me, sales_order, async (frm, data, items) => {
			frappe.call({
				method: "sabaintegration.overrides.sales_order.make_bdn",
				args: {
					sales_order: sales_order,
					parents_items: data.parents_items
				},
				callback: function(r){
					if(!r.exc) {
						var doc = frappe.model.sync(r.message);
						frappe.set_route("Form", r.message.doctype, r.message.name);
					}
				}
			})
		})
		
	}
	async setup_items(me, sales_order, callback){
		let items = [];
		let itemslist = await frappe.call({
			"method": "sabaintegration.sabaintegration.doctype.bundle_delivery_note.bundle_delivery_note.get_reminded_bundle_items",
			"args": {
				"sales_order": sales_order
			},
			"freeze": true,
			callback: function(r){
				if (r.message) return r.message
				return 0
			}
		})
		for (let index in itemslist.message){
			items.push(itemslist.message[index].item_code)
		}
		var fields = [
			{
				"label" : "Parents Items",
				"fieldname": "parents_items",
				"fieldtype": "Table",
				"reqd": 1,
				"fields": [
					{
					"label" : "Parent Item",
					"fieldname": "item_code",
					"options": "Item",
					"fieldtype": "Link",
					"in_list_view": 1,
					"reqd": 1,
					"get_query": function() {
						return {
							filters: {'name': ["in", items] }
						}
					}
					}
				]

			}
		]
		let dialog = frappe.prompt(fields, data => {
			let parents_items = data.parents_items || [];
			callback(me, data, parents_items);
		})
		let i = 1;
		dialog.fields_dict.parents_items.df.data = [];
		for (let row of items){
			dialog.fields_dict.parents_items.df.data.push({"idx": i, "item_code": row});
			i += 1;
		}
		dialog.fields_dict.parents_items.grid.refresh();
	}
	
}

extend_cscript(cur_frm.cscript, new erpnext.stock.CustomDeliveryNoteController({frm: cur_frm}));
