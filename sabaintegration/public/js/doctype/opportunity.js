frappe.ui.form.on("Opportunity", {
    setup(frm) {
        frm.set_df_property("bundle_items", "cannot_add_rows", true);
        frm.set_df_property("bundle_items", "cannot_delete_rows", true);

        frm.set_df_property('packed_items', 'cannot_add_rows', true);
		frm.set_df_property('packed_items', 'cannot_delete_rows', true);

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
        frm.toggle_display("bundle_items", false);
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
                    frm.doc.items=[];
                    cur_frm.set_value("items", frm.doc.option_1);
                    refresh_field("items");
                    // frm.doc.bundle_items = [];
                    // refresh_field("bundle_items");
                    validate_product_bundle(frm);

                }, num+ ' Options');
            }
            if (frm.doc.option_2.length != 0){
                frm.set_df_property('option_2', 'hidden', 0);
                frm.set_df_property('option_3', 'hidden', 0);
                frm.add_custom_button('Option 2', () => {
                    frm.doc.items=[];
                    cur_frm.set_value("items", frm.doc.option_2);
                    refresh_field("items");
                    // frm.doc.bundle_items = [];
                    // refresh_field("bundle_items");
                    validate_product_bundle(frm);

                }, num+ ' Options');
            }
            else{
                frm.set_df_property('option_2', 'hidden', 1);
            }
            if (frm.doc.option_3.length != 0){
                frm.set_df_property('option_3', 'hidden', 0);
                frm.set_df_property('option_4', 'hidden', 0);
                frm.add_custom_button('Option 3', () => {
                    frm.doc.items=[];
                    cur_frm.set_value("items", frm.doc.option_3);
                    refresh_field("items");
                    // frm.doc.bundle_items = [];
                    // refresh_field("bundle_items");
                    validate_product_bundle(frm);

                }, num+ ' Options');
            }
            else{
                frm.set_df_property('option_3', 'hidden', 1);
            }
            if (frm.doc.option_4.length != 0){
                frm.set_df_property('option_4', 'hidden', 0);
                frm.set_df_property('option_5', 'hidden', 0);
                frm.add_custom_button('Option 4', () => {
                    frm.doc.items=[];
                    cur_frm.set_value("items", frm.doc.option_4);
                    refresh_field("items");
                    // frm.doc.bundle_items = [];
                    // refresh_field("bundle_items");
                    validate_product_bundle(frm);

                }, num+ ' Options');
            }
            else{
                frm.set_df_property('option_4', 'hidden', 1);
            }
            if (frm.doc.option_5.length != 0){
                frm.set_df_property('option_5', 'hidden', 0);
                frm.set_df_property('option_6', 'hidden', 0);
                frm.add_custom_button('Option 5', () => {
                    frm.doc.items=[];
                    cur_frm.set_value("items", frm.doc.option_5);
                    refresh_field("items");
                    // frm.doc.bundle_items = [];
                    // refresh_field("bundle_items");
                    validate_product_bundle(frm);

                }, num+ ' Options');
            }
            else{
                frm.set_df_property('option_5', 'hidden', 1);
            }
            if (frm.doc.option_6.length != 0){
                frm.set_df_property('option_6', 'hidden', 0);
                frm.set_df_property('option_7', 'hidden', 0);
                frm.add_custom_button('Option 6', () => {
                    frm.doc.items=[];
                    cur_frm.set_value("items", frm.doc.option_6);
                    refresh_field("items");
                    // frm.doc.bundle_items = [];
                    // refresh_field("bundle_items");
                    validate_product_bundle(frm);

                }, num+ ' Options');
            }
            else{
                frm.set_df_property('option_6', 'hidden', 1);
            }
            if (frm.doc.option_7.length != 0){
                frm.set_df_property('option_7', 'hidden', 0);
                frm.set_df_property('option_8', 'hidden', 0);
                frm.add_custom_button('Option 7', () => {
                    frm.doc.items=[];
                    cur_frm.set_value("items", frm.doc.option_7);
                    refresh_field("items");
                    // frm.doc.bundle_items = [];
                    // refresh_field("bundle_items");
                    validate_product_bundle(frm);

                }, num+ ' Options');
            }
            else{
                frm.set_df_property('option_7', 'hidden', 1);
            }
            if (frm.doc.option_8.length != 0){
                frm.set_df_property('option_8', 'hidden', 0);
                frm.set_df_property('option_9', 'hidden', 0);
                frm.add_custom_button('Option 8', () => {
                    frm.doc.items=[];
                    cur_frm.set_value("items", frm.doc.option_8);
                    refresh_field("items");
                    // frm.doc.bundle_items = [];
                    // refresh_field("bundle_items");
                    validate_product_bundle(frm);

                }, num+ ' Options');
            }
            else{
                frm.set_df_property('option_8', 'hidden', 1);
            }
            if (frm.doc.option_9.length != 0){
                frm.set_df_property('option_9', 'hidden', 0);
                frm.set_df_property('option_10', 'hidden', 0);
                frm.add_custom_button('Option 9', () => {
                    frm.doc.items=[];
                    cur_frm.set_value("items", frm.doc.option_9);
                    refresh_field("items");
                    // frm.doc.bundle_items = [];
                    // refresh_field("bundle_items");
                    validate_product_bundle(frm);

                }, num+ ' Options');
            }
            else{
                frm.set_df_property('option_9', 'hidden', 1);
            }
            if (frm.doc.option_10.length != 0){
                frm.set_df_property('option_10', 'hidden', 0);
                frm.add_custom_button('Option 10', () => {
                    frm.doc.items=[];
                    cur_frm.set_value("items", frm.doc.option_10);
                    
                    refresh_field("items");
                    // frm.doc.bundle_items = [];
                    // refresh_field("bundle_items");
                    validate_product_bundle(frm);

                }, num+ ' Options');
            }
            else{
                frm.set_df_property('option_10', 'hidden', 1);
            }
        };
    },
    

    make_request_for_quotation: function(frm) {
		frappe.model.open_mapped_doc({
			method: "sabaintegration.overrides.opportunity.make_request_for_quotation",
			frm: frm
		})
	},
    

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
    // items_add(frm, cdt, cdn) { 
        
    // },
    

    
});


