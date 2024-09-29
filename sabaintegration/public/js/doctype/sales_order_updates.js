// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt
//this file is updated copy of apps/erpnext/erpnext/selling/doctype/sales_order/sales_order.js to add Bundle Delivery Note button
{% include 'erpnext/selling/doctype/sales_order/sales_order.js' %}
{% include 'sabaintegration/selling/costs.js' %}

frappe.provide("sabaintegration.costs")

frappe.ui.form.on("Sales Order", {
	setup: function (frm) {
		frm.custom_make_buttons = {
			'Bundle Delivery Note': 'Bundle Delivery Note',
			'Sales Order': 'Update Qtys'
		}
	},
	onload: function (frm) {
		frm.set_query("primary_sales_man", function () {
			return {
				query: "sabaintegration.overrides.sales_order.get_sales_person",
			};
		});
		frm.set_query("sales_person", "sales_commission", function () {
			return {
				query: "sabaintegration.overrides.sales_order.get_sales_person",
			};
		});
		frm.set_query("engineer", "pre_sales_activities", function () {
			return {
				query: "sabaintegration.overrides.sales_order.get_engineer",
			};
		});
	},
	items_on_form_rendered: function () {
		if (['erp@saba-eg.com', 'hossam@saba-eg.com', 'hayam@saba-eg.com', 'm.anas@saba-eg.com', 'nesma@saba-eg.com'].includes(frappe.session.user))
			cur_frm.cur_grid.set_field_property('rate_without_profit_margin', 'read_only', 0)
	},
	brands_on_form_rendered: function (frm) {
		var brands = frm.get_field('brands');
		if (brands && brands.grid) {
			$.each(brands.grid.fields_map, function (fieldname, field) {
				if (fieldname != "incentive_percentage")
					cur_frm.cur_grid.set_field_property(fieldname, 'read_only', 1)
			});
		}
	},
	refresh: function (frm) {
		frm.set_df_property("expected_profit_loss", "read_only", 1);
		frm.set_df_property("expected_profit_loss_value", "read_only", 1);
		frm.set_df_property("base_expected_profit_loss_value", "read_only", 1);
		if (['erp@saba-eg.com', 'hossam@saba-eg.com', 'hayam@saba-eg.com'].includes(frappe.session.user)) {
			const childTableName = "costs";

			if (frm.doc[childTableName] && frm.doc[childTableName].length > 0) {
				// Loop through each row in the child table
				frm.doc[childTableName].forEach((row) => {
					// Accessing the meta data of the child table to get all fields
					const childFields = frappe.get_meta(row.doctype).fields;

					// Loop through each field in the child row
					childFields.forEach((field) => {
						frm.set_df_property("costs", 'allow_on_submit', 1, frm.doc.name, field.fieldname, row.name);
					});
				});

			}
		}
		// Show the Download button under the items child table in submitted documents
		frm.fields_dict.items.grid.wrapper.find('.grid-upload').removeClass("hidden");
		if (frm.doc.docstatus == 1) {
			setTimeout(() => {
				frm.fields_dict.items.grid.wrapper.find('.grid-footer').css('display', 'block');
				frm.fields_dict.items.grid.wrapper.find('.grid-upload').addClass("hidden");
			}, 1000);
		}
		frm.events.set_base_rates();
	},
	conversion_rate: function (frm) {
		frm.events.set_rates_without_margin(frm)
	},
	currency: function (frm) {
		for (let i of frm.doc.items) {
			i.margin_type = '';
		}
	},
	set_rates_without_margin(frm) {
		for (let i of frm.doc.items) {
			i.rate_without_profit_margin = i.base_rate_without_profit_margin / frm.doc.conversion_rate;
			i.rate = i.base_rate / frm.doc.conversion_rate;
			if (i.rate_without_profit_margin == 0) i.to_set_rate = 0;
			if (i.margin_rate_or_amount !== undefined && i.margin_rate_or_amount > 0) {
				i.margin_rate_or_amount = (i.base_rate - i.base_price_list_rate) / frm.doc.conversion_rate;
				i.discount_amount = 0;
				i.discount_percentage = 0;
			}
			if (i.discount_amount > 0) {
				i.discount_amount = (i.base_price_list_rate - i.base_rate) / frm.doc.conversion_rate;
				i.discount_percentage = 0;
				i.margin_rate_or_amount = 0;
			}
			else i.discount_amount = 0;

		}
		cur_frm.refresh_field("items");
	},

	set_base_rates: function () {
		let conversion_rate = cur_frm.doc.conversion_rate;
		for (let i of cur_frm.doc.items) {
			if (i.base_rate_without_profit_margin == undefined ||
				i.base_rate_without_profit_margin == 'undefined' ||
				i.base_rate_without_profit_margin == 0) {
				i.base_rate_without_profit_margin = i.rate_without_profit_margin * conversion_rate;
			}
		}
	},
	contracting_tax_calculations: async function () {
		if (cur_frm.doc.contracting_tax_calculations == 1) {
			await cur_frm.add_child("costs", {
				cost_type: "Material Cost's VAT",
				cost_percentage: 14,
				cost_value: cur_frm.doc.total_rate_without_margin * 14 / 100
			});
			sabaintegration.update_costs()
		} else {
			for (let row of cur_frm.fields_dict["costs"].grid.grid_rows) {
				if (row.doc.cost_type == "Material Cost's VAT") {
					row.remove();
					sabaintegration.update_costs()
				}
			}
		}

		cur_frm.get_field("costs").grid.refresh();

	},
	taxes_and_charges: function () {
		if (cur_frm.doc.taxes_and_charges == "Contracting Tax - S") {
			cur_frm.set_value("contracting_tax_calculations", 1);
		} else {
			cur_frm.set_value("contracting_tax_calculations", 0);
		}
	},
	delivery_date: function(frm) {
        // Update delivery date for all items in the Items table
        frm.doc.items.forEach(item => {
            item.delivery_date = frm.doc.delivery_date;
        });
        frm.refresh_field('items');
    },

});

