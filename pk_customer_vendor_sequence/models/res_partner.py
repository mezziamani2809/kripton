from odoo import models, fields, api


class InheritResPartner(models.Model):
    _inherit = 'res.partner'

    sequence_number = fields.Char(string='Number', copy=False, readonly=False)

    @api.model
    def create(self, vals):
        if self.env.context.get('default_supplier_rank', 0) > 0:
            vals['sequence_number'] = self.env['ir.sequence'].next_by_code('res.partner.vendor.sequence')
        return super(InheritResPartner, self).create(vals)

    def unlink(self):
        for partner in self:
            if partner.supplier_rank > 0:
                next_number = partner.sequence_number[-3:]
                sequence = self.env['ir.sequence'].search([('code', '=', 'res.partner.vendor.sequence')], limit=1)
                if sequence and next_number:
                    sequence.number_next_actual = next_number
        return super(InheritResPartner, self).unlink()

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sequence_number = fields.Char(string='Number', readonly=False)

    @api.model
    def create(self, vals):
        if vals.get('partner_id'):

            partner = self.env['res.partner'].browse(vals['partner_id'])

            if partner.sequence_number:

                sequence_partner = partner.sequence_number
                # Get the last purchase order sequence number for this partner
                last_purchase_order = self.search([('partner_id', '=', partner.id)], order='id desc', limit=1)

                if last_purchase_order:

                    last_sequence = last_purchase_order.sequence_number.split('_')[-1][-2:]

                    sequence_number = f"{sequence_partner}-{str(int(last_sequence) + 1).zfill(2)}"


                else:
                    sequence_number = f"{sequence_partner}-01"

                vals['sequence_number'] = sequence_number
        return super(PurchaseOrder, self).create(vals)

