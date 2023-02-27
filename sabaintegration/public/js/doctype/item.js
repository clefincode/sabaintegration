// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Item", {
	onload: function(frm){
		if (frm.is_new()) {
            let row = frm.add_child('item_defaults', {
                default_warehouse: "General - S"
            });
            frm.refresh_field('item_defaults');
        } 
	},
	is_a_parent_bundle: function(frm) {
		if (frm.doc.is_a_parent_bundle == 1){
			frm.set_value('is_stock_item', 0);
			refresh_field("is_stock_item");
		}
		
	},
})

