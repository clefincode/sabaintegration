frappe.ui.form.on("Opportunity", {
    setup(frm) {
        // frm.set_df_property("bundle_items", "cannot_add_rows", true);
        // frm.set_df_property("bundle_items", "cannot_delete_rows", true);

        frm.set_df_property('packed_items', 'cannot_add_rows', true);
		frm.set_df_property('packed_items', 'cannot_delete_rows', true);

        if (!frm.doc.packed_items) frm.toggle_display('packed_items', false);
        if (frm.is_new) frm.selected_option = 0
        else{
            if (frm.doc.with_items) frm.trigger("set_option")
        }
    },
    

    condition(frm) {
        if (frm.doc.condition == "Internal Preparation") {
            set_field_options("status", [
            "Open",
            "Waiting for Technical Reply",
            "Waiting for Consultant/Customer Reply OR Updates",
            "Waiting for Marketing Response",
            "Waiting for Merge and/or Printing",
            "Ready for Quoting/Technical Submitting",
            ]);
        } else if (frm.doc.condition == "Sales Following Up") {
            set_field_options("status", [
            "Technical Proposal submitted & waiting For Consultant/Customer approval",
            "Waiting for Tender (Commercial submission) Date",
            "Quotation (Commercial Proposal )has been sent, Waiting for feedback",
            ]);
        } else if (frm.doc.condition == "Pipeline") {
            set_field_options("status", [
            "Super Hot Deal (Closing in less than a month)",
            "Serious Deal (Closing in the coming 3 months)",
            "True opportunity (Closing 3-6 months)",
            ]);
        } else if (frm.doc.condition == "Future Pipeline") {
            set_field_options("status", [
            "Closing 6-9 Months",
            "Closing 9-12 Months",
            "Closing in more than 1 Year",
            ]);
        } else if (frm.doc.condition == "Won") {
            set_field_options("status", [
            "Due to best Pricing",
            "Due to providing best technical option",
            "Due to our technical support",
            "Customer trust in us",
            "Stock Availability",
            "Multi winning reasons",
            ]);
        } else if (frm.doc.condition == "Lost") {
            set_field_options("status", [
            "Lost Due to High Prices",
            "Lost Due to Delay of Reply",
            "Lost Due to Customer Dissatisfaction",
            "Lost Due to Long Delivery Time",
            "Lost because Customer Preferred Another Partner",
            ]);
        } else if (frm.doc.condition == "Hold") {
            set_field_options("status", [
            "Project Postponed",
            "Customer Unreachable for more than 4 weeks",
            "No direct or clear response from the customer",
            ]);
        } else if (frm.doc.condition == "Closed") {
            set_field_options("status", [
            "Customer Was just budgeting",
            "More than Customer's Budget",
            "Project Cancelled",
            "Not Interested",
            "Not In Portfolio",
            "Too old/No enough data/Test",
            ]);
        }
    },
    refresh(frm) {
        //frm.toggle_display("bundle_items", false);
        if (frm.is_new()) frm.selected_option = 0; 
        else if (frm.doc.with_items) frm.trigger("set_option")
        if (!frm.is_new()){
            var num = 0;
            if (frm.doc.option_1.length != 0 ){num=num+1;}
            if (frm.doc.option_2.length != 0 ){num=num+1;}
            if (frm.doc.option_3.length != 0){num=num+1;}
            if (frm.doc.option_4.length != 0 ){num=num+1;}
            if (frm.doc.option_5.length != 0 ){num=num+1;}
            if (frm.doc.option_6.length != 0 ){num=num+1;}
            if (frm.doc.option_7.length != 0 ){num=num+1;}
            if (frm.doc.option_8.length != 0 ){num=num+1;}
            if (frm.doc.option_9.length != 0 ){num=num+1;}
            if (frm.doc.option_10.length != 0 ){num=num+1;}

            if (frm.doc.option_1.length != 0){
                frm.set_df_property('option_2', 'hidden', 0);
                frm.add_custom_button('Option 1', () => {
                    frm.events.set_option_items(frm,1);

                }, num+ ' Options');
            }
            if (frm.doc.option_2.length != 0){
                frm.set_df_property('option_2', 'hidden', 0);
                frm.set_df_property('option_3', 'hidden', 0);
                frm.add_custom_button('Option 2', () => {
                    frm.events.set_option_items(frm,2);

                }, num+ ' Options');
            }
            else{
                frm.set_df_property('option_2', 'hidden', 0);
            }
            if (frm.doc.option_3.length != 0){
                frm.set_df_property('option_3', 'hidden', 0);
                frm.set_df_property('option_4', 'hidden', 0);
                frm.add_custom_button('Option 3', () => {
                    frm.events.set_option_items(frm,3);

                }, num+ ' Options');
            }
            else{
                frm.set_df_property('option_3', 'hidden', 1);
            }
            if (frm.doc.option_4.length != 0){
                frm.set_df_property('option_4', 'hidden', 0);
                frm.set_df_property('option_5', 'hidden', 0);
                frm.add_custom_button('Option 4', () => {
                    frm.events.set_option_items(frm,4);

                }, num+ ' Options');
            }
            else{
                frm.set_df_property('option_4', 'hidden', 1);
            }
            if (frm.doc.option_5.length != 0){
                frm.set_df_property('option_5', 'hidden', 0);
                frm.set_df_property('option_6', 'hidden', 0);
                frm.add_custom_button('Option 5', () => {
                    frm.events.set_option_items(frm,5);

                }, num+ ' Options');
            }
            else{
                frm.set_df_property('option_5', 'hidden', 1);
            }
            if (frm.doc.option_6.length != 0){
                frm.set_df_property('option_6', 'hidden', 0);
                frm.set_df_property('option_7', 'hidden', 0);
                frm.add_custom_button('Option 6', () => {
                    frm.events.set_option_items(frm,6);
                }, num+ ' Options');
            }
            else{
                frm.set_df_property('option_6', 'hidden', 1);
            }
            if (frm.doc.option_7.length != 0){
                frm.set_df_property('option_7', 'hidden', 0);
                frm.set_df_property('option_8', 'hidden', 0);
                frm.add_custom_button('Option 7', () => {
                    frm.events.set_option_items(frm,7);

                }, num+ ' Options');
            }
            else{
                frm.set_df_property('option_7', 'hidden', 1);
            }
            if (frm.doc.option_8.length != 0){
                frm.set_df_property('option_8', 'hidden', 0);
                frm.set_df_property('option_9', 'hidden', 0);
                frm.add_custom_button('Option 8', () => {
                    frm.events.set_option_items(frm,8);

                }, num+ ' Options');
            }
            else{
                frm.set_df_property('option_8', 'hidden', 1);
            }
            if (frm.doc.option_9.length != 0){
                frm.set_df_property('option_9', 'hidden', 0);
                frm.set_df_property('option_10', 'hidden', 0);
                frm.add_custom_button('Option 9', () => {
                    frm.events.set_option_items(frm,9);

                }, num+ ' Options');
            }
            else{
                frm.set_df_property('option_9', 'hidden', 1);
            }
            if (frm.doc.option_10.length != 0){
                frm.set_df_property('option_10', 'hidden', 0);
                frm.add_custom_button('Option 10', () => {
                    frm.events.set_option_items(frm,10);

                }, num+ ' Options');
            }
            else{
                frm.set_df_property('option_10', 'hidden', 1);
            }
        };
    },
    set_option_items: function(frm, option_number){
        frm.doc.items=[];
        switch (option_number){
            case 1:
                cur_frm.set_value("items", frm.doc.option_1);
                break;
            case 2:
                cur_frm.set_value("items", frm.doc.option_2);
                break;
            case 3:
                cur_frm.set_value("items", frm.doc.option_3);
                break;
            case 4:
                cur_frm.set_value("items", frm.doc.option_4);
                break;
            case 5:
                cur_frm.set_value("items", frm.doc.option_5);
                break;
            case 6:
                cur_frm.set_value("items", frm.doc.option_6);
                break;
            case 7:
                cur_frm.set_value("items", frm.doc.option_7);
                break;
            case 8:
                cur_frm.set_value("items", frm.doc.option_8);
                break;
            case 9:
                cur_frm.set_value("items", frm.doc.option_9);
                break;
            case 10:
                cur_frm.set_value("items", frm.doc.option_10);
                break;
        
        }
        refresh_field("items");
        validate_product_bundle(frm);
    },

    make_request_for_quotation: function(frm) {
		frappe.model.open_mapped_doc({
			method: "sabaintegration.overrides.opportunity.make_request_for_quotation",
			frm: frm
		})
	},
    set_option: function(frm){
        for(let row in frm.doc.items){
            if (frm.doc.items[row]["option_number"]){
                frm.selected_option = frm.doc.items[row]["option_number"]
                break
            }
        }
        frm.events.set_option_html(frm.selected_option)
    },
    set_option_html: function(option){
        if (document.getElementById('option_number')) {
            document.getElementById('option_number').remove();
        }

        if (option != 0){
            var x = document.querySelectorAll(".section-head");
            for (var i = 0; i < x.length; i++) {
                if(x[i].innerHTML.indexOf("Items") !== -1 && x[i].innerHTML.indexOf("Parents of Packed Items") == -1 && x[i].innerHTML.indexOf("Packed Items") == -1) {
                    x[i].innerHTML+= "<small id='option_number'  style='padding: 3px 10px; font-weight: 500;background:#fff5f5; margin:10px; color:#e24c4c;'>Option "+option+"</small>";
                }
            }
        }
    }
});

