// Copyright (c) 2023, Ahmad and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Salesman Commission Progress"] = {
	"filters": [
		{
			"fieldname":"sales_man",
			"label": ("Sales Man"),
			"fieldtype": "Link",
			"options": "Sales Person",
			"default": getuser()
		},
		{
			"fieldname":"sales_order",
			"label": ("Sales Order"),
			"fieldtype": "Link",
			"options": "Sales Order"
		},
		{
			"fieldname":"quarter",
			"label": ("Quarter"),
			"fieldtype": "Select",
			"options": ["Q1", "Q2", "Q3", "Q4"],
			"reqd": 1,
		},
		{
			"fieldname":"year",
			"label": ("Year"),
			"fieldtype": "Data",
            "default": moment().year(),
			"reqd": 1
		},
	],
	"onload": async function(report) {
        frappe.query_report.set_filter_value({'quarter': await get_quarter()});
		frappe.query_report.refresh();
    },
};
function get_quarter(){
	var today = new Date();
	var quarter = Math.floor((today.getMonth() + 3) / 3);
	console.log(quarter)
	return "Q" + quarter;
}

function getuser(){
	let user = frappe.session.user;
	if (user == 'Administrator') return;
	else {
		frappe.call({
			method:"sabaintegration.sabaintegration.report.quota.get_person",
			args: {
				user_type: "Sales Person",
				user: user
			},
			callback: function(r){
				if (r.message) return r.message;
			}
		})
	}
}