
{% include 'erpnext/public/js/controllers/buying.js' %};

erpnext.buying.SupplierQuotationController = erpnext.buying.BuyingController.extend({

    refresh: function() {
        var me = this;
        this._super();

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
        }
    },

    make_quotation: function() {
        frappe.model.open_mapped_doc({
            method: "sabaintegration.overrides.supplier_quotation.make_quotation",
            frm: cur_frm
        })

    },
    default_warehouse: function(frm){
        $.each(frm.items || [], function(i, d) {
			if(!d.warehouse) d.warehouse = frm.default_warehouse;
		});
		refresh_field("items");
    },
    default_margin: function(frm){
        $.each(frm.items || [], function(i, d) {
            d.profit_margin = frm.default_margin;
        });
        refresh_field("items");
    },
});

// for backward compatibility: combine new and previous states
$.extend(cur_frm.cscript, new erpnext.buying.SupplierQuotationController({frm: cur_frm}));

cur_frm.fields_dict['items'].grid.get_field('project').get_query =
    function(doc, cdt, cdn) {
        return{
            filters:[
                ['Project', 'status', 'not in', 'Completed, Cancelled']
            ]
        }
    }

    frappe.ui.form.on("Supplier Quotation Item",{
        item_code: function(frm, cdt, cdn){
            var d = locals[cdt][cdn];
            if (!d.profit_margin)
                frappe.model.set_value(cdt, cdn, "profit_margin", frm.doc.default_margin)
            if (!d.warehouse)
                frappe.model.set_value(cdt, cdn, "warehouse", frm.doc.default_warehouse)
        },
    })