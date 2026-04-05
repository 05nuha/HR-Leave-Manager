from odoo import api, fields, models


class HrLeaveType(models.Model):
    _name = "hr.leave.type"
    _description = "Leave Type"

    name = fields.Char(required=True)
    description = fields.Text(string="Description")
    max_days = fields.Integer(string="Max Days Allowed", required=True)
    # if requires_approval is False, the request auto-approves on create
    requires_approval = fields.Boolean(string="Requires Approval", default=True)
    # color index used by the kanban view to color-code each leave type card
    color = fields.Integer(string="Color")
    allocation_ids = fields.One2many("hr.leave.allocation", "leave_type_id", string="Allocations")
    request_ids = fields.One2many("hr.leave.request", "leave_type_id", string="Requests")

    # computed counts for the stat buttons on the form view
    allocation_count = fields.Integer(string="Allocations", compute="_compute_allocation_count")
    request_count = fields.Integer(string="Requests", compute="_compute_request_count")

    _sql_constraints = [
        ('unique_leave_type_name', 'UNIQUE(name)', 'Leave type name must be unique!'),
        ('check_max_days', 'CHECK(max_days > 0)', 'Max days must be greater than zero!'),
    ]

    @api.depends("allocation_ids")
    def _compute_allocation_count(self):
        for record in self:
            record.allocation_count = len(record.allocation_ids)

    @api.depends("request_ids")
    def _compute_request_count(self):
        for record in self:
            record.request_count = len(record.request_ids)

    def action_view_allocations(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Allocations',
            'res_model': 'hr.leave.allocation',
            'view_mode': 'list,form',
            'domain': [('leave_type_id', '=', self.id)],
            'context': {'default_leave_type_id': self.id},
        }

    def action_view_requests(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Leave Requests',
            'res_model': 'hr.leave.request',
            'view_mode': 'list,form',
            'domain': [('leave_type_id', '=', self.id)],
            'context': {'default_leave_type_id': self.id},
        }
