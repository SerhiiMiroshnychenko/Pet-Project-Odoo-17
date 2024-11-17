from odoo import models, fields


class StockHistoryPlotWizard(models.TransientModel):
    _name = 'stock.history.plot.wizard'
    _description = 'Stock History Plot Wizard'

    plot_image = fields.Binary(string='Plot', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id:
            product = self.env['product.product'].browse(active_id)
            plot_image = product._generate_stock_history_plot()
            res.update({
                'product_id': active_id,
                'plot_image': plot_image,
            })
        return res
