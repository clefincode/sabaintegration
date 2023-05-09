frappe.provide("sabaintegration");
frappe.provide("sabaintegration.utils");
frappe.provide("sabaintegration.utils.bdn");


$.extend(sabaintegration.utils.bdn, {
    setup_serial_or_batch_no: function() {
		let grid_row = cur_frm.open_grid_row();
		if (!grid_row || !grid_row.grid_form.fields_dict.serial_no ||
			grid_row.grid_form.fields_dict.serial_no.get_status() !== "Write") return;

		frappe.model.get_value('Item', {'name': grid_row.doc.item_code},
			['has_serial_no', 'has_batch_no'], ({has_serial_no, has_batch_no}) => {
				Object.assign(grid_row.doc, {has_serial_no, has_batch_no});

				if (has_serial_no) {
					attach_selector_button(__("Add Serial No"),
						grid_row.grid_form.fields_dict.serial_no.$wrapper, this, grid_row);
				} else if (has_batch_no) {
					attach_selector_button(__("Pick Batch No"),
						grid_row.grid_form.fields_dict.batch_no.$wrapper, this, grid_row);
				}
			}
		);
	},
    
})
function attach_selector_button(inner_text, append_loction, context, grid_row) {
	let $btn_div = $("<div>").css({"margin-bottom": "10px", "margin-top": "10px"})
		.appendTo(append_loction);
	let $btn = $(`<button class="btn btn-sm btn-default">${inner_text}</button>`)
		.appendTo($btn_div);
	console.log(context)
	$btn.on("click", function() {
		context.show_serial_batch_selector(grid_row.frm, grid_row.doc, "", "", true);
	});
}
sabaintegration.utils.bdn.show_serial_batch_selector = function (frm, d, callback, on_close, show_dialog) {
    let warehouse, receiving_stock, existing_stock;
	if (frm.doc.is_return) {
		if (["Purchase Receipt", "Purchase Invoice"].includes(frm.doc.doctype)) {
			existing_stock = true;
			warehouse = d.warehouse;
		} else if (["Delivery Note", "Sales Invoice"].includes(frm.doc.doctype)) {
			receiving_stock = true;
		}
	} else {
		if (frm.doc.doctype == "Stock Entry") {
			if (frm.doc.purpose == "Material Receipt") {
				receiving_stock = true;
			} else {
				existing_stock = true;
				warehouse = d.s_warehouse;
			}
		} else {
			existing_stock = true;
			warehouse = d.warehouse;
		}
	}

	if (!warehouse) {
		if (receiving_stock) {
			warehouse = ["like", ""];
		} else if (existing_stock) {
			warehouse = ["!=", ""];
		}
	}

	frappe.require("assets/sabaintegration/js/utils/bdn_serial_no_batch_selector.js", function() {
		new sabaintegration.BDNSerialNoBatchSelector({
			frm: frm,
			item: d,
			warehouse_details: {
				type: "Warehouse",
				name: warehouse
			},
			callback: callback,
			on_close: on_close
		}, show_dialog);
	});
}