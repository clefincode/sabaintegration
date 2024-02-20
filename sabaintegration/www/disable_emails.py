#!/usr/bin/env python3

import frappe

def disable_emails():
    "Disable all Emails Account to Prevent Sending Email from Test Server"

    accounts = frappe.db.get_all("Email Account", fields = ["name"])

    for account in accounts:
        doc = frappe.get_doc("Email Account", account.name)
        if doc.enable_incoming: doc.enable_incoming = 0

        if doc.enable_outgoing: doc.enable_outgoing = 0

        if doc.enable_auto_reply: doc.enable_auto_reply = 0

        doc.save()

if __name__ == "__main__":
    disable_emails()
