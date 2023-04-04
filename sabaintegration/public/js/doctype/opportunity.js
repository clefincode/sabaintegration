{% include 'erpnext/crm/doctype/opportunity/opportunity.js' %}

frappe.ui.form.on("Opportunity", {
    setup(frm) {
        frm.all_options =  ['option_1', 'option_2', 'option_3', 'option_4', 'option_5', 'option_6', 'option_7', 'option_8', 'option_9', 'option_10'];
        frm.all_names =  ['name1', 'name2', 'name3', 'name4', 'name5', 'name6', 'name7', 'name8', 'name9', 'name10']
        frm.set_df_property('parent_items', 'cannot_add_rows', true);
		frm.set_df_property('parent_items', 'cannot_delete_rows', true);

        frm.set_df_property('items', 'cannot_add_rows', true);
		frm.set_df_property('items', 'cannot_delete_rows', true);
       
        // show download button under items and packed items tables
        frm.get_docfield("items").allow_bulk_edit = 1;
        frm.fields_dict.items.grid.wrapper.find('.grid-download').removeClass('hidden');
        frm.get_docfield("parent_items").allow_bulk_edit = 1;
        // this  function setup_download(); is located infrappe-bench/sites/assets/frappe/js/frappe/form/grid.js
        // it has been used so the dowload button download the custom child table
        cur_frm.get_field("parent_items").grid.setup_download();
        
        frm.fields_dict.parent_items.grid.wrapper.find('.grid-download').removeClass('hidden');
        
        // show download button for every option
        for ( let i=0; i<frm.all_options.length ; i++){
            frm.get_docfield(frm.all_options[i]).allow_bulk_edit = 1;
            cur_frm.get_field(frm.all_options[i]).grid.setup_download();
        }
        
    },
    onload(frm){
        if (frm.doc.items) frm.trigger("set_option");
        //for submitted option to stay read only after refresh
        for (let i=0; i<frm.all_options.length - 1; i++){
            let option = frm.all_options[i].replace('_','')
            if (frm.doc[option + 'status'] == "1" ){
                frm.set_df_property(frm.all_options[i], "read_only", 1);
                frm.set_df_property(option + '_submit', 'hidden', 1);
                // for cancel button showing for specific role users
                if (frappe.user_roles.includes('0 CRM – Opportunity Option Cancellation')) {
                    frm.set_df_property(option + '_cancel', 'hidden', 0);
                }
            }

        }
        // testing submit button
        frm.trigger("scheck_option_status")
        frm.trigger("check_empty_option")
 
    // testing submit button end
    },
    condition(frm) {
        //this edit has been cancelled -> here every status has been replaced with condition_status , the new field to be used as status 
        if (frm.doc.condition == "Internal Preparation") {
            set_field_options("status", [
            "Open",
            "Waiting for Technical Reply",
            "Waiting for Consultant/Customer Reply OR Updates",
            "Waiting for Marketing Response",
            "Waiting for Merge and/or Printing",
            "Ready for Quoting/Technical Submitting"
            ]);
        } else if (frm.doc.condition == "Sales Following Up") {
            set_field_options("status", [
            "Technical Proposal submitted & waiting For Consultant/Customer approval",
            "Waiting for Tender (Commercial submission) Date",
            "Quotation (Commercial Proposal )has been sent, Waiting for feedback"
            ]);
        } else if (frm.doc.condition == "Pipeline") {
            set_field_options("status", [
            "Super Hot Deal (Closing in less than a month)",
            "Serious Deal (Closing in the coming 3 months)",
            "True opportunity (Closing 3-6 months)"
            ]);
        } else if (frm.doc.condition == "Future Pipeline") {
            set_field_options("status", [
            "Closing 6-9 Months",
            "Closing 9-12 Months",
            "Closing in more than 1 Year"
            ]);
        } else if (frm.doc.condition == "Won") {
            set_field_options("status", [
            "Due to best Pricing",
            "Due to providing best technical option",
            "Due to our technical support",
            "Customer trust in us",
            "Stock Availability",
            "Multi winning reasons"
            ]);
        } else if (frm.doc.condition == "Lost") {
            set_field_options("status", [
            "Lost Due to High Prices",
            "Lost Due to Delay of Reply",
            "Lost Due to Customer Dissatisfaction",
            "Lost Due to Long Delivery Time",
            "Lost because Customer Preferred Another Partner"
            ]);
        } 
        //Hold ... diffrent in code and doctype
        else if (frm.doc.condition == "Hold") {
            set_field_options("status", [
            "Project Postponed",
            "Customer Unreachable for more than 4 weeks",
            "No direct or clear response from the customer"
            ]);
        } else if (frm.doc.condition == "Closed") {
            set_field_options("status", [
            "Customer Was just budgeting",
            "More than Customer's Budget",
            "Project Cancelled",
            "Not Interested",
            "Not In Portfolio",
            "Too old/No enough data/Test"
            ]);
        }
    },
    refresh(frm) {
        // set_css(frm);
        frm.add_custom_button(__('Request For Quotation New Tab'),
            function() {
                frm.trigger("make_request_for_quotation_new_tab")
            }, __('Create'));
        // $("a[data-label='Request%20For%20Quotation']").addClass("hidden");
        if (!frm.doc.parent_items || frm.doc.parent_items.length < 1) frm.toggle_display('parent_items', false);
        
        if (frm.is_new()) frm.doc.selected_option = 0; 
        else if (frm.doc.items) frm.trigger("set_option")
        
        //  submit button show
        frm.trigger("check_empty_option")
        // show the next empty option
        frm.trigger("scheck_option_status")
        
        if (!frm.is_new()){
            var num = 0;
            for (let option of frm.all_options){
                if (frm.fields_dict[option].grid.data.length != 0 ){num=num+1;}
            }

            for (let i=0; i<frm.all_options.length; i++){
                if (frm.fields_dict[frm.all_options[i]].grid.data.length != 0 ){
                    let option_number = frm.all_options[i].charAt(frm.all_options[i].length - 1) 
                    if (option_number == '0') option_number = '10'
                    
                    frm.set_df_property(frm.all_options[i], 'hidden', 0);
                    
                    if (option_number != '10')
                        frm.set_df_property(frm.all_options[i+1], 'hidden', 0);
                    
                    frm.add_custom_button('Option '+ option_number, () => {
                        frm.events.set_option_items(frm,parseInt(option_number));
    
                    }, num+ ' Options');
                }
                else if (i > 1){
                    frm.set_df_property(frm.all_options[i], 'hidden', 1);
                }
            }
        };
        // Only submitted options allowed to create rfq 
        // hiding the buttons when selected option is not submitted
        // Buttons will be visible when document is saved after submitting the selected option
        frm.trigger("check_selected_option_status");
        set_css(frm);

    },
    check_selected_option_status: function(frm) { 
        // console.log("triggered");
        var rfq = document.querySelectorAll('[data-label="Request%20For%20Quotation"]');
        var rfq_new_tab = document.querySelectorAll('[data-label="Request%20For%20Quotation%20New%20Tab"]');
        if (frm.doc['option'+frm.doc.selected_option+'status'] == "1" ){
            rfq[0].style.display = "block";
            rfq_new_tab[0].style.display = "block";
        }
        else{
            rfq[0].style.display = "none";
            rfq_new_tab[0].style.display = "none";
            frappe.show_alert({
                message:__("You can not create RFQ because the selected option hasn't been not submitted yet."),
                indicator:'red'
            }, 5);
        }
    },
    set_option_items: async function(frm, option_number){
        frm.doc.items=[];
            new Promise((resolve)=> {
                group_similar_items(frm,frm.fields_dict["option_"+option_number.toString()].grid.data , resolve)
            }).then(()=>{
                    refresh_field("items");
                    validate_product_bundle(frm);
                    frm.trigger("calculate_total");
            })
    },

    make_request_for_quotation: function(frm) { 
		frappe.model.open_mapped_doc({
			method: "sabaintegration.overrides.opportunity.make_request_for_quotation",
			frm: frm
		})
	},
    make_request_for_quotation_new_tab: function(frm) {
        var theWindow =  window.open(frm.docname,"_blank"),
        theDoc = theWindow.document,
        theScript = document.createElement('script');
        function injectThis() {
            var div1 = document.getElementsByClassName('inner-group-button');
            if (div1.length > 0) {
                var elements = document.querySelectorAll('[data-label="Request%20For%20Quotation"]');
                elements[0].click();
                return;
            }
            else{
                setTimeout(injectThis, 300);
            }
        }
        theScript.innerHTML = 'window.onload = ' + injectThis.toString() + ';';
        theDoc.body.appendChild(theScript);

	},
    // with_items: function(frm){
    //     if (cur_frm.doc.with_items == 1)
    //         frm.trigger("set_option")
    // },
    check_empty_option: function(frm){
        for (let i=0; i<frm.all_options.length - 1; i++){
            if (frm.fields_dict[frm.all_options[i]].grid.data && frm.fields_dict[frm.all_options[i]].grid.data.length != 0 ){
                frm.set_df_property(frm.all_options[i+1], 'hidden', 0);
                frm.set_df_property(frm.all_names[i+1], 'hidden', 0);
            } 
            if (frm.fields_dict[frm.all_options[i+1]].grid.data && frm.fields_dict[frm.all_options[i+1]].grid.data.length != 0 ){
                frm.set_df_property(frm.all_options[i+1], 'hidden', 0);
                frm.set_df_property(frm.all_names[i+1], 'hidden', 0);
            } 
        }
    },
    scheck_option_status: function(frm){
        for (let i=0; i<frm.all_options.length - 1; i++){
            let option_name = frm.all_options[i].replace('_','')
            if (!frm.fields_dict[frm.all_options[i]].grid.df.hidden) {
                frm.set_df_property(option_name + '_submit', 'hidden', 0);
                // Custom update for submit button to keep hidden if table submitted
                if (frm.doc[option_name + 'status'] == "1" ){
                    frm.set_df_property(option_name + '_submit', 'hidden', 1);
                }// Custom update end
                frm.set_df_property(option_name + '_copy', 'hidden', 0);
            }
            else {
                frm.set_df_property(option_name + '_submit', 'hidden', 1);
                frm.set_df_property(option_name + '_copy', 'hidden', 1);
            }
        }
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
            $('#option_number').remove();
        }
        //custom update for showing option number beside indicator
        if (document.querySelectorAll(".option_number_indicator").length>0) {
            var optionhead = document.querySelectorAll(".option_number_indicator");
            for (var i = 0; i < optionhead.length; i++) {
                optionhead[i].remove();
            }
            
        }
        //custom update for showing option number beside indicator
        if (document.querySelectorAll(".option_number_indicator").length>0) {
            var optionhead = document.querySelectorAll(".option_number_indicator");
            for (var i = 0; i < optionhead.length; i++) {
                optionhead[i].remove();
            }
            
        }

        if (option != 0){
            var x = document.querySelectorAll(".section-head");
            for (var i = 0; i < x.length; i++) {
                if(x[i].innerHTML.indexOf("Technical Options") !== -1 && x[i].innerHTML.indexOf("Bundle Items") == -1) {
                    x[i].innerHTML+= "<small id='option_number'  style='padding: 3px 10px; font-weight: 500;background:#fff5f5; margin:10px; color:#e24c4c;'>Option "+option+"</small>";
                }
            }
            //custom update for showing option number beside indicator
            var z = document.querySelectorAll(".page-head");
            for (var i = 0; i < z.length; i++) {
 
                if (window.getComputedStyle(z[i]).display === "none") {
                }
                else{
                    var ind = document.querySelectorAll(".indicator-pill");
                    for (var c = 0; c < ind.length; c++) {
                        let width = ind[c].offsetWidth;
                        let inner = ind[c].innerHTML;
                        if(width>=150){
                            ind[c].style.marginTop = "-24px";
                        }
                        else{
                            ind[c].style.marginTop = "4px";
                        }
                        var span = ind[c].getElementsByTagName("span") ;
                        if(span.length>0){
                            span[0].innerHTML+= "<small class='option_number_indicator'   style='padding: 3px 10px; font-weight: 500;background:#fff5f5; margin:10px; '>Option "+option+"</small>";
                            break;
                        }
                    }
                    break;
                }
            }            
        }
        
    },
    // new tasks  edits
    to_submit(frm, option) {
        frappe.confirm(
            'Are you sure you want to submit this option?',
            function(){
                //in the single option, before submitting the option, 
                //user must provide different section titles for duplicate items
                const allitems =[];
                const allitems_with_idx = [];
                frm.fields_dict[option].grid.data.forEach(
                    function(el){
                        var section ;
                        if (el.section_title == undefined){
                            section ="";
                        }
                        else{
                            section =el.section_title;
                        }
                        allitems_with_idx.push("idx:"+el.idx+", Item Code:"+el.item_code+", Section Title:"+section);
                        allitems.push("Item Code:"+el.item_code+", Section Title:"+section)
                    }
                )
                let strArray = allitems;
                let findDuplicates = arr => arr.filter((item, index) => arr.indexOf(item) !== index)
                let found =findDuplicates(strArray);
                
                if(found.length>0){
                    for (let i = 0; i < found.length; i++) {
                        frappe.show_alert({
                            message:__(found[i]+' ,is duplicated'),
                            indicator:'red'
                        }, 10);
                    }
                }
                else{
                    frm.set_df_property(option, "read_only", 1);
                    frm.set_value(option.replace('_','') + 'status', '1');
                    refresh_field(option.replace('_','') + 'status');
                    
                    let option_btn_name = option.replace('_','');
                    frm.set_df_property(option_btn_name + '_submit', 'hidden', 1);
                    if (frappe.user_roles.includes('0 CRM – Opportunity Option Cancellation')) {
                        frm.set_df_property(option_btn_name + '_cancel', 'hidden', 0);
                    }
                    // window.close();
                }                
            },
            function(){
            }
        )
    },
    cancel_option: function(frm ,option){
        frappe.confirm(
            'Are you sure you want to cancel this option?',
            function(){
                frm.set_df_property(option, "read_only", 0);
                frm.set_value(option.replace('_','') + 'status', '0');
                refresh_field(option.replace('_','') + 'status');
                let option_btn_name = option.replace('_','');
                // if (frappe.user_roles.includes('0 CRM – Opportunity Option Cancellation')) {
                    
                // }
                frm.set_df_property(option_btn_name + '_cancel', 'hidden', 1);
                frm.set_df_property(option_btn_name + '_submit', 'hidden', 0);
                // window.close();
            },
            function(){
            }
        )
    },
    option1_submit(frm) {
        frm.events.to_submit(frm, 'option_1')
    },
    option2_submit(frm) {
        frm.events.to_submit(frm, 'option_2')
    },
    option3_submit(frm) {
        frm.events.to_submit(frm, 'option_3')
    },
    option4_submit(frm) {
        frm.events.to_submit(frm, 'option_4')

    },
    option5_submit(frm) {
        frm.events.to_submit(frm, 'option_5')
    },
    option6_submit(frm) {
        frm.events.to_submit(frm, 'option_6')
    },
    option7_submit(frm) {
        frm.events.to_submit(frm, 'option_7')
    },
    option8_submit(frm) {
        frm.events.to_submit(frm, 'option_8')
    },
    option9_submit(frm) {
        frm.events.to_submit(frm, 'option_9')
    },
    option10_submit(frm) {
        frm.events.to_submit(frm, 'option_10')
    },

    option1_copy(frm) {
        frm.events.copy_option(frm,"option_1");
    },
    option2_copy(frm) {
        frm.events.copy_option(frm,"option_2");
    },
    option3_copy(frm) {
        frm.events.copy_option(frm,"option_3");
    },
    option4_copy(frm) {
        frm.events.copy_option(frm,"option_4");
    },
    option5_copy(frm) {
        frm.events.copy_option(frm,"option_5");
    },
    option6_copy(frm) {
        frm.events.copy_option(frm,"option_6");
    },
    option7_copy(frm) {
        frm.events.copy_option(frm,"option_7");
    },
    option8_copy(frm) {
        frm.events.copy_option(frm,"option_8");
    },
    option9_copy(frm) {
        frm.events.copy_option(frm,"option_9");
    },
    option10_copy(frm) {
        frm.events.copy_option(frm,"option_10");
    },
    option1_cancel(frm) {
        frm.events.cancel_option(frm,"option_1");
    },
    option2_cancel(frm) {
        frm.events.cancel_option(frm,"option_2");
    },
    option3_cancel(frm) {
        frm.events.cancel_option(frm,"option_3");
    },
    option4_cancel(frm) {
        frm.events.cancel_option(frm,"option_4");
    },
    option5_cancel(frm) {
        frm.events.cancel_option(frm,"option_5");
    },
    option6_cancel(frm) {
        frm.events.cancel_option(frm,"option_6");
    },
    option7_cancel(frm) {
        frm.events.cancel_option(frm,"option_7");
    },
    option8_cancel(frm) {
        frm.events.cancel_option(frm,"option_8");
    },
    option9_cancel(frm) {
        frm.events.cancel_option(frm,"option_9");
    },
    option10_cancel(frm) {
        frm.events.cancel_option(frm,"option_10");
    },
    copy_option: function(frm ,sourceoption){
        var emptyoption;
        var number ;
        // var sourceoption = sourceoption;
        for (let i=0; i<frm.all_options.length; i++){
            if (frm.fields_dict[frm.all_options[i]].grid.data.length == 0) {
                emptyoption = frm.all_options[i];
                number = parseInt(frm.all_options[i].charAt(frm.all_options[i].length - 1));
                if (number == 0) number = 10
                
                if (number != 10 )
                    frm.set_df_property(frm.all_options[i+1], 'hidden', 0)
                
                let option_name = frm.all_options[i].replace('_','')
                frm.set_df_property(option_name + '_submit', 'hidden', 0);
                frm.set_df_property(option_name + '_copy', 'hidden', 0);
                break;
            }
        }
        frm.fields_dict[sourceoption].grid.data.forEach(
            function(option){
                var childTable = frm.add_child(emptyoption);
                childTable.section_title = option.section_title;
                childTable.item_code = option.item_code;
                childTable.qty = option.qty ;
                childTable.item_group = option.item_group;
                childTable.brand = option.brand ;
                childTable.uom = option.uom;
                childTable.item_name = option.item_name;
                childTable.warehouse = option.warehouse;
                childTable.description = option.description;
                childTable.image = option.image;
                childTable.image_view = option.image_view;
                childTable.basic_rate = option.basic_rate;
                childTable.option_number = number;
                frm.refresh_fields(emptyoption);
            }
        )      
    },
});

