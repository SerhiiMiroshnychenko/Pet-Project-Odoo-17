import base64

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

    homeland_html = fields.Html(compute='_compute_homeland_html')

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

    def _compute_homeland_html(self):
        for land in self:
            print(f"{land.badge = }")
            image_html = ''
            if land.badge:
                # Якщо badge містить бінарні дані, перетворимо їх на base64
                badge_base64 = base64.b64encode(land.badge).decode('utf-8')
                print(f"{badge_base64 = }")
                image_html = f'<img src="data:image/png;base64, {badge_base64}" alt="My Image">'
                print(f"{image_html = }")

            land_html = f'''
<h2>{land.name}</h2>
{image_html}
'''
            land.update({'homeland_html': land_html})

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
