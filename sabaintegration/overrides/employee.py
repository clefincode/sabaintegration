# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
import frappe
from frappe import _

from erpnext.setup.doctype.employee.employee import Employee

class CustomEmployee(Employee):
	def validate(self):
		super(CustomEmployee, self).validate()
		self.share_todos() 

	###Custom Update
	def share_todos(self):
		"""if a new user has been added to ToDo Maintainer field, 
		employee's ToDo are shared with his ToDo Maintainer and with ToDo Maintainers higher levels """

		###Remove sharing todos from previous todo maintainer
		if self.get_doc_before_save() and self.get_doc_before_save().todo_maintainer_:
			from sabaintegration.overrides.todo import get_leaders

			prev_maintainer = self.get_doc_before_save().todo_maintainer_
			leaders = get_leaders(prev_maintainer)
			if leaders : leaders.add(prev_maintainer)
			else: leaders = [prev_maintainer]

			employess = get_employees(self.user_id)
			if employess: employess.add(self.user_id)
			else: employess = [self.user_id]

			todos = frappe.db.get_all("ToDo", {"owner": ("in", employess)})
			for todo in todos:
				docshares = frappe.db.get_all("DocShare", {"share_name": todo.name, "user": ("in", leaders), "share_doctype": "ToDo"}, ['name', 'share_name'])
				for docshare in docshares:
					doc = frappe.get_doc("DocShare", docshare.name)
					doc.delete(ignore_permissions=True)
			
			frappe.db.commit()
		
		###Check if todo maintainer field has reset
		toadd = False
		if self.todo_maintainer_:
			if self.get_doc_before_save():
				if self.get_doc_before_save().todo_maintainer_ != self.todo_maintainer_:
					toadd = True
				elif not self.get_doc_before_save().todo_maintainer_:
					toadd = True
			elif not self.get_doc_before_save():
				toadd = True

		if toadd:
			from sabaintegration.overrides.todo import get_leaders
			from frappe.share import add_docshare

			leaders = get_leaders(self.todo_maintainer_)
			if leaders : leaders.add(self.todo_maintainer_)
			else: leaders = [self.todo_maintainer_]
			
			employess = get_employees(self.user_id)
			if employess: employess.add(self.user_id)
			else: employess = [self.user_id]

			todos = frappe.db.get_all("ToDo", {"owner": ("in", employess)})
			for todo in todos:
				for leader in leaders:
					if not frappe.db.exists("ToDo", {"share_doctype": "ToDo", "share_name": todo.name, "user": leader}):
						add_docshare("ToDo", todo.name, leader , flags={"ignore_share_permission": True})
		

def get_employees(manager_id, employees_list = None):
	"Get the employees below a given employee"
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