frappe.ui.form.on('Opportunity Packed Item', { 
    // form_render(frm, cdt, cdn) { 
    //     function waitForElm(selector) {
    //         return new Promise(resolve => {
    //             if (document.querySelector(selector)) {
    //                 return resolve(document.querySelector(selector));
    //             }
        
    //             const observer = new MutationObserver(mutations => {
    //                 if (document.querySelector(selector)) {
    //                     resolve(document.querySelector(selector));
    //                     observer.disconnect();
    //                 }
    //             });
        
    //             observer.observe(document.body, {
    //                 childList: true,
    //                 subtree: true
    //             });
    //         });
    //     }
    //     waitForElm('.ace_editor').then((elm) => {
    //         $('.ace_editor').removeAttr('style');
    //         $('.html-preview').removeAttr('style');
    //         $('.ace_editor').css('display','none');
    //         $('.ace_editor').css('height','300px');
    //         $('.html-preview').css('display','block');
    //         $('.html-preview').css('height','300px');
    //     });
    // }
});
// if(row.parent_item){
//     var x =document.querySelectorAll('[data-fieldname="parent_item"]');
//     x.document.querySelectorAll('.ace_editor').style.display = "none";
//     x.document.querySelectorAll('.html-preview').style.display = "block";
// }

frappe.ui.form.on('Opportunity Option', { 

    option_1_add(frm, cdt, cdn) { 
        var child1 = locals[cdt][cdn];
        child1.qty = 1;
        refresh_field("option_1");
        frm.set_df_property('option_2', 'hidden', 0)
    },
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
    }
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
  
      const exists = await frappe.db.exists("Product Bundle", row.item_code);
  
      // if item is not a product bundle
      if (!exists) continue;
  
      //   get product bundle details
      const product_bundle = await frappe.db.get_doc(
        "Product Bundle",
        row.item_code
      );
      // iterate bundle items
      for (const bundled_item of product_bundle.items) {

        let parent = frm.add_child("parent_items");
        parent.parent_item = row.item_code;
        parent.item_code = bundled_item.item_code;
        parent.description = bundled_item.description;
        parent.qty = bundled_item.qty * row.qty;
        parent.uom = bundled_item.uom;
        //frm.refresh_field("parent_items");
      } 
      
    }

    frappe.call({
        doc: frm.doc,
        method: 'group_similar_bundle_items',
        callback: function(r) {
            frm.clear_table("bundle_items");
            if (r.message){
                r.message.forEach((row) => {
                    let bundle_item = frm.add_child("bundle_items");
                    //bundle_item.parent_item = row.parent_item || ''
                    bundle_item.item_code = row.item_code || ''
                    bundle_item.qty = row.qty || 0;
                    bundle_item.uom = row.uom || '';
                    bundle_item.description = row.description || '';
                    
                });
                frm.refresh_field("parent_items");
                frm.refresh_field("bundle_items");

                frappe.dom.unfreeze()
            }
            else{
                frappe.dom.unfreeze()
            }
            console.log(frm.doc.parent_items);
        }
        
    });

    
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
    //             console.log("tt11111");
    //         }
    //         else{
    //             console.log("tt22222");
    //         }
    //     }
    // });
};