frappe.ui.form.on('Opportunity Option', { 
    item_code: function(frm,cdt,cdn){
        var d = locals[cdt][cdn]
        frappe.model.set_value(cdt, cdn, "rate", 0)
        frm.trigger("calculate_option", cdt, cdn);
        if (d.parentfield.charAt(d.parentfield.length - 1) == "0")
            frappe.model.set_value(cdt, cdn, "option_number", 10)
        else frappe.model.set_value(cdt, cdn, "option_number", parseInt(d.parentfield.charAt(d.parentfield.length - 1)))

    },
    calculate_option: function(frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		frappe.model.set_value(cdt, cdn, "amount", flt(row.qty) * flt(row.rate));
		frappe.model.set_value(cdt, cdn, "base_rate", flt(frm.doc.conversion_rate) * flt(row.rate));
		frappe.model.set_value(cdt, cdn, "base_amount", flt(frm.doc.conversion_rate) * flt(row.amount));
	},
    rate: function(frm, cdt, cdn){
        frm.trigger("calculate_option", cdt, cdn);
    },
    qty: function(frm, cdt, cdn) {
		frm.trigger("calculate", cdt, cdn);
	},
    option_1_add(frm, cdt, cdn) { 
        var child1 = locals[cdt][cdn];
        child1.qty = 1;
        refresh_field("option_1");
        frm.set_df_property('option_2', 'hidden', 0);
        frm.set_df_property('name2', 'hidden', 0);
        frm.set_df_property('option1_submit', 'hidden', 0);
        frm.set_df_property('option1_copy', 'hidden', 0);
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
        frm.set_df_property('option_3', 'hidden', 0);
        frm.set_df_property('name3', 'hidden', 0);
        frm.set_df_property('option2_submit', 'hidden', 0);
        frm.set_df_property('option2_copy', 'hidden', 0);
        set_css(frm);
       
    },
    option_3_add(frm, cdt, cdn) { 
        var child3 = locals[cdt][cdn];
        child3.qty = 1;
        refresh_field("option_3");
        frm.set_df_property('option_4', 'hidden', 0);
        frm.set_df_property('name4', 'hidden', 0);
        frm.set_df_property('option3_submit', 'hidden', 0);
        frm.set_df_property('option3_copy', 'hidden', 0);
        set_css(frm);
        
    },
    option_4_add(frm, cdt, cdn) { 
        var child4 = locals[cdt][cdn];
        child4.qty = 1;
        refresh_field("option_4");
        frm.set_df_property('option_5', 'hidden', 0);
        frm.set_df_property('name5', 'hidden', 0);
        frm.set_df_property('option4_submit', 'hidden', 0);
        frm.set_df_property('option4_copy', 'hidden', 0);
        set_css(frm);
        
    },
    option_5_add(frm, cdt, cdn) { 
        var child5 = locals[cdt][cdn];
        child5.qty = 1;
        refresh_field("option_5");
        frm.set_df_property('option_6', 'hidden', 0);
        frm.set_df_property('name6', 'hidden', 0);
        frm.set_df_property('option5_submit', 'hidden', 0);
        frm.set_df_property('option5_copy', 'hidden', 0);
        set_css(frm);
        
    },
    option_6_add(frm, cdt, cdn) { 
        var child6 = locals[cdt][cdn];
        child6.qty = 1;
        refresh_field("option_6");
        frm.set_df_property('option_7', 'hidden', 0);
        frm.set_df_property('name7', 'hidden', 0);
        frm.set_df_property('option6_submit', 'hidden', 0);
        frm.set_df_property('option6_copy', 'hidden', 0);
        set_css(frm);
        
    },
    option_7_add(frm, cdt, cdn) { 
        var child7 = locals[cdt][cdn];
        child7.qty = 1;
        refresh_field("option_7");
        frm.set_df_property('option_8', 'hidden', 0);
        frm.set_df_property('name8', 'hidden', 0);
        frm.set_df_property('option7_submit', 'hidden', 0);
        frm.set_df_property('option7_copy', 'hidden', 0);
        set_css(frm);
        
    },
    option_8_add(frm, cdt, cdn) { 
        var child8 = locals[cdt][cdn];
        child8.qty = 1;
        refresh_field("option_8");
        frm.set_df_property('option_9', 'hidden', 0);
        frm.set_df_property('name9', 'hidden', 0);
        frm.set_df_property('option8_submit', 'hidden', 0);
        frm.set_df_property('option8_copy', 'hidden', 0);
        set_css(frm);
        
    },
    option_9_add(frm, cdt, cdn) { 
        var child9 = locals[cdt][cdn];
        child9.qty = 1;
        refresh_field("option_9");
        frm.set_df_property('option_10', 'hidden', 0);
        frm.set_df_property('name10', 'hidden', 0);
        frm.set_df_property('option9_submit', 'hidden', 0);
        frm.set_df_property('option9_copy', 'hidden', 0);
        set_css(frm);
        
    },
    option_10_add(frm, cdt, cdn) { 
        var child10 = locals[cdt][cdn];
        child10.qty = 1;
        refresh_field("option_10");
        frm.set_df_property('option10_submit', 'hidden', 0);
        frm.set_df_property('option10_copy', 'hidden', 0);
        set_css(frm);
    },
});



