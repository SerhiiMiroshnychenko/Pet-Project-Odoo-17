from odoo import models, fields, api
from datetime import datetime, timedelta
import logging
import matplotlib
matplotlib.use('Agg')  # Set backend before importing pyplot
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
import base64
import io
import json
from datetime import datetime
from PIL import Image

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    stock_history_data = fields.Text(
        string='Stock History Data',
        readonly=True
    )
    stock_history_plot = fields.Binary(
        string='Stock Level History Plot',
        compute='_compute_stock_level_plot',
        # store=True
    )

    last_stock_update = fields.Datetime(
        string='Last Stock Update',
        readonly=True
    )

    def _serialize_datetime(self, dt):
        """Convert datetime to string for JSON serialization"""
        return dt.isoformat() if dt else None

    def _deserialize_datetime(self, dt_str):
        """Convert string to datetime from JSON deserialization"""
        return datetime.fromisoformat(dt_str) if dt_str else None

    @api.depends('stock_move_ids', 'stock_move_ids.state', 'qty_available')
    def _compute_stock_history_data(self):
        for product in self:
            try:
                history = product.get_stock_history()
                # Convert datetime objects to strings for JSON serialization
                serializable_history = []
                for record in history:
                    serializable_history.append({
                        'date': self._serialize_datetime(record['date']),
                        'quantity': record['quantity']
                    })
                product.stock_history_data = json.dumps(serializable_history)
            except Exception as e:
                _logger.error(f"Error computing stock history data: {str(e)}")
                product.stock_history_data = "[]"

    def _compute_stock_level_plot(self):
        """Compute stock level history plot for form view"""
        for product in self:
            try:
                # Отримання історії
                if product.stock_history_data:
                    history_data = json.loads(product.stock_history_data)
                    history = [{
                        'date': datetime.strptime(item['date'], '%Y-%m-%d'),
                        'quantity': item['quantity']
                    } for item in history_data]
                else:
                    history = product.get_stock_history()

                if not history:
                    continue

                # Підготовка даних
                dates = [item['date'] for item in history]
                quantities = [item['quantity'] for item in history]
                dates_formatted = [date.strftime('%Y-%m-%d') for date in dates]

                # Створення графіку
                plt.figure(figsize=(10, 6))
                plt.step(dates_formatted, quantities, where='post', marker='o', color='b', label='Кількість товару')
                plt.xlabel('Дата визначення', fontsize=12)
                plt.ylabel('Кількість товару', fontsize=12)
                plt.title('Визначення кількості товару на складі', fontsize=14)
                plt.grid(visible=True, linestyle='--', alpha=0.5)
                plt.legend(fontsize=12)
                plt.xticks(rotation=45, fontsize=10)
                plt.tight_layout()

                # Збереження графіку у файл
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                image_data = buffer.read()
                buffer.close()
                product.stock_history_plot = base64.b64encode(image_data)
            except Exception as e:
                _logger.error(f"Error generating new plot: {str(e)}")
                product.stock_history_plot = False

    def update_plot(self):
        for product in self:
            product._compute_stock_level_plot()

    def get_stock_history(self):
        """
        Get stock quantity history for the last year
        Returns: list of dictionaries containing date and quantity
        """
        self.ensure_one()
        today = fields.Date.today()
        year_ago = today - timedelta(days=365)

        # Get all stock moves for this product in the last year
        stock_moves = self.env['stock.move'].search([
            ('product_id', '=', self.id),
            ('date', '>=', year_ago),
            ('date', '<=', today),
            ('state', '=', 'done'),
        ], order='date asc')

        # Initialize result with starting quantity
        initial_qty = self.with_context(to_date=year_ago).qty_available
        result = [{
            'date': year_ago,
            'quantity': initial_qty
        }]

        current_qty = initial_qty
        for move in stock_moves:
            if move.location_dest_id.usage == 'internal' and move.location_id.usage != 'internal':
                # Incoming to stock
                current_qty += move.product_uom_qty
            elif move.location_id.usage == 'internal' and move.location_dest_id.usage != 'internal':
                # Outgoing from stock
                current_qty -= move.product_uom_qty

            result.append({
                'date': move.date.date(),
                'quantity': current_qty
            })

        # Add current quantity if last move was not today
        if not result or result[-1]['date'] != today:
            result.append({
                'date': today,
                'quantity': self.qty_available
            })

        return result