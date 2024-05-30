// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt
//this file is updated copy of apps/erpnext/erpnext/stock/doctype/delivery_note/delivery_note.js to add Bundle Delivery Note button
{% include 'erpnext/stock/doctype/delivery_note/delivery_note.js' %};

frappe.ui.form.on("Delivery Note", {
	setup: function(frm) {
        frm.custom_make_buttons['Bundle Delivery Note'] = 'Bundle Delivery Note'
	},
})

erpnext.stock.DeliveryNoteController = class DeliveryNoteController extends erpnext.selling.SellingController {
	setup(doc) {
		this.setup_posting_date_time_check();
		super.setup(doc);
		this.frm.make_methods = {
			'Delivery Trip': this.make_delivery_trip,
		};
	}
	refresh(doc, dt, dn) {
		var me = this;
		super.refresh();
		if ((!doc.is_return) && (doc.status!="Closed" || this.frm.is_new())) {
			if (this.frm.doc.docstatus===0) {
				this.frm.add_custom_button(__('Sales Order'),
					function() {
						if (!me.frm.doc.customer) {
							frappe.throw({
								title: __("Mandatory"),
								message: __("Please Select a Customer")
							});
						}
						erpnext.utils.map_current_doc({
							method: "erpnext.selling.doctype.sales_order.sales_order.make_delivery_note",
							source_doctype: "Sales Order",
							target: me.frm,
							setters: {
								customer: me.frm.doc.customer,
							},
							get_query_filters: {
								docstatus: 1,
								status: ["not in", ["Closed", "On Hold"]],
								per_delivered: ["<", 99.99],
								company: me.frm.doc.company,
								// project: me.frm.doc.project || undefined,
							}
						})
					}, __("Get Items From"));
			}
		}

		if (!doc.is_return && doc.status!="Closed") {
			if(doc.docstatus == 1) {
				this.frm.add_custom_button(__('Shipment'), function() {
					me.make_shipment() }, __('Create'));
			}

			if(flt(doc.per_installed, 2) < 100 && doc.docstatus==1)
				this.frm.add_custom_button(__('Installation Note'), function() {
					me.make_installation_note() }, __('Create'));

			if (doc.docstatus==1) {
				this.frm.add_custom_button(__('Sales Return'), function() {
					me.make_sales_return() }, __('Create'));
			}

			if (doc.docstatus==1) {
				this.frm.add_custom_button(__('Delivery Trip'), function() {
					me.make_delivery_trip() }, __('Create'));
			}

			if(doc.docstatus==0 && !doc.__islocal) {
				this.frm.add_custom_button(__('Packing Slip'), function() {
					frappe.model.open_mapped_doc({
						method: "erpnext.stock.doctype.delivery_note.delivery_note.make_packing_slip",
						frm: me.frm
					}) }, __('Create'));
			}

			if (!doc.__islocal && doc.docstatus==1) {
				this.frm.page.set_inner_btn_group_as_primary(__('Create'));
			}
		}

		if (doc.docstatus > 0) {
			this.show_stock_ledger();
			if (erpnext.is_perpetual_inventory_enabled(doc.company)) {
				this.show_general_ledger();
			}
			if (this.frm.has_perm("submit") && doc.status !== "Closed") {
				me.frm.add_custom_button(__("Close"), function() { me.close_delivery_note() },
					__("Status"))
			}
		}

		if(doc.docstatus==1 && !doc.is_return && doc.status!="Closed" && flt(doc.per_billed) < 100) {
			// show Make Invoice button only if Delivery Note is not created from Sales Invoice
			var from_sales_invoice = false;
			from_sales_invoice = me.frm.doc.items.some(function(item) {
				return item.against_sales_invoice ? true : false;
			});

			if(!from_sales_invoice) {
				this.frm.add_custom_button(__('Sales Invoice'), function() { me.make_sales_invoice() },
					__('Create'));
			}
		}

		if(doc.docstatus==1 && doc.status === "Closed" && this.frm.has_perm("submit")) {
			this.frm.add_custom_button(__('Reopen'), function() { me.reopen_delivery_note() },
				__("Status"))
		}
		erpnext.stock.delivery_note.set_print_hide(doc, dt, dn);

		if(doc.docstatus==1 && !doc.is_return && !doc.auto_repeat) {
			cur_frm.add_custom_button(__('Subscription'), function() {
				erpnext.utils.make_subscription(doc.doctype, doc.name)
			}, __('Create'))
		}
	}

	make_shipment() {
		frappe.model.open_mapped_doc({
			method: "erpnext.stock.doctype.delivery_note.delivery_note.make_shipment",
			frm: this.frm
		})
	}

	make_sales_invoice() {
		frappe.model.open_mapped_doc({
			method: "erpnext.stock.doctype.delivery_note.delivery_note.make_sales_invoice",
			frm: this.frm
		})
	}

	make_installation_note() {
		frappe.model.open_mapped_doc({
			method: "erpnext.stock.doctype.delivery_note.delivery_note.make_installation_note",
			frm: this.frm
		});
	}

	make_sales_return() {
		frappe.model.open_mapped_doc({
			method: "erpnext.stock.doctype.delivery_note.delivery_note.make_sales_return",
			frm: this.frm
		})
	}

	make_delivery_trip() {
		frappe.model.open_mapped_doc({
			method: "erpnext.stock.doctype.delivery_note.delivery_note.make_delivery_trip",
			frm: cur_frm
		})
	}

	tc_name() {
		this.get_terms();
	}

	items_on_form_rendered(doc, grid_row) {
		erpnext.setup_serial_or_batch_no();
	}

	packed_items_on_form_rendered(doc, grid_row) {
		erpnext.setup_serial_or_batch_no();
	}

	close_delivery_note(doc){
		this.update_status("Closed")
	}

	reopen_delivery_note() {
		this.update_status("Submitted")
	}

	update_status(status) {
		var me = this;
		frappe.ui.form.is_saving = true;
		frappe.call({
			method:"erpnext.stock.doctype.delivery_note.delivery_note.update_delivery_note_status",
			args: {docname: me.frm.doc.name, status: status},
			callback: function(r){
				if(!r.exc)
					me.frm.reload_doc();
			},
			always: function(){
				frappe.ui.form.is_saving = false;
			}
		})
	}
};

extend_cscript(cur_frm.cscript, new erpnext.stock.DeliveryNoteController({frm: cur_frm}));
	
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
