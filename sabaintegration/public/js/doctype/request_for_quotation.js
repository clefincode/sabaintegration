

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
		frm.set_df_property('packed_items', 'cannot_delete_rows', true);
	},
    default_profit_margin: function(frm){
        $.each(frm.doc.packed_items || [], function(i, d) {
			if(!d.profit_margin) d.profit_margin = frm.doc.default_profit_margin;
		});
		refresh_field("packed_items");
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

frappe.ui.form.on("Request for Quotation Packed Item", {
	item_code: function(frm, cdt, cdn){
        var d = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "profit_margin", frm.doc.default_profit_margin)
    },
});