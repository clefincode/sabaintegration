frappe.ui.form.on('Sales Invoice', {
	onload: function(frm) {
        // Trigger the rate logic for all items on form load
        frm.doc.items.forEach(function(item) {
            if (!item.rate_100_percent || item.rate_100_percent == 0) {
                frappe.model.set_value(item.doctype, item.name, 'rate_100_percent', item.rate);
            }
        });
        frm.refresh_field('items');  // Refresh the items table
    },
	validate: function(frm) {

		// Create a set to track unique sales orders
        let sales_orders = new Set();

        // Loop through each item in the items table
        frm.doc.items.forEach(item => {
            if (item.sales_order) {
                // Add the sales_order to the set
                sales_orders.add(item.sales_order);
            }
        });

        // Check if there is more than one unique sales order
        if (sales_orders.size > 1) {
            // Throw an error to reject the validation
            frappe.throw(__('Items have different Sales Orders. Please make sure all items are linked to the same Sales Order.'));
            frappe.validated = false; // Prevent form submission
        } else {
            // If there is exactly one sales order, use it
            let sales_order = Array.from(sales_orders)[0];
			
			let total_billing_percentage = 0;

			frappe.call({
				method: "sabaintegration.www.api.get_sales_order_invoices",
				args: {
					sales_order: sales_order
				},
				async: false, 
				callback: function(res) {
						if (res.message) {
							total_billing_percentage = res.message;
						}
				}
			});

			total_billing_percentage += frm.doc.billing_percentage


			if (total_billing_percentage > 100) {
				frappe.msgprint(__('The total billing amount exceeds the %100.'));
				frappe.validated = false;
			}
			
		}
		
  },
  
  billing_percentage: function(frm) {
    frm.doc.items.forEach(function(item) {
        if (item.sales_order) {
            // Calculate the new rate
            item.rate = item.rate_100_percent * frm.doc.billing_percentage / 100;

            // Trigger the rate field's onchange function to ensure other fields get updated
            frm.script_manager.trigger('rate', item.doctype, item.name);

            // Refresh the items table to reflect the changes
            frm.refresh_field('items');
        }
    });
	},

	
})

frappe.ui.form.on('Sales Invoice Item', {
	rate: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        // Check if rate_100_percent is 0, empty, or null
        if (!row.rate_100_percent || row.rate_100_percent == 0) {
            // Set the value of rate_100_percent to rate
            frappe.model.set_value(cdt, cdn, 'rate_100_percent', row.rate);
        }
    },
	refresh: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        // Trigger the rate logic on refresh (including first load)
        if (!row.rate_100_percent || row.rate_100_percent == 0) {
            frappe.model.set_value(cdt, cdn, 'rate_100_percent', row.rate);
        }
    },
});
