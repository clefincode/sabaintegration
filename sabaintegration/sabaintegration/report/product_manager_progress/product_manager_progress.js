// Copyright (c) 2024, Ahmad and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Product Manager Progress"] = {
	"filters": [
		{
			"fieldname":"product_manager",
			"label": ("Product Manager"),
			"fieldtype": "Link",
			"options": "Product Manager",
			"default": getuser()
		},
		{
			"fieldname":"brand",
			"label": ("Brand"),
			"fieldtype": "Link",
			"options": "Brand",
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
				user_type: "Product Manager",
				user: user
			},
			callback: function(r){
				if (r.message) return r.message;
			}
		})
	}
}
