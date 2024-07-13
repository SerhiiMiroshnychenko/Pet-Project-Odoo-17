from odoo import models, fields


class Styler(models.Model):
    _name = 'styling.styler'
    _description = "A class for Odoo stylization"

    name = fields.Char()
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('new', 'New'),
            ('doing', 'Doing'),
            ('done', 'Done'),
            ('canceled', 'Canceled')
        ]
    )