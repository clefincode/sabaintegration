import frappe

def quotation_query(user):
    if not user:
        user = frappe.session.user
    roles = frappe.get_roles()

    strroles = "("
    for role in roles:
       strroles += f"'{role}'," 
    strroles = strroles[:-1]
    strroles += ')'

    strWhere = """
    (`tabQuotation`.opportunity_owner is null or `tabQuotation`.opportunity_owner = '' or `tabQuotation`.opportunity_owner = {user})
    or ('Sales Manager' in {roles} or 
        'System Manager' in {roles} or
        '0 Selling - Quotation Creation (Can view All)' in {roles} or
        '0 Selling - Quotation Admin' in {roles}
        )

    """.format(user=frappe.db.escape(user), roles = strroles)
    
    return strWhere

def has_permission(doc, user):
    from frappe.permissions import has_permission
    if doc.event_type == "Public" or doc.owner == user:
        return True
    if has_permission("Event", user = user, ptype = "write"):
        return True
    return False