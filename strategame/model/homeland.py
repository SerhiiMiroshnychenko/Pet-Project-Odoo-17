from odoo import models, fields


class HomeLand(models.Model):
    _name = 'home.land'
    _description = 'Country in the Game'

    name = fields.Char(string='Homeland', required=True)
    gold = fields.Monetary()
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env['res.currency'].search([('name', '=', 'USD')]))
    