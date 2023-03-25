{% include 'erpnext/crm/doctype/lead/lead.js' %}

erpnext.CustomLeadController = class CustomLeadController extends erpnext.LeadController {
    refresh () {
		var me = this;
		let doc = this.frm.doc;
		erpnext.toggle_naming_series();
		frappe.dynamic_link = {
			doc: doc,
			fieldname: 'name',
			doctype: 'Lead'
		};

		if (!this.frm.is_new() && doc.__onload && !doc.__onload.is_customer) {
			this.frm.add_custom_button(__("Customer"), this.make_customer, __("Create"));
			this.frm.add_custom_button(__("Opportunity"), function() {
				me.frm.trigger("make_opportunity");
			}, __("Create"));
			this.frm.add_custom_button(__("Quotation"), this.make_quotation, __("Create"));
			if (!doc.__onload.linked_prospects.length) {
				this.frm.add_custom_button(__("Prospect"), this.make_prospect, __("Create"));
				this.frm.add_custom_button(__('Add to Prospect'), this.add_lead_to_prospect, __('Action'));
			}
		}

		if (!this.frm.is_new()) {
			frappe.contacts.render_address_and_contact(this.frm);
		} else {
			frappe.contacts.clear_address_and_contact(this.frm);
		}

		this.show_notes();
		console.log("*****")
        ///remove show activities tab
	}

}

extend_cscript(cur_frm.cscript, new erpnext.CustomLeadController({frm: cur_frm}));

frappe.ui.form.on("Lead", {

})