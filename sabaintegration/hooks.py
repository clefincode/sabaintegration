from . import __version__ as app_version

app_name = "sabaintegration"
app_title = "Sabaintegration"
app_publisher = "Ahmad"
app_description = "saba"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "ahmad@clefincode.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/sabaintegration/css/sabaintegration.css"
# app_include_js = "/assets/sabaintegration/js/sabaintegration.js"

# include js, css files in header of web template
# web_include_css = "/assets/sabaintegration/css/sabaintegration.css"
# web_include_js = "/assets/sabaintegration/js/sabaintegration.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "sabaintegration/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Sales Order" : "public/js/doctype/sales_order_updates.js",
	"Delivery Note" : "public/js/doctype/delivery_note_updates.js",
	"Product Bundle" : "public/js/doctype/product_bundle_item_prevents.js",
	"Opportunity" : "public/js/doctype/opportunity.js",
	"Request for Quotation": "public/js/doctype/request_for_quotation.js",
	"Supplier Quotation": "public/js/doctype/supplier_quotation.js",
	"Quotation": "public/js/doctype/quotation.js",
	"Item": "public/js/doctype/item.js",
	"Product Bundle": "public/js/doctype/product_bundle.js",
	"Lead": "public/js/doctype/lead.js",
	"Attendance": "public/js/doctype/attendance.js",
	"Purchase Order": "public/js/doctype/purchase_order.js"
	}
# doctype_list_js = {"Opportunity" : "public/js/doctype/opportunity_list.js"}
doctype_list_js = {"Request for Quotation" : "public/js/doctype/request_for_quotation_list.js"}
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "sabaintegration.install.before_install"
# after_install = "sabaintegration.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "sabaintegration.uninstall.before_uninstall"
# after_uninstall = "sabaintegration.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "sabaintegration.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"Quotation": "sabaintegration.www.permissions.quotation_query"
}
#
has_permission = {
 	"Event": "sabaintegration.www.permissions.has_permission",
}

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	'Opportunity': 'sabaintegration.overrides.opportunity.CustomOpportunity',
	'Warranty Claim': 'sabaintegration.overrides.warranty_claim.CustomWarrantyClaim',
	'Issue': 'sabaintegration.overrides.issue.CustomIssue',
	'Supplier Quotation': 'sabaintegration.overrides.supplier_quotation.CustomSupplierQuotation',
	'Request for Quotation': 'sabaintegration.overrides.request_for_quotation.CustomRequestforQuotation',
	'Quotation': 'sabaintegration.overrides.quotation.CustomQuotation',
	'ToDo': 'sabaintegration.overrides.todo.CustomToDo',
	#'Employee': 'sabaintegration.overrides.employee.CustomEmployee',
	'Stock Entry': 'sabaintegration.overrides.stock_entry.CustomStockEntry',
    'Delivery Note': 'sabaintegration.overrides.delivery_note.CustomDeliveryNote',
    'Sales Order': 'sabaintegration.overrides.sales_order.CustomSalesOrder'
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Employee": {
        "validate": "sabaintegration.overrides.employee.custom_validate"
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"sabaintegration.tasks.all"
# 	],
# 	"daily": [
# 		"sabaintegration.tasks.daily"
# 	],
# 	"hourly": [
# 		"sabaintegration.tasks.hourly"
# 	],
# 	"weekly": [
# 		"sabaintegration.tasks.weekly"
# 	]
# 	"monthly": [
# 		"sabaintegration.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "sabaintegration.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "sabaintegration.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "sabaintegration.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"sabaintegration.auth.validate"
# ]

# Translation
# --------------------------------

# Make link fields search translated document names for these DocTypes
# Recommended only for DocTypes which have limited documents with untranslated names
# For example: Role, Gender, etc.
# translated_search_doctypes = []
