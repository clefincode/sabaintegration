// Copyright (c) 2023, Ahmad and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Commission Template', {
	// refresh: function(frm) {

	// }
});

frappe.ui.form.on('Sales Commission', {
	stage_title: function(frm, cdt, cdn){
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
    }
})
