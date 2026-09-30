import base64

from odoo import api, fields, models


class AttachmentDocument(models.TransientModel):
    _name = 'attachment.document.wizard'
    _description = 'Attachement Documents'

    d_attachment_ids = fields.Many2many('ir.attachment', string="Attachment")
    document_ref = fields.Many2one('document.document', string='Document Reference')


    def add_attachment_all(self):
        move_ids = self.env.context.get('active_ids', [])
        moves = self.env['account.move'].browse(move_ids)

        for move in moves:
            if move.doc_attachment_id:
                # Convertir les données de la pièce jointe en base64
                attachment_data = move.doc_attachment_id

                # Créer l'enregistrement dans sapres.document.document
                vals = {
                    'name': move.doc_attachment_name,
                    'doc_attachment_id': attachment_data,
                    'document_ref': self.document_ref.id,
                }
                self.env['sapres.document.document'].create(vals)


class CrmLeadAttachment(models.Model):
    _inherit = 'ir.attachment'

    d_attach_ref_ = fields.Many2many('attachment.document.wizard', 'd_attachment_ids', 'attach_id3', 'doc_id',
                                      string="Attachment", invisible=1)
