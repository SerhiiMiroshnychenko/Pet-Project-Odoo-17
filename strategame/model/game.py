from odoo import models, fields


class Game(models.Model):
    _name = 'strategic.game'
    _description = 'Strategic Game Instance'

    name = fields.Char(required=True)
    day = fields.Integer()

    player_country = fields.Many2one('home.land', string='Homeland', help='Choose your Country')

    def start_game(self):
        for game in self:
            game.day += 1

    def new_day(self):
        for game in self:
            game.day += 1

