from odoo import api, fields, models


class HrLeaveDashboard(models.TransientModel):
    _name = "hr.leave.dashboard"
    _description = "Leave Manager Dashboard"
    _rec_name = "name"

    name = fields.Char(default="Leave Manager — Overview")

    # request counts by state
    total_requests = fields.Integer(string="Total Requests", compute="_compute_stats")
    draft_count = fields.Integer(string="Draft", compute="_compute_stats")
    submitted_count = fields.Integer(string="Pending Approval", compute="_compute_stats")
    approved_count = fields.Integer(string="Approved", compute="_compute_stats")
    refused_count = fields.Integer(string="Refused", compute="_compute_stats")

    # percentages per state (used for progress bars)
    draft_percent = fields.Integer(string="Draft %", compute="_compute_stats")
    submitted_percent = fields.Integer(string="Pending %", compute="_compute_stats")
    approved_percent = fields.Integer(string="Approved %", compute="_compute_stats")
    refused_percent = fields.Integer(string="Refused %", compute="_compute_stats")

    # allocation stats
    total_allocations = fields.Integer(string="Total Allocations", compute="_compute_stats")
    total_leave_types = fields.Integer(string="Leave Types", compute="_compute_stats")

    @api.depends()
    def _compute_stats(self):
        for record in self:
            requests = self.env["hr.leave.request"].search([])
            total = len(requests) or 1  # avoid division by zero
            record.total_requests = len(requests)
            record.draft_count = len(requests.filtered(lambda r: r.state == "draft"))
            record.submitted_count = len(requests.filtered(lambda r: r.state == "submitted"))
            record.approved_count = len(requests.filtered(lambda r: r.state == "approved"))
            record.refused_count = len(requests.filtered(lambda r: r.state == "refused"))
            record.draft_percent = int(record.draft_count * 100 / total)
            record.submitted_percent = int(record.submitted_count * 100 / total)
            record.approved_percent = int(record.approved_count * 100 / total)
            record.refused_percent = int(record.refused_count * 100 / total)
            record.total_allocations = self.env["hr.leave.allocation"].search_count([])
            record.total_leave_types = self.env["hr.leave.type"].search_count([])

    def action_view_draft(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Draft Requests',
            'res_model': 'hr.leave.request',
            'view_mode': 'list,form',
            'domain': [('state', '=', 'draft')],
        }

    def action_view_submitted(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pending Approval',
            'res_model': 'hr.leave.request',
            'view_mode': 'list,form',
            'domain': [('state', '=', 'submitted')],
        }

    def action_view_approved(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Approved Requests',
            'res_model': 'hr.leave.request',
            'view_mode': 'list,form',
            'domain': [('state', '=', 'approved')],
        }

    def action_view_refused(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Refused Requests',
            'res_model': 'hr.leave.request',
            'view_mode': 'list,form',
            'domain': [('state', '=', 'refused')],
        }

    def action_view_allocations(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Allocations',
            'res_model': 'hr.leave.allocation',
            'view_mode': 'list,form',
        }

    def action_view_leave_types(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Leave Types',
            'res_model': 'hr.leave.type',
            'view_mode': 'kanban,list,form',
        }

    def action_open_dashboard(self):
        # creates a fresh dashboard record and opens it
        record = self.create({'name': 'Leave Manager — Overview'})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dashboard',
            'res_model': 'hr.leave.dashboard',
            'res_id': record.id,
            'view_mode': 'form',
            'target': 'main',
        }