const validate_product_bundle = async (frm) => {
    frappe.dom.freeze()

    if (!frm.doc.items) return;
  
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

    if (frm.doc.parent_items.length > 0) frm.toggle_display('parent_items', true);
    frappe.dom.unfreeze()
    
};


///NOT USED FOR NOW
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


///NOT USED FOR NOW
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

erpnext.crm.CustomOpportunity = class CustomOpportunity extends erpnext.crm.Opportunity {
    refresh() {
        this.show_notes();
        ///remove show activities tab
    }
}

extend_cscript(cur_frm.cscript, new erpnext.crm.CustomOpportunity({frm: cur_frm}));

cur_frm.cscript.item_code = function(doc, cdt, cdn) {
	var d = locals[cdt][cdn];
	if (d.item_code) {
		get_item_details(doc, d, cdt, cdn);
	}
}
const set_css = (frm)=>{
    for( var x=1; x<11 ; x++){
        if($("div[data-fieldname='name"+x+"']").css('display') != "none"){
            document.querySelectorAll("[data-fieldname='name"+x+"']")[0].getElementsByTagName("label")[0].style.fontSize = 'large';
            document.querySelectorAll("[data-fieldname='name"+x+"']")[0].getElementsByTagName("label")[0].style.fontWeight = 'bold';
            document.querySelectorAll("[data-fieldname='name"+x+"']")[0].getElementsByTagName("input")[0].style.position = "absolute";
            document.querySelectorAll("[data-fieldname='name"+x+"']")[0].getElementsByTagName("input")[0].style.top = "-40px";
            document.querySelectorAll("[data-fieldname='name"+x+"']")[0].getElementsByTagName("input")[0].style.left = "100px";

        }
        //document.querySelectorAll("[data-fieldname='option_"+x+"']")[0].firstChild.style.display = "none";
    }

    for( var z=1; z<11 ; z++){
        if($("div[data-fieldname='name"+x+"']").css('display') != "none"){
            document.querySelectorAll("[data-fieldname='option"+z+"_submit']")[0].style.cssFloat = "left" ;
            document.querySelectorAll("[data-fieldname='option"+z+"_cancel']")[0].style.cssFloat = "left";
            document.querySelectorAll("[data-fieldname='option"+z+"_copy']")[0].style.cssFloat = "left";
        }

    }
    
}