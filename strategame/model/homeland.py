from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HomeLand(models.Model):
    _name = 'home.land'
    _description = 'Country in the Game'

    name = fields.Char(string='Country name:', required=True)
    badge = fields.Image()
    gold = fields.Monetary(default=100.0)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env['res.currency'].search([('name', '=', 'USD')]))
    game_id = fields.Many2one('strategic.game')
    farms = fields.Integer(string='Farms', default=1)
    army = fields.Integer(string='Army', default=50)

    def action_open_homeland(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Homeland',
            'res_model': 'home.land',
            'view_mode': 'form',
            'res_id': self.id,  # Додано ID запису
            'target': 'new'
        }

    # def write(self, vals):
    #     result = super().write(vals)
    #     army = vals.get('army')
    #     if army and army <= 0:
    #         title = _("GAME OVER")
    #         message = _("You Lost!")
    #         self.game_id.set_to_start()
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': title,
    #                 'message': message,
    #                 'sticky': False,
    #             }
    #         }
    #     return result
