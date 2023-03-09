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
	total_margin: function(frm){
		if (frm.doc.items){		
			$.each(frm.doc.items || [], function(i, d) {
				d.margin_from_supplier_quotation = frm.doc.total_margin / frm.doc.items.length;
				frm.script_manager.trigger("margin_from_supplier_quotation", d.doctype, d.name);
			});
			refresh_field("items");
		}
	}
});

////
frappe.ui.form.on('Quotation Item', {
	margin_from_supplier_quotation: function(frm,cdt,cdn){
		var d = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "rate", d.rate_without_profit_margin + (d.margin_from_supplier_quotation / 100 * d.rate_without_profit_margin))
		//frappe.model.set_value(cdt, cdn, "price_list_rate", d.rate_without_profit_margin + (d.margin_from_supplier_quotation / 100 * d.rate_without_profit_margin))
	
	},
	rate: function(frm,cdt,cdn){
		var d = locals[cdt][cdn];
		if (!d.rate_without_profit_margin){
			d.rate_without_profit_margin = d.price_list_rate
		}
		d.margin_from_supplier_quotation = (d.rate - d.rate_without_profit_margin) / d.rate_without_profit_margin * 100 
	}
	

})