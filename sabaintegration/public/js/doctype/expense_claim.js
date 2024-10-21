cur_frm.cscript.onload = function(doc) {
	if (doc.__islocal) {
		cur_frm.cscript.clear_sanctioned_in_expense_claim_currency(doc);
	}
};

cur_frm.cscript.clear_sanctioned_in_expense_claim_currency = function(doc) {
	var val = doc.expenses || [];
	for(var i = 0; i<val.length; i++){
		val[i].sanctioned_amount_in_expense_claim_currency ='';
	}

	doc.total_sanctioned_amount_in_expense_claim_currency = '';
	refresh_many(['sanctioned_amount_in_expense_claim_currency', 'total_sanctioned_amount_in_expense_claim_currency']);
};

cur_frm.cscript.validate = function(doc) {
	cur_frm.cscript.calculate_total_in_expense_claim_currency(doc);
};

frappe.ui.form.on('Expense Claim', {
    onload: function(frm){
        if (frm.is_new()){
            if (!frm.doc.exchange_rate || frm.doc.exchange_rate == 0){
                var company_currency = frappe.get_doc(":Company", frm.doc.company).default_currency;
                frm.events.set_exchange_rate(frm, frm.doc.currency, company_currency);
            }
        }
    },
    refresh: function(frm){
        frm.trigger("change_form_labels");
    },
    change_form_labels: function(frm){
        let company_currency = erpnext.get_currency(frm.doc.company);
        let base_fields = ["total_sanctioned_amount", "total_taxes_and_charges", 
        "total_advance_amount", "grand_total", "total_claimed_amount", 
        "total_amount_reimbursed"]

        let currency_fields = ["total_sanctioned_amount_in_expense_claim_currency", "total_taxes_and_charges_in_expense_claim_currency",
        "total_advance_amount_in_expense_claim_currency", "grand_total_in_expense_claim_currency", "total_claimed_amount_in_expense_claim_currency"]
        
        for (let f of base_fields){
            frm.set_df_property(f, "options", company_currency);
            frm.set_currency_labels([f], company_currency);
        }

        for (let f of currency_fields){
            //frm.set_df_property(f, "options", frm.doc.currency);
            frm.set_currency_labels([f], frm.doc.currency);
        }
        
        frm.set_currency_labels(["sanctioned_amount_in_expense_claim_currency", "amount_in_expense_claim_currency"], frm.doc.currency, "expenses");
		
        frm.set_currency_labels([
			"rate_in_in_expense_claim_currency", "tax_amount_in_expense_claim_currency", "total_in_expense_claim_currency"
		], frm.doc.currency, "taxes");

        

    },
    currency: function(frm){
        var company_currency = frappe.get_doc(":Company", frm.doc.company).default_currency;
        frm.events.set_exchange_rate(frm, frm.doc.currency, company_currency);
        frm.trigger("change_form_labels")
    },
    set_exchange_rate: function(frm, from_currency, to_currency){
        frappe.call({
            method: "erpnext.setup.utils.get_exchange_rate",
            args: {
                "from_currency": from_currency,
                "to_currency": to_currency
            },
            freeze: true,
            callback: function(r){
                if (r.message){
                    frappe.model.set_value(frm.doc.doctype, frm.doc.name, "exchange_rate", r.message);
                    frm.refresh_field("exchange_rate")
                }
            }
        })
    },
    grand_total_in_expense_claim_currency: function(frm) {
		frm.set_value("grand_total", frm.doc.grand_total_in_expense_claim_currency * frm.doc.exchange_rate);
	},
    get_taxes: function(frm){
        if(frm.doc.taxes) {
			frappe.call({
				method: "calculate_taxes_in_expense_claim_currency",
				doc: frm.doc,
				callback: () => {
					refresh_field("taxes");
				}
			});
		}
    },
    calculate_grand_total_in_expense_claim_currency: function(frm) {
		var grand_total_in_expense_calim_currency = flt(frm.doc.total_sanctioned_amount_in_expense_claim_currency) + flt(frm.doc.total_taxes_and_charges_in_expense_claim_currency) - flt(frm.doc.total_advance_amount_in_expense_claim_currency);
		frm.set_value("grand_total_in_expense_claim_currency", grand_total_in_expense_calim_currency);
		frm.refresh_fields();
	},
    exchange_rate: function(frm){
        $.each((frm.doc.expenses || []), function(i, d) {
            d.amount = d.amount_in_expense_claim_currency * frm.doc.exchange_rate;  
            frappe.model.set_value(d.doctype, d.name, "sanctioned_amount", d.sanctioned_amount_in_expense_claim_currency * frm.doc.exchange_rate);
        });
        $.each((frm.doc.taxes || []), function(i, d) {
            d.rate = d.rate_in_in_expense_claim_currency * frm.doc.exchange_rate;  
            frappe.model.set_value(d.doctype, d.name, "tax_amount", d.tax_amount_in_expense_claim_currency * frm.doc.exchange_rate);
        });
    },
    project: function(frm) {
        if (frm.doc.project) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Project',
                    name: frm.doc.project,
                },
                callback: function(r) {
                    if (r.message) {
                        let project = r.message;
                        if (project.cost_center) {
                            frm.set_value('cost_center', project.cost_center);
    
                            // Set cost center for table field
                            if (frm.doc.expenses) {
                                frm.doc.expenses.forEach(function(row) {
                                    frappe.model.set_value(row.doctype, row.name, 'cost_center', project.cost_center);
                                    frappe.model.set_value(row.doctype, row.name, 'project', frm.doc.project);

                                });
                            }
                        } else {
                            frappe.msgprint(__('The selected project does not have a default cost center.'));
                        }
                    }
                }
            });
        }
    }
})

