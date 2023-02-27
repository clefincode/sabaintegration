// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Product Bundle", {
	refresh: function (frm) {
		frm.toggle_enable("new_item_code", frm.is_new());
		frm.set_query("new_item_code", () => {
			return {
				query: "sabaintegration.overrides.product_bundle_filters_for_new_item_code.get_new_item_code",
                // custom update ... new function created for filters
			};
		});
	},
});
