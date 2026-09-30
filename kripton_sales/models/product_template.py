# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from datetime import timedelta

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    vendor_id = fields.Many2one('res.partner', string='Consultant', force_save="1")


    @api.model
    def default_get(self, vals):
        res = super(ProductTemplate, self).default_get(vals)
        res['detailed_type'] = 'service'
        res['service_policy'] = 'delivered_timesheet'
        res['service_tracking'] = 'task_in_project'
        res['list_price'] = 0.0
        return res
