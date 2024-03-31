// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

{% include 'erpnext/selling/doctype/quotation/quotation.js' %}
{% include 'sabaintegration/selling/costs.js' %}

frappe.provide("sabaintegration.costs")


frappe.ui.form.on('Quotation', {
	setup: function(frm){
		frm.set_query("from_buying_price_list", "items", function(doc, cdt, cdn) {
			return {
				filters:{
					"buying": 1
				}
			}
		});
	},
	onload: function(frm){
		if (frm.doc.option_number_from_opportunity > 0 ){
			frm.toggle_display('option_number_from_opportunity', true)
		}
		if (frm.is_new()) frappe.model.set_value(frm.doc.doctype, frm.doc.name, "costs_template", "Projects Indirect Cost Analysis");

		$("[data-fieldname= 'expected_profit_loss'] .control-label").css("font-weight", "bold")
		$("[data-fieldname= 'expected_profit_loss_value'] .control-label").css("font-weight", "bold")

		$("[data-fieldname= 'expected_profit_loss'] .control-value").css("font-weight", "bold")
		$("[data-fieldname= 'expected_profit_loss_value'] .control-value").css("font-weight", "bold")

        const originalSave = frappe.ui.form.save;
        frappe.ui.form.save = function() {
            if (cur_frm && cur_frm.doc.doctype === 'Quotation') {
                cur_frm.set_value('is_saved_from_ui', 1);
            }
            originalSave.apply(this, arguments);
        };
    },
    before_save: function(frm) {
        if (!frm.doc.__islocal) {
            setTimeout(() => frm.set_value('is_saved_from_ui', 0), 100);
        }
    },
	after_save: function(frm){
		if (frm.doc.option_number_from_opportunity > 0 ){
			frm.toggle_display('option_number_from_opportunity', true)
		}
	},
	items_on_form_rendered: function(){
		if (frappe.user.has_role("0 Selling -Quotation-Edit Rate without Markup") || frappe.user.has_role("0 Selling -Quotation-Edit Cost")) 
			cur_frm.cur_grid.set_field_property('rate_without_profit_margin', 'read_only', 0)
	},
	refresh: async function(frm){
		frm.events.set_base_rates();
		if (frm.is_new()){
			frappe.model.set_value(frm.doc.doctype, frm.doc.name, "costs_template", "Projects Indirect Cost Analysis");
		}
		if(frm.$wrapper.find(`.form-documents [data-doctype="Opportunity"]`).length == 0 && frm.doc.opportunity ){
            frm.$wrapper.find(".form-documents .row .col-md-4:first-child").append(
                `<div class="document-link" data-doctype="Opportunity">
                    <div class="document-link-badge" data-doctype="Opportunity">
                        <span class="count">1</span>
                        <a class="badge-link" href="/app/opportunity/view/list?name=${frm.doc.opportunity}">Opportunity</a>
                </div>`);
        }
		else if (frm.$wrapper.find(`.form-documents [data-doctype="Opportunity"]`).length > 0){
			frm.$wrapper.find('.form-documents .document-link-badge[data-doctype="Opportunity"] a.badge-link').each(function(){

				if (frm.doc.opportunity){
					$(this).attr('href', `/app/opportunity/view/list?name=${frm.doc.opportunity}`);
				}
				else $(this).removeAttr('href');
				
			  });
		}

		await frappe.call({
			method: "sabaintegration.overrides.quotation.get_docs_related_to_quotation",
			args: {
				doc_name: frm.doc.name
			},
			callback: function(r) {
				if (frm.$wrapper.find(`.form-documents [data-doctype="Request for Quotation"]`).length == 0){
					if(r.message.rfq && r.message.rfq.length != 0){					
						frm.$wrapper.find(".form-documents .row .col-md-4:first-child").append(
							`<div class="document-link" data-doctype="Request for Quotation">
								<div class="document-link-badge" data-doctype="Request for Quotation">
									<span class="count">${r.message.rfq.length}</span>
									<a class="badge-link" href='/app/request-for-quotation/view/list?name=["in" , [${r.message.rfq.map((r) => {return r.request_for_quotation?'"'+r.request_for_quotation+'"':''})}]]'>Request for Quotation</a>
							</div>`);
					}
				}
				else {
					frm.$wrapper.find('.form-documents .document-link-badge[data-doctype="Request for Quotation"] a.badge-link').each(function(){
						const spanElement = $(this).closest('.document-link-badge').find('span.count');
						
						// Change the text value of the 'span.count'
						if(r.message.rfq && r.message.rfq.length != 0){	
							spanElement.removeClass('hidden');
							spanElement.text(r.message.rfq.length);
							$(this).attr('href', `/app/request-for-quotation/view/list?name=["in" , [${r.message.rfq.map((r) => {return r.request_for_quotation?'"'+r.request_for_quotation+'"':''})}]]`);
						}
						else {
							spanElement.addClass('hidden');
							$(this).removeAttr('href');
						}
					})
				}
				if (frm.$wrapper.find(`.form-documents [data-doctype="Supplier Quotation"]`).length == 0){
					if(r.message.sq && r.message.sq.length != 0){					
						frm.$wrapper.find(".form-documents .row .col-md-4:first-child").append(
							`<div class="document-link" data-doctype="Supplier Quotation">
								<div class="document-link-badge" data-doctype="Supplier Quotation">
									<span class="count">${r.message.sq.length}</span>
									<a class="badge-link" href='/app/supplier-quotation/view/list?name=["in" , [${r.message.sq.map((r) => {return r.supplier_quotation?'"'+r.supplier_quotation+'"':''})}]]'>SupplierQuotation</a>
							</div>`);
					}
				}
				else {
					frm.$wrapper.find('.form-documents .document-link-badge[data-doctype="Supplier Quotation"] a.badge-link').each(function(){
						const spanElement = $(this).closest('.document-link-badge').find('span.count');
						
						// Change the text value of the 'span.count'
						if(r.message.sq && r.message.sq.length != 0){	
							spanElement.removeClass('hidden');
							spanElement.text(r.message.sq.length);
							$(this).attr('href', `/app/supplier-quotation/view/list?name=["in" , [${r.message.sq.map((r) => {return r.supplier_quotation?'"'+r.supplier_quotation+'"':''})}]]`);
						}
						else {
							spanElement.addClass('hidden');
							$(this).removeAttr('href');
						}
					})
				}
			}
		});			

		const badgeLinks = document.querySelectorAll('.document-link-badge a.badge-link');

		// Loop through all the selected 'a' tags
		badgeLinks.forEach((badgeLink) => {
		// Check if the 'href' attribute exists
		if (badgeLink.hasAttribute('href')) {
			// Find the parent div element
			const parentDiv = badgeLink.closest('.document-link-badge');
			// Find the span within the parent div and remove 'hidden' class
			const spanElement = parentDiv.querySelector('span.count');
			if (spanElement.textContent.trim() !== "") {
				// Remove 'hidden' class
				spanElement.classList.remove('hidden');
			  }
		}
		});

	},
	conversion_rate: async function(frm){
		frm.events.set_rates_without_margin(frm)
	},
	currency: function(frm){
		for (let i of frm.doc.items){
			i.margin_type = '';
		}
	},
	set_rates_without_margin(frm){
		for (let i of frm.doc.items){
			i.rate_without_profit_margin = i.base_rate_without_profit_margin / frm.doc.conversion_rate;
			i.rate = i.base_rate / frm.doc.conversion_rate;
			if (i.rate_without_profit_margin == 0) i.to_set_rate = 0;
			if (i.margin_rate_or_amount !== undefined && i.margin_rate_or_amount > 0){
				i.margin_rate_or_amount = (i.base_rate - i.base_price_list_rate) / frm.doc.conversion_rate;
				i.discount_amount = 0;
				i.discount_percentage = 0;
			}
			if (i.discount_amount > 0){
				i.discount_amount = (i.base_price_list_rate - i.base_rate) / frm.doc.conversion_rate;
				i.discount_percentage = 0;
				i.margin_rate_or_amount = 0;
			}
			else i.discount_amount = 0;

		}
		cur_frm.doc.correct_to_save = 1
		cur_frm.refresh_field("items");
	},

	set_base_rates: function(){
		let conversion_rate = cur_frm.doc.conversion_rate;
		for (let i of cur_frm.doc.items){
			if (i.base_rate_without_profit_margin == undefined || 
				i.base_rate_without_profit_margin == 'undefined' ||
				i.base_rate_without_profit_margin == 0){
					i.base_rate_without_profit_margin = i.rate_without_profit_margin * conversion_rate;
			}	
		}
	},
	contracting_tax_calculations: async function(){
		if(cur_frm.doc.contracting_tax_calculations == 1){
			await cur_frm.add_child("costs" , {
				cost_type: "Material Cost's VAT",
				cost_percentage : 14,
				cost_value : cur_frm.doc.total_rate_without_margin * 14 / 100
			});
			sabaintegration.update_costs()			
		}else{
			for(let row of cur_frm.fields_dict["costs"].grid.grid_rows){
				if(row.doc.cost_type == "Material Cost's VAT"){
					row.remove();
					sabaintegration.update_costs()
				}
			}
		}
		cur_frm.get_field("costs").grid.refresh();
		
	},
	taxes_and_charges: function(){
		if(cur_frm.doc.taxes_and_charges == "Contracting Tax - S"){
			cur_frm.set_value("contracting_tax_calculations" , 1);
		}else{
			cur_frm.set_value("contracting_tax_calculations" , 0);
		}
	},

});

