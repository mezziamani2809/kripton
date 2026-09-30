# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, float_round
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _rec_name = 'name'

    date = fields.Date('Start Date', required=False, index=True)
    end_date = fields.Date('End Date', required=False, index=True)
    end_date_timesheet = fields.Date('End Date Timesheets', required=False, index=True)

    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=0.0)
    number_of_hour_by_day = fields.Float('Daily hours', default=8.0)
    service_type = fields.Selection([
        ('mixte', 'Mixte'),
        ('site', 'On Site'),
        ('romote', 'Remote'),
    ], string="Service Type")
    vendor_id = fields.Many2one('res.partner', string="Consultant", required=False)
    tcs_ba_id = fields.Char(string='TCS BA ID', default="")
    tcs = fields.Boolean(string='TCS', compute="_depends_tcs", store=True)
    add_line = fields.Boolean(string='Add To Invoiced', default=True)

    @api.depends('order_id')
    def _depends_tcs(self):
        for rec in self:
            rec.tcs = rec.order_id.tcs

    @api.onchange('vendor_id')
    def _onchange_tcs_ba_id(self):
        for rec in self:
            if rec.vendor_id:
                rec.tcs_ba_id = rec.vendor_id.tcs_ba_id

    def copy_sol(self):
        if self:
            self.copy(default={'order_id': self.order_id.id})

    def _prepare_invoice_line(self, **optional_values):
        invoice_line = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        if not self.tcs:
            invoice_line['service_type'] = self.service_type
            invoice_line['start_date'] = self.end_date_timesheet
        else:
            invoice_line['tcs_ba_id'] = self.tcs_ba_id
            invoice_line['tcs'] = self.tcs
            invoice_line['service_type'] = self.service_type
            invoice_line['start_date'] = self.end_date_timesheet
            invoice_line['end_date'] = self.vendor_id.id

        return invoice_line

    def _get_delivered_quantity_by_analytic(self, additional_domain):
        """ Compute and write the delivered quantity of current SO lines, based on their related
            analytic lines.
            :param additional_domain: domain to restrict AAL to include in computation (required since timesheet is an AAL with a project ...)
        """
        result = {}

        # avoid recomputation if no SO lines concerned
        if not self:
            return result

        # group analytic lines by product uom and so line
        domain = expression.AND([[('so_line', 'in', self.ids)], additional_domain])
        data = self.env['account.analytic.line'].read_group(
            domain,
            ['so_line', 'unit_amount', 'product_uom_id'], ['product_uom_id', 'so_line'], lazy=False
        )

        # convert uom and sum all unit_amount of analytic lines to get the delivered qty of SO lines
        # browse so lines and product uoms here to make them share the same prefetch
        lines = self.browse([item['so_line'][0] for item in data])
        lines_map = {line.id: line for line in lines}
        product_uom_ids = [item['product_uom_id'][0] for item in data if item['product_uom_id']]
        product_uom_map = {uom.id: uom for uom in self.env['uom.uom'].browse(product_uom_ids)}
        for item in data:
            if not item['product_uom_id']:
                continue
            so_line_id = item['so_line'][0]
            so_line = lines_map[so_line_id]
            result.setdefault(so_line_id, 0.0)
            uom = product_uom_map.get(item['product_uom_id'][0])
            if so_line.product_uom.category_id == uom.category_id:
                if so_line.product_uom.id == 3:
                    if so_line.number_of_hour_by_day:
                        qty = item['unit_amount'] / so_line.number_of_hour_by_day
                    else:
                        qty = 0
                else:
                    qty = uom._compute_quantity(item['unit_amount'], so_line.product_uom, rounding_method='HALF-UP')
            else:
                qty = item['unit_amount']
            result[so_line_id] += qty

        return result

    def _purchase_service_prepare_order_values(self, supplierinfo):
        res = super()._purchase_service_prepare_order_values(supplierinfo)
        if not self.order_id.tcs:
            print('innnnn')
            if self.order_id.vendor_id.freelance:
                vendor = self.vendor_id.id
                res.update({
                    'date': self.order_id.date,
                    'client_order_ref': self.order_id.client_order_ref,
                    'tcs': self.order_id.tcs,
                    'end_date': self.order_id.end_date,
                    'contract_type': self.order_id.contract_type,
                    'totol_hours': self.order_id.totol_hours,
                    'number_of_hour_by_day': self.order_id.number_of_hour_by_day,
                    'quantity_by_day': self.order_id.quantity_by_day,
                    'partner_id': vendor,

                })
        else:
            res.update({
                    'date': self.order_id.date,
                    'client_order_ref': self.order_id.client_order_ref,
                    'tcs': self.order_id.tcs,
                    'end_date': self.order_id.end_date,
                    'contract_type': self.order_id.contract_type,
                    'totol_hours': self.order_id.totol_hours,
                    'number_of_hour_by_day': self.order_id.number_of_hour_by_day,
                    'quantity_by_day': self.order_id.quantity_by_day,
                    'multi_vendor_id': [(6, 0, self.order_id.multi_vendor_id.ids)],

                })

        return res

    def _purchase_service_prepare_line_values(self, purchase_order, quantity=False):
        res = super()._purchase_service_prepare_line_values(purchase_order, quantity=False)
        res.update({
            'number_of_hour_by_day': self.order_id.number_of_hour_by_day,
            'date': self.date,
            'end_date': self.end_date,
            'vendor_id': self.vendor_id.id,
            'service_type': self.service_type,
            'tcs_ba_id': self.tcs_ba_id,
        })
        return res

    def _timesheet_create_task_prepare_values(self, project):
        res = super(SaleOrderLine, self)._timesheet_create_task_prepare_values(project)
        project.multi_vendor_id = [(6, 0, self.order_id.multi_vendor_id.ids)]

        if not self.tcs:
            if self.service_type == "site":
                title = "On Site"
            elif self.service_type == "romote":
                title = "Remote"
            res.update({
                'name': title if project.sale_line_id else '%s: %s' % (self.order_id.name or '', title),
            })
            return res
        else:
            self.ensure_one()
            planned_hours = self._convert_qty_company_hours(self.company_id)
            sale_line_name_parts = self.name.split('\n')
            title = sale_line_name_parts[0] or self.product_id.name
            if self.service_type == "site":
                if self.vendor_id.name:
                    title = "On Site" + " : " + sale_line_name_parts[0]  + " / " + self.vendor_id.name or "On Site" + " : " + self.product_id.name + " / " + self.vendor_id.name
                else:
                    title = "On Site" + ":" + sale_line_name_parts[0] or "On Site" + ": " + self.product_id.name + " / " + self.vendor_id.name

            elif self.service_type == "romote":
                if self.vendor_id.name:
                    title = "Remote" + ":" + sale_line_name_parts[0] + " / " + self.vendor_id.name or "Remote" + " :" + self.product_id.name + " / " + self.vendor_id.name
                else:
                    title = "Remote" + ":" + sale_line_name_parts[0] or "Timesheet Remote" + " :" + self.product_id.name + " / " + self.vendor_id.name

            else:
                title = sale_line_name_parts[
                            0] + " / " + self.vendor_id.name or self.product_id.name + " / " + self.vendor_id.name

            description = '<br/>'.join(sale_line_name_parts[1:])
            return {
                'name': title if project.sale_line_id else '%s: %s' % (self.order_id.name or '', title),
                'planned_hours': planned_hours,
                'partner_id': self.order_id.partner_id.id,
                'email_from': self.order_id.partner_id.email,
                'description': description,
                'project_id': project.id,
                'sale_line_id': self.id,
                'sale_order_id': self.order_id.id,
                'company_id': project.company_id.id,
                'user_ids': False,  # force non assigned task, as created as sudo()
            }

    def _timesheet_create_project_prepare_values(self):
        """Generate project values"""
        account = self.order_id.analytic_account_id
        if not account:
            self.order_id._create_analytic_account(prefix=self.product_id.default_code or None)
            account = self.order_id.analytic_account_id

        # create the project or duplicate one
        return {
            'name': '%s - %s' % (self.order_id.client_order_ref,
                                 self.order_id.name) if self.order_id.client_order_ref else self.order_id.name,
            'analytic_account_id': account.id,
            'partner_id': self.order_id.partner_id.id,
            'sale_line_id': self.id,
            'active': True,
            'company_id': self.company_id.id,
            'multi_vendor_id': [(6, 0, self.order_id.multi_vendor_id.ids)],

        }
    def _purchase_service_prepare_order_values_(self, supplierinfo):
        """ Returns the values to create the purchase order from the current SO line.
            :param supplierinfo: record of product.supplierinfo
            :rtype: dict
        """
        self.ensure_one()
        partner_supplier = supplierinfo
        if partner_supplier.parent_id:
            partner_supplier = supplierinfo.parent_id

        return {
            'partner_id': partner_supplier.id,
            'partner_ref': partner_supplier.ref,
            'company_id': self.company_id.id,
            'currency_id': partner_supplier.property_purchase_currency_id.id or self.env.company.currency_id.id,
            'dest_address_id': False,  # False since only supported in stock
            'origin': self.order_id.name,
            'payment_term_id': partner_supplier.property_supplier_payment_term_id.id,
            'client_order_ref': self.order_id.client_order_ref,
            'date': self.order_id.date,
            'end_date': self.order_id.end_date,
            'payment_term_id': self.order_id.payment_term_id.id,

        }

    def _purchase_service_generation(self):
        sale_line_purchase_map = {}
        for line in self:
            if line.vendor_id.related_user_id:
                line.product_id.service_to_purchase = False
            else:
                line.product_id.service_to_purchase = True
            # Do not regenerate PO line if the SO line has already created one in the past (SO cancel/reconfirmation case)
            if line.product_id.service_to_purchase and not line.purchase_line_count:
                result = line._purchase_service_create()
                sale_line_purchase_map.update(result)
        return sale_line_purchase_map

    def _purchase_service_create(self, quantity=False):
        """ On Sales Order confirmation, some lines (services ones) can create a purchase order line and maybe a purchase order.
            If a line should create a RFQ, it will check for existing PO. If no one is find, the SO line will create one, then adds
            a new PO line. The created purchase order line will be linked to the SO line.
            :param quantity: the quantity to force on the PO line, expressed in SO line UoM
        """
        if not self.tcs:
            PurchaseOrder = self.env['purchase.order']
            supplier_po_map = {}
            sale_line_purchase_map = {}
            for line in self:
                line = line.with_company(line.company_id)
                # determine vendor of the order (take the first matching company and product)
                suppliers = line.product_id._select_seller(quantity=line.product_uom_qty, uom_id=line.product_uom)
                if not suppliers:
                    raise UserError(
                        _("There is no vendor associated to the product %s. Please define a vendor for this product.") % (
                            line.product_id.display_name,))
                supplierinfo = suppliers[0]
                partner_supplier = supplierinfo.name  # yes, this field is not explicit .... it is a res.partner !

                # determine (or create) PO
                purchase_order = supplier_po_map.get(partner_supplier.id)
                if not purchase_order:
                    purchase_order = PurchaseOrder.search([
                        ('partner_id', '=', partner_supplier.id),
                        ('state', '=', 'draft'),
                        ('company_id', '=', line.company_id.id),
                    ], limit=1)
                if not purchase_order:
                    values = line._purchase_service_prepare_order_values(supplierinfo)
                    purchase_order = PurchaseOrder.with_context(mail_create_nosubscribe=True).create(values)
                else:  # update origin of existing PO
                    so_name = line.order_id.name
                    origins = []
                    if purchase_order.origin:
                        origins = purchase_order.origin.split(', ') + origins
                    if so_name not in origins:
                        origins += [so_name]
                        purchase_order.write({
                            'origin': ', '.join(origins)
                        })
                supplier_po_map[partner_supplier.id] = purchase_order

                # add a PO line to the PO
                values = line._purchase_service_prepare_line_values(purchase_order, quantity=quantity)
                purchase_line = line.env['purchase.order.line'].create(values)

                # link the generated purchase to the SO line
                sale_line_purchase_map.setdefault(line, line.env['purchase.order.line'])
                sale_line_purchase_map[line] |= purchase_line
            return sale_line_purchase_map
        else:
            PurchaseOrder = self.env['purchase.order']
            supplier_po_map = {}
            sale_line_purchase_map = {}
            for line in self:
                line = line.with_company(line.company_id)
                # determine vendor of the order (take the first matching company and product)
                suppliers = line.product_id._select_seller(quantity=line.product_uom_qty, uom_id=line.product_uom)
                supplierinfo_ = line.vendor_id
                partner_supplier = supplierinfo_  # yes, this field is not explicit .... it is a res.partner !

                # determine (or create) PO
                purchase_order = supplier_po_map.get(partner_supplier.id)
                if not purchase_order:
                    purchase_order = PurchaseOrder.search([
                        ('partner_id', '=', partner_supplier.id),
                        ('state', '=', 'draft'),
                        ('company_id', '=', line.company_id.id),
                    ], limit=1)
                if not purchase_order:
                    values = line._purchase_service_prepare_order_values_(supplierinfo_)
                    purchase_order = PurchaseOrder.with_context(mail_create_nosubscribe=True).create(values)
                else:  # update origin of existing PO
                    so_name = line.order_id.name
                    origins = []
                    if purchase_order.origin:
                        origins = purchase_order.origin.split(', ') + origins
                    if so_name not in origins:
                        origins += [so_name]
                        purchase_order.write({
                            'origin': ', '.join(origins)
                        })
                supplier_po_map[partner_supplier.id] = purchase_order

                # add a PO line to the PO
                values = line._purchase_service_prepare_line_values(purchase_order, quantity=quantity)
                purchase_line = line.env['purchase.order.line'].create(values)

                # link the generated purchase to the SO line
                sale_line_purchase_map.setdefault(line, line.env['purchase.order.line'])
                sale_line_purchase_map[line] |= purchase_line
            return sale_line_purchase_map



