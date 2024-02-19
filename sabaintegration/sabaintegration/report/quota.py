from copy import deepcopy

import frappe
from sabaintegration.overrides.employee import get_employees, get_leaders
from sabaintegration.sabaintegration.doctype.commission_rule.commission_rule import calculate_commission
from sabaintegration.sabaintegration.doctype.default_kpi.default_kpi import get_default_kpi

class QuotaCalculations:
	def __init__(self, *args):
		args = args[0]
		self.doctype = args['doctype']
		self.user = args['user']
		self.role = args['role']
		self.rule = args['rule']
		self.filters = args['filters']

		if self.doctype == "Sales Person":
			self.qq_doctype = "Quarter Quota"
			self.person_type = "sales_man"
		elif self.doctype == "Pre-Sales Engineer":
			self.qq_doctype = "Pre-Sales Quarter Quota"
			self.person_type = "engineer"
		elif self.doctype == "Product Manager":
			self.qq_doctype = "Marketing Quarter Quota"
			self.person_type = "product_manager"
	
	def get_incentives(self):
		# get achievement values for each person
		if not self.filters.get('quarter') or not self.filters.get('year'): return None, None

		total_achievement_values, achievement_values, leaders = self.get_achievement_values()
		
		list_filters = {}
		list_filters['year'] = self.filters['year']
		list_filters['quarter'] = self.filters['quarter']

		person_comm, achieved_target_person = {}, {}
		msg = ""
		
		if self.doctype == "Product Manager":
			achievement_list = achievement_values
			if not frappe.db.exists(self.qq_doctype, list_filters): 
				msg += "No Quarter Quota was found"
				return None, msg
			quarter_quota = frappe.get_doc(self.qq_doctype, list_filters)
			rows = quarter_quota.brands
		else:
			achievement_list = total_achievement_values
		if not achievement_list:
			return (None, None)

		for ach_row in achievement_list:
			# Sales Commission -> ach_row = sales_man
			# Pre-Sales Activity -> ach_row = engineer
			# Marketing Incentive -> ach_row = (product_manager, brand)
			
			quota, person = None, ""
			if self.doctype == "Product Manager":
				found, person = False, ach_row[0]
				for row in rows:
					if row.product_manager == person and row.brand == ach_row[1]:
						found = True
						quota = row
						break
				if not found: 
					msg += "</br> {0}, {1}".format(row.product_manager, row.brand) 
					continue
			else:
				person = list_filters[self.person_type] = ach_row
				if not frappe.db.exists(self.qq_doctype, list_filters): 
					msg += "</br> {}".format(ach_row) 
					continue

				quota = frappe.get_doc(self.qq_doctype, list_filters)
			
			# 	Calculate the achievement percentage depending on the quarter quota
			achievemnt_percent = achievement_list[ach_row] / quota.total_quota * 100 if quota.total_quota > 0 else 100

			# Calculate the incentive milestone percentage depending on the rule
			comm = calculate_commission(achievemnt_percent, self.rule)

			if not person_comm.get(ach_row):
				person_comm[ach_row] = {}

			person_comm[ach_row]['kpi'] = quota.kpi
			person_comm[ach_row]['achieve_percent'] = achievemnt_percent
			person_comm[ach_row]['quota'] = quota.total_quota
			person_comm[ach_row]['achieve_value'] = achievement_values.get(ach_row, 0)
			person_comm[ach_row]['total_achieve_value'] = total_achievement_values[person]
			person_comm[ach_row]['achieved_target'] = comm
			person_comm[ach_row]['leaders'] = leaders.get(person, [])

			if self.doctype == "Pre-Sales Engineer":
				person_comm[ach_row]['incentive_percentage'] = quota.incentive_percentage
			
			if not comm:
				if self.doctype == "Product Manager": person_comm[ach_row]['incentive_percentage'] = quota.incentive_percentage
				elif self.doctype == "Sales Person": person_comm[ach_row]['incentive_percentage'] = quota.commission_percentage

				continue

			achieved_target_person[ach_row] = comm
			
			if self.doctype == "Product Manager":
				ach_row = {
					"product_manager": ach_row[0],
					"brand": ach_row[1]
				}
			docs = self.get_docs_achievements(ach_row)

			for doc in docs:
				self.calculate_incentive_in_so(
					sales_order = doc.sales_order, 
					person_comm = person_comm, 
					row = ach_row, 
					achieve_milestone = comm, 
					filters = list_filters)

			if self.doctype != "Product Manager":
				if self.doctype == "Sales Person":
					if len(docs):
						person_comm[ach_row]['incentive_percentage'] = person_comm[ach_row].get('incentive_percentage',0) / len(docs)
					else:
						if self.doctype == "Sales Person": person_comm[ach_row]['incentive_percentage'] = quota.commission_percentage
						
				else: person_comm[ach_row]['incentive_percentage'] = quota.incentive_percentage

		self.set_leaders_extra(person_comm, achieved_target_person, total_achievement_values)
		person_comm = self.get_permitted_rows(person_comm)
		return person_comm, msg

	def get_achievement_values(self):
		"Get the Achievement and the Total Achievement of a Person in Addition to his Leaders"
		
		total_achievement_values, achievement_values, emp_leaders = {}, {}, {}
		checked_sos = []
		docs = self.get_docs()

		if not docs: return (None, None, None)

		# Iterate through all the docs/ Engineer / Product Managers of the quarter
		for doc in docs:
			if self.doctype != "Sales Person":
				if self.doctype == "Product Manager":
					field_cond = {"product_manager": doc}
				else:
					field_cond = doc
				docs_achievements = self.get_docs_achievements(field_cond)
				if not docs_achievements: continue

				employee = get_employee(self.doctype, doc)
				if not employee:
					frappe.throw("{} is not Linked to any Employee Record".format(doc))
				
				leaders = get_leaders(employee.name, "name", "reports_to", None)

				# Iterate through the docs that has a specific Engineer/ (Product Manager, Brand) to calculate the achievement
				for d in docs_achievements:
					if self.doctype == "Product Manager": 
						record = (doc, d.brand)
						achieve = d.brand_achievement
					else: 
						record = doc
						achieve = d.base_expected_profit_loss_value * d.contribution_percentage / 100
					achievement_values[record] = achievement_values.get(record, 0) + achieve
					total_achievement_values[doc] = total_achievement_values.get(doc, 0) +achieve

					if leaders:
						self.set_leaders_achievements(leaders, doc, achieve, total_achievement_values, emp_leaders)

			else:
				if not doc.primary_sales_man:
					frappe.throw("Sales Order: {} doesn't have a primary sales man for it".format(doc.sales_order))

				if doc.sales_order in checked_sos: continue
				checked_sos.append(doc.sales_order)
				
				employee = get_employee(self.doctype, doc.primary_sales_man)
				if not employee:
					frappe.throw("Sales Person {} is not Linked to any Employee Record".format(doc.primary_sales_man))

				achievement_values[doc.primary_sales_man] = achievement_values.get(doc.primary_sales_man, 0) + doc.base_expected_profit_loss_value
				total_achievement_values[doc.primary_sales_man] = total_achievement_values.get(doc.primary_sales_man,0) + doc.base_expected_profit_loss_value

				leaders = get_leaders(employee.name, "name", "reports_to", None)
				if leaders:
					self.set_leaders_achievements(leaders, doc.primary_sales_man, doc.base_expected_profit_loss_value, total_achievement_values, emp_leaders)
		
		return total_achievement_values, achievement_values, emp_leaders

	def set_leaders_achievements(self, leaders, person, achieve, total_achievement_values, emp_leaders):
		for leader in leaders:
			leader_doc = frappe.get_doc("Employee", leader)
			if check_if_leader(leader_doc, self.doctype):
				l_person = frappe.db.get_value(self.doctype, {"employee": leader}, "name")
				
				if not l_person: continue
				
				if not emp_leaders.get(person):
					emp_leaders[person] = [l_person]
				elif l_person not in emp_leaders[person]:
					emp_leaders[person].append(l_person)


				total_achievement_values[l_person] = total_achievement_values.get(l_person, 0) + achieve
	
	def get_conditions(self):
		conditions = ""
		if self.filters.get("year"):
			conditions += " and EXTRACT(YEAR FROM so.submitting_date) = %(year)s"
		if self.filters.get("quarter"):
			conditions += " and CONCAT('Q', CEILING(EXTRACT(MONTH FROM so.submitting_date) / 3.0)) = %(quarter)s"
		return conditions

	def get_docs(self):
		if self.doctype == "Sales Person": return self.get_docs_achievements()

		if self.doctype == "Pre-Sales Engineer": return self.get_engineers()

		if self.doctype == "Product Manager": return self.get_product_managers()

	def get_product_managers(self):
		"Get All Prdouct Managers of a Specific Year and Quarter"
		product_managers = []
		if frappe.db.exists("Marketing Quarter Quota", {
			"year": self.filters.get("year"),
			"quarter": self.filters.get("quarter"),
			"docstatus": 1
		}):
			doc = frappe.get_doc("Marketing Quarter Quota", {
			"year": self.filters.get("year"),
			"quarter": self.filters.get("quarter"),
			"docstatus": 1
			})
			for row in doc.brands:
				if row.product_manager in product_managers: continue
				product_managers.append(row.product_manager)
			return product_managers
	
	def get_engineers(self):
		"Get All Engineers of a Specific Year and Quarter"
		engs = frappe.db.get_all("Pre-Sales Quarter Quota", {
			"year": self.filters.get("year"),
			"quarter": self.filters.get("quarter"),
			"docstatus": 1
		}, "engineer")
		if not engs: return
		
		engineers = []

		for eng in engs:
			engineers.append(eng.engineer)
		return engineers


	def get_docs_achievements(self, field_cond=None):
		"Get SOs Expected P&L in a Specifc Year and Quarter"
		conditions = self.get_conditions()
		if self.doctype == "Sales Person":
			strQuery= """
				select so.name as sales_order, 
				so.base_expected_profit_loss_value as base_expected_profit_loss_value,
				so.primary_sales_man as primary_sales_man,
				prm_sup_percentage, sec_sup_percentage
				from `tabSales Order` as so
				where so.submitting_date != '' and so.submitting_date is not null and so.docstatus = 1
				and so.primary_sales_man != '' and so.primary_sales_man is not null
				and so.base_expected_profit_loss_value > 0
				{conditions}
				""".format(conditions = conditions)
			if field_cond:
				strQuery += " and so.primary_sales_man = '{primary_sales_man}'".format(primary_sales_man = field_cond)
		elif self.doctype == "Pre-Sales Engineer":
			strQuery= """
				select so.name as sales_order, so.base_expected_profit_loss_value as base_expected_profit_loss_value, pre_sales.contribution_percentage
				from `tabSales Order` as so
				inner join `tabPre-Sales Incentive` as pre_sales on so.name = pre_sales.parent
				where so.submitting_date != '' and so.submitting_date is not null and so.docstatus = 1
				and so.base_expected_profit_loss_value > 0
				{conditions}
				""".format(conditions = conditions)
			if field_cond:
				strQuery += " and pre_sales.engineer = '{engineer}' ".format(engineer = field_cond)
		
		else:
			if field_cond.get('brand'):
				strQuery = """
					select so.name as sales_order, brand_details.brand, brand_details.total_quota as brand_achievement """
			else:
				strQuery= """
					select brand_details.brand, sum(brand_details.total_quota) as brand_achievement """
			
			strQuery += """
			from `tabSales Order` as so
			inner join `tabBrand Details` as brand_details on so.name = brand_details.parent
			where so.submitting_date != '' and so.submitting_date is not null and so.docstatus = 1
			and brand_details.product_manager = '{product_manager}'
			{conditions}
			""".format(product_manager = field_cond.get('product_manager'), conditions = conditions)
			if field_cond.get('brand'):
				strQuery += " and brand_details.brand = '{brand}' ".format(brand=field_cond.get('brand'))
		
			else: 
				strQuery += """ group by brand_details.brand
				having sum(brand_details.total_quota) > 0 """

		return frappe.db.sql(strQuery, self.filters, as_dict = 1)

	def calculate_incentive_in_so(self, **kwargs):
		"Calculae the Deserved Incentive Value in Each SO"
		doc = frappe.get_doc("Sales Order", kwargs['sales_order'])
		filters = kwargs['filters']

		kpi_doc = False
		if frappe.db.exists("Default KPI", {'quarter': filters['quarter'], 'year': filters['year'], 'docstatus': 1}):
			kpi_doc = True

		profit_loss_value, table = 0, "brands"
		if self.doctype == "Pre-Sales Engineer":
			table = "pre_sales_activities"
			row = ele = kwargs["row"]
			column = "engineer"
			profit_loss_value = doc.base_expected_profit_loss_value * kwargs['achieve_milestone'] / 100 
	
		elif self.doctype == "Sales Person":
			table = "sales_commission"
			profit_loss_value = doc.base_expected_profit_loss_value * kwargs["achieve_milestone"] / 100 * doc.commission_percentage / 100
			kwargs["person_comm"][kwargs["row"]]['incentive_percentage'] = kwargs["person_comm"][kwargs["row"]].get('incentive_percentage', 0) + doc.commission_percentage
		else:
			ele = kwargs["row"]["brand"]
			row = (kwargs["row"]["product_manager"], kwargs["row"]["brand"])
			column = "brand"
			profit_loss_value = kwargs["achieve_milestone"] / 100

		for d in doc.get(table):
			person = ""
			if self.doctype != "Sales Person":
				if ele != d.get(column): continue
				person = d.get(self.person_type)
			else:
				person = d.sales_person
				row = d.sales_person

			if not kwargs["person_comm"].get(row):
				kwargs["person_comm"][row] = {}
			
			
			if not kwargs["person_comm"][row].get("kpi"):
				if kpi_doc:
					kwargs["person_comm"][row]['kpi'] = get_default_kpi(
						doc = self.qq_doctype,
						person = person,
						year = filters['year'],
						quarter = filters['quarter']
						)
				else:
					kwargs["person_comm"][row]['kpi'] = 0

			kpi = kwargs["person_comm"][row]['kpi'] or 0

			if self.doctype == "Product Manager":
				new_profit_loss_value = profit_loss_value * d.total_quota * d.incentive_percentage / 100
				kwargs["person_comm"][row]['incentive_value'] = kwargs["person_comm"][row].get('incentive_value', 0) + new_profit_loss_value 
				break
			elif self.doctype == "Pre-Sales Engineer":
				incentive_percentage = kwargs["person_comm"][row]["incentive_percentage"]
				new_profit_loss_value = profit_loss_value * d.contribution_percentage / 100 * incentive_percentage / 100

				kwargs["person_comm"][row]['incentive_value'] = kwargs["person_comm"][row].get('incentive_value', 0) + new_profit_loss_value 
				break
			else:
				if not kwargs["person_comm"][d.sales_person].get('quota'):
					kwargs["person_comm"][d.sales_person]['quota'] = frappe.db.get_value('Quarter Quota', {'sales_man': d.sales_person, 'quarter': filters['quarter'], 'year': filters['year'], 'docstatus': 1}, 'quota')
				
				new_profit_loss_value = profit_loss_value * (d.comm_percent / 100)
				
				if d.sales_person == doc.primary_sales_man:
					kwargs["person_comm"][d.sales_person]['direct_sales_contribution'] = kwargs["person_comm"].get(d.sales_person).get('direct_sales_contribution', 0) + (doc.base_expected_profit_loss_value * (d.comm_percent / 100))
					kwargs["person_comm"][d.sales_person]['commission_value'] = kwargs["person_comm"].get(d.sales_person).get('commission_value', 0) + new_profit_loss_value
				else:
					kwargs["person_comm"][d.sales_person]['other_commission'] = kwargs["person_comm"][d.sales_person].get('other_commission', 0) + (new_profit_loss_value * kpi / 100)

	def set_leaders_extra(self, person_comm, achieved_target_person, total_achievement_values):
		for row in achieved_target_person:
			if self.doctype != 'Product Manager':
				docs = self.get_docs_achievements(row)

				if not docs or len(docs[0])<= 0: continue

				for doc in docs:

					own_level = self.set_extra_on_direct_so(person_comm, row, doc)

					if own_level == "primary": self.set_extra_on_indirect_so(person_comm, row, doc = doc, leader_level = "secondary")
					else: self.set_extra_on_indirect_so(person_comm, row, doc = doc)

			else:
				own_level = self.set_extra_on_direct_so(person_comm, row)

				if own_level == "primary": self.set_extra_on_indirect_so(person_comm, row, total_achievement_values = total_achievement_values, leader_level = "secondary")
				else: self.set_extra_on_indirect_so(person_comm, row, total_achievement_values = total_achievement_values)
				
	def set_extra_on_direct_so(self, person_comm, person_row, doc = None):
		"Set the Deserved Extra Percentage from a Person's Docs"
		person = person_row
		if self.doctype == "Product Manager":
			person = person[0]
		employee = get_employee(self.doctype, person)
		if not check_if_leader(employee, self.doctype): return

		prm_extra = 0
		if self.doctype == "Sales Person":
			prm_extra = doc.prm_sup_percentage
			if not prm_extra:
				prm_extra = frappe.db.get_value("Quarter Quota", {
				'sales_man': person_row, 
				'year': self.filters['year'],
				'quarter': self.filters['quarter'],
				'docstatus': 1
				}, 'primary_commission_percentage') or 1.5
			extra_incentive = doc.base_expected_profit_loss_value * prm_extra / 100 
		
		elif self.doctype == "Pre-Sales Engineer":
			prm_extra = frappe.db.get_value("Pre-Sales Quarter Quota", {
				'engineer': person_row, 
				'year': self.filters['year'],
				'quarter': self.filters['quarter'],
				'docstatus': 1
				}, 'primary_incentive_percentage')

			extra_incentive = doc.base_expected_profit_loss_value * doc.contribution_percentage / 100 * prm_extra / 100

		else:
			qq = frappe.get_doc("Marketing Quarter Quota", {
				'year': self.filters['year'],
				'quarter': self.filters['quarter'],
				'docstatus': 1
			})
			prm_extra = 0
			for row in qq.leaders:
				if row.leading_product_manager == person:
					prm_extra = row.primary_extra
					break
			extra_incentive = person_comm[person_row]['achieve_value'] * prm_extra / 100 
		
		comm = person_comm[person_row].get('achieved_target', 0)

		if comm:
			person_comm[person_row]['primary_supervision_incentive'] = person_comm[person_row].get('primary_supervision_incentive', 0) + (extra_incentive * comm / 100)
			return "primary"

	def set_extra_on_indirect_so(self, person_comm, row, doc = None, total_achievement_values = None, leader_level= None):
		"Set the Deserved Extra Percentage from Person's Indirect SOs"
		person = row
		if self.doctype == "Product Manager":
			person = row[0]
			brand = row[1]
		employee = get_employee(self.doctype, person)
		set_employee = False
		if person_comm[row].get("leaders") and person_comm[row]['leaders'][0]:
			leaders = person_comm[row]["leaders"]
			set_employee = True
		else:
			leaders = get_leaders(employee.name, "name", "reports_to", None)

		own_so = False
		if not leaders or not leaders[0]: 
			leaders = [employee.name]
			leader_level = "secondary"
			own_so = True

		if leader_level == "secondary":
			level = 'secondary'
			
		else:
			level = 'primary'

		if self.doctype == "Product Manager":
			qq = frappe.get_doc("Marketing Quarter Quota", {
				'year': self.filters['year'],
				'quarter': self.filters['quarter'],
				'docstatus': 1
			})
		templeaders = deepcopy(leaders)
		for leader in leaders:

			templeaders.remove(leader)

			if set_employee:
				leader_doc = get_employee(self.doctype, leader)
				if leader_doc:
					leader = leader_doc.name
				else: frappe.throw("There is no Employee record for sales man: "+ leader)
			
			leader = frappe.get_doc("Employee", leader)

			if not check_if_leader(leader, self.doctype) : continue

			leader_person = frappe.db.get_value(self.doctype, {"employee": leader.name}, "name")

			if not leader_person:
				if not templeaders: 
					leaders.append(employee.name)
					templeaders.append(employee.name)
					set_employee = False
				continue
			
			extra_value = 0
			leader_row = leader_person
			if self.doctype == "Product Manager":
				leader_row = (leader_person, brand)
				l_row = None

				for row in qq.leaders:
					if row.leading_product_manager == leader_person:
						l_row = row
						break

				if not l_row: continue
				
				extra_value = person_comm[(person, brand)]['achieve_value'] * l_row.get(level+"_extra") / 100 

			elif self.doctype == "Pre-Sales Engineer":
				extra = frappe.db.get_value("Pre-Sales Quarter Quota", {
					'engineer': leader_person, 
					'year': self.filters['year'],
					'quarter': self.filters['quarter'],
					'docstatus': 1
				}, level + '_incentive_percentage')

				extra_value = doc.base_expected_profit_loss_value * doc.contribution_percentage / 100 * extra / 100 

			else:
				if level == "primary":
					extra = doc.prm_sup_percentage
				else:
					extra = doc.sec_sup_percentage
				
				if not extra:
					extra = frappe.db.get_value("Quarter Quota", {
						'sales_man': leader_person, 
						'year': self.filters['year'],
						'quarter': self.filters['quarter'],
						'docstatus': 1
						}, level+'_commission_percentage')

				extra_value = doc.base_expected_profit_loss_value * extra / 100
			
			if not leader_row in person_comm:
				if self.doctype == "Product Manager":
					kpi = get_default_kpi(doc = 'Marketing Quarter Quota', person = leader_person, year = self.filters['year'] , quarter = self.filters['quarter'])
					achieve_percent = total_achievement_values[leader_person] / l_row.total_margin_quota * 100
					person_comm[leader_row] = {
						"kpi": kpi,
						"achieve_percent": achieve_percent,
						"achieved_target": calculate_commission(achieve_percent, self.rule),
						"quota": l_row.total_margin_quota,
						"total_achieve_value": total_achievement_values[leader_person],
					}
				else: continue
			
			comm = person_comm[leader_row].get('achieved_target', 0)
			if comm:

				person_comm[leader_row][level+'_supervision_incentive'] = person_comm[leader_row].get(level+'_supervision_incentive', 0) + (extra_value * comm / 100)

				if not own_so and self.doctype == "Sales Person":
					person_comm[leader_row]["achiever_sub_pl"] = person_comm[leader_row].get("achiever_sub_pl", 0) + doc.base_expected_profit_loss_value
		

			if level == "secondary":
				return
			else:
				level = "secondary"
	
	def get_permitted_rows(self, person_comm):
		admin, _person = is_admin(self.user, self.role, self.doctype)
		
		if not admin and _person:

			dict_sm = {}

			employee = frappe.db.get_value("Employee", {"user_id": self.user}, "name")

			if self.doctype == "Product Manager":
				selected_values = {key: value for key, value in person_comm.items() if key[0] == _person}
				if selected_values:
					dict_sm = selected_values
			else:
				if person_comm.get(_person):
					dict_sm = {_person : person_comm[_person]}

			employees = get_employees(employee, "name", "reports_to")
			if not employees: return dict_sm
			for emp in employees:
				sp = frappe.db.get_value(self.doctype, {"employee": emp}, "name")
				if not sp: continue

				if self.doctype != "Product Manager":
					if not person_comm.get(sp): continue

					dict_sm[sp] = person_comm[sp]
				else:
					selected_values = {key: value for key, value in person_comm.items() if key[0] == sp}
					if not selected_values: continue

					dict_sm = dict_sm | selected_values
				
			return dict_sm
		
		else: return person_comm