frappe.ui.form.on('Expense Claim Detail', {
    amount_in_expense_claim_currency: function(frm, cdt, cdn){
        var d = locals[cdt][cdn];
        if (frm.doc.exchange_rate == 0 || !frm.doc.exchange_rate || frm.doc.exchange_rate == undefined || frm.doc.exchange_rate == 'undefined'){
            d.amount_in_expense_claim_currency = 0;
            frm.refresh_field("amount_in_expense_claim_currency")
            frappe.throw("Exchange Rate is Zero!!");
        }
        frappe.model.set_value(cdt, cdn, 'sanctioned_amount_in_expense_claim_currency', d.amount_in_expense_claim_currency);
        d.amount = d.amount_in_expense_claim_currency * frm.doc.exchange_rate;
    },
    sanctioned_amount_in_expense_claim_currency: async function(frm, cdt, cdn){
        var d = locals[cdt][cdn];
        if (frm.doc.exchange_rate == 0 || !frm.doc.exchange_rate || frm.doc.exchange_rate == undefined || frm.doc.exchange_rate == 'undefined'){
            d.amount_in_expense_claim_currency = 0;
            frm.refresh_field("sanctioned_amount_in_expense_claim_currency")
            frappe.throw("Exchange Rate is Zero!!");
        }
        frappe.model.set_value(cdt, cdn, "sanctioned_amount", d.sanctioned_amount_in_expense_claim_currency * frm.doc.exchange_rate); 
        await cur_frm.cscript.calculate_total_in_expense_claim_currency(frm.doc, cdt, cdn);
        await frm.trigger("get_taxes");
        frm.trigger("calculate_grand_total_in_expense_claim_currency");
        if (d.amount_in_expense_claim_currency != 0){
            frappe.model.set_value(cdt, cdn, 'amount_in_expense_claim_currency', d.sanctioned_amount_in_expense_claim_currency)
            d.amount = d.amount_in_expense_claim_currency * frm.doc.exchange_rate;
        }
    
    }
})

frappe.ui.form.on("Expense Taxes and Charges", {
    rate_in_in_expense_claim_currency: function(frm, cdt, cdn){
        var d = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "rate", d.rate_in_in_expense_claim_currency * frm.doc.exchange_rate);

        if(!d.tax_amount_in_expense_claim_currency) {
			d.tax_amount_in_expense_claim_currency = flt(frm.doc.total_sanctioned_amount_in_expense_claim_currency) * (flt(d.rate_in_expense_claim_currency)/100);
		}
		frm.trigger("calculate_total_tax_in_expense_claim_currency", cdt, cdn);
    },
    calculate_total_tax_in_expense_claim_currency: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		child.total_in_expense_claim_currency = flt(frm.doc.total_sanctioned_amount_in_expense_claim_currency) + flt(child.tax_amount_in_expense_claim_currency);
		frm.trigger("calculate_tax_amount_in_expense_claim_currency", cdt, cdn);

    },
    calculate_tax_amount_in_expense_claim_currency: function(frm) {
		frm.doc.total_taxes_and_charges_in_expense_claim_currency = 0;
		(frm.doc.taxes || []).forEach(function(d) {
			frm.doc.total_taxes_and_charges_in_expense_claim_currency += d.tax_amount_in_expense_claim_currency;
		});
		frm.trigger("calculate_grand_total_in_expense_claim_currency");
	},
    tax_amount_in_expense_claim_currency: function(frm, cdt, cdn) {
		frm.trigger("calculate_total_tax_in_expense_claim_currency", cdt, cdn);
	}
})

cur_frm.cscript.calculate_total_in_expense_claim_currency = function(doc){
	doc.total_claimed_amount_in_expense_claim_currency = 0;
	doc.total_sanctioned_amount_in_expense_claim_currency = 0;
	$.each((doc.expenses || []), function(i, d) {
		doc.total_claimed_amount_in_expense_claim_currency += d.amount_in_expense_claim_currency;
		doc.total_sanctioned_amount_in_expense_claim_currency += d.sanctioned_amount_in_expense_claim_currency;
	});
};