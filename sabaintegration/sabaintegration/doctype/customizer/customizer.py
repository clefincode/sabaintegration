# Copyright (c) 2024, Ahmad and contributors
# For license information, please see license.txt
import os
import json
import frappe
from frappe.model.document import Document
from frappe.modules.utils import get_module_path, scrub

ignored_keys = ["_assign","_comments","_liked_by","_user_tags", 
				"creation", "modified", "modified_by", "owner"]

class Customizer(Document):
	pass


@frappe.whitelist()
def get_doctypes_customization(module, export):
	"Get All the Doctypes That was Updated"
	module = module.lower()
	doctypes = frappe.get_all(
		'DocType', filters={'issingle': 0}, fields=['name']
	)
	doctypeslist = [doc.get("name") for doc in doctypes]
	customized_doctypes = []
	for doc in doctypeslist:
		if not has_json_file(doc, module): continue
		# Get All Doctype Customization
		details = get_doc_customization(doc)
		if not details[0]: continue

		# Compare the Current Customization with the Latese Exported Customization File
		to_export = compare_current_json_to_new_custom(details[1], module)
		
		# If the Doctype has to be Exported, Then Add it to the Customized Doctypes List
		if to_export == 1:
			customized_doctypes.append(doc)
			if export == '1':
				export_customizations(doc, details[1], module)
		
	return customized_doctypes

def has_json_file(doctype, module):
	# If Path 'custom' or the JSON File don't Exist, then There is No Json File to Compare with
	folder_path = os.path.join(get_module_path(module), "custom")
	if not os.path.exists(folder_path):
		return False

	path = os.path.join(folder_path, scrub(doctype) + ".json")
	if not os.path.exists(path):
		return False

	return True

def get_doc_customization(doctype):
	"Get Custom Fields, Permissions, Properties and Links of a Doctype "
	custom = {
		"custom_fields": [],
		"property_setters": [],
		"custom_perms": [],
		"links": [],
		"doctype": doctype,
		"sync_on_migrate": 1
	}

	def add(_doctype):
		custom["custom_fields"] += frappe.get_all("Custom Field", fields="*", filters={"dt": _doctype})
		custom["property_setters"] += frappe.get_all(
			"Property Setter", fields="*", filters={"doc_type": _doctype}
		)
		custom["links"] += frappe.get_all("DocType Link", fields="*", filters={"parent": _doctype})

	add(doctype)

	custom["custom_perms"] = frappe.get_all(
		"Custom DocPerm", fields="*", filters={"parent": doctype}
	)

	if custom["custom_fields"] or custom["property_setters"] or custom["custom_perms"]:
		return True, custom
	else:
		return False, None
	
def compare_current_json_to_new_custom(details, module):
	"Compare the Current Customization with the Latest JSON File"

	# If Path 'custom' or the JSON File don't Exist, then There is No Json File to Compare with
	folder_path = os.path.join(get_module_path(module), "custom")
	if not os.path.exists(folder_path):
		return True

	path = os.path.join(folder_path, scrub(details["doctype"]) + ".json")
	if not os.path.exists(path):
		return True

	# Compare with Fields, Permissions, Properties and Links
	if compare_fields(details["custom_fields"], path) or compare_perms(details["custom_perms"], path) or compare_properties(details["property_setters"], path) or compare_links(details["links"], path):
		return True 

	return False

def compare_fields(custom_fields, path):
	with open(path, 'r') as f:
		data = json.load(f)

	file_custom_fields = data.get('custom_fields', [])
	
	for field in custom_fields:
		found = False
		for ffield in  file_custom_fields:
			if ffield["fieldname"] == field["fieldname"]:
				found = True
				for fkey, fvalue in ffield.items():
					if fkey in ignored_keys: 
						continue

					for key, value in field.items():
						if key == fkey:
							if fvalue != value:
								return True # To Export
		if not found:
			return True
	return False


def compare_perms(custom_perms, path):
	with open(path, 'r') as f:
		data = json.load(f)

	file_custom_perms = data.get('custom_perms', [])
	
	for perm in custom_perms:
		found = False
		for fperm in  file_custom_perms:
			if fperm["role"] == perm["role"]:
				found = True
				for fkey, fvalue in fperm.items():
					if fkey in ignored_keys: 
						continue

					for key, value in perm.items():
						if key == fkey:
							if fvalue != value:
								return True # To Export
		if not found:
			return True
	return False

def compare_properties(property_setters, path):
	
	with open(path, 'r') as f:
		data = json.load(f)

	file_property_setters = data.get('property_setters', [])
	
	for property in property_setters:
		found = False
		for fproperty in  file_property_setters:
			if fproperty["field_name"] == property["field_name"]:
				found = True
				for fkey, fvalue in fproperty.items():
					if fkey in ignored_keys: 
						continue

					for key, value in property.items():
						if key == fkey:
							if fvalue != value:
								return True # To Export
		if not found:
			return True
	return False

def compare_links(links, path):
	with open(path, 'r') as f:
		data = json.load(f)

	file_links = data.get('links', [])

	for link in links:
		found = False
		for flink in  file_links:
			if flink["link_doctype"] == link["link_doctype"] and \
			   flink["link_fieldname"] == link["link_fieldname"] and \
			   flink["group"] == link["group"]:
				found = True
				break
		if not found:
			return True
	return False	

def export_customizations(doctype, custom, module):
	"Export Customizations to a Specific Module"
	if custom["custom_fields"] or custom["property_setters"] or custom["custom_perms"] or custom["links"]:
		folder_path = os.path.join(get_module_path(module), "custom")
		if not os.path.exists(folder_path):
			os.makedirs(folder_path)

		path = os.path.join(folder_path, scrub(doctype) + ".json")

		with open(path, "w") as f:
			f.write(frappe.as_json(custom))	
