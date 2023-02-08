// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt


{% include 'sabaintegration/selling/sales_common.js' %}

frappe.ui.form.on('Quotation', {
	setup: function(frm){
		if (frm.doc.option_number_from_opportunity > 0 ){
			frm.toggle_display('option_number_from_opportunity', true)
		}
	},
	after_save: function(frm){
		if (frm.doc.option_number_from_opportunity > 0 ){
			frm.toggle_display('option_number_from_opportunity', true)
		}
	},
	set_total_without_margin: function(frm){
		let total = 0;
		$.each(frm.doc.items || [], function(i, d) {
			total = total + (d.rate_without_profit_margin * d.qty);
		});
		frm.doc.total_rate_without_margin = total;
		frm.refresh_field("total_rate_without_margin");
	}
});

erpnext.selling.QuotationController = erpnext.selling.SellingController.extend({
	onload: function(doc, dt, dn) {
		var me = this;
		this._super(doc, dt, dn);

	},
	party_name: function() {
		var me = this;
		erpnext.utils.get_party_details(this.frm, null, null, function() {
			me.apply_price_list();
		});

		if(me.frm.doc.quotation_to=="Lead" && me.frm.doc.party_name) {
			me.frm.trigger("get_lead_details");
		}
	},
	refresh: function(doc, dt, dn) {
		this._super(doc, dt, dn);
		doctype = doc.quotation_to == 'Customer' ? 'Customer':'Lead';
		frappe.dynamic_link = {doc: this.frm.doc, fieldname: 'party_name', doctype: doctype}

		var me = this;

		if (doc.__islocal && !doc.valid_till) {
			if(frappe.boot.sysdefaults.quotation_valid_till){
				this.frm.set_value('valid_till', frappe.datetime.add_days(doc.transaction_date, frappe.boot.sysdefaults.quotation_valid_till));
			} else {
				this.frm.set_value('valid_till', frappe.datetime.add_months(doc.transaction_date, 1));
			}
		}

		if (doc.docstatus == 1 && !["Lost", "Ordered"].includes(doc.status)) {
			this.frm.add_custom_button(
				__("Sales Order"),
				this.frm.cscript["Make Sales Order"],
				__("Create")
			);

			if(doc.status!=="Ordered") {
				this.frm.add_custom_button(__('Set as Lost'), () => {
						this.frm.trigger('set_as_lost_dialog');
					});
				}

			if(!doc.auto_repeat) {
				cur_frm.add_custom_button(__('Subscription'), function() {
					erpnext.utils.make_subscription(doc.doctype, doc.name)
				}, __('Create'))
			}

			cur_frm.page.set_inner_btn_group_as_primary(__('Create'));
		}

		if (this.frm.doc.docstatus===0) {
			this.frm.add_custom_button(__('Opportunity'),
				function() {
					erpnext.utils.map_current_doc({
						method: "erpnext.crm.doctype.opportunity.opportunity.make_quotation",
						source_doctype: "Opportunity",
						target: me.frm,
						setters: [
							{
								label: "Party",
								fieldname: "party_name",
								fieldtype: "Link",
								options: me.frm.doc.quotation_to,
								default: me.frm.doc.party_name || undefined
							},
							{
								label: "Opportunity Type",
								fieldname: "opportunity_type",
								fieldtype: "Link",
								options: "Opportunity Type",
								default: me.frm.doc.order_type || undefined
							}
						],
						get_query_filters: {
							status: ["not in", ["Lost", "Closed"]],
							company: me.frm.doc.company
						}
					})
				}, __("Get Items From"), "btn-default");
		}

		this.toggle_reqd_lead_customer();

	},

	set_dynamic_field_label: function(){
		if (this.frm.doc.quotation_to == "Customer")
		{
			this.frm.set_df_property("party_name", "label", "Customer");
			this.frm.fields_dict.party_name.get_query = null;
		}

		if (this.frm.doc.quotation_to == "Lead")
		{
			this.frm.set_df_property("party_name", "label", "Lead");

			this.frm.fields_dict.party_name.get_query = function() {
				return{	query: "erpnext.controllers.queries.lead_query" }
			}
		}
	},

	toggle_reqd_lead_customer: function() {
		var me = this;

		// to overwrite the customer_filter trigger from queries.js
		this.frm.toggle_reqd("party_name", this.frm.doc.quotation_to);
		this.frm.set_query('customer_address', this.address_query);
		this.frm.set_query('shipping_address_name', this.address_query);
	},

	tc_name: function() {
		this.get_terms();
	},

	address_query: function(doc) {
		return {
			query: 'frappe.contacts.doctype.address.address.address_query',
			filters: {
				link_doctype: frappe.dynamic_link.doctype,
				link_name: doc.party_name
			}
		};
	},

	validate_company_and_party: function(party_field) {
		if(!this.frm.doc.quotation_to) {
			frappe.msgprint(__("Please select a value for {0} quotation_to {1}", [this.frm.doc.doctype, this.frm.doc.name]));
			return false;
		} else if (this.frm.doc.quotation_to == "Lead") {
			return true;
		} else {
			return this._super(party_field);
		}
	},

	get_lead_details: function() {
		var me = this;
		if(!this.frm.doc.quotation_to === "Lead") {
			return;
		}

		frappe.call({
			method: "erpnext.crm.doctype.lead.lead.get_lead_details",
			args: {
				'lead': this.frm.doc.party_name,
				'posting_date': this.frm.doc.transaction_date,
				'company': this.frm.doc.company,
			},
			callback: function(r) {
				if(r.message) {
					me.frm.updating_party_details = true;
					me.frm.set_value(r.message);
					me.frm.refresh();
					me.frm.updating_party_details = false;

				}
			}
		})
	},
	total_margin: async function(){
		var me = this;
		if (me.frm.doc.items){
			let difference = me.frm.doc.total_rate_without_margin * me.frm.doc.total_margin / 100;
			let ratetoadd = flt(difference / me.frm.doc.total_qty, precision("ratetoadd"));
			let total = 0;
			await $.each(me.frm.doc.items || [], function(i, d) {
				d.rate = d.rate_without_profit_margin + ratetoadd;
				d.margin_from_supplier_quotation = (d.rate - d.rate_without_profit_margin) / d.rate_without_profit_margin * 100 
				d.amount = d.rate * d.qty;
				total += d.amount;
			});
			cur_frm.cscript.calculate_taxes_and_totals();
			refresh_field("items");
		}
	},
	calculate_total_margin: function(){
		let total = 0
		$.each(this.frm.doc.items || [], function(i, d) {
			console.log(d.rate)
			total = total  + (d.rate * d.qty);
		});
		this.frm.doc.total_margin = (total - this.frm.doc.total_rate_without_margin) / this.frm.doc.total_rate_without_margin * 100;
	}
});

cur_frm.script_manager.make(erpnext.selling.QuotationController);

////
frappe.ui.form.on('Quotation Item', {
	items_remove: function(frm){
		frm.trigger("set_total_without_margin");
	},
	margin_from_supplier_quotation: function(frm,cdt,cdn){
		var d = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "rate", d.rate_without_profit_margin + (d.margin_from_supplier_quotation / 100 * d.rate_without_profit_margin))
		//frappe.model.set_value(cdt, cdn, "price_list_rate", d.rate_without_profit_margin + (d.margin_from_supplier_quotation / 100 * d.rate_without_profit_margin))
		frm.script_manager.trigger("calculate_total_margin");
	},
	rate: function(frm,cdt,cdn){
		var d = locals[cdt][cdn];
		if (!d.rate_without_profit_margin){
			d.rate_without_profit_margin = d.price_list_rate
		}
		d.margin_from_supplier_quotation = (d.rate - d.rate_without_profit_margin) / d.rate_without_profit_margin * 100 
		frm.trigger("set_total_without_margin");
	},
	qty: function(frm, cdt, cdn){
		frm.trigger("set_total_without_margin");
	}
	

})