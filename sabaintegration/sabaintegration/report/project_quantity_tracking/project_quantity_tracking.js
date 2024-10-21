// Copyright (c) 2024, Ahmad and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Project Quantity Tracking"] = {
	"filters": [
		{
			"fieldname":"project",
			"label": __("Project"),
			"fieldtype": "Link",
			"options": "Project"
		},
		{
			"fieldname":"parent_item",
			"label": __("Parent Item"),
			"fieldtype": "Link",
			"options": "Item"
		},
	],
    "formatter": function(value, row, column, data, default_formatter) {
        // Check if the column is "Project"
        if (column.fieldname === "project" && value !== null && value !== "") {
            // Create the link with the project value, applying bold formatting only for display
            return `<a href="/app/project/${data.project}" style="font-weight: bold;" data-doctype="Project" data-name="${value}" data-value="${value}">${value}</a>`;
        }

        // Call the default formatter for other fields
        return default_formatter(value, row, column, data);
    }
}
