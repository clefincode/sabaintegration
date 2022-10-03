
frappe.ui.form.on('Product Bundle', {

	refresh(frm) {
		// your code here
	}
    ,
    new_item_code: function(frm) {
		let new_item_code1 = frm.doc.new_item_code;
		frappe.call({
			method: 'sabaintegration.www.api.product_bundle_prevents',
			args: {
				item: new_item_code1
			},
			freeze: true,
			callback: function(r) {
				if(r.message) {
					frm.set_value('new_item_code', '');
					// console.log("ss");
					
					// frm.refresh();
				}
				else{
					// console.log("tt");
				}
			}
		});
	}
	// ,
    // items: function(frm) {
	// }
})

frappe.ui.form.on('Product Bundle Item', {

	// refresh(frm) {
	// 	// your code here
	// },
	item_code(frm, cdt, cdn) {
        // let row = frappe.get_doc(cdt, cdn);

		var item = locals[cdt][cdn];

		let item_code1 = item.item_code;

		frappe.call({
			method: 'sabaintegration.www.api.product_bundle_item_prevents',
			args: {
				item: item_code1
			},
			freeze: true,
			callback: function(r) {
				if(r.message) {
					item.item_code = '';
					frm.refresh_field('item_code');

					// console.log("ss1");
					
					// frm.refresh();
				}
				else{
					// console.log("tt1");
				}
			}
		});
    }
	// ,

    // item_code: function(frm) {
	// 	let item_code1 = frm.doc.item_code;
	// 	frappe.call({
	// 		method: 'sabaintegration.www.api.product_bundle_item_prevents',
	// 		args: {
	// 			item: item_code1
	// 		},
	// 		freeze: true,
	// 		callback: function(r) {
	// 			if(r.message) {
	// 				frm.set_value('item_code', '');
	// 				console.log("ss");
					
	// 				// frm.refresh();
	// 			}
	// 			else{
	// 				console.log("tt");
	// 			}
	// 		}
	// 	});
	// }
})





// frappe.call({
// 	method: 'sabaintegration.www.api.producr_bundle_item_prevents',
// 	args: {
// 		item: item_code
// 	},
// 	freeze: true,
// 	callback: function(r) {
// 		if(r.message) {
// 			let doc = frappe.model.sync(r.message)[0];
// 		}
// 	}
// });