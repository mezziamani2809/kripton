from odoo import models, api, exceptions
import logging


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(HrLeave, self).create(vals_list)
        for leave in res:
            if leave.date_to and leave.date_from:
                mail_template = self.env.ref('time_off_reminder.request_for_time_off_mail_template')
                if mail_template:
                    mail_template.send_mail(leave.id, force_send=True)
        return res

    def action_approve(self, *args, **kwargs):
        # Appel de la fonction d'approbation d'origine
        res = super(HrLeave, self).action_approve(*args, **kwargs)

        # Envoi de l'email après l'approbation
        template_id = self.env.ref('time_off_reminder.approval_time_off_mail_template').id
        self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)

        return res


