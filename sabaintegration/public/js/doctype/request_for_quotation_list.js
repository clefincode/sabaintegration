frappe.listview_settings['Request for Quotation'] = {
	add_fields: ["status"],
	get_indicator: function(doc) {
		if(doc.status==="Converted to Supplier Quotation") {
			return [__("Converted to Supplier Quotation"), "orange", "status,=,Converted to Supplier Quotation"];
		} 
	}
};
