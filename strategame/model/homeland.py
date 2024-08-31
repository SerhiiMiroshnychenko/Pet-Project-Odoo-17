from odoo import models, fields


class HomeLand(models.Model):
    _name = 'home.land'
    _description = 'Country in the Game'

    name = fields.Char(string='Homeland', required=True)
    gold = fields.Monetary(default=100.0)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env['res.currency'].search([('name', '=', 'USD')]))
    game_id = fields.Many2one('strategic.game')
    farms = fields.Integer(string='Farms', default=1)
    army = fields.Integer(string='Army', default=50)


