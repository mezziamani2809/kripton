from odoo import models, fields, api


class InheritResPartner(models.Model):
    _inherit = "hr.employee"

    cost_id = fields.One2many(
        "cost.employee",
        "employee_id",
        string="Costs By Employee",
        readonly=True,
    )


class CostEmployee(models.Model):
    _name = 'cost.employee'

    employee_id = fields.Many2one('hr.employee')
    date = fields.Date(string="Date")
    cost = fields.Float(string='Cost',store=True)
