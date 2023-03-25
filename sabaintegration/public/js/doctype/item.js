frappe.ui.form.on("Item", {
	onload: function(frm){
		if (!frm.is_new()){
			set_bundle_check(frm.doc.item_code).then((response) => {
				if( response =="Found"){
					frm.set_df_property("is_a_parent_bundle", "read_only", 1);
				}
				else{
					frm.set_df_property("is_a_parent_bundle", "read_only", 0);
				}
			});
		}
		else {
			if (frm.doc.item_defaults == "undefined" || frm.doc.item_defaults == undefined){
				let row = frm.add_child('item_defaults', {
					default_warehouse: "General - S"
				});
				frm.refresh_field('item_defaults');
			}
			
			
        } 
	},
	is_stock_item: function(frm){
		if (frm.doc.is_stock_item == 1){
			frm.set_value('is_a_parent_bundle', 0);
			refresh_field("is_a_parent_bundle");
		}
	},
	is_a_parent_bundle: function(frm) {
		if (frm.doc.is_a_parent_bundle == 1){
			frm.set_value('is_stock_item', 0);
			refresh_field("is_stock_item");
		}
		
	},
})

const set_bundle_check = async (item_code) => {
    const exists = await frappe.db.get_list("Product Bundle", {filters : {new_item_code: item_code}});
    // if item is in a product bundle
    if (exists.length > 0) {
		return "Found" ;
	}
}
