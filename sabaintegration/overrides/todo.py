# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import frappe

from frappe.desk.doctype.todo.todo import ToDo
from sabaintegration.overrides.employee import get_leaders
exclude_from_linked_with = True

class CustomToDo(ToDo):
    def after_insert(self):
        self.share_with_leaders() 

    def share_with_leaders(self):
        employees = get_leaders(self.allocated_to, "user_id", "todo_maintainer_")
        if employees:
            from frappe.share import add_docshare
            for employee in employees:
                add_docshare("ToDo", self.name, employee , flags={"ignore_share_permission": True})
