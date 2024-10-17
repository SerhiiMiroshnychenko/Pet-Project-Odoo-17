from random import randint
from odoo import models, fields, api


class Enemy(models.Model):
    _name = 'enemy'
    _description = 'Enemy in the Game'

    name = fields.Char(string='Enemy name:', required=True)
    badge = fields.Image()
    army = fields.Integer(string='Army', default=0)
    aggression = fields.Integer(string=' ', default=0)
    game_id = fields.Many2one('strategic.game')

    enemy_html = fields.Html(compute='_compute_enemy_html')

    def new_day(self):
        for enemy in self:
            enemy.army += randint(0, 10)
            enemy.aggression += randint(0, 10) - randint(0, 5)
            enemy.aggression = enemy.aggression if enemy.aggression >= 0 else 0

    def action_open_enemy(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Enemy',
            'res_model': 'enemy',
            'view_mode': 'form',
            'res_id': self.id,  # Додано ID запису
            'target': 'new'
        }

    def _compute_enemy_html(self):
        for enemy in self:
            enemy_html = f'''
        <h2>{enemy.name}</h2>
        '''
            enemy.update({'enemy_html': enemy_html})

    # def write(self, vals):
    #     result = super().write(vals)
    #     if 'aggression' in vals:
    #         for enemy in self:
    #             if enemy.aggression >= 100:
    #                 lands = enemy.game_id.player_country_ids
    #                 for land in lands:
    #                     land_army = land.army
    #                     land.army -= enemy.army
    #                     enemy.army -= land_army
    #                 enemy.aggression = 0
    #     return result