def is_admin(user, role, doctype):
    if user != "Administrator" and role not in frappe.get_roles():
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    
        if not employee: 
            frappe.throw(f"User {user} doesn't have an Employee Record")

        person = frappe.db.get_value(doctype, {"employee": employee}, "name")
        
        if not person:
            frappe.throw("Not Permitted!")
        
        return False, person
    return True, ""


@frappe.whitelist()
def get_person(user_type, user = ''):
	if user:
		employee = frappe.db.get_all("Employee", {"user_id": user})

		if not employee: return ''
		if employee and employee[0]:
			employee = employee[0].name
			person = frappe.db.get_all(user_type, {"employee": employee}, "name")
			if not person: return ''
			
			employees = get_employees(employee, "name", "reports_to")

			if not employees: return "'" + person[0].name + "'"
			
			st_person = ""
			for employee in employees:
				_person = frappe.db.get_value(user_type, {"employee": employee}, "name")
				if not _person: continue
				st_person += f"'{_person}',"

			st_person += "'" + person[0].name + "'"

			return st_person			

	else:
		person_s = frappe.db.get_all(user_type, {"enabled":1}, "name")
		if not person_s: return ''
		st_person = ''
		for sm in person_s:
			st_person += f"'{sm.name}',"
		return st_person[:-1]

def check_if_leader(employee, doctype):
	if employee.position != "Senior" and\
		employee.position != "Team Leader" and\
		employee.position != "Manager" : 
		return False
	
	if employee.position == "Senior":
		_person = frappe.db.get_value(doctype, {"employee": employee.name}, "name")
		if _person:
			is_leader = check_if_team_leader(employee)
			if not is_leader: return
		else: return False
	return True

def check_if_team_leader(employee):
	if employee.get("reports_to") and employee.position == "Senior":
		reports_to = employee.reports_to
		position = frappe.db.get_value("Employee", reports_to, "position")
		if position and position == "Manager":
			return True
	if employee.position == "Manager" or employee.position == "Team Leader":
		return True

	return False


def get_employee(doctype, person):
	employee = frappe.db.get_all(doctype, {"name": person}, "employee")
	if employee and employee[0].employee:
		return frappe.get_doc("Employee", employee[0].employee)
	return