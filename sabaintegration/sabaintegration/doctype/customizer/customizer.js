// Copyright (c) 2024, Ahmad and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customizer', {
	refresh: function(frm){
		frm.add_custom_button("Show Customized Doctypes", function() {frm.trigger("show_customized_doctypes")})
	},
	show_customized_doctypes: function(frm){
		frm.events.get_customized_doctypes(frm, async (frm, data, ex_doctypes) => {
			frappe.call({
				method: "sabaintegration.sabaintegration.doctype.customizer.customizer.get_doctypes_customization",
				args: {
					"module": frm.doc.module,
					"export": 1
				},
				callback: function(r){
					if (r.message && r.message.length > 0){
						frappe.msgprint("Number of Exported Doctypes is "+ r.message.length + "<br>Exported Files: "
						+ frm.doc.module + "/" + frm.doc.module + "/custom")
					}
					else frappe.msgprint("Nothing is Exported")
				}
			})
		})
	},
	get_customized_doctypes: function(frm, callback){
		frappe.call({
			method: "sabaintegration.sabaintegration.doctype.customizer.customizer.get_doctypes_customization",
			args: {
				"module": frm.doc.module,
				"export": 0
			},
			callback: function(r){
				if (r.message){
					const field = [
						{	
							"fieldtype": "Table",
							"label": __("Doctypes"),
							"fieldname": "ex_doctypes",
							"fields": [
								{
									fieldname: "ex_doctype",
									options: "Doctype",
									label: __("Doctype"),
									fieldtype: "Link",
									in_list_view: 1,
									reqd: 1,
								}
							],
						}
					];
					let dialog = frappe.prompt(field, data => {
						let ex_doctypes = data.ex_doctypes || [];
						callback(frm, data, ex_doctypes);
					})
					let i = 1;
					dialog.fields_dict.ex_doctypes.df.data = [];
					for (let row of r.message){
						dialog.fields_dict.ex_doctypes.df.data.push({"idx": i, "ex_doctype": row});
						i += 1;
					}
					dialog.fields_dict.ex_doctypes.grid.refresh();
				}
			}
		})
	}
});
