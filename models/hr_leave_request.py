from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_is_zero, float_compare


class HrLeaveRequest(models.Model):
    _name = "hr.leave.request"
    _description = "Leave Request"
    # mail.thread enables the chatter and message log on the form
    # mail.activity.mixin adds the activity scheduling feature
    _inherit = ['mail.thread', 'mail.activity.mixin']

    employee_id = fields.Many2one("res.users", string="Employee", required=True, default=lambda self: self.env.user, tracking=True)
    leave_type_id = fields.Many2one("hr.leave.type", string="Leave Type", required=True, tracking=True)
    # domain filters allocations to only show ones matching the selected employee and leave type
    allocation_id = fields.Many2one("hr.leave.allocation", string="Allocation",
                                    domain="[('employee_id', '=', employee_id), ('leave_type_id', '=', leave_type_id)]")
    date_from = fields.Date(string="From", required=True, tracking=True)
    date_to = fields.Date(string="To", required=True, tracking=True)
    # computed and stored so we can filter/sort by it in list view
    number_of_days = fields.Integer(string="Duration (days)", compute="_compute_number_of_days", store=True)
    reason = fields.Text(string="Reason")
    # shows remaining days from the linked allocation directly on the form
    remaining_days_in_allocation = fields.Integer(
        string="Days Available",
        related="allocation_id.remaining_days",
        readonly=True,
    )
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'), ('refused', 'Refused')],
        default='draft',
        string="Status",
        tracking=True,  # logs every state change in the chatter
    )

    @api.depends("date_from", "date_to")
    def _compute_number_of_days(self):
        for record in self:
            if record.date_from and record.date_to:
                delta = record.date_to - record.date_from
                # +1 because a one-day leave (same from/to) should count as 1, not 0
                record.number_of_days = delta.days + 1
            else:
                record.number_of_days = 0

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for record in self:
            if record.date_from and record.date_to:
                if record.date_to < record.date_from:
                    raise ValidationError("End date cannot be before start date.")

    @api.constrains("date_from", "date_to", "employee_id")
    def _check_overlapping_requests(self):
        # prevent an employee from having two active requests on the same dates
        for record in self:
            if not record.date_from or not record.date_to:
                continue
            overlapping = self.search([
                ('employee_id', '=', record.employee_id.id),
                ('state', 'not in', ['refused']),
                ('id', '!=', record.id),
                ('date_from', '<=', record.date_to),
                ('date_to', '>=', record.date_from),
            ])
            if overlapping:
                raise ValidationError(
                    f"You already have a leave request overlapping these dates: "
                    f"{overlapping[0].date_from} → {overlapping[0].date_to}."
                )

    @api.constrains("number_of_days", "allocation_id")
    def _check_remaining_days(self):
        # make sure the employee has enough remaining days in their allocation
        for record in self:
            if record.allocation_id:
                if record.number_of_days > record.allocation_id.remaining_days:
                    raise ValidationError(
                        f"Not enough remaining days. You have {record.allocation_id.remaining_days} day(s) left."
                    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            # skip approval flow if the leave type doesn't require it
            if record.leave_type_id and not record.leave_type_id.requires_approval:
                record.state = "approved"
        return records

    def action_submit(self):
        for record in self:
            if record.state != "draft":
                raise UserError("Only draft requests can be submitted.")
            record.state = "submitted"
            record.message_post(
                body=(
                    f"<b>{record.employee_id.name}</b> submitted a leave request for "
                    f"<b>{record.number_of_days}</b> day(s) "
                    f"({record.date_from} → {record.date_to}).<br/>"
                    f"<i>Reason: {record.reason or 'No reason provided.'}</i>"
                ),
                subject=f"Leave Request Submitted — {record.employee_id.name}",
                message_type='email',
                subtype_xmlid='mail.mt_comment',
            )

    def action_approve(self):
        for record in self:
            if record.state != "submitted":
                raise UserError("Only submitted requests can be approved.")
            record.state = "approved"
            record.message_post(
                body=(
                    f"Your leave request for <b>{record.number_of_days}</b> day(s) "
                    f"({record.date_from} → {record.date_to}) has been <b>approved</b>."
                ),
                subject=f"Leave Request Approved — {record.employee_id.name}",
                message_type='email',
                subtype_xmlid='mail.mt_comment',
            )

    def action_refuse(self):
        for record in self:
            if record.state == "approved":
                raise UserError("Approved requests cannot be refused. Reset to draft first.")
            record.state = "refused"
            record.message_post(
                body=(
                    f"Your leave request for <b>{record.number_of_days}</b> day(s) "
                    f"({record.date_from} → {record.date_to}) has been <b>refused</b>."
                ),
                subject=f"Leave Request Refused — {record.employee_id.name}",
                message_type='email',
                subtype_xmlid='mail.mt_comment',
            )

    def action_reset_draft(self):
        for record in self:
            if record.state not in ("refused", "submitted"):
                raise UserError("Only refused or submitted requests can be reset to draft.")
            record.state = "draft"

    @api.model
    def action_auto_refuse_expired(self):
        # called daily by the cron job — refuses any draft/submitted requests whose end date has passed
        today = fields.Date.today()
        expired = self.search([
            ('state', 'in', ['draft', 'submitted']),
            ('date_to', '<', today),
        ])
        for record in expired:
            record.state = 'refused'
            record.message_post(
                body="This leave request was automatically refused because the leave dates have passed.",
                subject="Leave Request Auto-Refused",
                message_type='email',
                subtype_xmlid='mail.mt_comment',
            )
