
{% include 'erpnext/buying/doctype/supplier_quotation/supplier_quotation.js' %};

erpnext.buying.CustomSupplierQuotationController = class CustomSupplierQuotationController extends erpnext.buying.SupplierQuotationController {

    refresh() {
        var me = this;
        this._super;

        if (this.frm.doc.__islocal && !this.frm.doc.valid_till) {
            this.frm.set_value('valid_till', frappe.datetime.add_months(this.frm.doc.transaction_date, 1));
        }
        if (this.frm.doc.docstatus === 1) {
            cur_frm.add_custom_button(__("Purchase Order"), this.make_purchase_order,
                __('Create'));
            cur_frm.page.set_inner_btn_group_as_primary(__('Create'));
            cur_frm.add_custom_button(__("Quotation"), this.make_quotation,
                __('Create'));
        }
        else if (this.frm.doc.docstatus===0) {

            this.frm.add_custom_button(__('Material Request'),
                function() {
                    erpnext.utils.map_current_doc({
                        method: "erpnext.stock.doctype.material_request.material_request.make_supplier_quotation",
                        source_doctype: "Material Request",
                        target: me.frm,
                        setters: {
                            schedule_date: undefined,
                            status: undefined
                        },
                        get_query_filters: {
                            material_request_type: "Purchase",
                            docstatus: 1,
                            status: ["!=", "Stopped"],
                            per_ordered: ["<", 100],
                            company: me.frm.doc.company
                        }
                    })
                }, __("Get Items From"));

            // Link Material Requests
            this.frm.add_custom_button(__('Link to Material Requests'),
                function() {
                    erpnext.buying.link_to_mrs(me.frm);
                }, __("Tools"));

            this.frm.add_custom_button(__("Request for Quotation"),
            function() {
                if (!me.frm.doc.supplier) {
                    frappe.throw({message:__("Please select a Supplier"), title:__("Mandatory")})
                }
                erpnext.utils.map_current_doc({
                    method: "erpnext.buying.doctype.request_for_quotation.request_for_quotation.make_supplier_quotation_from_rfq",
                    source_doctype: "Request for Quotation",
                    target: me.frm,
                    setters: {
                        transaction_date: null
                    },
                    get_query_filters: {
                        supplier: me.frm.doc.supplier,
                        company: me.frm.doc.company
                    },
                    get_query_method: "erpnext.buying.doctype.request_for_quotation.request_for_quotation.get_rfq_containing_supplier"

                })
            }, __("Get Items From"));
            
            if (!this.frm.is_new())
            this.frm.add_custom_button(__("Set Rates from Another SQ"),
                () => {this.frm.trigger("set_rates")});

        }
    }

    make_quotation() {
        frappe.model.open_mapped_doc({
            method: "sabaintegration.overrides.supplier_quotation.make_quotation",
            frm: cur_frm
        })
    }
    
    async set_rates(){
        let me = this;
        // let opportunity = "";
        // if (me.frm.doc.items.length > 0 && me.frm.doc.items[0].request_for_quotation){
        //     let rfq = me.frm.doc.items[0].request_for_quotation;
        //     opportunity = await frappe.db.get_value("Request for Quotation", {"name": rfq}, "opportunity");
        // }
        var dialog = new frappe.ui.Dialog({
			title: __("Choose a Supplier Quotation"),
			fields: [
				{	"fieldtype": "Link",
					"label": __("Supplier Quotation"),
					"fieldname": "supplier_quotation",
					"options": 'Supplier Quotation',
					"reqd": 1,
                    get_query: function(){
                        var opportunity = me.frm.doc.opportunity;
                        return {
                            query:"sabaintegration.overrides.supplier_quotation.get_supplier_quotations",
                            filters: {
                                opportunity : opportunity
                            }
                        }
                    }
				}
			],
			primary_action_label: __("Submit"),
			primary_action: (arg) => {
				if(!arg) return;
				dialog.hide();
				return frappe.call({
					type: "POST",
					method: "sabaintegration.overrides.supplier_quotation.set_rates",
					args: {
						"source_name": arg.supplier_quotation,
                        "target_name": me.frm.doc.name
					},
					freeze: true,
					callback: function(r) {
						if(r.message) {                            
                            me.frm.clear_table("items");                            
                            me.frm.refresh_field("items");
                            r.message[1].not_updated_items.forEach((row) => {                                
								let item = me.frm.add_child("items");
                               
								//$.extend(item, row);
                                for (const field in row){                                    
                                    if (field != 'name')
                                    item[field] = row[field];
                                }
                                me.frm.refresh_field("items");
                                me.frm.page.body.find(`[data-fieldname="items"] [data-idx="${row.idx}"] .data-row`).addClass("highlight");                                
							});

                            r.message[0].updated_items.forEach((row) => {
								let item = me.frm.add_child("items");                                
								//$.extend(item, row);
                                for (const field in row){
                                    if (field != 'name')
                                    item[field] = row[field];
                                }                                
							});
							me.frm.refresh_field("items"); 
                                                       
                            
						}
					}
				});
			}
		});

		dialog.show()
    }

    default_warehouse(frm){
        $.each(frm.items || [], function(i, d) {
			if(!d.warehouse) d.warehouse = frm.default_warehouse;
		});
		refresh_field("items");
    }
    default_margin(frm){
        $.each(frm.items || [], function(i, d) {
            d.profit_margin = frm.default_margin;
        });
        refresh_field("items");
    }
};

extend_cscript(cur_frm.cscript, new erpnext.buying.CustomSupplierQuotationController({frm: cur_frm}));


frappe.ui.form.on("Supplier Quotation Item",{
    item_code: function(frm, cdt, cdn){
        var d = locals[cdt][cdn];
        if (!d.profit_margin)
            frappe.model.set_value(cdt, cdn, "profit_margin", frm.doc.default_margin)
        if (!d.warehouse)
            frappe.model.set_value(cdt, cdn, "warehouse", frm.doc.default_warehouse)
    },
})