// Old function that we edited
// const validate_product_bundle = async (frm) => {
//     frappe.dom.freeze()

//     if (!frm.doc.with_items) return;
  
//     // let's empty the table first
//     frm.doc.bundle_items = [];
  
//     //   iterate opportunity items
//     for (const row of frm.doc.items) {
//       if (!row.item_code) continue;
  
//       const exists = await frappe.db.exists("Product Bundle", row.item_code);
  
//       // if item is not a product bundle
//       if (!exists) continue;
  
//       //   get product bundle details
//       const product_bundle = await frappe.db.get_doc(
//         "Product Bundle",
//         row.item_code
//       );
  
//       // iterate bundle items
//       for (const bundled_item of product_bundle.items) {
//         //   get item details
//         const item = await frappe.db.get_doc("Item", bundled_item.item_code);
  
//         // validations
//         let item_default = item.item_defaults.filter(
//           (item_default) => item_default.company == frm.doc.company
//         );
//         let uom = item.uoms.filter((uom) => uom.uom == bundled_item.uom);
  
//         if (!item_default.length || !uom.length) continue;
  
//         // preparing defualts
//         const rate = item.standard_rate;
//         item_default = item_default[0];
//         uom = uom[0];
  
//         const bin_docs = await frappe.db.get_list("Bin", {
//           fields: ["*"],
//           filters: {
//             item_code: item.item_code,
//             warehouse: item_default.default_warehouse,
//           },
//         });
  
//         const bin_doc = bin_docs.length
//           ? bin_docs[0]
//           : { actual_qty: item.opening_stock, projected_qty: item.opening_stock };
  
//         // appending bundle item
  
//         frm.add_child("bundle_items", {
//           parent_item: row.item_code,
//           item_code: bundled_item.item_code,
//           item_name: item.item_name,
//           description: item.description,
//           warehouse: item_default.default_warehouse,
//           qty: bundled_item.qty * row.qty,
//           rate: rate,
//           uom: item.uom,
//           conversion_factor: uom.conversion_factor,
//           actual_qty: bin_doc.actual_qty,
//           projected_qty: bin_doc.projected_qty,
//         });
//         console.log(bundled_item.item_code);
//       }
//     }

//     frm.refresh_field("bundle_items");
//     frappe.dom.unfreeze()
// };