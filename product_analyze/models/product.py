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
        compute='_compute_stock_history_data',
        store=True,
    )
    stock_history_plot = fields.Binary(
        string='Stock History Plot',
        attachment=False,  # Changed to False to avoid image processing
        help='Stock quantity history visualization'
    )
    last_stock_update = fields.Datetime(
        string='Last Stock Update',
        help='Technical field to track stock updates'
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
                product._generate_stock_history_plot()
            except Exception as e:
                _logger.error(f"Error computing stock history data: {str(e)}")
                product.stock_history_data = "[]"
                product.stock_history_plot = False

    def _generate_stock_history_plot(self):
        """Generate and save stock history plot"""
        self.ensure_one()
        
        try:
            if self.stock_history_data:
                # Parse JSON and convert dates back to datetime objects
                history_data = json.loads(self.stock_history_data)
                history = [{
                    'date': self._deserialize_datetime(record['date']),
                    'quantity': record['quantity']
                } for record in history_data]
            else:
                history = self.get_stock_history()
            
            if not history:
                return

            # Prepare data for plotting
            dates = [record['date'] for record in history]
            quantities = [record['quantity'] for record in history]
            
            # Calculate quantity changes for bar chart
            qty_changes = []
            for i in range(1, len(quantities)):
                qty_changes.append(quantities[i] - quantities[i-1])
            
            # Create figure with two subplots sharing x-axis
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # Add title
            fig.suptitle(f'Stock History for {self.name}\n({self.default_code or "No Reference"})', 
                        fontsize=14, y=1.0)
            
            # Plot step chart on the first subplot
            ax1.step(dates, quantities, where='post', color='blue', linewidth=2, 
                    label='Stock Level')
            ax1.scatter(dates, quantities, color='blue', s=50, zorder=5)
            ax1.set_ylabel(f'Stock Level ({self.uom_id.name})', fontsize=12)
            ax1.grid(True, linestyle='--', alpha=0.7)
            ax1.legend()
            
            # Format dates on x-axis
            for ax in [ax1, ax2]:
                ax.tick_params(axis='x', rotation=45)
                # Встановлюємо фіксовані позиції для міток
                ax.set_xticks(dates)
                # Форматуємо дати для міток
                date_labels = [d.strftime('%Y-%m-%d') for d in dates]
                ax.set_xticklabels(date_labels, ha='right')
            
            # Plot bar chart on the second subplot
            bars = ax2.bar(dates[1:], qty_changes, color=['g' if x >= 0 else 'r' for x in qty_changes],
                          alpha=0.6)
            ax2.set_ylabel('Stock Changes', fontsize=12)
            ax2.grid(True, linestyle='--', alpha=0.7)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                value = height if height >= 0 else -height
                y_pos = height + 0.5 if height >= 0 else height - 0.5
                ax2.text(bar.get_x() + bar.get_width()/2., y_pos,
                        f'{value:+.1f}',
                        ha='center', va='bottom' if height >= 0 else 'top',
                        fontsize=10)
            
            # Adjust layout
            plt.subplots_adjust(top=0.9, bottom=0.15, hspace=0.4)
            
            # Save plot to memory
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none', pad_inches=0.2)
            plt.close(fig)
            
            # Convert to base64
            buf.seek(0)
            self.stock_history_plot = base64.b64encode(buf.getvalue())
            self.last_stock_update = fields.Datetime.now()
            
        except Exception as e:
            _logger.error(f"Error generating stock history plot: {str(e)}")
            self.stock_history_plot = False

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

    def show_stock_history(self):
        """Generate and show stock history plot in popup window"""
        history = self.get_stock_history()
        
        # Prepare data for plotting
        dates = [record['date'] for record in history]
        quantities = [record['quantity'] for record in history]
        
        # Calculate quantity changes for bar chart
        qty_changes = []
        for i in range(1, len(quantities)):
            qty_changes.append(quantities[i] - quantities[i-1])
        
        # Create figure with two subplots sharing x-axis
        fig = plt.figure(figsize=(12, 10))
        
        # Create grid spec to control subplot sizes and spacing
        gs = fig.add_gridspec(2, 1, height_ratios=[2, 1], hspace=0.3)
        
        # Add title with padding
        fig.suptitle(f'Stock History for {self.name}\n({self.default_code or "No Reference"})', 
                    fontsize=14, y=0.95)
        
        # Create subplots
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])
        
        # Plot step chart on the first subplot
        ax1.step(dates, quantities, where='post', color='blue', linewidth=2, 
                label='Stock Level')
        ax1.scatter(dates, quantities, color='blue', s=50, zorder=5)
        ax1.set_ylabel(f'Stock Level ({self.uom_id.name})', fontsize=12, labelpad=10)
        ax1.grid(True, linestyle='--', alpha=0.7)
        ax1.legend()
        
        # Format dates on x-axis
        for ax in [ax1, ax2]:
            ax.tick_params(axis='x', rotation=45)
            labels = ax.get_xticklabels()
            ax.set_xticklabels(labels, ha='right')
        
        # Plot bar chart on the second subplot
        bars = ax2.bar(dates[1:], qty_changes, color=['g' if x >= 0 else 'r' for x in qty_changes],
                      alpha=0.6)
        ax2.set_ylabel('Stock Changes', fontsize=12, labelpad=10)
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            value = height if height >= 0 else -height
            y_pos = height + 0.5 if height >= 0 else height - 0.5
            ax2.text(bar.get_x() + bar.get_width()/2., y_pos,
                    f'{value:+.1f}',
                    ha='center', va='bottom' if height >= 0 else 'top',
                    fontsize=10)
        
        # Adjust layout with specific padding
        fig.set_tight_layout(True)
        plt.subplots_adjust(top=0.9, bottom=0.15)
        
        # Save plot to memory with high quality
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        # Encode image to base64
        buf.seek(0)
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        
        # Return action to open wizard
        return {
            'name': 'Stock History Plot',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.history.plot.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_plot_image': image_base64,
                'default_product_id': self.id,
            },
        }