// Copyright (c) 2022, Ahmad and contributors
// For license information, please see license.txt
//{% include 'erpnext/selling/sales_common.js' %};
frappe.provide("erpnext");
frappe.provide("erpnext.utils");

frappe.provide("sabaintegration.utils");
{% include 'sabaintegration/public/js/utils/utils.js' %}

frappe.ui.form.on('Bundle Delivery Note', {
	setup: function(frm){
		frm.set_df_property('excluded_items', 'cannot_add_rows', true);
		frm.set_df_property('excluded_items', 'cannot_delete_rows', true);
	},
	onload: function(frm){
		if(frm.is_new()){
			frm.set_df_property('excluded_items', 'hidden', 1)
		}
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
		frm.set_query("item_code", "parents_items", function(doc, cdt, cdn) {
			return {
				filters:{
					"is_stock_item": 0,
					"is_sales_item": 1
				}
			}
		});
		frm.set_query("item_code", "stock_entries", function(doc, cdt, cdn) {
			return {
				query:"sabaintegration.sabaintegration.doctype.bundle_delivery_note.bundle_delivery_note.get_bundle_items",
				filters: {
					"parent":frm.doc.item_parent
				}
			}
		}); 	
		
	},
	refresh: function(frm) {
		if(frm.is_new()){
			frm.set_df_property('excluded_items', 'hidden', 1)
		}else if (!frm.doc.is_return){
			frm.set_df_property('excluded_items', 'hidden', 0)
		}
		erpnext.hide_company();
		if (frm.doc.docstatus == 0 && frm.doc.is_return == 0){
			frm.add_custom_button(__('Get Items'), function () {
				frm.trigger("get_items");
			});
			if(!frm.is_new() && frm.doc.is_return == 0){
				frm.add_custom_button(__('Exclude Items'), function () {
					frm.trigger("exclude_items")
				});
			}
		}
		else if (frm.doc.docstatus == 1 && frm.doc.is_return == 0){
			frm.add_custom_button('Bundle Return', function () {
				frm.trigger("bundle_return");
			}, "Create");
		}
	},
	validate: function(frm){
		if (frm.doc.multiple_items == 1){
			frm.doc.item_parent = ""
		}
		else{
			frm.doc.parents_items = []
		}
	},
	default_warehouse(frm){
        $.each(frm.doc.stock_entries || [], function(i, d) {
			d.warehouse = frm.doc.default_warehouse;
		});
		frm.refresh_field("stock_entries");
	},
	get_items: function(frm){
		let items = []
		if (frm.doc.multiple_items == 0) items.push(frm.doc.item_parent);
		else {
			for (let item of frm.doc.parents_items){
				items.push(item.item_code);
			}
		}
		let itemsPromise = new Promise(function(resolve){
			frm.events.set_items(frm, items, resolve)
		})
		itemsPromise.then(value =>{
			frm.refresh_field("stock_entries");
		})

	},

	set_items: function(frm, items , resolve) {
		frappe.call({
			method: "sabaintegration.sabaintegration.doctype.bundle_delivery_note.bundle_delivery_note.get_items",
			args: {
				sales_order: frm.doc.sales_order,
				parents : items, 
			},
			freeze: true,
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

	exclude_items: function(frm) {
		frm.events.setup_excluded_items(frm, async (frm, data, items) => {
			frappe.call({
				method: "sabaintegration.sabaintegration.doctype.bundle_delivery_note.bundle_delivery_note.update_items",
				args: {
					stock_entries: frm.doc.stock_entries,
					excluded_items: items,
					sales_order: frm.doc.sales_order,	
					price_list: frm.doc.price_list,
					company: frm.doc.company
				},
				freeze: true,
				callback: function(r) {
					if(r.message) {
						if (r.message.stock_entries)
						{
							frm.clear_table("stock_entries");
							frm.refresh_field("stock_entries");
							r.message.stock_entries.forEach((row) => {
								let item = frm.add_child("stock_entries");
								//$.extend(item, row);
								item.item_code = row.item_code;
								item.item_name = row.item_name;								
								item.qty = row.qty;
								item.warehouse = row.warehouse || '';
								item.uom = row.uom;
								item.rate = row.rate;
								item.currency = row.currency;
								
							});
							frm.refresh_field("stock_entries");

							// update Excluded Items
							items.forEach((row) => {
								let item = frm.add_child("excluded_items");
								item.parent_item = row.parent_item;
								item.item_code = row.item_code;
								item.alt_item = row.alt_item;
								item.warehouse = row.warehouse;
								frm.events.get_qty(frm, item)
								if (item.alt_item) frm.events.get_alt_details(frm, item)
								
							});
							frm.refresh_field("excluded_items");
						}
						frm.dirty();
					}
				}
			});
		})
	},
	bundle_return: function(){
		frappe.model.open_mapped_doc({
			method: "sabaintegration.sabaintegration.doctype.bundle_delivery_note.bundle_delivery_note.create_return_bdn",
			frm: cur_frm
		})
	},
	setup_excluded_items: function(frm , callback) {
		let me = this;		
		const field = [
			{	
				"fieldtype": "Table",
				"label": __("Excluded Items"),
				"fieldname": "items",
				"fields": [
					{
						fieldname: "parent_item",
						options: "Item",
						label: __("Parent Item"),
						fieldtype: "Link",
						in_list_view: 1,
						reqd: 1,
						get_query: (data) => {
							return {
								query:"sabaintegration.sabaintegration.doctype.bundle_delivery_note.bundle_delivery_note.get_parents_items",
								filters: {
									"parent": frm.doc.name,
									"item_parent":frm.doc.item_parent,
									"child_item": data.item_code
								}
							}	
						},
						change: function() {
							const item_code = this.grid_row.on_grid_fields_dict.item_code.get_value();
							const parent_item = this.get_value();

							if (item_code && parent_item){
								frappe.call({
									method: "sabaintegration.sabaintegration.doctype.bundle_delivery_note.bundle_delivery_note.get_item_qty",
									args: {
										sales_order: cur_frm.doc.sales_order,
										item_code: item_code,
										parent_item: parent_item
									},
									callback: (r) => {
										this.grid_row.on_grid_fields_dict
											.qty.set_value(r.message || 0);
									}
								})
							}
						}
					},
					{
						fieldname: "item_code",
						options: "Item",
						label: __("Item Code"),
						fieldtype: "Link",
						in_list_view: 1,
						reqd: 1,
						get_query: (data) => {							
							return {
								query:"sabaintegration.sabaintegration.doctype.bundle_delivery_note.bundle_delivery_note.get_packed_items",
								filters: {
									"parent": frm.doc.name,
									"parent_item": data.parent_item
								}
							}							
						},
						change: function() {
							const item_code = this.get_value();
							const parent_item = this.grid_row.on_grid_fields_dict.parent_item.get_value();

							if (item_code && parent_item){
								frappe.call({
									method: "sabaintegration.sabaintegration.doctype.bundle_delivery_note.bundle_delivery_note.get_item_qty",
									args: {
										sales_order: cur_frm.doc.sales_order,
										item_code: item_code,
										parent_item: parent_item
									},
									callback: (r) => {
										this.grid_row.on_grid_fields_dict
											.qty.set_value(r.message || 0);
									}
								})
							}
						}
					},
					{
						fieldname: "qty",
						label: __("Qty"),
						fieldtype: "Float",
						read_only: 1,
						in_list_view: 1,
					},
					{
						fieldname: "alt_item",
						options: "Item",
						label: __("Alternative Item"),
						fieldtype: "Link",
						in_list_view: 1,
						get_query: () => {
							return {
								filters: {
									"is_stock_item": 1 
								}
							};							
						}
					},
					{
						fieldname: "warehouse",
						options: "Warehouse",
						label: __("Warehouse"),
						fieldtype: "Link",
						in_list_view: 0,
					}
				],
			}
		];
		let dialog = frappe.prompt(field, data => {
			let items = data.items || [];		
			callback(frm, data, items);
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
		sabaintegration.utils.bdn.setup_serial_or_batch_no();
	},
	get_qty: function(frm, d) {
		frappe.call({
			method: "sabaintegration.sabaintegration.doctype.bundle_delivery_note.bundle_delivery_note.get_item_qty",
			args: {
				sales_order: frm.doc.sales_order,
				parent_item: d.parent_item, 
				item_code: d.item_code
			},
			callback: async function(r){
				if (r.message) {
					d.qty = r.message;
					frm.refresh_field("excluded_items");
				}
			}
		})	
	},
	get_alt_details: function(frm, d){
		let has_warehouse = true;
		if (!d.warehouse) has_warehouse = false;
		frappe.call({
			method: "sabaintegration.sabaintegration.doctype.bundle_delivery_note.bundle_delivery_note.get_alt_details",
			args: {
				item_code: d.alt_item,
				sales_order: frm.doc.sales_order,
				price_list: frm.doc.price_list, 
				company: frm.doc.company,
				has_warehouse: has_warehouse
			},
			callback: function(r){
				if (r.message){
					d.rate = r.message.rate;
					d.uom = r.message.uom
					d.currency = r.message.currency;
					d.item_name = r.message.item_name;
					if (!has_warehouse) d.warehouse = r.message.warehouse;
					frm.refresh_field("excluded_items");
				}
			}
		})
		frm.refresh_field("excluded_items");
	}
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

frappe.ui.form.on('Bundle Delivery Note Parent Item', {
	parents_items_remove: function(frm, cdt, cdn){
		frm.trigger("get_items")
	}
})
