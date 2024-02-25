// Copyright (c) 2023, Ahmad and contributors
// For license information, please see license.txt

frappe.ui.form.on('Default KPI', {
	refresh: function(frm) {
		frm.add_custom_button("Get Employees", function(){
			frm.events.get_employees(frm)
		})
	},
	get_employees: function(frm){
		var dialog = new frappe.ui.Dialog({
			title: "Get Employees",
			fields: [
				{
					"label": "Department",
					"fieldname": "department",
					"fieldtype": "Link",
					"options": "Department",
					change: () => {
						
						let department = cur_dialog.get_values().department;
						frm.events.setup_employees(frm, cur_dialog, department, () => {});
					}
				},
				{
					"label": "Employees",
					"fieldname": "employees",
					"fieldtype": "Table",
					"fields": [
						{
						"label": "Employee",
						"fieldname": "employee",
						"fieldtype": "Link",
						"options": "Employee",
						"in_list_view": 1
						},
						{
						"label": "Full Name",
						"fieldname": "employee_name",
						"fieldtype": "Data",
						"in_list_view": 1
						},
						{
						"label": "Department",
						"fieldname": "department",
						"fieldtype": "Link",
						"options": "Department",
						"in_list_view": 1,
						},
						{
						"label": "KPI",
						"fieldname": "kpi",
						"fieldtype": "Percent",
						"default": 100,
						"in_list_view": 1
						},
					]
				}
			],
			primary_action: function() {
				var data = dialog.get_values();

				if (data.employees !== undefined){
					for (const row of data.employees){
						let new_row = frm.add_child("kpi_details", {
							"employee" : row.employee,
							"employee_name": row.employee_name,
							"department": row.department,
							"kpi": row.kpi
						})
					}
				}
				frm.refresh_field("kpi_details");
				dialog.hide()
			}
		})
		frm.events.setup_employees(frm, dialog, undefined, (dialog) => {dialog.show();})
	},
	setup_employees: function(frm, dialog, department, callback_method){
		if (department === undefined) department = ''
		dialog.fields_dict.employees.df.data = [];
		frappe.call({
			"method": "sabaintegration.sabaintegration.doctype.default_kpi.default_kpi.get_all_employees",
			"args": {
				'department': department
			},
			callback: function(r){
				if (r.message){
					let employees = r.message;
					let i = 1;
					for (let row of employees){
						dialog.fields_dict.employees.df.data.push({
							"idx": i, 
							"employee": row.name, 
							"employee_name": row.employee_name,
							"department": row.department,
							"kpi": 100
						})
						i += 1;
					}
					dialog.fields_dict.employees.grid.refresh();
				}
				callback_method(dialog);
			}
		})
	}
});
