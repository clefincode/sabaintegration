// Copyright (c) 2023, Ahmad and contributors
// For license information, please see license.txt

frappe.ui.form.on('Commission Rule Condition', {
	calculation: function(frm, cdt, cdn){
		let d = locals[cdt][cdn];
		if (d.calculation == "Zero"){
			frappe.model.set_value(cdt, cdn, "comm_precent", 0);
		}
		else if (d.calculation == "As Milestone"){
			frappe.model.set_value(cdt, cdn, "comm_precent", d.milestone);
		}
	}
});
