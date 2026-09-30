from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    def _check_contract_status(self, vals):
        task_id = vals.get('task_id') or self.task_id.id
        if task_id:
            task = self.env['project.task'].browse(task_id)
            order = task.sale_order_id
            if order and order.state == 'done':
                raise UserError(_(
                    "Action Blocked: You cannot record or modify time for an "
                    "Expired contract (%s)."
                ) % order.name)

    @api.model
    def create(self, vals):
        self._check_contract_status(vals)
        return super(AccountAnalyticLine, self).create(vals)

    def write(self, vals):
        if 'task_id' in vals or 'project_id' in vals:
            self._check_contract_status(vals)
        return super(AccountAnalyticLine, self).write(vals)