frappe.ui.form.on('Opportunity Item', { 
    item_code(frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        child.qty = 1;
        refresh_field("items");
        validate_product_bundle(frm);

    },
    qty(frm, cdt, cdn) {
        validate_product_bundle(frm);
    },
    items_remove(frm, cdt, cdn) { 
        validate_product_bundle(frm);
    },
    
 
});


frappe.ui.form.on('Opportunity Option', { 
    //set option number in option field 
    //and add the new item to the items table if this option is the selected one
    item_code: function(frm,cdt,cdn){
        var d = locals[cdt][cdn]
        if (d.parentfield.charAt(d.parentfield.length - 1) == "0")
            frappe.model.set_value(cdt, cdn, "option_number", 10)
        else frappe.model.set_value(cdt, cdn, "option_number", parseInt(d.parentfield.charAt(d.parentfield.length - 1)))
        if (frm.selected_option == d.option_number) 
        update_product_bundle(frm, d, cdt, cdn, "add")
    },
    ///change the qty of the item in items if this option is the selected option
    qty: function(frm,cdt,cdn){
        var d = locals[cdt][cdn]
        if (frm.selected_option == d.option_number) 
        update_product_bundle(frm, d, cdt, cdn, "qty")
    },
    //for each option, when adding new row, show the next option table
    option_1_add(frm, cdt, cdn) { 
        var child1 = locals[cdt][cdn];
        child1.qty = 1;
        refresh_field("option_1");
        frm.set_df_property('option_2', 'hidden', 0)
    },
    option_1_remove(frm, cdt, cdn) { 
        if (frm.selected_option == 1 && frm.doc.option_1.length > 0)  frm.events.set_option_items(frm,1);
        else if (frm.selected_option == 1 && frm.doc.option_1.length == 0) {
            frm.selected_option = 0
            frm.events.set_option_items(frm,0);
            
        }
    },
    option_2_add(frm, cdt, cdn) { 
        var child2 = locals[cdt][cdn];
        child2.qty = 1;
        refresh_field("option_2");
        frm.set_df_property('option_3', 'hidden', 0)
    },
    option_2_remove(frm, cdt, cdn) { 
        if (frm.selected_option == 2 && frm.doc.option_2.length > 0) frm.events.set_option_items(frm,2);
        else if (frm.selected_option == 2 && frm.doc.option_2.length == 0) {
            frm.selected_option = 0
            frm.events.set_option_items(frm,0);
        }
    },
    option_3_add(frm, cdt, cdn) { 
        var child3 = locals[cdt][cdn];
        child3.qty = 1;
        refresh_field("option_3");
        frm.set_df_property('option_4', 'hidden', 0)
    },
    option_3_remove(frm, cdt, cdn) { 
        if (frm.selected_option == 3 && frm.doc.option_3.length > 0) frm.events.set_option_items(frm,3);
        else if (frm.selected_option == 3 && frm.doc.option_3.length == 0) {
            frm.selected_option = 0
            frm.events.set_option_items(frm,0);
        }
    },
    option_4_add(frm, cdt, cdn) { 
        var child4 = locals[cdt][cdn];
        child4.qty = 1;
        refresh_field("option_4");
        frm.set_df_property('option_5', 'hidden', 0)
    },
    option_4_remove(frm, cdt, cdn) { 
        if (frm.selected_option == 4 && frm.doc.option_4.length > 0) frm.events.set_option_items(frm,4);
        else if (frm.selected_option == 4 && frm.doc.option_4.length == 0) {
            frm.selected_option = 0
            frm.events.set_option_items(frm,0);
        }
    },
    option_5_add(frm, cdt, cdn) { 
        var child5 = locals[cdt][cdn];
        child5.qty = 1;
        refresh_field("option_5");
        frm.set_df_property('option_6', 'hidden', 0)
    },
    option_5_remove(frm, cdt, cdn) { 
        if (frm.selected_option == 5 && frm.doc.option_5.length > 0) frm.events.set_option_items(frm,5);
        else if (frm.selected_option == 5 && frm.doc.option_5.length == 0) {
            frm.selected_option = 0
            frm.events.set_option_items(frm,0);
        }
    },
    option_6_add(frm, cdt, cdn) { 
        var child6 = locals[cdt][cdn];
        child6.qty = 1;
        refresh_field("option_6");
        frm.set_df_property('option_7', 'hidden', 0)
    },
    option_6_remove(frm, cdt, cdn) { 
        if (frm.selected_option == 6 && frm.doc.option_6.length > 0) frm.events.set_option_items(frm,6);
        else if (frm.selected_option == 6 && frm.doc.option_6.length == 0) {
            frm.selected_option = 0
            frm.events.set_option_items(frm,0);
        }
    },
    option_7_add(frm, cdt, cdn) { 
        var child7 = locals[cdt][cdn];
        child7.qty = 1;
        refresh_field("option_7");
        frm.set_df_property('option_8', 'hidden', 0)
    },
    option_7_remove(frm, cdt, cdn) { 
        if (frm.selected_option == 7 && frm.doc.option_7.length > 0) frm.events.set_option_items(frm,7);
        else if (frm.selected_option == 7 && frm.doc.option_7.length == 0) {
            frm.selected_option = 0
            frm.events.set_option_items(frm,0);
        }
    },
    option_8_add(frm, cdt, cdn) { 
        var child8 = locals[cdt][cdn];
        child8.qty = 1;
        refresh_field("option_8");
        frm.set_df_property('option_9', 'hidden', 0)
    },
    option_8_remove(frm, cdt, cdn) { 
        if (frm.selected_option == 8 && frm.doc.option_8.length > 0) frm.events.set_option_items(frm,8);
        else if (frm.selected_option == 8 && frm.doc.option_8.length == 0) {
            frm.selected_option = 0
            frm.events.set_option_items(frm,0);
        }
    },
    option_9_add(frm, cdt, cdn) { 
        var child9 = locals[cdt][cdn];
        child9.qty = 1;
        refresh_field("option_9");
        frm.set_df_property('option_10', 'hidden', 0)
    },
    option_9_remove(frm, cdt, cdn) { 
        if (frm.selected_option == 9 && frm.doc.option_9.length > 0) frm.events.set_option_items(frm,9);
        else if (frm.selected_option == 9 && frm.doc.option_9.length == 0) {
            frm.selected_option = 0
            frm.events.set_option_items(frm,0);
        }
    },
    option_10_add(frm, cdt, cdn) { 
        var child10 = locals[cdt][cdn];
        child10.qty = 1;
        refresh_field("option_10");
    },
    option_10_remove(frm, cdt, cdn) { 
        if (frm.selected_option == 10 && frm.doc.option_10.length > 0) frm.events.set_option_items(frm,10);
        else if (frm.selected_option == 10 && frm.doc.option_10.length == 0) {
            frm.selected_option = 0
            frm.events.set_option_items(frm,0);
        }
    },
});



