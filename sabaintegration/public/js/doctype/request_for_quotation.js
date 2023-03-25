

frappe.ui.form.on("Request for Quotation",{
	setup: function(frm) {
		frm.custom_make_buttons = {
			'Supplier Quotation From Opportunity': 'Create'
		}
		frm.set_df_property('packed_items', 'cannot_add_rows', true);
		//frm.set_df_property('packed_items', 'cannot_delete_rows', true);
		if (!frm.doc.packed_items || frm.doc.packed_items.length < 1) frm.toggle_display('packed_items', false);
	},
	refresh: function(frm, cdt, cdn) {
		if (frm.doc.docstatus === 1 && frm.doc.opportunity) {

			frm.add_custom_button(__('Supplier Quotation From Opportunity'),
				function(){ frm.trigger("make_supplier_quotation_opp") }, __("Create"));

			frm.page.set_inner_btn_group_as_primary(__('Create'));
		}
		else if (frm.doc.docstatus === 0 && frm.doc.packed_items){
			frm.add_custom_button(__('Select Brands'),
				function(){ frm.trigger("select_brands");});
		}
		if (frm.is_new()){
			frm.trigger("schedule_date");
		}
	},

    make_supplier_quotation_opp: function(frm) {
		var doc = frm.doc;
		if (doc.suppliers.length == 1){
			return frappe.call({
				type: "GET",
				method: "sabaintegration.overrides.request_for_quotation.make_supplier_quotation_from_rfq",
				args: {
					"source_name": doc.name,
					"for_supplier": doc.suppliers[0].supplier
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
		var dialog = new frappe.ui.Dialog({
			title: __("Create Supplier Quotation From Opportunity"),
			fields: [
				{	"fieldtype": "Link",
					"label": __("Supplier"),
					"fieldname": "supplier",
					"options": 'Supplier',
					"reqd": 1,
					get_query: () => {
						return {
							filters: [
								["Supplier", "name", "in", frm.doc.suppliers.map((row) => {return row.supplier;})]
							]
						}
					}
				}
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

	select_brands: async function(frm){
		frm.events.setup_by_brand(frm, async (frm, data, brands) => {
			frappe.call({
				method: "sabaintegration.overrides.request_for_quotation.delete_by_brand",
				args: {
					items: frm.doc.items,
					packed_items: frm.doc.packed_items,
					brands: brands
				},
				freeze: true,
				callback: function(r) {
					if(r.message) {
						if (r.message.items)
						{
							frm.clear_table("items");
							frm.refresh_field("items");
							r.message.items.forEach((row) => {
								let item = frm.add_child("items");
								$.extend(item, row);
								item.warehouse = item.warehouse || '';
							});
							frm.clear_table("items");
							frm.refresh_field("items");
							r.message.items.forEach((row) => {
								let item = frm.add_child("items");
								$.extend(item, row);
								item.warehouse = item.warehouse || '';
							});
							frm.refresh_field("items");
						}
						if (r.message.packed_items)
						{
							frm.clear_table("packed_items");
							r.message.packed_items.forEach((row) => {
								let item = frm.add_child("packed_items");
								$.extend(item, row);
								item['warehouse'] = item['warehouse'] || '';
							});
							frm.refresh_field("packed_items");
						}
						frm.dirty();
					}
				}
			});
			
		})
	},

	setup_by_brand: async function(frm, callback) {
		frappe.dom.freeze(__('Please Wait...'))
		let items_brands = [];
		let tested_rows = [];
		for (const item of cur_frm.doc.packed_items){
			if (!tested_rows.includes(item.brand))
			{
				tested_rows.push(item.brand);
				items_brands.push(item.brand);
			}
		}
		for (const item of cur_frm.doc.items){
			if (!tested_rows.includes(item.brand))
			{
				tested_rows.push(item.brand);
				const exists = await frappe.db.get_list("Product Bundle", {filters : {new_item_code: item.item_code}});
				if (!exists || !exists.length) items_brands.push(item.brand);
			}
		}
		frappe.dom.unfreeze()
		const field = [
			{	
				"fieldtype": "Table",
				"label": __("Brands"),
				"fieldname": "brands",
				"fields": [
					{
						fieldname: "brand",
						options: "Brand",
						label: __("Brand"),
						fieldtype: "Link",
						in_list_view: 1,
						reqd: 1,
						get_query: () => {
							return {
								filters: [
									["Brand", "name", "in",  items_brands]
								]
							}
						}
					}
				],
			}
		];
		let dialog = frappe.prompt(field, data => {
			let brands = data.brands || [];
			callback(frm, data, brands);
		})
		let i = 1;
		dialog.fields_dict.brands.df.data = [];
		for (let row of items_brands){
			dialog.fields_dict.brands.df.data.push({"idx": i, "brand": row});
			i += 1;
		}
		dialog.fields_dict.brands.grid.refresh();
	}
})

frappe.ui.form.on("Request for Quotation Item", {
	item_code(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		child.qty = 1;
		refresh_field("items");
		get_item_details(frm.doc, child, cdt, cdn);
		update_product_bundle(frm, child, "add");
	},
	qty(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		update_product_bundle(frm, child, "qty");
	},
	items_remove(frm, cdt, cdn) { 
		var child = locals[cdt][cdn];
		update_product_bundle(frm, child, "remove");
	},	
		
});

const validate_product_bundle = async (frm) => {
    if (!frm.doc.items) return;
	frappe.dom.freeze();

	frappe.call({
		doc: frm.doc,
		method: "make_packing_list",
		callback: function(r){
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

const update_product_bundle = async (frm, row, method) => {
	frappe.dom.freeze()
    if (!frm.doc.items) {
        validate_product_bundle(frm); 
        return;
    }
	if (method == "add"){
		const product_bundle = await get_packed_items(row)
		if (product_bundle){
			let toorder = false;
			for (const bundled_item of product_bundle.items) {
				let exists = false 
				if (cur_frm.doc.packed_items){
					for (const item of cur_frm.doc.packed_items) {
						if (item.item_code == bundled_item.item_code){
							item.qty += bundled_item.qty * row.qty;
							exists = true;
							break
						}
					}
				}
				if (!exists){
					toorder = true;
					let child = frm.add_child("packed_items");
					child.item_code = bundled_item.item_code;
					child.description = bundled_item.description;
					child.qty = bundled_item.qty * row.qty;
					child.uom = bundled_item.uom;
				}
				
			}

			if (toorder){
				new Promise(function (resolve){
					frappe.call({
						doc: frm.doc,
						method: "update_packing_list",
						callback: function(r){
							if (r.message){
								if (r.message){
									frm.doc.packed_items = [];
									frm.refresh_field("packed_items");
									r.message.forEach((row) => {
										let item = frm.add_child("packed_items");
										$.extend(item, row);
										item.item_code = item.item_code || ''
										item.qty = item.qty || 0;
										item.item_name = item.item_name || '';
										item.warehouse = item.warehouse || '';
										item.rate = item.rate || '';
										item.uom = item.uom || '';
										item.brand = item.brand || '';
										
									});
								}
								resolve(true);
							}
						}
					})
				}).then(() => {frm.refresh_field("packed_items");})
			}
			frm.toggle_display('packed_items', true);
		}
	}
	else if (method == "qty"){
		const packed_items = await get_packed_items(row);
		if (!packed_items) {
			frappe.dom.unfreeze();
			return;
		}

		for (const packed_item of packed_items.items){
			for (let pitem of cur_frm.doc.packed_items){
				if (pitem.item_code == packed_item.item_code){
					pitem.qty = packed_item.qty * row.qty;
					const parents = await frappe.db.get_list("Product Bundle Item", {
						filters: {item_code: pitem.item_code}, 
						fields: ["parent", "qty"]
					})
					if (parents.length == 1) continue;

					for (let item of cur_frm.doc.items){
						if (item.item_code != row.item_code){
							for (let parent of parents){
								const item_code = await frappe.db.get_value("Product Bundle", {"name" : parent.parent}, "new_item_code");
								if (item_code.message.new_item_code == item.item_code){
									pitem.qty += parent.qty * item.qty
									break
								}
							}	
						}
					}
				}
			}
		}
	}
	else if (method == "remove"){
		// const exists = await frappe.db.get_list("Product Bundle", {filters : {new_item_code: parent.item_code}});
		// if (exists){
			new Promise(function (resolve){
				frappe.call({
					doc: frm.doc,
					method: "remove_from_packing_list",
					callback: function(r){
						if (r.message){
							frm.doc.packed_items = [];
							frm.refresh_field("packed_items");
							r.message.forEach((row) => {
								let item = frm.add_child("packed_items");
								$.extend(item, row);
								item.item_code = item.item_code || ''
								item.qty = item.qty || 0;
								item.item_name = item.item_name || '';
								item.warehouse = item.warehouse || '';
								item.rate = item.rate || '';
								item.uom = item.uom || '';
								item.brand = item.brand || '';
								
							});
						}
						else frm.doc.packed_items = [];
						resolve(true);
					}
				})
			}).then(() => {frm.refresh_field("packed_items");})
		//}
	}
	frappe.dom.unfreeze()
	frm.refresh_field("packed_items");
}

const get_packed_items = async (parent) => {
    const exists = await frappe.db.get_list("Product Bundle", {filters : {new_item_code: parent.item_code}});

    // if item is not a product bundle
    if (exists.length == 0) return;
  
    //   get product bundle details
    const product_bundle = await frappe.db.get_doc(
        "Product Bundle", exists[0]['name']
    );

    return product_bundle
}

const get_item_details = (doc, row , cdt, cdn) => {
    return frappe.call({
        method: "sabaintegration.overrides.opportunity.get_item_details",
        args: {"item_code":row.item_code, "company": doc.company},
        callback: function(r, rt) {
            if(r.message) {
                $.each(r.message, function(k, v) {
                    frappe.model.set_value(cdt, cdn, k, v);
                });
                refresh_field('image_view', row.name, 'items');
            }
        }
    })
}