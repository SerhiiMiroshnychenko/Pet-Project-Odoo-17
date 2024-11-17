from odoo import models, fields


class StockHistoryPlotWizard(models.TransientModel):
    _name = 'stock.history.plot.wizard'
    _description = 'Stock History Plot Wizard'

    plot_image = fields.Binary(string='Plot', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
