# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
import frappe
from frappe import _

#from hrms.overrides.employee_master import EmployeeMaster

# class CustomEmployee(EmployeeMaster):
def custom_validate(self, *args, **kwargs):
	share_todos(self) 

###Custom Update
def share_todos(self):
	"""if a new user has been added to ToDo Maintainer field, 
	employee's ToDo are shared with his ToDo Maintainer and with ToDo Maintainers higher levels """

	###Remove sharing todos from previous todo maintainer
	if self.get_doc_before_save() and self.get_doc_before_save().todo_maintainer_ and self.get_doc_before_save().todo_maintainer_ != self.todo_maintainer_:

		prev_maintainer = self.get_doc_before_save().todo_maintainer_
		leaders = get_leaders(prev_maintainer, "user_id", "todo_maintainer_")
		if leaders : leaders.append(prev_maintainer)
		else: leaders = [prev_maintainer]

		employess = get_employees(self.user_id, "user_id", "todo_maintainer_")
		if employess: employess.append(self.user_id)
		else: employess = [self.user_id]

		todos = frappe.db.get_all("ToDo", {"allocated_to": ("in", employess)})

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
		_share_todos(self.user_id, self.todo_maintainer_)
		
def _share_todos(user_id, todo_maintainer_):
	from frappe.share import add_docshare

	leaders = get_leaders(todo_maintainer_, "user_id", "todo_maintainer_")
	if leaders : leaders.append(todo_maintainer_)
	else: leaders = [todo_maintainer_]
	
	employess = get_employees(user_id, "user_id" ,"todo_maintainer_")
	if employess: employess.append(user_id)
	else: employess = [user_id]

	todos = frappe.db.get_all("ToDo", {"allocated_to": ("in", employess)})
	for todo in todos:
		for leader in leaders:
			if not frappe.db.exists("ToDo", {"share_doctype": "ToDo", "share_name": todo.name, "user": leader}):
				add_docshare("ToDo", todo.name, leader , flags={"ignore_share_permission": True})

def get_employees(maintainer_id, maintainer_id_fieldname, maintainer_field, employees_list = None):
	"Get the employees below a given employee"
	if not employees_list:
		employees_list = []

	employees = frappe.db.get_all("Employee", {maintainer_field: maintainer_id},  maintainer_id_fieldname)

	if employees:
		for employee in employees:
			employees_list.append(employee.get(maintainer_id_fieldname))
			get_employees(employee.get(maintainer_id_fieldname), maintainer_id_fieldname, maintainer_field, employees_list)
	else:
		return
	return set(employees_list)

def get_leaders(user, user_field, maintainer_field, employees = None, direct_leader = False):
    if not employees:
        employees = []
    leader = frappe.db.get_value("Employee", {user_field: user} , maintainer_field)
    if not leader:
        return 
    else:
        if direct_leader: return leader
        if not leader in employees:
            employees.append(leader)
        get_leaders(leader, user_field, maintainer_field, employees)
    return employees

@frappe.whitelist()
def share_todos_with_team():
	employees = frappe.db.get_all("Employee", {"user_id": ("!=", ""), "todo_maintainer_": ("!=", "")}, ["name", "user_id", "todo_maintainer_"])
	for emp in employees:
		_share_todos(emp.user_id, emp.todo_maintainer_)
	frappe.db.commit()