erpnext.selling.CustomSalesOrderController = class CustomSalesOrderController extends erpnext.selling.SalesOrderController {

	refresh(doc, dt, dn) {
		super.refresh(doc, dt, dn);
		this.set_dynamic_labels();
		if (doc.docstatus == 1 && doc.status !== 'Closed' && doc.status !== 'On Hold') {
			if (flt(doc.per_delivered, 6) < 100) {
				if (this.frm.doc.packed_items) {
					this.frm.add_custom_button(__('Bundle Delivery Note'), () => this.make_bundle_delivery_note(), __('Create'));
				}
			}
			this.frm.add_custom_button(__('Update Qtys'), () => this.update_qtys());
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
		this.frm.set_currency_labels([
			"base_cost_value"
		], company_currency, "costs");

		this.frm.set_currency_labels([
			"rate_without_profit_margin"
		], this.frm.doc.currency, "items");

		this.frm.set_currency_labels([
			"cost_value"
		], this.frm.doc.currency, "costs");

		this.frm.set_currency_labels([
			"base_commission_value", "base_net_commission_value"
		], company_currency, "sales_commission");

		this.frm.set_currency_labels([
			"commission_value", "net_commission_value"
		], this.frm.doc.currency, "sales_commission");

		// this.frm.set_currency_labels([
		// 	"base_incentive_value", "base_net_incentive_value"
		// ], company_currency, "pre_sales_activities");

		// this.frm.set_currency_labels([
		// 	"incentive_value", "net_incentive_value"
		// ], this.frm.doc.currency, "pre_sales_activities");
	}
	additional_discount_percentage() {
		this.frm.cscript.calculate_taxes_and_totals();
		sabaintegration.set_cost_value()
		sabaintegration.update_costs()
	}

	apply_discount_on() {
		this.frm.cscript.calculate_taxes_and_totals();
		sabaintegration.set_cost_value()
		sabaintegration.update_costs()
	}

	discount_amount() {
		this.frm.cscript.calculate_taxes_and_totals();
		sabaintegration.set_cost_value()
		sabaintegration.update_costs()
	}

	make_bundle_delivery_note() {
		var me = this;
		me.setup_items(me, async (frm, data, items) => {
			frappe.call({
				method: "sabaintegration.overrides.sales_order.make_bdn",
				args: {
					sales_order: me.frm.doc.name,
					parents_items: data.parents_items
				},
				callback: function (r) {
					if (!r.exc) {
						var doc = frappe.model.sync(r.message);
						frappe.set_route("Form", r.message.doctype, r.message.name);
					}
				}
			})
		})

	}
	async setup_items(me, callback) {
		let items = [];
		let itemslist = await frappe.call({
			"method": "sabaintegration.sabaintegration.doctype.bundle_delivery_note.bundle_delivery_note.get_reminded_bundle_items",
			"args": {
				"sales_order_name": me.frm.doc.name
			},
			"freeze": true,
			callback: function (r) {
				if (r.message) return r.message
				return 0
			}
		})
		for (let index in itemslist.message) {
			items.push(itemslist.message[index].item_code)
		}
		var fields = [
			{
				"label": "Parents Items",
				"fieldname": "parents_items",
				"fieldtype": "Table",
				"reqd": 1,
				"fields": [
					{
						"label": "Parent Item",
						"fieldname": "item_code",
						"options": "Item",
						"fieldtype": "Link",
						"in_list_view": 1,
						"reqd": 1,
						"get_query": function () {
							return {
								filters: { 'name': ["in", items] }
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
		for (let row of items) {
			dialog.fields_dict.parents_items.df.data.push({ "idx": i, "item_code": row });
			i += 1;
		}
		dialog.fields_dict.parents_items.grid.refresh();
	}

	update_qtys() {
		var me = this;
		me.setup_items_with_qtys(me, (frm, data) => {
			frappe.call({
				method: "sabaintegration.overrides.sales_order.make_sales_order",
				args: {
					sales_order: me.frm.doc.name,
					items: data.new_items
				},
				callback: function (r) {
					if (!r.exc) {
						var doc = frappe.model.sync(r.message);
						frappe.set_route("Form", r.message.doctype, r.message.name);
					}
				}
			})
		})
	}
	setup_items_with_qtys(me, callback) {
		let items = [];
		let itemslist = cur_frm.doc.items
		for (let item in itemslist) {
			items.push(item.item_code)
		}
		var fields = [
			{
				"label": "Items",
				"fieldname": "new_items",
				"fieldtype": "Table",
				"reqd": 1,
				"fields": [
					{
						"label": "Section Title",
						"fieldname": "section_title",
						"fieldtype": "Data",
						"in_list_view": 1
					},
					{
						"label": "Item",
						"fieldname": "item_code",
						"options": "Item",
						"fieldtype": "Link",
						"in_list_view": 1,
						"reqd": 1,
						"get_query": function () {
							return {
								filters: { 'name': ["in", items] }
							}
						}
					},
					{
						"label": "Qty",
						"fieldname": "qty",
						"fieldtype": "Float",
						"in_list_view": 1
					}
				]

			}
		]
		let dialog = frappe.prompt(fields, data => {
			callback(me, data);
		})
		let i = 1;
		dialog.fields_dict.new_items.df.data = [];
		for (let row of itemslist) {
			dialog.fields_dict.new_items.df.data.push({
				"idx": i,
				"item_code": row.item_code,
				"section_title": row.section_title,
				"qty": row.qty
			});
			i += 1;
		}
		dialog.fields_dict.new_items.grid.refresh();
	}

	async total_margin() {
		var me = this;
		if (me.frm.doc.items) {
			await $.each(me.frm.doc.items || [], function (i, d) {
				d.margin_from_supplier_quotation = me.frm.doc.total_margin;
				d.rate = d.rate_without_profit_margin + (d.rate_without_profit_margin * d.margin_from_supplier_quotation / 100)
				d.amount = d.rate * d.qty;
			});
			cur_frm.cscript.calculate_taxes_and_totals();
			me.frm.doc.total_items_markup_value = me.frm.doc.total - me.frm.doc.total_rate_without_margin
			me.frm.doc.base_total_items_markup_value = me.frm.doc.total_items_markup_value * me.frm.doc.conversion_rate
			sabaintegration.set_cost_value()
			sabaintegration.update_costs()
		}
	}
	costs_template() {
		var me = this;
		if (this.frm.doc.costs_template) {
			return this.frm.call({
				method: "sabaintegration.overrides.quotation.get_costs",
				args: {
					"costs_template": this.frm.doc.costs_template
				},
				callback: function (r) {
					if (!r.exc) {
						me.frm.set_value("costs", r.message);
						sabaintegration.set_cost_value()
						sabaintegration.update_costs()
					}
				}
			});
		}
	}
	primary_sales_man() {
		var me = this;
		frappe.call({
			"method": "sabaintegration.overrides.sales_order.get_commission_percent",
			"args": { "sales_man": me.frm.doc.primary_sales_man },
			callback: function (r) {
				if (r.message) {
					for (const field in r.message) {
						me.frm.doc[field] = r.message[field];
						me.frm.refresh_field(field);
					}

				}
			}
		})
	}
	sales_commission_template() {
		var me = this;
		if (this.frm.doc.sales_commission_template) {
			return this.frm.call({
				method: "sabaintegration.overrides.sales_order.get_commission",
				args: {
					"commission_template": this.frm.doc.sales_commission_template
				},
				callback: function (r) {
					if (!r.exc) {
						me.frm.set_value("sales_commission", r.message);

					}
				}
			});
		}
	}

	pre_sales_incentive_template() {
		var me = this;
		if (this.frm.doc.pre_sales_incentive_template) {
			return this.frm.call({
				method: "sabaintegration.overrides.sales_order.get_pre_sales_activities",
				args: {
					"pre_sales_incentive_template": this.frm.doc.pre_sales_incentive_template
				},
				callback: function (r) {
					if (!r.exc) {
						me.frm.set_value("pre_sales_activities", r.message);

					}
				}
			});
		}
	}

}

extend_cscript(cur_frm.cscript, new erpnext.selling.CustomSalesOrderController({ frm: cur_frm }));

frappe.ui.form.on('Sales Order Item', {
	item_code: function (frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		if (!(d.from_buying_price_list == '' ||
			d.from_buying_price_list == undefined ||
			d.from_buying_price_list == 'undifined'))
			set_buying_rate(frm, d)

	},
	items_remove: function (frm) {
		sabaintegration.set_total_without_margin(frm);
		sabaintegration.calculate_total_margin(frm, true);
	},
	margin_from_supplier_quotation: function (frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		//frappe.model.set_value(cdt, cdn, "rate", d.rate_without_profit_margin + (d.margin_from_supplier_quotation / 100 * d.rate_without_profit_margin))
		//frappe.model.set_value(cdt, cdn, "price_list_rate", d.rate_without_profit_margin + (d.margin_from_supplier_quotation / 100 * d.rate_without_profit_margin))
		d.rate = d.rate_without_profit_margin + (d.margin_from_supplier_quotation / 100 * d.rate_without_profit_margin)
		if (d.rate > d.price_list_rate) {
			d.margin_type = "Amount";
			d.margin_rate_or_amount = (d.rate - d.price_list_rate);
			d.discount_amount = 0;
			d.discount_percentage = '';
		}
		else if (d.rate < d.price_list_rate) {
			d.discount_amount = d.price_list_rate - d.rate;
			d.discount_percentage = d.discount_amount / d.price_list_rate * 100;
			d.margin_type = '';
			d.margin_rate_or_amount = 0;
		}
		sabaintegration.calculate_total_margin(frm, true);
	},
	price_list_rate: function (frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		if (!d.rate_without_profit_margin && d.to_set_rate == 1) {
			if (d.from_buying_price_list == '' ||
				d.from_buying_price_list == undefined ||
				d.from_buying_price_list == 'undifined') {
				d.rate_without_profit_margin = d.price_list_rate
				d.base_rate_without_profit_margin = d.base_price_list_rate;
			}
			else {
				set_buying_rate(frm, d)
			}
		}
		d.to_set_rate = 1;
	},
	rate: function (frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		if (d.rate_without_profit_margin)
			d.margin_from_supplier_quotation = (d.rate - d.rate_without_profit_margin) / d.rate_without_profit_margin * 100
		else
			d.margin_from_supplier_quotation = 0
		sabaintegration.set_total_without_margin(frm);
		sabaintegration.calculate_total_margin(frm, false);
	},
	from_buying_price_list: function (frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		if (d.from_buying_price_list == '' ||
			d.from_buying_price_list == undefined ||
			d.from_buying_price_list == 'undifined')
			d.rate_without_profit_margin = d.price_list_rate
		else {
			set_buying_rate(frm, d)
		}
		d.margin_from_supplier_quotation = (d.rate - d.rate_without_profit_margin) / d.rate_without_profit_margin * 100;
		frm.refresh_field("items");
	},
	qty: function (frm, cdt, cdn) {
		sabaintegration.set_total_without_margin(frm);
		sabaintegration.calculate_total_margin(frm, true);
	},
	rate_without_profit_margin: function (frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		var margin_from_supplier_quotation = (d.rate - d.rate_without_profit_margin) / d.rate_without_profit_margin * 100
		d.margin_from_supplier_quotation = margin_from_supplier_quotation;
		sabaintegration.set_total_without_margin(frm);
		sabaintegration.calculate_total_margin(frm, true);
	}
})
frappe.ui.form.on('Cost', {
	cost_value: function (frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		if (d.cost_value == 0) frappe.model.set_value(cdt, cdn, "cost_percentage", 0)
		if (d.cost_type == "Material Cost's VAT") {
			d.cost_percentage = d.cost_value / frm.doc.total_rate_without_margin * 100;
		} else {
			d.cost_percentage = d.cost_value / frm.doc.net_total * 100;
		}
		sabaintegration.update_costs()
	},
	cost_percentage: function (frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		if (d.cost_type == "Material Cost's VAT") {
			d.cost_value = frm.doc.total_rate_without_margin * d.cost_percentage / 100;
		} else {
			d.cost_value = frm.doc.net_total * d.cost_percentage / 100;
		}
		d.base_cost_value = d.cost_value * frm.doc.conversion_rate;
		sabaintegration.update_costs()
	},
	costs_remove: function (frm, cdt, cdn) {
		sabaintegration.update_costs()
	}
})

frappe.ui.form.on('Sales Commission', {
	sales_commission_add: function (frm, cdt, cdn) {
		let d = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "sales_person", "Sales Team");
	},
	sales_person: function (frm, cdt, cdn) {
		let d = locals[cdt][cdn];
		get_default_rule(d, "commission");
	},
	stage_title: function (frm, cdt, cdn) {
		let d = locals[cdt][cdn];
		if (d.stage_title == "Lead (Prospecting)")
			d.comm_percent = 5;
		else if (d.stage_title == "Approaching (Initiating & Opening communication)")
			d.comm_percent = 20;
		else if (d.stage_title == "Technical Submittal")
			d.comm_percent = 8;
		else if (d.stage_title == "Financial Submittal")
			d.comm_percent = 7;
		else if (d.stage_title == "Following Up")
			d.comm_percent = 30;
		else if (d.stage_title == "Closing")
			d.comm_percent = 30;
		frm.refresh_field("sales_commission");
	},
})

frappe.ui.form.on('Pre-Sales Incentive', {
	engineer: function (frm, cdt, cdn) {
		let d = locals[cdt][cdn];
		get_default_rule(d, "pre_sales");
		frappe.call({
			"method": "sabaintegration.overrides.sales_order.get_incentive_percent",
			"args": { "engineer": d.engineer },
			callback: function (r) {
				if (r.message) {
					d.incentive_percentage = r.message;
					frm.refresh_field("pre_sales_activities");
				}
				else {
					d.incentive_percentage = 0;
					frm.refresh_field("pre_sales_activities");
				}
			}
		})
	},
})

const get_default_rule = function (row, reason) {
	frappe.call({
		method: "sabaintegration.sabaintegration.doctype.commission_rule.commission_rule.get_default_rule",
		args: {
			"reason": reason
		},
		callback: function (r) {
			if (r.message) {
				row.rule = r.message;
				if (reason == "commission") cur_frm.refresh_field("sales_commission");
				else if (reason == "pre_sales") {
					row.incentive_rule = r.message;
					cur_frm.refresh_field("pre_sales_activities");
				}
			}
		}

	})
}

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
// 			console.log(r.message)
// 			if (r.message){
// 				row.commission_value = r.message;
// 				row.net_commission_value = row.commission_value * row.kpi / 100;
// 				cur_frm.refresh_field("sales_commission");
// 			}
// 		}

// 	})

// }

const set_buying_rate = function (frm, d) {
	/// use get_item_price
	frappe.call({
		method: "sabaintegration.stock.get_item_details._get_item_price",
		args: {
			item_code: d.item_code,
			price_list: d.from_buying_price_list,
			transaction_date: frm.doc.transaction_date,
			batch_no: d.batch_no
		},
		callback: function (r) {
			if (r.message && r.message[0]) {
				let conversion_rate = 1;
				if (frm.doc.conversion_rate) conversion_rate = frm.doc.conversion_rate
				d.base_rate_without_profit_margin = r.message[0][1];
				d.rate_without_profit_margin = r.message[0][1] / conversion_rate;
				d.margin_from_supplier_quotation = (d.rate - d.rate_without_profit_margin) / d.rate_without_profit_margin * 100;
				frm.refresh_fields("items")
			}
		}
	})
}