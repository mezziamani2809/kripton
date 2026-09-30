import base64
from itertools import combinations

from odoo import api, fields, models


class Attachment(models.TransientModel):
    _name = 'attachment.doc.wizard'
    _description = 'Attachement Documents'

    attachment_ids = fields.Many2many('ir.attachment', string="Attachment")
    document_ref = fields.Many2one('document.document', string='Document Reference')

    def add_doc_attachment_all(self):
        move_ids = self.env.context.get('active_ids', [])
        moves = self.env['account.move'].browse(move_ids)

        if moves:
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


class PaidAccountMove(models.TransientModel):
    _name = 'paid.account.move'
    _description = 'Paid Account Move'

    amount = fields.Float(string="Amount")  # User entered amount
    results = fields.Text(string="Results", readonly=True)  # To display results

    def add_paid_account(self):
        move_ids = self.env.context.get('active_ids', [])
        moves = self.env['account.move'].browse(move_ids)

        # Extract invoice numbers and amounts
        invoices = [(move.invoice_number, move.amount_total) for move in moves if move.amount_total]
        invoice_names, invoice_amounts = zip(*invoices) if invoices else ([], [])

        # Find combinations that total the specified amount
        resultats = []
        target_amount = self.amount

        # Early exit for large number of invoices
        max_invoices_to_process = 15  # Adjust based on performance needs
        invoice_count = min(len(invoice_names), max_invoices_to_process)

        # Variable to track the closest match
        closest_match = None
        closest_diff = float('inf')

        for r in range(1, invoice_count + 1):
            for combo in combinations(range(invoice_count), r):
                current_sum = sum(invoice_amounts[i] for i in combo)
                diff = target_amount - current_sum

                # Check if the sum matches the target amount
                if diff == 0:
                    resultats.append(" + ".join(invoice_names[i] for i in combo) + " (reste: 0)")
                    break  # Early exit if we found an exact match
                elif diff > 0 and diff < closest_diff:  # If the sum is less than the target but closer
                    closest_match = " + ".join(invoice_names[i] for i in combo)
                    closest_diff = diff

            if resultats:  # If exact matches were found, no need to continue
                break

        # Prepare results for display
        if resultats:
            self.results = "\n".join(resultats)
        elif closest_match:
            self.results = f"{closest_match} (Rest: {closest_diff:.2f})"
        else:
            self.results = "Aucune combinaison trouvée."

        # Log results (useful for debugging)
        print('Résultats:', self.results)

        # Return an action to display results in a new window
        return {
            'type': 'ir.actions.act_window',
            'name': 'Results',
            'res_model': 'paid.account.move',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
