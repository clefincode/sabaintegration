

frappe.ui.form.on("Request for Quotation",{
	setup: function(frm) {
		frm.custom_make_buttons = {
			'Supplier Quotation': 'Create'
		}
		frm.fields_dict["suppliers"].grid.get_field("contact").get_query = function(doc, cdt, cdn) {
			let d = locals[cdt][cdn];
			return {
				query: "erpnext.buying.doctype.request_for_quotation.request_for_quotation.get_supplier_contacts",
				filters: {'supplier': d.supplier}
			}
		}
		frm.set_df_property('packed_items', 'cannot_add_rows', true);
		//frm.set_df_property('packed_items', 'cannot_delete_rows', true);
		if (!frm.doc.packed_items) frm.toggle_display('packed_items', false);
	},
    
    make_suppplier_quotation: function(frm) {
		var doc = frm.doc;
		var dialog = new frappe.ui.Dialog({
			title: __("Create Supplier Quotation"),
			fields: [
				{	"fieldtype": "Select", "label": __("Supplier"),
					"fieldname": "supplier",
					"options": doc.suppliers.map(d => d.supplier),
					"reqd": 1,
					"default": doc.suppliers.length === 1 ? doc.suppliers[0].supplier_name : "" },
			],
			primary_action_label: __("Create"),
			primary_action: (args) => {
				if(!args) return;
				dialog.hide();

				return frappe.call({
					type: "GET",
					method: "sabaintegration.overrides.request_for_quotation.make_supplier_quotation_from_rfq",
					args: {
						"source_name": doc.name,
						"for_supplier": args.supplier
					},
					freeze: true,
					callback: function(r) {
						if(!r.exc) {
							var doc = frappe.model.sync(r.message);
							frappe.set_route("Form", r.message.doctype, r.message.name);
						}
					}
				});
			}
		});

		dialog.show()
	},
})

frappe.ui.form.on("Request for Quotation Item", {
	item_code(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		child.qty = 1;
		refresh_field("items");
		//validate_product_bundle(frm);

	},
	qty(frm, cdt, cdn) {
		//validate_product_bundle(frm);
	},
	items_remove(frm, cdt, cdn) { 
		//validate_product_bundle(frm);
	},	
		
});

const validate_product_bundle = async (frm) => {
    if (!frm.doc.items) return;
	frappe.dom.freeze();

	frappe.call({
		doc: frm.doc,
		method: "make_packing_list",
		callback: function(r){
			console.log(r.message)
			frm.clear_table("packed_items");
			if (r.message){
				r.message.forEach((row) => {
					let packed_item = frm.add_child("packed_items");
					packed_item.item_code = row.item_code || '';
					packed_item.qty = row.qty || 0;
					packed_item.uom = row.uom || '';
					packed_item.description = row.description || '';
					packed_item.brand = row.brand || '';

				})
				
				if (frm.doc.packed_items) frm.toggle_display('packed_items', true);
    			
			}
			frm.refresh_field("packed_items");
			frappe.dom.unfreeze()
		}
		

	})

}