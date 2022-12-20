frappe.ui.form.on("Opportunity", {
    setup(frm) {
        
        frm.set_df_property('parent_items', 'cannot_add_rows', true);
		frm.set_df_property('parent_items', 'cannot_delete_rows', true);

        frm.set_df_property('items', 'cannot_add_rows', true);
		frm.set_df_property('items', 'cannot_delete_rows', true);

        if (!frm.doc.parent_items) frm.toggle_display('parent_items', false);
        if (frm.is_new) frm.doc.selected_option = 0
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
        frm.set_df_property('parent_items', 'cannot_add_rows', true);
		frm.set_df_property('parent_items', 'cannot_delete_rows', true);

        frm.set_df_property('items', 'cannot_add_rows', true);
		frm.set_df_property('items', 'cannot_delete_rows', true);

        if (!frm.doc.parent_items) frm.toggle_display('parent_items', false);
        
        if (frm.is_new()) frm.doc.selected_option = 0; 
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
    set_option_items: async function(frm, option_number){
        frm.doc.items=[];
        switch (option_number){
            case 1:
                new Promise((resolve)=> {
                    group_similar_items(frm,frm.doc.option_1, resolve)
                }).then(()=>{
                    refresh_field("items");
                    validate_product_bundle(frm);
                }
                )
                break;
            case 2:
                new Promise((resolve)=> {
                    group_similar_items(frm,frm.doc.option_2, resolve)
                }).then(()=>{
                    refresh_field("items");
                    validate_product_bundle(frm);
                }
                )
                break;
            case 3:
                new Promise((resolve)=> {
                    group_similar_items(frm,frm.doc.option_3, resolve)
                }).then(()=>{
                    refresh_field("items");
                    validate_product_bundle(frm);
                }
                )
                break;
            case 4:
                new Promise((resolve)=> {
                    group_similar_items(frm,frm.doc.option_4, resolve)
                }).then(()=>{
                    refresh_field("items"); 
                    validate_product_bundle(frm);
                }
                )
                break;
            case 5:
                new Promise((resolve)=> {
                    group_similar_items(frm,frm.doc.option_5, resolve)
                }).then(()=>{
                    refresh_field("items");
                    validate_product_bundle(frm);
                }
                )
                break;
            case 6:
                new Promise((resolve)=> {
                    group_similar_items(frm,frm.doc.option_6, resolve)
                }).then(()=>{
                    refresh_field("items");
                    validate_product_bundle(frm);
                }
                )
                break;
            case 7:
                new Promise((resolve)=> {
                    group_similar_items(frm,frm.doc.option_7, resolve)
                }).then(()=>{
                    refresh_field("items");
                    validate_product_bundle(frm);
                }
                )
                break;
            case 8:
                new Promise((resolve)=> {
                    group_similar_items(frm,frm.doc.option_8, resolve)
                }).then(()=>{
                    refresh_field("items");
                    validate_product_bundle(frm);
                }
                )
                break;
            case 9:
                new Promise((resolve)=> {
                    group_similar_items(frm,frm.doc.option_9, resolve)
                }).then(()=>{
                    refresh_field("items");
                    validate_product_bundle(frm);
                }
                )
                break;
            case 10:
                new Promise((resolve)=> {
                    group_similar_items(frm,frm.doc.option_10, resolve)
                }).then(()=>{
                    refresh_field("items");
                    validate_product_bundle(frm);
                }
                )
                break;
        
        }
    },

    make_request_for_quotation: function(frm) {
		frappe.model.open_mapped_doc({
			method: "sabaintegration.overrides.opportunity.make_request_for_quotation",
			frm: frm
		})
	},
    set_option: function(frm){
        let found = false;
        for(let row in cur_frm.doc.items){
            if (frm.doc.items[row]["option_number"]){
                frm.doc.selected_option = cur_frm.doc.items[row]["option_number"]
                found = true;
                break
            }
        }
        if (found == false) frm.doc.selected_option = 0
        frm.events.set_option_html(frm.doc.selected_option)
    },
    set_option_html: function(option){
        if (document.getElementById('option_number')) {
            document.getElementById('option_number').remove();
        }

        if (option != 0){
            var x = document.querySelectorAll(".section-head");
            for (var i = 0; i < x.length; i++) {
                if(x[i].innerHTML.indexOf("More Options Or Products") !== -1 && x[i].innerHTML.indexOf("Parents of Packed Items") == -1) {
                    x[i].innerHTML+= "<small id='option_number'  style='padding: 3px 10px; font-weight: 500;background:#fff5f5; margin:10px; color:#e24c4c;'>Option "+option+"</small>";
                }
            }
        }
    }
});

frappe.ui.form.on('Opportunity Item', { 
    // item_code(frm, cdt, cdn) {
    //     var child = locals[cdt][cdn];
    //     child.qty = 1;
    //     refresh_field("items");
    //     update_product_bundle(frm, child, cdt, cdn, "add")

    // },
    // qty(frm, cdt, cdn) {
    //     //validate_product_bundle(frm);
    //     var d = locals[cdt][cdn]
    //     update_product_bundle(frm, d, cdt, cdn, "qty")
    // },
    // items_remove(frm, cdt, cdn) { 
    //     if (cur_frm.doc.packed_items) validate_product_bundle(frm);
    // },
    
 
});


frappe.ui.form.on('Opportunity Option', { 
    item_code: function(frm,cdt,cdn){
        var d = locals[cdt][cdn]
        if (d.parentfield.charAt(d.parentfield.length - 1) == "0")
            frappe.model.set_value(cdt, cdn, "option_number", 10)
        else frappe.model.set_value(cdt, cdn, "option_number", parseInt(d.parentfield.charAt(d.parentfield.length - 1)))
        // if (frm.doc.selected_option == d.option_number) 
        // update_product_bundle(frm, d, cdt, cdn, "add")
    },
    qty: function(frm,cdt,cdn){
        var d = locals[cdt][cdn]
        // if (frm.doc.selected_option == d.option_number) 
        // update_product_bundle(frm, d, cdt, cdn, "qty")
    },
    //for each option, when adding new row, show the next option table
    option_1_add(frm, cdt, cdn) { 
        var child1 = locals[cdt][cdn];
        child1.qty = 1;
        refresh_field("option_1");
        frm.set_df_property('option_2', 'hidden', 0)
    },
    // option_1_remove(frm, cdt, cdn) { 
    //     //if (frm.doc.selected_option == 1 && frm.doc.option_1.length > 0)  frm.events.set_option_items(frm,1);
    //     if (frm.doc.selected_option == 1 && frm.doc.option_1.length == 0) {
    //         frm.doc.selected_option = 0
    //         frm.events.set_option_items(frm,0);
            
    //     }
    // },
    option_2_add(frm, cdt, cdn) { 
        var child2 = locals[cdt][cdn];
        child2.qty = 1;
        refresh_field("option_2");
        frm.set_df_property('option_3', 'hidden', 0)
    },
    option_3_add(frm, cdt, cdn) { 
        var child3 = locals[cdt][cdn];
        child3.qty = 1;
        refresh_field("option_3");
        frm.set_df_property('option_4', 'hidden', 0)
    },
    option_4_add(frm, cdt, cdn) { 
        var child4 = locals[cdt][cdn];
        child4.qty = 1;
        refresh_field("option_4");
        frm.set_df_property('option_5', 'hidden', 0)
    },
    option_5_add(frm, cdt, cdn) { 
        var child5 = locals[cdt][cdn];
        child5.qty = 1;
        refresh_field("option_5");
        frm.set_df_property('option_6', 'hidden', 0)
    },
    option_6_add(frm, cdt, cdn) { 
        var child6 = locals[cdt][cdn];
        child6.qty = 1;
        refresh_field("option_6");
        frm.set_df_property('option_7', 'hidden', 0)
    },
    option_7_add(frm, cdt, cdn) { 
        var child7 = locals[cdt][cdn];
        child7.qty = 1;
        refresh_field("option_7");
        frm.set_df_property('option_8', 'hidden', 0)
    },
    option_8_add(frm, cdt, cdn) { 
        var child8 = locals[cdt][cdn];
        child8.qty = 1;
        refresh_field("option_8");
        frm.set_df_property('option_9', 'hidden', 0)
    },
    option_9_add(frm, cdt, cdn) { 
        var child9 = locals[cdt][cdn];
        child9.qty = 1;
        refresh_field("option_9");
        frm.set_df_property('option_10', 'hidden', 0)
    },
    option_10_add(frm, cdt, cdn) { 
        var child10 = locals[cdt][cdn];
        child10.qty = 1;
        refresh_field("option_10");
    },
});



const validate_product_bundle = async (frm) => {
    frappe.dom.freeze()

    if (!frm.doc.with_items) return;
  
    // let's empty the table first
    frm.doc.parent_items = [];
    frm.clear_table("parent_items");
    //   iterate opportunity items
    for (const row of cur_frm.doc.items) {
        if (!row.item_code) continue;
        await add_packed_items(frm, row)
    }
    frm.refresh_field("parent_items");
    frm.trigger("set_option")

    if (frm.doc.parent_items) frm.toggle_display('parent_items', true);
    frappe.dom.unfreeze()
    
};

const update_product_bundle = async (frm, row, cdt, cdn, method) => {
    frappe.dom.freeze()
    if (!frm.doc.items) {
        validate_product_bundle(frm); 
        return;
    }
    if (method == "add"){
        let exists = false;
        if (row.doctype == "Opportunity Option"){
            for (let item of frm.doc.items){
                if (item.item_code == row.item_code){
                    item.qty += row.qty;
                    const product_bundle = await get_packed_items(row)
                    await update_packed_items_qty(product_bundle.items, row)
                    exists = true;
                    break;
                }
            }
            if (!exists){
                let child = frm.add_child("items");

                child.item_code = row.item_code;
                child.qty = row.qty || 1;
                child.description = row.description || "";
                child.uom = row.uom;
                child.option_number = row.option_number;
                child.item_name = row.item_name || "";
                //child.section_title = row.section_title || "";
                child.warehouse = row.warehouse || "";
                await get_item_details(frm, row, cdt, cdn);
                await add_packed_items(frm, row);
            }
        }
        
        //await add_packed_items(frm, row);

    }
    else if (method == "qty"){
        let items = frm.doc.items
        for (let i in items){
            if (items[i].item_code == row.item_code){
                frm.doc.items[i].qty = row.qty;
                const product_bundle = await get_packed_items(row)
                if (product_bundle){
                    await update_packed_items_qty(product_bundle, row)
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
            // await frappe.db.get_value("Item Default", {"parent": bundled_item.item_code}, "default_warehouse",  (r) => {
            //     if (r) child.warehouse = r.default_warehouse
            // }, "Item")
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
const update_packed_items_qty = async (product_bundle_items, row) => {
    for (const bundled_item of product_bundle_items) {
        for (const packed_item of cur_frm.doc.parent_items){
            if (packed_item.item_code == bundled_item.item_code &&
                packed_item.parent_item == row.item_code){
                packed_item.qty = row.qty * bundled_item.qty;
                break
            }
        }
    }
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
const group_similar_items = (frm, option, resolve) => {
    frappe.call({
        method: "sabaintegration.overrides.opportunity.group_similar_items",
        args: {"items": option, "company": frm.doc.company},
        callback: function(r) {
            if(r.message) {
                cur_frm.set_value("items", r.message);
                frm.refresh_field("items");
                resolve();
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