const validate_product_bundle = async (frm) => {
    frappe.dom.freeze()

    if (!frm.doc.with_items) return;
  
    // let's empty the table first
    frm.doc.parent_items = [];
    frm.clear_table("parent_items");
    //   iterate opportunity items
    for (const row of frm.doc.items) {
        if (!row.item_code) continue;
        await add_packed_items(frm, row)
    }
    frm.refresh_field("parent_items");
    frm.trigger("set_option")
    frappe.dom.unfreeze()
    // frappe.call({
    //     doc: frm.doc,
    //     method: 'group_similar_bundle_items',
    //     callback: function(r) {
    //         frm.clear_table("bundle_items");
    //         if (r.message){
    //             r.message.forEach((row) => {
    //                 let bundle_item = frm.add_child("bundle_items");
    //                 //bundle_item.parent_item = row.parent_item || ''
    //                 bundle_item.item_code = row.item_code || ''
    //                 bundle_item.qty = row.qty || 0;
    //                 bundle_item.uom = row.uom || '';
    //                 bundle_item.description = row.description || '';
                    
    //             });
    //             frm.refresh_field("parent_items");
    //             frm.refresh_field("bundle_items");

    //             frappe.dom.unfreeze()
    //         }
    //         else{
    //             frappe.dom.unfreeze()
    //         }
    //     }
        
    // });

    
    //frappe.dom.unfreeze()
    // frm.save();
        // frm.save();
    // let myPromise = new Promise(function (resolve, reject){
    //     ///
    //     resolve()
    // })
    // myPromise.then()
    // frappe.call({
    //     method: 'sabaintegration.www.api.group_similar_bundle_items',
    //     args: {
    //         doc: frm.doc.name
    //     },
    //     freeze: true,
    //     callback: function(r) {
    //         if(r.message) {
    //             console.log(r.message.bundle_items);
    //             // frm.doc.bundle_items=[];
    //             cur_frm.set_value("bundle_items", r.message.bundle_items);
    //             cur_frm.refresh_field("bundle_items");
    //         }
    //     }
    // });
};