erpnext.selling.CustomQuotationController = class CustomQuotationController extends erpnext.selling.QuotationController {
	setup() {
		super.setup();
		frappe.ui.form.on(this.frm.cscript.tax_table, "included_in_print_rate", function(frm, cdt, cdn) {
			cur_frm.cscript.set_dynamic_labels();
			cur_frm.cscript.calculate_taxes_and_totals();
		});
		frappe.ui.form.on(this.frm.doctype, "discount_amount", function(frm) {
			frm.cscript.set_dynamic_labels();

			if (!frm.via_discount_percentage) {
				frm.doc.additional_discount_percentage = 0;
			}

			frm.cscript.calculate_taxes_and_totals();
		});
	}
	onload(){
        if (!this.frm.is_new()) {
            if (this.frm.doc.from_buying_price_list == 1) {
                this.frm.toggle_reqd("buying_price_list", 1)
				this.frm.set_df_property("buying_price_list", "hidden", 0);
            }
            else {
				this.frm.doc.buying_price_list = ''
				this.frm.toggle_reqd("buying_price_list", 0)
				this.frm.set_df_property("buying_price_list", "hidden", 1);
            }
        }
		else if (!this.frm.doc.is_duplicated){
			this.frm.doc.from_buying_price_list = 1
			this.frm.toggle_reqd("buying_price_list", 1)
			for (let d of this.frm.doc.items){
				d.from_buying_price_list = this.frm.doc.buying_price_list;
				this.frm.refresh_field("items");
			}
		}
    }
	refresh(doc, dt, dn) {
		super.refresh(doc, dt, dn);
		this.set_dynamic_labels();
	}
	customer() {
		var me = this;
		erpnext.utils.get_party_details(this.frm, null, null, function() {
			me.apply_price_list();
		});
	}
	from_buying_price_list(){
        if (!this.frm.doc.from_buying_price_list) {
            this.frm.doc.buying_price_list = '';
            this.frm.doc.selling_price_list = 'Standard Selling';
            this.frm.refresh_field("selling_price_list");
            this.frm.set_df_property("buying_price_list", "hidden", 1);
            this.frm.set_df_property("selling_price_list", "hidden", 0);
			this.frm.toggle_reqd("selling_price_list", 1)
			this.frm.toggle_reqd("buying_price_list", 0)
        }
        else {
           // this.frm.doc.selling_price_list = '';
            this.frm.doc.buying_price_list = 'Standard Buying';
            this.frm.refresh_field("buying_price_list");
            this.frm.set_df_property("buying_price_list", "hidden", 0);
			this.frm.toggle_reqd("buying_price_list", 1)
		}
		this.set_buying_price_list(this.frm)
    }
	set_buying_price_list(frm) {
		for (let d of frm.doc.items){
			frappe.model.set_value(d.doctype, d.name, 'from_buying_price_list', frm.doc.buying_price_list)
		}
	}
	sales_partner() {
		this.apply_pricing_rule();
	}

	campaign() {
		this.apply_pricing_rule();
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
			"base_rate_without_profit_margin"
		], company_currency, "items");

		this.frm.set_currency_labels([
			"base_cost_value"
		], company_currency, "costs");

		this.frm.set_currency_labels([
			"rate_without_profit_margin"
		], this.frm.doc.currency, "items");

		this.frm.set_currency_labels([
			"cost_value"
		], this.frm.doc.currency, "costs");
	}
	campaign() {
		this.apply_pricing_rule();
	}

	selling_price_list() {
		this.apply_price_list();
		this.set_dynamic_labels();
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

	async total_margin(){
		var me = this;
		if (me.frm.doc.items){
			await $.each(me.frm.doc.items || [], function(i, d) {
				d.margin_from_supplier_quotation = me.frm.doc.total_margin;
				d.rate = d.rate_without_profit_margin + (d.rate_without_profit_margin * d.margin_from_supplier_quotation  / 100)
				d.amount = d.rate * d.qty;
				d.margin_rate_or_amount = d.rate - d.price_list_rate;
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

extend_cscript(cur_frm.cscript, new erpnext.selling.CustomQuotationController({frm: cur_frm}));

////
frappe.ui.form.on('Quotation Item', {
	items_add: function(frm, cdt, cdn){
		var d = locals[cdt][cdn];
		if (frm.doc.from_buying_price_list == 1)
			d.from_buying_price_list = frm.doc.buying_price_list;

	},
	item_code: function(frm,cdt,cdn){
		var d = locals[cdt][cdn];
		if (!(d.from_buying_price_list == '' || 
		d.from_buying_price_list == undefined || 
		d.from_buying_price_list == 'undifined'))
			set_buying_rate(frm, d)

	},
	items_remove: function(frm){
		sabaintegration.set_total_without_margin(frm);
		sabaintegration.calculate_total_margin(frm, true);
	},
	margin_from_supplier_quotation: function(frm,cdt,cdn){
		var d = locals[cdt][cdn];
		//frappe.model.set_value(cdt, cdn, "rate", d.rate_without_profit_margin + (d.margin_from_supplier_quotation / 100 * d.rate_without_profit_margin))
		//frappe.model.set_value(cdt, cdn, "price_list_rate", d.rate_without_profit_margin + (d.margin_from_supplier_quotation / 100 * d.rate_without_profit_margin))
		d.rate = d.rate_without_profit_margin + (d.margin_from_supplier_quotation / 100 * d.rate_without_profit_margin)
		if (d.rate > d.price_list_rate ){
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
	price_list_rate: function(frm, cdt, cdn){
		var d = locals[cdt][cdn];
		if (!d.rate_without_profit_margin && d.to_set_rate == 1){
			if (d.from_buying_price_list == '' || 
			d.from_buying_price_list == undefined || 
			d.from_buying_price_list == 'undifined'){
				d.rate_without_profit_margin = d.price_list_rate
				d.base_rate_without_profit_margin = d.base_price_list_rate;
			}
			else {
				set_buying_rate(frm, d)
			}
		}
		d.to_set_rate = 1;
	},
	rate: function(frm,cdt,cdn){
		var d = locals[cdt][cdn];
		if (d.rate_without_profit_margin)
			d.margin_from_supplier_quotation = (d.rate - d.rate_without_profit_margin) / d.rate_without_profit_margin * 100 
		else
			d.margin_from_supplier_quotation = 0
		sabaintegration.set_total_without_margin(frm);
		sabaintegration.calculate_total_margin(frm, false);
	},
	from_buying_price_list: function(frm, cdt, cdn){
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
	qty: function(frm, cdt, cdn){
		if (frm.doc.supplier_quotations.length != 0){
			var d = locals[cdt][cdn];
			check_change_qty(frm, d)
		}
		else {
			sabaintegration.set_total_without_margin(frm);
			sabaintegration.calculate_total_margin(frm, true);
		}

	},
	rate_without_profit_margin: function(frm, cdt, cdn){
		var d = locals[cdt][cdn];
		var margin_from_supplier_quotation = (d.rate - d.rate_without_profit_margin) / d.rate_without_profit_margin * 100 
		d.margin_from_supplier_quotation = margin_from_supplier_quotation;
		sabaintegration.set_total_without_margin(frm);
		sabaintegration.calculate_total_margin(frm, true);
	}
	

})

frappe.ui.form.on('Cost', {
	cost_value: function(frm, cdt, cdn){
		var d = locals[cdt][cdn];
		if (d.cost_value == 0) frappe.model.set_value(cdt, cdn, "cost_percentage", 0)
		if(d.cost_type == "Material Cost's VAT"){
			d.cost_percentage = d.cost_value / frm.doc.total_rate_without_margin * 100;
		}else{
			d.cost_percentage = d.cost_value / frm.doc.net_total * 100;
		}		
		sabaintegration.update_costs()
	},
	cost_percentage: function(frm, cdt, cdn){
		var d = locals[cdt][cdn];
		if(d.cost_type == "Material Cost's VAT"){
			d.cost_value = frm.doc.total_rate_without_margin * d.cost_percentage / 100;
		}else{
			d.cost_value = frm.doc.net_total * d.cost_percentage / 100;
		}
		d.base_cost_value = d.cost_value * frm.doc.conversion_rate;
		sabaintegration.update_costs()
	},
	costs_remove: function(frm, cdt, cdn){
		sabaintegration.update_costs()
	}
})

const check_change_qty = async function(frm, d){
	frappe.call({
		method: "sabaintegration.overrides.quotation.check_permission_qty",
		args: {
			"user": frappe.session.user
		},
		freeze: true,
		callback: async function(r){
			if (r.message == false){
				frm.reload_doc()
				frappe.throw("You don't have enough permission to edit qty of items that coming from opportunity")
				return;
			}
			else {
				frappe.dom.freeze();
				let warn = await check_qty(frm, d);
				if (warn.message == false){
					await frappe.confirm("The quantity in opportunity of this item is not the same as you've provided. Are you sure of changing the qty", 
					() => {
						setTimeout(async () => {
							let packed_items = await get_packed_items(frm, d);
							if (packed_items) update_packed_items_qty(frm, packed_items.items, d)					
							sabaintegration.set_total_without_margin(frm);
							sabaintegration.calculate_total_margin(frm, true);
							frappe.dom.unfreeze();
						}, 2000)
					},
					() => {
						frappe.dom.unfreeze();
						frm.reload_doc()
					})
				}
				else {
					setTimeout(async () => {
						let packed_items = await get_packed_items(frm, d);
						if (packed_items) update_packed_items_qty(frm, packed_items, d)	
						sabaintegration.set_total_without_margin(frm);
						sabaintegration.calculate_total_margin(frm, true);
						frappe.dom.unfreeze();
					}, 2000)
				}
			}
		}
	})
}

const get_packed_items = async(frm, row) => {
	const exists = await frappe.db.get_list("Product Bundle", {filters : {new_item_code: row.item_code}});
	if (!exists || exists.length == 0) return false;

	const product_bundle = await frappe.db.get_doc(
        "Product Bundle", exists[0]['name']
    );

    return product_bundle
}

const update_packed_items_qty = async (frm, packed_items, row) => {
	let items = packed_items;
	for (let packed_item of frm.doc.packed_items){
		let i = 0;
		for (let item of items){
			if (item.item_code == packed_item.item_code && packed_item.section_title == row.section_title){
				packed_item.qty = item.qty * row.qty;
				items.splice(i, 1);
				break;
			}
			i += 1;
		}
	}
	frm.refresh_field("packed_items")
	
}

const check_qty = async function(frm, row){
	if (!frm.doc.opportunity) return true;

	if (!frm.doc.option_number_from_opportunity){
		for (let item of frm.doc.items){
			if (item.opportunity_option_number > 0) {
				frm.doc.option_number_from_opportunity = item.opportunity_option_number
				break
			}
		}
	}
	if (!frm.doc.option_number_from_opportunity) return true;
	return await frappe.call({
		method: "sabaintegration.overrides.quotation.check_qty",
		args: {
			"opportunity": frm.doc.opportunity,
			"option_number": frm.doc.option_number_from_opportunity,
			"item_code": row.item_code,
			"qty":row.qty,
			"section_title": row.section_title
		},
		callback: function(r){
			if (r.message) return r.message;
			else return true
		}
	})
	
	
}

const set_buying_rate = function(frm, d){
	/// use get_item_price
	frappe.call({
		method: "sabaintegration.stock.get_item_details._get_item_price",
		args: {
			item_code: d.item_code,
			price_list: d.from_buying_price_list,
			transaction_date: frm.doc.transaction_date,
			batch_no: d.batch_no
		},
		callback: function(r){
			console.log(r.message)
			if (r.message && r.message[0]){
				let conversion_rate = 1;
				if (frm.doc.conversion_rate) conversion_rate = frm.doc.conversion_rate
				d.base_rate_without_profit_margin = r.message[0][1];
				d.rate_without_profit_margin = r.message[0][1] / conversion_rate;
			}
			else {
				d.base_rate_without_profit_margin = d.base_price_list_rate;
				d.rate_without_profit_margin = d.price_list_rate;
			}
			d.margin_from_supplier_quotation = (d.rate - d.rate_without_profit_margin) / d.rate_without_profit_margin * 100;
			frm.refresh_fields("items")
		}
	})
}