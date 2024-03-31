frappe.provide("sabaintegration");
frappe.provide("sabaintegration.costs")

$.extend(sabaintegration, {
    set_total_without_margin: function(frm){
		let total = 0;
		$.each(frm.doc.items || [], function(i, d) {
			total = total + (d.rate_without_profit_margin * d.qty);
		});
		frm.doc.total_rate_without_margin = total;
		frm.refresh_field("total_rate_without_margin");

	},
    calculate_total_margin: function(frm, set_taxes = true){
        if (set_taxes){
            cur_frm.cscript.calculate_taxes_and_totals();
        }
		   
		frm.doc.total_margin = (frm.doc.total - frm.doc.total_rate_without_margin) / frm.doc.total_rate_without_margin * 100;
		frm.doc.total_items_markup_value = frm.doc.total - frm.doc.total_rate_without_margin
		frm.doc.base_total_items_markup_value = frm.doc.total_items_markup_value * frm.doc.conversion_rate;
		
		sabaintegration.set_cost_value()
		sabaintegration.update_costs()
	},
    set_cost_value(){
        if (cur_frm.doc.costs == undefined) return;
        for (let row of cur_frm.doc.costs){
            row.cost_value = cur_frm.doc.net_total * row.cost_percentage / 100;
            row.base_cost_value = row.cost_value * cur_frm.doc.conversion_rate;
        }
        cur_frm.refresh_field("costs")
    },
    update_costs(){
        sabaintegration.update_total_cost()
        sabaintegration.update_profit_loss()
        cur_frm.refresh_fields()
    },
    update_total_cost(){
        let costs_table = cur_frm.doc.costs;
        let total_costs = 0.00;
        if (cur_frm.doc.costs !== undefined) 
        {
            for (let row of costs_table){
                total_costs += row.cost_value;
            }
        }
        cur_frm.doc.total_costs = total_costs;
        cur_frm.doc.base_total_costs = total_costs * cur_frm.doc.conversion_rate;
        cur_frm.doc.total_costs_with_material_costs = cur_frm.doc.total_costs + cur_frm.doc.total_rate_without_margin;
        cur_frm.doc.base_total_costs_with_material_costs = cur_frm.doc.total_costs_with_material_costs * cur_frm.doc.conversion_rate;
    },
    update_profit_loss(){
        cur_frm.doc.expected_profit_loss_value = cur_frm.doc.net_total - cur_frm.doc.total_costs_with_material_costs
        cur_frm.doc.base_expected_profit_loss_value = cur_frm.doc.expected_profit_loss_value * cur_frm.doc.conversion_rate;
        cur_frm.doc.expected_profit_loss = (cur_frm.doc.expected_profit_loss_value * 100) / cur_frm.doc.net_total;
    }
})