const update_product_bundle = async (frm, row, cdt, cdn, method) => {
    frappe.dom.freeze()
    if (!frm.doc.items) {
        validate_product_bundle(frm); 
        return;
    }
    if (method == "add"){
        let child = frm.add_child("items");

        child.item_code = row.item_code;
        child.qty = row.qty || 1;
        child.description = row.description || "";
        child.uom = row.uom;
        child.option_number = row.option_number;
        child.item_name = row.item_name || "";
        child.section_title = row.section_title || "";
        child.warehouse = row.warehouse || "";
        await get_item_details(frm, row, cdt, cdn);
        await add_packed_items(frm, row);

    }
    else if (method == "qty"){
        let items = frm.doc.items
        for (let i in items){
            if (items[i].item_code == row.item_code){
                frm.doc.items[i].qty = row.qty;
                const product_bundle = await get_packed_items(row)
                if (product_bundle){
                    for (const bundled_item of product_bundle.items) {
                        for (const packed_item of cur_frm.doc.parent_items){
                            if (packed_item.item_code == bundled_item.item_code &&
                                packed_item.parent_item == row.item_code){
                                packed_item.qty = row.qty * bundled_item.qty;
                                break
                            }
                        }
                    }
                }
                break;
            }
        }
    }
    
    frm.refresh_field("items");
    frm.refresh_field("parent_items");
    frappe.dom.unfreeze()
}

const add_packed_items = async (frm, parent) => {
    const product_bundle = await get_packed_items(parent)
    // iterate bundle items
    if (product_bundle){
        for (const bundled_item of product_bundle.items) {

            let child = frm.add_child("parent_items");
            child.parent_item = parent.item_code;
            child.item_code = bundled_item.item_code;
            child.description = bundled_item.description;
            child.qty = bundled_item.qty * parent.qty;
            child.uom = bundled_item.uom;
            await frappe.db.get_value("Item Default", {"parent": bundled_item.item_code}, "default_warehouse",  (r) => {
                if (r) child.warehouse = r.default_warehouse
            }, "Item")
        } 
    }
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

$.extend(cur_frm.cscript, new erpnext.crm.Opportunity({frm: cur_frm}));

cur_frm.cscript.item_code = function(doc, cdt, cdn) {
	var d = locals[cdt][cdn];
	if (d.item_code) {
		get_item_details(doc, d, cdt, cdn);
	}
}
