from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError


class Game(models.Model):
    _name = 'strategic.game'
    _description = 'Strategic Game Instance'

    name = fields.Char(required=True)
    day = fields.Integer()

    player_country_id = fields.Many2one('home.land', string='Homeland', help='Choose your Country')
    player_country_ids = fields.One2many(
        'home.land',
        inverse_name='game_id',
        compute='_compute_player_country_ids',
        store=True)

    has_homeland = fields.Boolean(compute='_compute_has_homeland', store=True)

    def start_game(self):
        for game in self:
            game.day += 1

    def new_day(self):
        for game in self:
            game.day += 1
            for land in game.player_country_ids:
                land.gold += land.farms * 10

    @api.depends('player_country_id')
    def _compute_player_country_ids(self):
        for game in self:
            if game.player_country_id:
                game.update({'player_country_ids': [Command.set(game.player_country_id.ids)]})
                for land in game.player_country_ids:
                    land.update({
                        'gold': 100,
                        'farms': 1,
                        'army': 50
                    })

    @api.depends('player_country_id', 'player_country_ids')
    def _compute_has_homeland(self):
        for game in self:
            game.update({
                'has_homeland': all([game.player_country_id, game.player_country_ids])
            })

    def buy_farm(self):
        for game in self:
            for land in game.player_country_ids:
                if land.gold >= 50:
                    land.gold -= 50
                    land.farms += 1
                else:
                    raise UserError(_('Not enough gold...'))

    def buy_army(self):
        for game in self:
            for land in game.player_country_ids:
                if land.gold >= 50:
                    land.gold -= 50
                    land.army += 10
                else:
                    raise UserError(_('Not enough gold...'))

    def set_to_start(self):
        for game in self:
            game.update({
                'day': 1
            })
            for land in game.player_country_ids:
                land.update({
                    'gold': 100,
                    'farms': 1,
                    'army': 50
                })