// Copyright (c) 2022, Ahmad and contributors
// For license information, please see license.txt
//{% include 'erpnext/selling/sales_common.js' %};
frappe.provide("erpnext");
frappe.provide("erpnext.utils");

frappe.ui.form.on('Bundle Delivery Note', {
	onload: function(frm){
		frm.set_query("item_parent", function(doc){
			return {
				filters:{
					"is_stock_item": 0,
					"is_sales_item": 1
				}
			}
		})
		frm.set_query("sales_order", function(doc){
			return {
				filters:{
					"docstatus": 1
				}
			}
		})
		frm.set_query("item_code", "stock_entries", function(doc, cdt, cdn) {
			return {
				query:"sabaintegration.sabaintegration.doctype.bundle_delivery_note.bundle_delivery_note.get_bundle_items",
				filters: {'parent': doc.item_parent}
			}
		}); 
		frm.set_query("batch_no", "stock_entries", function(doc, cdt, cdn) {
			var item = locals[cdt][cdn];
			return {
				filters: {
					'item': item.item_code
				}
			};
		}); 
		
	},
	refresh: function(frm) {
		erpnext.hide_company();
		if (frm.doc.docstatus == 0){
			frm.add_custom_button(__('Get Items'), function () {
				frm.trigger("get_items");
			});
		}
	},
	item_parent: function(frm){
		let itemsPromise = new Promise(function(resolve){
			frm.events.set_items(frm, null,  resolve)
		})
		itemsPromise.then(value =>{
			frm.refresh_field("stock_entries");
		})
	},
	
	get_items: function(frm){
		var dialog = new frappe.ui.Dialog({
			title: __("Get Items"),
			fields: [
			{
				label: 'Item Code',
				fieldname: 'item_code',
				fieldtype: 'Link',
				options: 'Item',
				"get_query": function () {
					return {
						query:"sabaintegration.sabaintegration.doctype.bundle_delivery_note.bundle_delivery_note.get_bundle_items",
						filters: {'parent': frm.doc.item_parent}
					}
				}
			},
			]
		});
		dialog.set_primary_action(__("Submit"), function() {
			var data = dialog.get_values();
			let itemsPromise = new Promise(function(resolve){
				frm.events.set_items(frm, data.item_code, resolve)
			})
			itemsPromise.then(value =>{
				frm.refresh_field("stock_entries");
				dialog.hide();
			})
						
		})
		dialog.show();
	},

	set_items: function(frm, item_code = null, resolve) {
		frappe.call({
			method: "sabaintegration.sabaintegration.doctype.bundle_delivery_note.bundle_delivery_note.get_items",
			args: {
				sales_order: frm.doc.sales_order,
				item_parent : frm.doc.item_parent, 
				item_code: item_code
			},
			callback: function(r){
				if (r.exc || !r.message || !r.message.length) {
					resolve();
				}
				else{
					frm.clear_table("stock_entries");
					r.message.forEach((row) => {
						let item = frm.add_child("stock_entries");
						$.extend(item, row);
						item.item_code = item.item_code || ''
						item.qty = item.qty || 0;
						item.item_name = item.item_name || '';
						item.warehouse = item.warehouse || '';
						item.rate = item.rate || '';
						item.uom = item.uom || '';
						
					});
					resolve(true);
				}
				
			}
		})
	},

	set_rate_and_qty: function(frm, cdt, cdn) {
		var d = frappe.model.get_doc(cdt, cdn);
		frappe.model.set_value(cdt, cdn, "qty", 1);
		if (d.item_code && frm.doc.price_list){
			frappe.db.get_list("Packed Item", {
				filters: {'item_code': d.item_code, 'parent': frm.doc.sales_order}, 
				fields: ['*']}).then((doc) => {
				if (doc){
					frappe.model.set_value(cdt, cdn, "rate", doc[0].price_list_rate);
					frappe.model.set_value(cdt, cdn, "uom", doc[0].uom);
					frappe.model.set_value(cdt, cdn, "currency", doc[0].currency);
					frappe.model.set_value(cdt, cdn, "item_name", doc[0].item_name);
					if (doc[0].uom && doc[0].item_name) return
				}
				frappe.db.get_list("Sales Order", {
					filters: {'name': frm.doc.sales_order}, 
					fields: ['currency']}).then((item) => {
						frappe.model.set_value(cdt, cdn, "currency", item[0].currency);
				})
				
			})
		}
	},
	set_warehouse: function(frm, cdt, cdn){
		var d = frappe.model.get_doc(cdt, cdn);
		var doc = frappe.db.get_list("Packed Item", 
			{filters: {'parent': frm.doc.sales_order, 'item_code': d.item_code, 'parent_item': frm.doc.item_parent}, 
			fields: ['warehouse']}).then((doc) => {
				if (doc)
					frappe.model.set_value(cdt, cdn, "warehouse", doc[0].warehouse);
			})
	},
	sales_order: function(frm){
		frappe.db.get_value("Sales Order", frm.doc.sales_order, ["selling_price_list", "company", "project"], (r) => {
			frm.set_value("price_list", r.selling_price_list);
			frm.refresh_field("price_list");
			frm.set_value("company", r.company);
			frm.refresh_field("company");
			frm.set_value("project", r.project);
			frm.refresh_field("project");

		})
		let itemsPromise = new Promise(function(resolve){
			frm.events.set_items(frm, null,  resolve)
		})
		itemsPromise.then(value =>{
			frm.refresh_field("stock_entries");
		})
	},
	stock_entries_on_form_rendered: function() {
		erpnext.setup_serial_or_batch_no();
	},
});

frappe.ui.form.on('Bundle Delivery Note Item', {
	item_code: function(frm, cdt, cdn){
		frm.events.set_rate_and_qty(frm, cdt, cdn);
		frm.events.set_warehouse(frm, cdt, cdn);
	},
	qty: function(frm, cdt, cdn){
		let row = locals[cdt][cdn];
		if (row.rate){
			frappe.model.set_value(cdt, cdn, "amount", row.rate * row.qty);
		}
	},
	rate: function(frm, cdt, cdn){
		let row = locals[cdt][cdn];
		if (row.qty){
			frappe.model.set_value(cdt, cdn, "amount", row.rate * row.qty);
		}
	},
})
