# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import frappe

from frappe.desk.doctype.todo.todo import ToDo
exclude_from_linked_with = True

class CustomToDo(ToDo):
    def after_insert(self):
        self.share_with_leaders() 

    def share_with_leaders(self):
        employees = get_leaders(self.owner)
        if employees:
            from frappe.share import add
            for employee in employees:
                add("ToDo", self.name, employee ,flags = {"ignore_share_permission": 1})

def get_leaders(user, employees = None):
    if not employees:
        employees = []
    leader = frappe.db.get_value("Employee", {"user_id": user} ,"todo_maintainer_")
    if not leader:
        return 
    else:
        employees.append(leader)
        get_leaders(leader, employees)
    return set(employees)