from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrLeaveAllocation(models.Model):
    _name = "hr.leave.allocation"
    _description = "Leave Allocation"

    # auto-generated display name so the allocation shows up nicely in dropdowns
    name = fields.Char(string="Name", compute="_compute_name", store=True)
    employee_id = fields.Many2one("res.users", string="Employee", required=True, default=lambda self: self.env.user)
    leave_type_id = fields.Many2one("hr.leave.type", string="Leave Type", required=True)
    number_of_days = fields.Integer(string="Allocated Days", required=True)
    # remaining_days is stored so it can be used in list view decorations and domain filters
    remaining_days = fields.Integer(string="Remaining Days", compute="_compute_remaining_days", store=True)
    request_ids = fields.One2many("hr.leave.request", "allocation_id", string="Leave Requests")
    request_count = fields.Integer(string="Requests Used", compute="_compute_request_count")

    _sql_constraints = [
        ('check_allocated_days', 'CHECK(number_of_days > 0)', 'Allocated days must be greater than zero!'),
    ]

    @api.depends("employee_id", "leave_type_id")
    def _compute_name(self):
        for record in self:
            employee = record.employee_id.name or "Unknown"
            leave_type = record.leave_type_id.name or "Unknown"
            record.name = f"{employee} — {leave_type}"

    @api.depends("number_of_days", "request_ids.number_of_days", "request_ids.state")
    def _compute_remaining_days(self):
        for record in self:
            # only count approved requests as "used" days
            used = sum(record.request_ids.filtered(lambda r: r.state == "approved").mapped("number_of_days"))
            record.remaining_days = record.number_of_days - used

    @api.depends("request_ids")
    def _compute_request_count(self):
        for record in self:
            record.request_count = len(record.request_ids)

    def action_view_requests(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Leave Requests',
            'res_model': 'hr.leave.request',
            'view_mode': 'list,form',
            'domain': [('allocation_id', '=', self.id)],
            'context': {'default_allocation_id': self.id},
        }

    @api.constrains("number_of_days", "leave_type_id")
    def _check_max_days(self):
        # allocation cannot exceed what the leave type allows
        for record in self:
            if record.leave_type_id and record.number_of_days > record.leave_type_id.max_days:
                raise ValidationError(
                    f"Allocated days ({record.number_of_days}) cannot exceed the maximum allowed "
                    f"for '{record.leave_type_id.name}' ({record.leave_type_id.max_days} days)."
                )
