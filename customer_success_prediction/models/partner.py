import base64
import logging
import matplotlib
import numpy as np
matplotlib.use('Agg')  # Install backend before importing pyplot
from io import BytesIO
from datetime import datetime
import matplotlib.pyplot as plt
from collections import defaultdict

from odoo import models, fields, api, Command

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit='res.partner'

    # Analytics fields
    successful_order = fields.Float(compute='_compute_orders_statistics', store=True)
    orders_chart = fields.Binary(compute='_compute_charts', store=True)
    all_order_ids = fields.Many2many('sale.order', compute='_compute_all_orders')


    def update_analytics(self):
        self._compute_orders_statistics()
        self._compute_charts()

    def _compute_all_orders(self):
        for partner in self:
            if domain := partner.action_view_sale_order().get('domain'):
                orders = self.env['sale.order'].search(domain)
            else:
                orders = partner.sale_order_ids
            partner.update({
                'all_order_ids': [Command.set(orders.ids)]
            })


    @api.depends('sale_order_ids', 'sale_order_ids.state')
    def _compute_orders_statistics(self):
        for partner in self:
            orders = partner.all_order_ids
            completed_orders = orders.filtered(lambda o: o.state == 'sale')
            partner.successful_order = (len(completed_orders) / len(orders)) if orders else 0

    @staticmethod
    def _create_combined_chart(months, orders_data, successful_data, rate_data):
        """Helper function for creating combined chart with three metrics"""
        try:
            # Create figure with primary axis
            fig, ax1 = plt.subplots(figsize=(15, 8))

            # Create second axis that shares x with ax1
            ax2 = ax1.twinx()

            # Set the positions for the bars
            x = np.arange(len(months))
            width = 0.25  # width of the bars

            # Plot bars
            bars1 = ax1.bar(x - width, orders_data, width, label='Total Orders', color='skyblue')
            bars2 = ax1.bar(x, successful_data, width, label='Successful Orders', color='green')
            bars3 = ax2.bar(x + width, rate_data, width, label='Success Rate (%)', color='orange')

            # Set labels and title
            ax1.set_xlabel('Month')
            ax1.set_ylabel('Number of Orders')
            ax2.set_ylabel('Success Rate (%)')

            plt.title('Customer Orders Analysis')

            # Set x-axis labels
            months_display = [datetime.strptime(m, '%m/%Y').strftime('%B %Y') for m in months]
            plt.xticks(x, months_display, rotation=45, ha='right')

            # Add grid
            ax1.grid(True, axis='y', linestyle='--', alpha=0.7)

            # Add values above bars
            def autolabel(bars, ax):
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                            f'{int(height)}',
                            ha='center', va='bottom')

            autolabel(bars1, ax1)
            autolabel(bars2, ax1)
            autolabel(bars3, ax2)

            # Add legends
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

            # Adjust layout
            plt.tight_layout()

            # Save to buffer
            buffer = BytesIO()
            fig.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            _logger.warning(f"Error creating chart: {str(e)}")
            return False
        finally:
            plt.close('all')

    def _compute_charts(self):
        for partner in self:
            try:
                # Get sorted orders
                orders = partner.all_order_ids.sorted('date_order')
                if not orders:
                    partner.orders_chart = False
                    continue

                # Group orders by month
                monthly_data = defaultdict(lambda: {'orders': 0, 'successful': 0})

                for order in orders:
                    month_key = order.date_order.strftime('%m/%Y')
                    monthly_data[month_key]['orders'] += 1
                    if order.state == 'sale':
                        monthly_data[month_key]['successful'] += 1

                # Sort months
                months = sorted(monthly_data.keys(),
                                key=lambda x: datetime.strptime(x, '%m/%Y'))

                # Prepare data arrays
                orders_data = [monthly_data[m]['orders'] for m in months]
                successful_data = [monthly_data[m]['successful'] for m in months]
                success_rate_data = [(monthly_data[m]['successful'] / monthly_data[m]['orders'] * 100)
                                     if monthly_data[m]['orders'] else 0 for m in months]

                # Create combined chart
                partner.orders_chart = partner._create_combined_chart(
                    months, orders_data, successful_data, success_rate_data)

            except Exception as e:
                _logger.warning(f"Error computing chart: {str(e)}")
                partner.orders_chart = False
            finally:
                plt.close('all')
