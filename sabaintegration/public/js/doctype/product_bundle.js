// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Product Bundle", {
	refresh: function (frm) {
		
		frm.toggle_enable("new_item_code", frm.is_new());
		frm.set_query("new_item_code", () => {
			return {
				query: "sabaintegration.overrides.product_bundle.get_new_item_code",
                // custom update ... new function created for filters
			};
		});
	}, 
});

frappe.ui.form.on('Product Bundle Item', {
	item_code: function(frm, cdt, cdn){
		var item = locals[cdt][cdn];
		
		for (var row in frm.doc.items){

            if( row != frm.doc.items.length-1){
                if (frm.doc.items[row].item_code == item.item_code){
                    cur_frm.get_field("items").grid.grid_rows[item.idx-1].remove();
                    frappe.show_alert({
                        message:__('Duplicated items not allowed, this row has been deleted automatically'),
                        indicator:'red'
                    }, 6);
                    break;
                }
            }
		}
		frm.refresh();
		
	}
});
		
