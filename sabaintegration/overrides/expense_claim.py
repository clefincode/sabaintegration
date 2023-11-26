import frappe
from frappe.utils import flt

from hrms.hr.doctype.expense_claim.expense_claim import ExpenseClaim, validate_active_employee, set_employee_name

class CustomExpenseClaim(ExpenseClaim):
    def validate(self):
        validate_active_employee(self.employee)
        set_employee_name(self)
        self.validate_sanctioned_amount()
        self.calculate_total_amount()
        self.validate_advances()
        self.set_expense_account(validate=True)
        self.set_payable_account()
        self.set_cost_center()
        self.calculate_taxes()
        self.calculate_taxes_in_expense_claim_currency()
        self.set_status()
        if self.task and not self.project:
            self.project = frappe.db.get_value("Task", self.task, "project")
    
    def calculate_total_amount(self):
        self.total_claimed_amount, self.total_claimed_amount_in_expense_claim_currency = 0, 0
        self.total_sanctioned_amount, self.total_sanctioned_amount_in_expense_claim_currency = 0, 0
        for d in self.get("expenses"):
            if self.approval_status == "Rejected":
                d.sanctioned_amount = 0.0
                d.sanctioned_amount_in_expense_claim_currency = 0.0

            self.total_claimed_amount += flt(d.amount)
            self.total_sanctioned_amount += flt(d.sanctioned_amount)

            self.total_claimed_amount_in_expense_claim_currency += flt(d.amount_in_expense_claim_currency)
            self.total_sanctioned_amount_in_expense_claim_currency += flt(d.sanctioned_amount_in_expense_claim_currency)

    def validate_advances(self):
        self.total_advance_amount, self.total_advance_amount_in_expense_claim_currency = 0, 0
        for d in self.get("advances"):
            ref_doc = frappe.db.get_value(
                "Employee Advance",
                d.employee_advance,
                ["posting_date", "paid_amount", "claimed_amount", "advance_account"],
                as_dict=1,
            )
            d.posting_date = ref_doc.posting_date
            d.advance_account = ref_doc.advance_account
            d.advance_paid = ref_doc.paid_amount
            d.unclaimed_amount = flt(ref_doc.paid_amount) - flt(ref_doc.claimed_amount)

            if d.allocated_amount and flt(d.allocated_amount) > flt(d.unclaimed_amount):
                frappe.throw(
                    _("Row {0}# Allocated amount {1} cannot be greater than unclaimed amount {2}").format(
                        d.idx, d.allocated_amount, d.unclaimed_amount
                    )
                )

            self.total_advance_amount += flt(d.allocated_amount)

        if self.total_advance_amount:
            precision = self.precision("total_advance_amount")
            amount_with_taxes = flt(
                (flt(self.total_sanctioned_amount, precision) + flt(self.total_taxes_and_charges, precision)),
                precision,
            )

            if flt(self.total_advance_amount, precision) > amount_with_taxes:
                frappe.throw(_("Total advance amount cannot be greater than total sanctioned amount"))

            self.total_advance_amount_in_expense_claim_currency = self.total_advance_amount / self.exchange_rate
    
    @frappe.whitelist()
    def calculate_taxes_in_expense_claim_currency(self):
        self.total_taxes_and_charges_in_expense_claim_currency = 0
        for tax in self.taxes:
            if tax.rate_in_expense_claim_currency:
                tax.tax_amount_in_expense_claim_currency = flt(self.total_sanctioned_amount_in_expense_claim_currency) * flt(tax.rate_in_expense_claim_currency / 100)

            tax.total_in_expense_claim_currency = flt(tax.tax_amount_in_expense_claim_currency) + flt(self.total_sanctioned_amount_in_expense_claim_currency)
            self.total_taxes_and_charges_in_expense_claim_currency += flt(tax.tax_amount_in_expense_claim_currency)

        self.grand_total_in_expense_claim_currency = (
            flt(self.total_sanctioned_amount_in_expense_claim_currency)
            + flt(self.total_taxes_and_charges_in_expense_claim_currency)
            - flt(self.total_advance_amount_in_expense_claim_currency)
        )
