from odoo import fields, models, api


class Lead(models.Model):
    """
    Extending of Lead model.
    """
    _inherit = 'crm.lead'

    has_notebook = fields.Boolean(default=True)

    def notebook_on(self):
        for rec in self:
            rec.has_notebook = True

    def notebook_off(self):
        for rec in self:
            rec.has_notebook = False

    internal_notes_visible = fields.Boolean(default=True)
    extra_information_visible = fields.Boolean(default=True)

    refers_to = fields.Reference(
        [('res.users', 'Staff User'), ('res.partner', 'Contact')],
        'Staff or Contact',
    )
    resulting_document = fields.Reference(selection=[('sale.order', 'Sale Order'),
                                                     ('purchase.order', 'Purchase Order'),
                                                     ('account.move', 'Invoice')],
                                          string="Resulting Document")

    related_document = fields.Reference(selection='_select_target_model', string="Related Document")

    @api.model
    def _select_target_model(self):
        models_ = self.env['ir.model'].search([])
        return [(model.model, model.name) for model in models_]
