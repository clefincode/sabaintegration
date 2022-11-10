# Copyright (c) 2022, Ahmad and contributors
# For license information, please see license.txt

import frappe
from copy import deepcopy

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	return [
		{
			"label": ("Status"),
			"fieldtype": "Data",
			"fieldname": "status",
			"width": 100,
		},
		{
			"label": ("Allocated To"),
			"fieldtype": "Link",
			"fieldname": "owner",
			"options": "User",
			"width": 100,
		},
		{
			"label": ("Priority"),
			"fieldtype": "Data",
			"fieldname": "priority",
			"width": 100,
		},
		{
			"label": ("Due Date"),
			"fieldtype": "Date",
			"fieldname": "date",
			"width": 100,
		},
		{
			"label": ("Description"),
			"fieldtype": "Data",
			"fieldname": "description",
			"width": 400,
		},
		{
			"label": ("Reference Type"),
			"fieldtype": "Data",
			"fieldname": "reference_type",
			"width": 100,
		},
		{
			"label": ("Reference Name"),
			"fieldtype": "Data",
			"fieldname": "reference_name",
			"width": 100,
		},
		
		{
			"label": ("Role"),
			"fieldtype": "Data",
			"fieldname": "role",
			"width": 100,
		},
		{
			"label": ("Assigned By"),
			"fieldtype": "Link",
			"fieldname": "assigned_by",
			"options": "User",
			"width": 100,
		},

	]
def get_conditions(filters):
	conditions = ""

	if filters.get("status"):
		conditions += " and status=%(status)s"

	if filters.get("owner"):
		conditions += " and owner=%(owner)s"

	if filters.get("date"):
		conditions += " and date=%(date)s"

	return conditions

def get_data(filters):
	conditions = get_conditions(filters)
	employees = get_employees(frappe.session.user)
	employees_str = ""
	if employees:
		for employee in employees:
			employees_str += f"'{employee}',"
	employees_str += f"'{frappe.session.user}'"
	strQuery = """
		SELECT todo.status, todo.owner, todo.priority, todo.date,
		todo.description, todo.reference_type, todo.reference_name, todo.role,
		todo.assigned_by
		FROM `tabToDo` as todo
		where todo.owner in ({employees_str}) {conditions}
	
	""".format(employees_str = employees_str, conditions = conditions)
	return frappe.db.sql(strQuery, filters, as_dict = 1)

def get_employees(manager_id, employees_list = None):
	if not employees_list:
		employees_list = []
	employees = frappe.db.get_all("Employee", {"todo_maintainer_": manager_id},  "user_id")
	if employees:
		for employee in employees:
			employees_list.append(employee.user_id)
			get_employees(employee.user_id, employees_list)
	else:
		return
	return set(employees_list)
