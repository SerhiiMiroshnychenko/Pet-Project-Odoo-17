from matplotlib.dates import DateFormatter

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

    sales_orders_html = fields.Html(string='Sales Orders', compute='_compute_sales_orders_html')

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
        """Compute stock level history plot for form view."""
        for product in self:
            try:
                # Отримання історії
                if product.stock_history_data:
                    history_data = json.loads(product.stock_history_data)
                    history = [{
                        'date': datetime.strptime(item['date'], '%Y-%m-%d').date(),
                        'quantity': item['quantity']
                    } for item in history_data]
                else:
                    history = product.get_stock_history()

                if not history:
                    continue

                # Підготовка даних
                dates = [item['date'] for item in history]
                quantities = [item['quantity'] for item in history]
                dates_formatted = [date.strftime('%d.%m.%y') for date in dates]

                # Створення графіку
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.step(dates, quantities, where='post', color='g', label='Кількість', linewidth=2)

                # Додаємо точки у місцях зламу
                ax.scatter(dates, quantities, color='red', zorder=5, label='Точки зламу')

                # Додаємо підписи біля кожної точки
                for x, y, label in zip(dates, quantities, dates_formatted):
                    ax.annotate(label, xy=(x, y), xytext=(5, 5), textcoords="offset points",
                                fontsize=10, color='blue', ha='center', va='bottom')

                # Форматуємо осі
                ax.set_title("Графік кількості за датами", fontsize=14)
                ax.set_xlabel("Дати", fontsize=12)
                ax.set_ylabel("Кількість", fontsize=12)
                ax.xaxis.set_major_formatter(DateFormatter("%b %Y"))
                ax.set_ylim(min(quantities) - max(quantities) * 0.1, max(quantities) * 1.1)  # Додаємо простір зверху і знизу
                ax.grid(True, linestyle='--', alpha=0.7)

                # Основне форматування осі X
                plt.xticks(rotation=45)
                ax.legend()

                # Збереження графіку у файл
                buffer = io.BytesIO()
                plt.tight_layout()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                image_data = buffer.read()
                buffer.close()
                plt.close(fig)

                # Зберігаємо графік у полі моделі
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

    def _compute_sales_orders_html(self):
        for product in self:
            domain = [
                ('order_line.product_id', '=', product.id),
            ]
            sale_orders = self.env['sale.order'].search(domain, order='date_order desc')

            if not sale_orders:
                product.sales_orders_html = '<p>No sales orders found for this product.</p>'
                continue

            html = ["""
            <h3 class='text-muted'>Sales Order History</h3>
            <ul style='list-style: none;'>
            """]

            for order in sale_orders:
                order_line = order.order_line.filtered(lambda l: l.product_id.id == product.id)
                product_qty = sum(line.product_uom_qty for line in order_line)
                html.append(
                    f"""<li style="
                    display: inline-block;
                    max-width: 100%; /* або конкретна ширина, якщо потрібно */
                    white-space: nowrap; /* або 'normal', якщо потрібен перенос тексту */
                    background-size: 20px;
                    background-repeat: no-repeat;
                    background-position: left center;
                    background-image: url('/product_analysis/static/description/{order.state}.png');
                    padding-left: 25px; /* щоб текст не перекривав зображення */
                    ">
                    [{order.date_order.strftime("%Y-%m-%d")}]
                    <a href="/web#id={order.id}&view_type=form&model=sale.order">{order.name}</a>
                     - {order.partner_id.name}
                    <span class='text-muted'>(<i>quantity</i>: <b>{product_qty}</b>)</span></li><br/>""")

            html.append('</ul>')

            # Додаємо легенду після списку
            html.append("<hr style='margin: 20px 0;'/>")  # Горизонтальна лінія
            html.append("<div style='display: flex; flex-wrap: wrap; gap: 15px;'>")

            states = {
                'draft': 'Quotation',
                'sent': '"Quotation Sent',
                'sale': 'Sales Order',
                'cancel': 'Cancelled'
            }

            for state, label in states.items():
                html.append(f"""
                                <div style='display: flex; align-items: center; margin-right: 15px;'>
                                    <div style='width: 20px; height: 20px; background-image: url("/product_analysis/static/description/{state}.png");
                                         background-size: contain; background-repeat: no-repeat; margin-right: 5px;'></div>
                                    <span>{label}</span>
                                </div>
                            """)

            html.append("</div></div>")

            product.sales_orders_html = '\n'.join(html)
            print(f"{ product.sales_orders_html = }")
