// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

cur_frm.cscript.tax_table = "Sales Taxes and Charges";
// {% include 'erpnext/selling/sales_common.js' %}
{% include 'erpnext/public/js/utiles/sales_common.js' %}


cur_frm.email_field = "contact_email";

frappe.provide("erpnext.selling");
erpnext.selling.CustomSellingController = class CustomSellingController extends erpnext.selling.SellingController{ 

	campaign() {
		this.apply_pricing_rule();
	}

	selling_price_list() {
		this.apply_price_list();
		this.set_dynamic_labels();
	}

	///Custom Update this method is from erpnext transaction.js
	apply_price_list(item, reset_plc_conversion) {
		// We need to reset plc_conversion_rate sometimes because the call to
		// `erpnext.stock.get_item_details.apply_price_list` is sensitive to its value
		if (!reset_plc_conversion) {
			this.frm.set_value("plc_conversion_rate", "");
		}
		var me = this;
		var args = this._get_args(item);
		if (!((args.items && args.items.length) || args.price_list)) {
			return;
		}

		if (me.in_apply_price_list == true) return;

		me.in_apply_price_list = true;
		return this.frm.call({
			method: "sabaintegration.stock.get_item_details.apply_price_list", ////Custom Update
			args: {	args: args},
			callback: function(r) {
				if (!r.exc) {
					frappe.run_serially([
						() => me.frm.set_value("price_list_currency", r.message.parent.price_list_currency),
						() => me.frm.set_value("plc_conversion_rate", r.message.parent.plc_conversion_rate),
						() => {
							if(args.items.length) {
								me._set_values_for_item_list(r.message.children);
							}
						},
						() => { me.in_apply_price_list = false; }
					]);

				} else {
					me.in_apply_price_list = false;
				}
			}
		}).always(() => {
			me.in_apply_price_list = false;
		});
	}
	_set_values_for_item_list(children) {
		var me = this;
		var items_rule_dict = {};

		for(var i=0, l=children.length; i<l; i++) {
			var d = children[i] ;
			let item_row = frappe.get_doc(d.doctype, d.name);
			var existing_pricing_rule = frappe.model.get_value(d.doctype, d.name, "pricing_rules");
			for(var k in d) {
				var v = d[k];
				if (["doctype", "name"].indexOf(k)===-1) {
					///Custom Update
					if(k=="price_list_rate") {
						
						item_row['rate'] = v
						item_row['rate_without_profit_margin'] = item_row['rate']

						item_row["margin_from_supplier_quotation"] = (item_row["rate"] - item_row["rate_without_profit_margin"]) / item_row["rate_without_profit_margin"] * 100
						
					}
					///End Custom Update
					if (k !== 'free_item_data') {
						item_row[k] = v;
					}
					
				}
			}

			frappe.model.round_floats_in(item_row, ["price_list_rate", "discount_percentage"]);

			// if pricing rule set as blank from an existing value, apply price_list
			if(!me.frm.doc.ignore_pricing_rule && existing_pricing_rule && !d.pricing_rules) {
				me.apply_price_list(frappe.get_doc(d.doctype, d.name));
			} else if(!d.pricing_rules) {
				me.remove_pricing_rule(frappe.get_doc(d.doctype, d.name));
			}

			if (d.free_item_data.length > 0) {
				me.apply_product_discount(d);
			}

			if (d.apply_rule_on_other_items) {
				items_rule_dict[d.name] = d;
			}
		}

		me.frm.refresh_field('items');
		me.apply_rule_on_other_items(items_rule_dict);

		me.calculate_taxes_and_totals();

	}
}

