// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt
//this file is updated copy of apps/erpnext/erpnext/selling/doctype/sales_order/sales_order.js to add Bundle Delivery Note button
{% include 'erpnext/selling/doctype/sales_order/sales_order.js' %}
{% include 'sabaintegration/selling/costs.js' %}

frappe.provide("sabaintegration.costs")

frappe.ui.form.on("Sales Order", {
	setup: function(frm) {
		frm.custom_make_buttons['Bundle Delivery Note'] = 'Bundle Delivery Note'
	},
	items_on_form_rendered: function(){
		if (['erp@saba-eg.com', 'hossam@saba-eg.com', 'hayam@saba-eg.com', 'm.anas@saba-eg.com', 'nesma@saba-eg.com'].includes(frappe.session.user))
			cur_frm.cur_grid.set_field_property('rate_without_profit_margin', 'read_only', 0)
	},

});

erpnext.selling.CustomSalesOrderController = class CustomSalesOrderController extends erpnext.selling.SalesOrderController{

	refresh(doc, dt, dn) {
		super.refresh(doc, dt, dn);
		this.set_dynamic_labels();
		if (doc.docstatus==1 && doc.status !== 'Closed' && doc.status !== 'On Hold') {
			if(flt(doc.per_delivered, 6) < 100 ) {
				if (this.frm.doc.packed_items){
					this.frm.add_custom_button(__('Bundle Delivery Note'), () => this.make_bundle_delivery_note(), __('Create'));
				}
			}
		}
	}

	currency() {
		super.currency();
		this.set_dynamic_labels();
	}

	selling_price_list() {
		this.apply_price_list();
		this.set_dynamic_labels();
	}
	price_list_currency() {
		super.price_list_currency();
		this.set_dynamic_labels();
	}
	set_dynamic_labels() {
		// What TODO? should we make price list system non-mandatory?
		this.frm.toggle_reqd("plc_conversion_rate",
			!!(this.frm.doc.price_list_name && this.frm.doc.price_list_currency));

		var company_currency = this.get_company_currency();
		this.change_form_labels(company_currency);
		this.change_grid_labels(company_currency);
		this.frm.refresh_fields();
	}

	change_grid_labels(company_currency) {
		super.change_grid_labels(company_currency);
		this.frm.set_currency_labels(["base_total_rate_without_markup", "base_total_items_markup_value",
			"base_expected_profit_loss_value", "base_total_costs", "base_total_costs_with_material_costs"], company_currency);
		
		this.frm.set_currency_labels(["total_rate_without_margin", "total_items_markup_value",
			"expected_profit_loss_value", "total_costs", "total_costs_with_material_costs"], this.frm.doc.currency);

		// toggle fields
		this.frm.toggle_display(["base_total_rate_without_markup", "base_total_items_markup_value",
			"base_expected_profit_loss_value", "base_total_costs", "base_total_costs_with_material_costs"], this.frm.doc.currency != company_currency);

		// this.frm.toggle_display(["total_rate_without_margin", "total_items_markup_value",
		// 	"expected_profit_loss_value"], this.frm.doc.price_list_currency != company_currency);
	}
	additional_discount_percentage() {
		this.frm.cscript.calculate_taxes_and_totals();
		sabaintegration.set_cost_value()
		sabaintegration.update_costs()
	}

	apply_discount_on(){
		this.frm.cscript.calculate_taxes_and_totals();
		sabaintegration.set_cost_value()
		sabaintegration.update_costs()
	}

	discount_amount(){
		this.frm.cscript.calculate_taxes_and_totals();
		sabaintegration.set_cost_value()
		sabaintegration.update_costs()
	}

	make_bundle_delivery_note(){
		var me = this;
		me.setup_items(me, async (frm, data, items) => {
			frappe.call({
				method: "sabaintegration.overrides.sales_order.make_bdn",
				args: {
					sales_order: me.frm.doc.name,
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
	async setup_items(me, callback){
		let items = [];
		let itemslist = await frappe.call({
			"method": "sabaintegration.sabaintegration.doctype.bundle_delivery_note.bundle_delivery_note.get_reminded_bundle_items",
			"args": {
				"sales_order_name": me.frm.doc.name
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
	async total_margin(){
		var me = this;
		if (me.frm.doc.items){
			await $.each(me.frm.doc.items || [], function(i, d) {
				d.margin_from_supplier_quotation = me.frm.doc.total_margin;
				d.rate = d.rate_without_profit_margin + (d.rate_without_profit_margin * d.margin_from_supplier_quotation  / 100)
				d.amount = d.rate * d.qty;
			});
			cur_frm.cscript.calculate_taxes_and_totals();
			me.frm.doc.total_items_markup_value = me.frm.doc.total - me.frm.doc.total_rate_without_margin
			me.frm.doc.base_total_items_markup_value = me.frm.doc.total_items_markup_value * me.frm.doc.conversion_rate
			sabaintegration.set_cost_value()
			sabaintegration.update_costs()
		}
	}
	costs_template(){
		var me = this;
		if(this.frm.doc.costs_template) {
			return this.frm.call({
				method: "sabaintegration.overrides.quotation.get_costs",
				args: {
					"costs_template": this.frm.doc.costs_template
				},
				callback: function(r) {
					if(!r.exc) {
						me.frm.set_value("costs", r.message);
						sabaintegration.set_cost_value()
						sabaintegration.update_costs()
					}
				}
			});
		}
	}

}

extend_cscript(cur_frm.cscript, new erpnext.selling.CustomSalesOrderController({frm: cur_frm}));

frappe.ui.form.on('Sales Order Item', {
	items_remove: function(frm){
		sabaintegration.set_total_without_margin(frm);
		sabaintegration.calculate_total_margin(frm);
	},
	margin_from_supplier_quotation: function(frm,cdt,cdn){
		var d = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "rate", d.rate_without_profit_margin + (d.margin_from_supplier_quotation / 100 * d.rate_without_profit_margin))
		//frappe.model.set_value(cdt, cdn, "price_list_rate", d.rate_without_profit_margin + (d.margin_from_supplier_quotation / 100 * d.rate_without_profit_margin))
		sabaintegration.calculate_total_margin(frm);
	},
	rate: function(frm,cdt,cdn){
		var d = locals[cdt][cdn];
		if (!d.rate_without_profit_margin || d.rate_without_profit_margin == undefined || d.rate_without_profit_margin == 'undefined'){
			d.rate_without_profit_margin = d.price_list_rate
		}
		d.margin_from_supplier_quotation = (d.rate - d.rate_without_profit_margin) / d.rate_without_profit_margin * 100 
		sabaintegration.set_total_without_margin(frm);
		sabaintegration.calculate_total_margin(frm);
	},
	qty: function(frm, cdt, cdn){
		sabaintegration.set_total_without_margin(frm);
		sabaintegration.calculate_total_margin(frm);		
	},
	rate_without_profit_margin: function(frm, cdt, cdn){
		var d = locals[cdt][cdn];
		var margin_from_supplier_quotation = (d.rate - d.rate_without_profit_margin) / d.rate_without_profit_margin * 100 
		frappe.model.set_value(cdt, cdn, "margin_from_supplier_quotation", margin_from_supplier_quotation)
		sabaintegration.set_total_without_margin(frm);
		sabaintegration.calculate_total_margin(frm);
	}
})
frappe.ui.form.on('Cost', {
	cost_value: function(frm, cdt, cdn){
		var d = locals[cdt][cdn];
		if (d.cost_value == 0) frappe.model.set_value(cdt, cdn, "cost_percentage", 0)
		d.cost_percentage = d.cost_value / frm.doc.net_total * 100;
		sabaintegration.update_costs()
	},
	cost_percentage: function(frm, cdt, cdn){
		var d = locals[cdt][cdn];
		d.cost_value = frm.doc.net_total * d.cost_percentage / 100;
		d.base_cost_value = d.cost_value * frm.doc.conversion_rate;
		sabaintegration.update_costs()
	},
	costs_remove: function(frm, cdt, cdn){
		sabaintegration.update_costs()
	}
})

// frappe.ui.form.on('Sales Commission', {
// 	sales_person: function(frm, cdt, cdn){
// 		let d = locals[cdt][cdn];
// 		frappe.model.set_value(cdt, cdn, "comm_percent", 5);
// 		get_default_rule(d);
// 	},
// 	profits_quota: function(frm, cdt, cdn){
// 		let d = locals[cdt][cdn];
// 		if (d.achieve_percent !== undefined) {
// 			d.achieve_value = d.profits_quota * d.achieve_percent / 100;
// 			calculate_commission(d);
// 		}
// 	},
// 	achieve_percent: function(frm, cdt, cdn){
// 		let d = locals[cdt][cdn];
// 		if (d.profits_quota !== undefined) d.achieve_value = d.profits_quota * d.achieve_percent / 100;
// 		cur_frm.refresh_field("sales_commission");
// 		calculate_commission(d);
// 	},
// 	achieve_value: function(frm, cdt, cdn){
// 		let d = locals[cdt][cdn];
// 		if (d.profit_quota !== undefined) d.achieve_percent = d.achieve_value / d.profits_quota * 100;
// 		cur_frm.refresh_field("sales_commission");
// 		calculate_commission(d);
// 	},
// 	rule: function(frm, cdt, cdn){
// 		let d = locals[cdt][cdn];
// 		if (d.achieve_percent !== undefined) calculate_commission(d);
// 	},
// 	comm_percent: function(frm, cdt, cdn){
// 		let d = locals[cdt][cdn];
// 		if (d.achieve_percent !== undefined) calculate_commission(d);
// 	},
	
// })

// const get_default_rule = function(row){
// 	frappe.call({
// 		method: "sabaintegration.sabaintegration.doctype.commission_rule.commission_rule.get_default_rule",
// 		callback: function(r){
// 			if (r.message){
// 				row.rule = r.message;
// 				cur_frm.refresh_field("sales_commission");
// 			}
// 		}
		
// 	})	
// }

// const calculate_commission = function(row){
	
// 	if (row.comm_percent === undefined || row.rule === undefined || row.profits_quota === undefined) return;
// 	let args = {
// 		"comm_percent" : row.comm_percent,
// 		"rule": row.rule,
// 		"achieve_percent": row.achieve_percent,
// 		"achieve_value": row.achieve_value
// 	}
// 	frappe.call({
// 		method: "sabaintegration.overrides.sales_order.calculate_commission_value",
// 		args: {
// 			"args": args
// 		},
// 		callback: function(r){
// 			if (r.message){
// 				row.commission_value = r.message;
// 				cur_frm.refresh_field("sales_commission");
// 			}
// 		}

// 	})

// }