from odoo import models, fields, api


class ContractEndWizard(models.TransientModel):
    _name = 'contract.end.wizard'
    _description = 'Contract End Date'

    sale_order_id = fields.Many2one('sale.order', string="Contrat", required=True)
    end_date = fields.Date(string="Contract End Date", required=True, default=fields.Date.today)

    def action_confirm(self):
        self.ensure_one()
        today = fields.Date.today()

        # Mise à jour de la date sur la commande
        self.sale_order_id.write({'end_date': self.end_date})

        # Logique de changement d'état immédiat
        if self.end_date <= today:
            self.sale_order_id.write({'state': 'done'})