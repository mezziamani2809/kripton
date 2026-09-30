import base64

from odoo import api, fields, models


class AttachmentDocument(models.TransientModel):
    _name = 'attachment.document.wizard'
    _description = 'Attachement Documents'

    d_attachment_ids = fields.Many2many('ir.attachment', string="Attachment")
    document_ref = fields.Many2one('document.document', copy=False)
    sequence_parent_full_name = fields.Char("Sequence", readonly=True)

    def add_attachment_all(self):
        sequence_counter = self.document_ref.document_count  # Démarre à la valeur actuelle du compteur
        for rec in self.d_attachment_ids:
            sequence_counter += 1  # Incrémente le compteur pour chaque pièce jointe
            vals = {
                'name': rec.name,
                'doc_attachment_id': rec.datas,
                'document_ref': self.document_ref.id,
                'sequence_parent_full_name': str(sequence_counter),
            }
            self.env['sapres.document.document'].create(vals)
class CrmLeadAttachment(models.Model):
    _inherit = 'ir.attachment'

    d_attach_ref_ = fields.Many2many('attachment.document.wizard', 'd_attachment_ids', 'attach_id3', 'doc_id',
                                      string="Attachment", invisible=1)
