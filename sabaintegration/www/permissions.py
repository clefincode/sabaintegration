import frappe

def quotation_query(user):
    from sabaintegration.overrides.employee import get_employees
    if not user:
        user = frappe.session.user
    roles = frappe.get_roles()
    users = "("
    if user != "Administrator" and "System Manager" not in roles:
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
        employees = get_employees(employee, "name", "reports_to")
        if employees:
            for emp in employees:
                user_id = frappe.db.get_value("Employee", {"employee": emp}, "user_id")
                if not user_id: continue
                users += f'"{user_id}",'
    users += f'"{user}")'

    strroles = "("
    for role in roles:
       strroles += f"'{role}'," 
    strroles = strroles[:-1]
    strroles += ')'

    strWhere = """
    `tabQuotation`.opportunity_owner in {users}
    or ('Sales Manager' in {roles} or 
        'System Manager' in {roles} or
        '0 Selling - Quotation Creation (Can view All)' in {roles} or
        '0 Selling - Quotation Admin' in {roles}
        )

    """.format(users=users, roles = strroles)
    return strWhere

def has_permission(doc, user=None, ptype=None):
    from frappe.permissions import has_permission
    if doc.doctype == "Event":
        if doc.event_type == "Public" or doc.owner == user:
            return True
        if has_permission("Event", user = user, ptype = "write"):
            return True
        return False
    if doc.doctype == "Quotation" and ptype == "write":
        if doc.opportunity_owner == frappe.session.user:
            return True
        elif any(role in frappe.get_roles() for role in ['Sales Manager', 'System Manager', '0 Selling - Quotation Creation (Can view All)', '0 Selling - Quotation Admin']):
            return True
        return False

