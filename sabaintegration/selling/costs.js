frappe.provide("sabaintegration");
frappe.provide("sabaintegration.costs")

$.extend(sabaintegration, {
    set_cost_value(){
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
        for (let row of costs_table){
            total_costs += row.cost_value;
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