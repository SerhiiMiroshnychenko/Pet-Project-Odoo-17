import base64
import csv
import logging
import matplotlib
matplotlib.use('Agg')
from io import BytesIO, StringIO
from datetime import datetime
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CustomerDataCollection(models.Model):
    _name = 'customer.data.collection'
    _description = 'Customer Data Collection'

    name = fields.Char(required=True)
    date_from = fields.Date(readonly=True)
    date_to = fields.Date(readonly=True)
    date_range_display = fields.Char(string='Analysis Period', compute='_compute_date_range_display', store=True)

    # Data file fields
    data_file = fields.Binary(string='Data File (CSV)', attachment=True)
    data_filename = fields.Char(string='Data Filename')

    # Statistics fields (computed from CSV data)
    total_partners = fields.Integer(string='Total number of clients', compute='_compute_statistics', store=True)
    total_orders = fields.Integer(string='Total number of orders', compute='_compute_statistics', store=True)
    total_success_rate = fields.Float(string='Total % of successful orders', compute='_compute_statistics', store=True)

    # Distribution fields
    orders_by_state = fields.Text(string='Distribution of orders by status', compute='_compute_statistics', store=True)
    orders_by_state_chart = fields.Binary(string='Orders by Status Distribution', compute='_compute_distribution_charts', store=True)
    partners_by_success_rate = fields.Text(string='Distribution of customers by success_rate', compute='_compute_statistics', store=True)
    partners_by_rate_chart = fields.Binary(string='Partners by Success Rate Distribution', compute='_compute_distribution_charts', store=True)
    partners_by_rate_plot = fields.Binary(string='Partners Success Rate Plot', compute='_compute_distribution_charts', store=True)
    monthly_analysis_chart = fields.Binary(string='Monthly Orders Analysis', compute='_compute_monthly_charts')

    # Amount-Success Rate Analysis
    amount_success_chart = fields.Binary(
        string='Success Rate by Order Amount',
        attachment=True
    )
    partner_age_success_chart = fields.Binary(
        string='Success Rate by Partner Age',
        attachment=True
    )
    salesperson_success_chart = fields.Binary(
        string='Success Rate by Salesperson',
        compute='_compute_distribution_charts',
        store=True
    )
    weekday_success_chart = fields.Binary(
        string='Success Rate by Weekday',
        compute='_compute_weekday_charts',
        store=True
    )
    month_success_chart = fields.Binary(
        string='Success Rate by Month',
        compute='_compute_month_charts',
        store=True
    )
    partner_orders_success_chart = fields.Binary(
        string='Success Rate by Partner Orders Count',
        compute='_compute_partner_orders_charts',
        store=True
    )
    total_amount_success_chart = fields.Binary(
        string='Success Rate by Total Orders Amount',
        compute='_compute_amount_success_charts',
        store=True
    )
    success_amount_success_chart = fields.Binary(
        string='Success Rate by Successful Orders Amount',
        compute='_compute_amount_success_charts',
        store=True
    )
    avg_amount_success_chart = fields.Binary(
        string='Success Rate by Average Order Amount',
        compute='_compute_amount_success_charts',
        store=True
    )
    avg_success_amount_success_chart = fields.Binary(
        string='Success Rate by Average Successful Order Amount',
        compute='_compute_amount_success_charts',
        store=True
    )

    def action_collect_data(self):
        """Collect data from database and save to CSV"""
        self.ensure_one()

        try:
            # Get sale orders
            orders = self.env['sale.order'].search([])
            print(f"\nFound {len(orders)} orders")
            partners = self.env['res.partner'].search([])
            print(f"\nFound {len(partners)} partners")

            # Prepare CSV data
            csv_data = self._prepare_csv_data(orders)
            print(f"Prepared {len(csv_data)} rows of data")

            # Convert to CSV
            output = StringIO()
            writer = csv.writer(output)
            writer.writerows(csv_data)

            # Save to binary field
            self.data_file = base64.b64encode(output.getvalue().encode('utf-8'))
            self.data_filename = f'customer_data_{fields.Date.today()}.csv'

            return True

        except Exception as e:
            raise UserError(_('Error collecting data: %s') % str(e))

    def _prepare_csv_data(self, orders):
        """Prepare raw data for CSV file"""
        print("\nPreparing CSV data...")

        # Find min and max dates
        min_date = False
        max_date = False
        for order in orders:
            order_date = order.date_order.date()
            if not min_date or order_date < min_date:
                min_date = order_date
            if not max_date or order_date > max_date:
                max_date = order_date

        # Update date range
        self.date_from = min_date
        self.date_to = max_date

        # Header
        csv_data = [['order_id', 'partner_id', 'date_order', 'state', 'amount_total', 'partner_create_date', 'user_id']]

        # Data rows
        for order in orders:
            csv_data.append([
                order.id,
                order.partner_id.id,
                order.date_order,
                order.state,
                order.amount_total,
                order.partner_id.create_date,
                order.user_id.id if order.user_id else False
            ])

        print(f"CSV data prepared. Total rows: {len(csv_data)}")
        return csv_data

    def action_compute_statistics(self):
        if not self.data_file:
            raise UserError(_('Please collect data or upload a CSV file first.'))
        self._compute_statistics()


    def _validate_csv_data(self, csv_content):
        """Validate CSV file structure and content"""
        try:
            csv_file = StringIO(csv_content.decode())
            reader = csv.reader(csv_file)
            header = next(reader)

            required_columns = ['order_id', 'partner_id', 'date_order', 'state', 'amount_total', 'partner_create_date', 'user_id']
            if not all(col in header for col in required_columns):
                raise UserError(_('Invalid CSV format. Required columns: %s') % ', '.join(required_columns))

            return True
        except Exception as e:
            raise UserError(_('Error validating CSV file: %s') % str(e))

    def _read_csv_data(self):
        print("Starting _read_csv_data")
        if not self.data_file:
            print("No data file found")
            return []

        try:
            # Decode base64 data
            csv_data = base64.b64decode(self.data_file).decode('utf-8')
            print("Successfully decoded CSV data")

            # Read CSV data
            csv_file = StringIO(csv_data)
            reader = csv.DictReader(csv_file)
            data = []
            for row in reader:
                try:
                    # Обрізаємо мікросекунди з дат
                    if 'date_order' in row:
                        date_str = row['date_order'].split('.')[0]  # Видаляємо мікросекунди
                        row['date_order'] = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue

                try:
                    if 'partner_create_date' in row:
                        date_str = row['partner_create_date'].split('.')[0]  # Видаляємо мікросекунди
                        row['partner_create_date'] = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue

                # Ensure required fields are present
                if not all(field in row for field in ['order_id', 'partner_id', 'date_order', 'state', 'amount_total', 'partner_create_date', 'user_id']):
                    print(f"Missing required fields in row: {row}")
                    continue

                data.append(row)

            print(f"Successfully read {len(data)} rows from CSV")
            return data

        except Exception as e:
            print(f"Error reading CSV data: {str(e)}")
            return []

    @api.depends('date_from', 'date_to')
    def _compute_date_range_display(self):
        """Compute display string for date range"""
        for record in self:
            if record.date_from and record.date_to:
                # Calculate the difference in days
                delta = (record.date_to - record.date_from).days

                # Convert to years and months
                years = delta // 365
                remaining_days = delta % 365
                months = remaining_days // 30
                days = remaining_days % 30

                # Build the display string
                parts = []
                if years > 0:
                    parts.append(f"{years} {'year' if years == 1 else 'years'}")
                if months > 0:
                    parts.append(f"{months} {'month' if months == 1 else 'months'}")
                if days > 0 and not years:  # show days only if period is less than a year
                    parts.append(f"{days} {'day' if days == 1 else 'days'}")

                record.date_range_display = f"{' '.join(parts)} (from {record.date_from.strftime('%d.%m.%Y')} to {record.date_to.strftime('%d.%m.%Y')})"
            else:
                record.date_range_display = "Period not defined"

    def action_create_charts(self):
        """Create charts from CSV data"""
        self.ensure_one()

        if not self.data_file:
            raise UserError(_('Please collect data or upload a CSV file first.'))

        try:
            # Read CSV data
            data = self._read_csv_data()
            if not data:
                raise UserError(_('No data available in the CSV file.'))

            self._compute_charts()

            return True
        except Exception as e:
            raise UserError(_('Error creating charts: %s') % str(e))

    def action_visualize(self):
        """Create all visualization charts"""
        self.ensure_one()
        print("\n=== Starting action_visualize ===")

        if not self.data_file:
            raise UserError(_('Please collect data first.'))

        try:
            # Create amount-success rate chart
            print("\n--- Preparing amount-success data ---")
            amount_success_data = self._prepare_amount_success_data()
            if amount_success_data:
                print("Creating amount-success chart")
                self.amount_success_chart = self._create_amount_success_chart(amount_success_data)
            else:
                print("WARNING: No amount-success data available")

            # Create partner age-success rate chart
            print("\n--- Preparing partner-age success data ---")
            partner_age_success_data = self._prepare_partner_age_success_data()
            if partner_age_success_data:
                print("Creating partner-age success chart")
                self.partner_age_success_chart = self._create_partner_age_success_chart(partner_age_success_data)
            else:
                print("WARNING: No partner-age success data available")

            self._compute_month_charts()
            self._compute_weekday_charts()
            self._compute_partner_orders_charts()
            self._compute_amount_success_charts()

            return True

        except Exception as e:
            print(f"\nERROR in action_visualize: {str(e)}")
            import traceback
            print(traceback.format_exc())
            raise UserError(_('Error creating visualization. Please check the logs.'))

    def _prepare_amount_success_data(self):
        """Prepare data for amount-success rate chart"""
        try:
            # Read CSV data
            data = self._read_csv_data()
            if not data:
                return None

            # Get all amounts and sort them
            amounts_data = [(float(row['amount_total']), row['state'] == 'sale')
                            for row in data]

            # Видаляємо замовлення з нульовою сумою
            amounts_data = [x for x in amounts_data if x[0] > 0]
            amounts_data.sort(key=lambda x: x[0])

            total_orders = len(amounts_data)
            if total_orders == 0:
                return None

            # Визначаємо кількість груп (зменшуємо якщо замовлень мало)
            num_groups = min(30, total_orders // 50)  # Мінімум 50 замовлень на групу
            if num_groups < 5:  # Якщо груп менше 5, встановлюємо мінімум 5 груп
                num_groups = 5

            # Розраховуємо розмір кожної групи
            group_size = total_orders // num_groups
            remainder = total_orders % num_groups

            # Ініціалізуємо результат
            result = {
                'ranges': [],
                'rates': [],
                'orders_count': []
            }

            # Розбиваємо на групи
            start_idx = 0
            for i in range(num_groups):
                # Додаємо +1 до розміру групи для перших remainder груп
                current_group_size = group_size + (1 if i < remainder else 0)
                if current_group_size == 0:
                    break

                end_idx = start_idx + current_group_size
                group_orders = amounts_data[start_idx:end_idx]

                # Рахуємо статистику для групи
                min_amount = group_orders[0][0]
                max_amount = group_orders[-1][0]
                successful = sum(1 for _, is_success in group_orders if is_success)
                success_rate = (successful / len(group_orders)) * 100

                # Форматуємо діапазон в залежності від розміру чисел
                if max_amount >= 1000000:  # Більше 1 млн
                    range_str = f'{min_amount/1000000:.1f}M-{max_amount/1000000:.1f}M'
                elif max_amount >= 1000:  # Більше 1000
                    range_str = f'{min_amount/1000:.0f}K-{max_amount/1000:.0f}K'
                else:
                    range_str = f'{min_amount:.0f}-{max_amount:.0f}'

                # Додаємо дані до результату
                result['ranges'].append(range_str)
                result['rates'].append(success_rate)
                result['orders_count'].append(len(group_orders))

                start_idx = end_idx

            return result

        except Exception as e:
            print(f"Error preparing amount-success data: {str(e)}")
            return None

    def _create_amount_success_chart(self, data):
        """Create chart showing success rate by order amount"""
        if not data:
            return False

        try:
            plt.figure(figsize=(15, 8))

            # Фільтруємо точки з нульовою кількістю ордерів
            x_points = []
            y_points = []
            counts = []
            for i, (rate, count) in enumerate(zip(data['rates'], data['orders_count'])):
                if count > 0:
                    x_points.append(i)
                    y_points.append(rate)
                    counts.append(count)

            # Створюємо градієнт кольорів від червоного до зеленого в залежності від success rate
            colors = ['#ff4d4d' if rate < 50 else '#00cc00' for rate in y_points]
            sizes = [max(80, min(150, count/2)) for count in counts]  # Розмір точки залежить від кількості замовлень

            # Малюємо точки
            scatter = plt.scatter(x_points, y_points, s=sizes, alpha=0.6, c=colors)

            # Розраховуємо середню кількість ордерів на точку
            avg_orders = sum(counts) // len(counts) if counts else 0

            plt.title(f'Success Rate by Order Amount\n(each point represents ~{avg_orders} orders, point size shows relative number in range)',
                      pad=20, fontsize=12)
            plt.xlabel('Order Amount Range', fontsize=10)
            plt.ylabel('Success Rate (%)', fontsize=10)

            # Налаштовуємо осі
            plt.ylim(-5, 105)  # Додаємо трохи простору зверху і знизу

            # Показуємо всі мітки, якщо їх менше 10, інакше кожну другу
            if len(data['ranges']) <= 10:
                plt.xticks(range(len(data['ranges'])), data['ranges'],
                           rotation=45, ha='right')
            else:
                plt.xticks(range(len(data['ranges']))[::2], [data['ranges'][i] for i in range(0, len(data['ranges']), 2)],
                           rotation=45, ha='right')

            plt.grid(True, linestyle='--', alpha=0.7)

            # Додаємо горизонтальні лінії
            plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
            plt.axhline(y=50, color='gray', linestyle='--', alpha=0.3)
            plt.axhline(y=100, color='gray', linestyle='-', alpha=0.3)

            # Додаємо легенду
            legend_elements = [
                plt.Line2D([0], [0], marker='o', color='w',
                           markerfacecolor='#ff4d4d', markersize=10,
                           label='Success Rate < 50%'),
                plt.Line2D([0], [0], marker='o', color='w',
                           markerfacecolor='#00cc00', markersize=10,
                           label='Success Rate ≥ 50%')
            ]
            plt.legend(handles=legend_elements, loc='upper right')

            # Зберігаємо графік
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight',
                        dpi=100, pad_inches=0.2)
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error creating amount-success chart: {str(e)}")
            return False

    def _prepare_partner_age_success_data(self):
        """Prepare data for partner age-success rate chart"""
        try:
            print("\nStarting _prepare_partner_age_success_data")

            # Read CSV data
            data = self._read_csv_data()
            if not data:
                print("WARNING: No CSV data available")
                return None

            # Розраховуємо вік партнера для кожного замовлення
            partner_age_data = []
            print("\nProcessing partner age data...")

            missing_create_date = 0
            missing_order_date = 0
            processed_rows = 0
            error_rows = 0

            for row in data:
                if not row.get('partner_create_date'):
                    missing_create_date += 1
                    continue
                if not row.get('date_order'):
                    missing_order_date += 1
                    continue

                try:
                    # Якщо дати в строковому форматі, конвертуємо їх
                    if isinstance(row['partner_create_date'], str):
                        row['partner_create_date'] = datetime.strptime(row['partner_create_date'], '%Y-%m-%d %H:%M:%S')
                    if isinstance(row['date_order'], str):
                        row['date_order'] = datetime.strptime(row['date_order'], '%Y-%m-%d %H:%M:%S')

                    partner_age = (row['date_order'] - row['partner_create_date']).days
                    partner_age_data.append((partner_age, row['state'] == 'sale'))
                    processed_rows += 1
                except Exception as e:
                    error_rows += 1

            print(f"\nProcessing summary:")
            print(f"- Total rows: {len(data)}")
            print(f"- Missing create date: {missing_create_date}")
            print(f"- Missing order date: {missing_order_date}")
            print(f"- Successfully processed: {processed_rows}")
            print(f"- Errors: {error_rows}")

            if not partner_age_data:
                print("WARNING: No valid partner age data found")
                return None

            print(f"Found {len(partner_age_data)} valid orders for analysis")
            # Сортуємо за віком партнера
            partner_age_data.sort(key=lambda x: x[0])

            total_orders = len(partner_age_data)
            print(f"Total orders for analysis: {total_orders}")

            # Визначаємо кількість груп
            num_groups = min(30, total_orders // 50)
            if num_groups < 5:
                num_groups = 5
            print(f"Number of groups: {num_groups}")

            # Розраховуємо розмір кожної групи
            group_size = total_orders // num_groups
            remainder = total_orders % num_groups
            print(f"Group size: {group_size}, remainder: {remainder}")

            # Ініціалізуємо результат
            result = {
                'ranges': [],
                'rates': [],
                'orders_count': []
            }

            # Розбиваємо на групи
            start_idx = 0
            for i in range(num_groups):
                current_group_size = group_size + (1 if i < remainder else 0)
                if current_group_size == 0:
                    break

                end_idx = start_idx + current_group_size
                group_orders = partner_age_data[start_idx:end_idx]

                # Рахуємо статистику для групи
                min_age = group_orders[0][0]
                max_age = group_orders[-1][0]
                successful = sum(1 for _, is_success in group_orders if is_success)
                success_rate = (successful / len(group_orders)) * 100

                print(f"\nGroup {i}:")
                print(f"- Orders: {len(group_orders)}")
                print(f"- Success rate: {success_rate:.1f}%")
                print(f"- Age range: {min_age}-{max_age} days")

                # Форматуємо діапазон
                if max_age >= 365:
                    range_str = f'{min_age/365:.1f}y-{max_age/365:.1f}y'
                elif max_age >= 30:
                    range_str = f'{min_age/30:.0f}m-{max_age/30:.0f}m'
                else:
                    range_str = f'{min_age}d-{max_age}d'

                # Додаємо дані до результату
                result['ranges'].append(range_str)
                result['rates'].append(success_rate)
                result['orders_count'].append(len(group_orders))

                start_idx = end_idx

            print("\nSuccessfully prepared partner age success data")
            return result

        except Exception as e:
            print(f"\nERROR in _prepare_partner_age_success_data: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None

    def _create_partner_age_success_chart(self, data):
        """Create chart showing success rate by partner age"""
        if not data:
            return False

        try:
            plt.figure(figsize=(15, 8))

            # Фільтруємо точки з нульовою кількістю ордерів
            x_points = []
            y_points = []
            counts = []
            for i, (rate, count) in enumerate(zip(data['rates'], data['orders_count'])):
                if count > 0:
                    x_points.append(i)
                    y_points.append(rate)
                    counts.append(count)

            # Створюємо градієнт кольорів від червоного до зеленого в залежності від success rate
            colors = ['#ff4d4d' if rate < 50 else '#00cc00' for rate in y_points]
            sizes = [max(80, min(150, count/2)) for count in counts]  # Розмір точки залежить від кількості замовлень

            # Малюємо точки
            scatter = plt.scatter(x_points, y_points, s=sizes, alpha=0.6, c=colors)

            # Розраховуємо середню кількість ордерів на точку
            avg_orders = sum(counts) // len(counts) if counts else 0

            plt.title(f'Success Rate by Partner Age\n(each point represents ~{avg_orders} orders, point size shows relative number in range)',
                      pad=20, fontsize=12)
            plt.xlabel('Partner Age (d=days, m=months, y=years)', fontsize=10)
            plt.ylabel('Success Rate (%)', fontsize=10)

            # Налаштовуємо осі
            plt.ylim(-5, 105)

            # Показуємо всі мітки, якщо їх менше 10, інакше кожну другу
            if len(data['ranges']) <= 10:
                plt.xticks(range(len(data['ranges'])), data['ranges'],
                           rotation=45, ha='right')
            else:
                plt.xticks(range(len(data['ranges']))[::2], [data['ranges'][i] for i in range(0, len(data['ranges']), 2)],
                           rotation=45, ha='right')

            plt.grid(True, linestyle='--', alpha=0.7)

            # Додаємо горизонтальні лінії
            plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
            plt.axhline(y=50, color='gray', linestyle='--', alpha=0.3)
            plt.axhline(y=100, color='gray', linestyle='-', alpha=0.3)

            # Додаємо легенду
            legend_elements = [
                plt.Line2D([0], [0], marker='o', color='w',
                           markerfacecolor='#ff4d4d', markersize=10,
                           label='Success Rate < 50%'),
                plt.Line2D([0], [0], marker='o', color='w',
                           markerfacecolor='#00cc00', markersize=10,
                           label='Success Rate ≥ 50%')
            ]
            plt.legend(handles=legend_elements, loc='upper right')

            # Зберігаємо графік
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight',
                        dpi=100, pad_inches=0.2)
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error creating partner-age success chart: {str(e)}")
            return False

    def _compute_statistics(self):
        print("Starting _compute_statistics")
        for record in self:
            print(f"Processing record {record.id}")

            # Read CSV data
            data = record._read_csv_data()
            print(f"Read {len(data)} rows from CSV for record {record.id}")
            if not data:
                continue

            # Initialize statistics
            partners = set()  # використовуємо set для унікальних партнерів
            total_orders = 0
            successful_orders = 0
            orders_by_state = defaultdict(int)
            partners_success_rate = defaultdict(lambda: {'total': 0, 'successful': 0})
            salesperson_success_rate = defaultdict(lambda: {'total': 0, 'successful': 0})

            # Process data
            for row in data:
                partner_id = int(row['partner_id'])
                order_state = row['state']
                user_id = row['user_id']

                # Update statistics
                partners.add(partner_id)
                total_orders += 1
                orders_by_state[order_state] += 1

                # Update partner success rate
                partners_success_rate[partner_id]['total'] += 1
                if order_state == 'sale':
                    partners_success_rate[partner_id]['successful'] += 1
                    successful_orders += 1

                # Update salesperson success rate
                if user_id:
                    salesperson_success_rate[user_id]['total'] += 1
                    if order_state == 'sale':
                        salesperson_success_rate[user_id]['successful'] += 1

            print(f"Processed data for record {record.id}: {len(partners)} partners, {total_orders} orders")

            # Calculate success rate ranges
            success_rate_ranges = defaultdict(int)
            for partner_data in partners_success_rate.values():
                success_rate = (partner_data['successful'] / partner_data['total'] * 100) if partner_data['total'] > 0 else 0

                # Розподіляємо по діапазонах
                if success_rate == 100:
                    range_key = '100%'
                elif success_rate >= 80:
                    range_key = '80-99%'
                elif success_rate >= 60:
                    range_key = '60-79%'
                elif success_rate >= 40:
                    range_key = '40-59%'
                elif success_rate >= 20:
                    range_key = '20-39%'
                else:
                    range_key = '0-19%'

                success_rate_ranges[range_key] += 1

            # Update computed fields
            record.total_partners = len(partners)
            record.total_orders = total_orders
            record.total_success_rate = (successful_orders / total_orders) if total_orders > 0 else 0
            record.orders_by_state = str(dict(orders_by_state))
            record.partners_by_success_rate = str(dict(success_rate_ranges))

            # Create salesperson success rate chart
            salesperson_success_data = []
            for user_id, data in salesperson_success_rate.items():
                success_rate = (data['successful'] / data['total'] * 100) if data['total'] > 0 else 0
                salesperson_success_data.append((user_id, success_rate))

            salesperson_success_data.sort(key=lambda x: x[1])
            record.salesperson_success_chart = record._create_salesperson_success_chart(salesperson_success_data)

            print(f"Updated statistics for record {record.id}")

    def _compute_charts(self):
        self._compute_distribution_charts()
        self._compute_monthly_charts()

    def _compute_distribution_charts(self):
        """Compute distribution charts"""
        print("\nStarting _compute_distribution_charts")
        for record in self:
            if not record.data_file:
                record.orders_by_state_chart = False
                record.partners_by_rate_chart = False
                record.partners_by_rate_plot = False
                record.salesperson_success_chart = False
                continue

            try:
                # Read CSV data
                data = record._read_csv_data()
                if not data:
                    continue

                # Prepare orders by state data with specific order and colors
                state_order = ['draft', 'sent', 'sale', 'cancel']
                state_colors = {
                    'draft': '#808080',  # Gray
                    'sent': '#FFD700',   # Yellow
                    'sale': '#28a745',   # Green
                    'cancel': '#dc3545'  # Red
                }

                # Count orders by state
                states_count = defaultdict(int)
                for row in data:
                    states_count[row['state']] += 1

                # Create ordered dictionary with all states (even if count is 0)
                states_data = {state: states_count.get(state, 0) for state in state_order}
                state_colors_list = [state_colors[state] for state in state_order]

                # Create orders by state chart
                record.orders_by_state_chart = record._create_distribution_chart(
                    states_data,
                    'Orders Distribution by Status',
                    'Status',
                    'Number of Orders',
                    state_colors_list
                )

                # Calculate success rates per partner
                partner_orders = defaultdict(list)
                for row in data:
                    partner_orders[row['partner_id']].append(row['state'])

                partner_success_rates = {}
                for partner_id, states in partner_orders.items():
                    success_count = states.count('sale')
                    total_count = len(states)
                    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
                    partner_success_rates[partner_id] = success_rate

                # Create partners rate charts
                record.partners_by_rate_chart = record._create_partners_rate_chart(partner_success_rates)
                record.partners_by_rate_plot = record._create_partners_rate_plot(partner_success_rates)

                # Create salesperson success rate chart
                print("\nPreparing salesperson data...")
                salesperson_orders = defaultdict(lambda: {'total': 0, 'successful': 0})

                # Збираємо статистику
                for row in data:
                    if row['user_id']:
                        salesperson_orders[row['user_id']]['total'] += 1
                        if row['state'] == 'sale':
                            salesperson_orders[row['user_id']]['successful'] += 1

                print(f"\nFound {len(salesperson_orders)} salespersons")

                # Формуємо дані для графіка
                salesperson_success_data = []
                for user_id, stats in salesperson_orders.items():
                    success_rate = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    salesperson_success_data.append({
                        'user_id': user_id,
                        'success_rate': success_rate,
                        'total_orders': stats['total']
                    })

                # Сортуємо за success_rate
                salesperson_success_data.sort(key=lambda x: x['success_rate'])

                print("\nFirst 3 records of prepared data:")
                for i, item in enumerate(salesperson_success_data[:3]):
                    print(f"Record {i + 1}:")
                    print(f"  user_id: {item['user_id']}")
                    print(f"  success_rate: {item['success_rate']:.2f}%")
                    print(f"  total_orders: {item['total_orders']}")

                # Створюємо графік
                record.salesperson_success_chart = record._create_salesperson_success_chart(salesperson_success_data)

            except Exception as e:
                print(f"Error computing distribution charts: {str(e)}")
                import traceback
                print(traceback.format_exc())
                record.orders_by_state_chart = False
                record.partners_by_rate_chart = False
                record.partners_by_rate_plot = False
                record.salesperson_success_chart = False
            finally:
                plt.close('all')

    def _create_salesperson_success_chart(self, data):
        if not data:
            return False

        try:
            plt.figure(figsize=(15, 8))

            # Create data arrays
            x_values = [str(d['user_id']) for d in data]
            success_rates = [d['success_rate'] for d in data]
            total_orders = [d['total_orders'] for d in data]

            # Create bar chart
            bars = plt.bar(x_values, success_rates, color='#4CAF50', alpha=0.7)

            # Add value labels above bars
            for i, (bar, orders) in enumerate(zip(bars, total_orders)):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2, height + 2,
                         f'{orders}',
                         ha='right', va='bottom',
                         rotation=90,
                         fontsize=10,
                         )

            plt.title('Success Rate by Salesperson\n(numbers show total orders)',
                      pad=20, fontsize=12)
            plt.xlabel('Salesperson ID', fontsize=10)
            plt.ylabel('Success Rate (%)', fontsize=10)

            # Add grid
            plt.grid(True, axis='y', linestyle='--', alpha=0.7)

            # Rotate x labels
            plt.xticks(rotation=45, ha='right')

            # Adjust layout and y-axis limit
            plt.ylim(0, max(success_rates) * 1.15)
            plt.tight_layout()

            # Save chart
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error creating salesperson success chart: {str(e)}")
            return False
        finally:
            plt.close('all')

    def _create_partners_rate_chart(self, partner_success_rates):
        """Create bar chart showing distribution of partners by success rate ranges"""
        try:
            # Define success rate ranges with specific order
            success_ranges = [
                ('0-20%', (0, 20)),
                ('21-40%', (21, 40)),
                ('41-60%', (41, 60)),
                ('61-80%', (61, 80)),
                ('81-100%', (81, 100))
            ]

            # Generate green shades from light to dark
            green_shades = [
                '#c8e6c9',  # Very light green
                '#a5d6a7',  # Light green
                '#81c784',  # Medium green
                '#66bb6a',  # Dark green
                '#43a047',  # Very dark green
            ]

            # Calculate distribution
            distribution = defaultdict(int)
            for rate in partner_success_rates.values():
                for range_name, (min_val, max_val) in success_ranges:
                    if min_val <= rate <= max_val:
                        distribution[range_name] += 1
                        break

            # Create ordered dictionary for success rate ranges
            ordered_distribution = {range_name: distribution.get(range_name, 0)
                                    for range_name, _ in success_ranges}

            # Create the chart
            plt.figure(figsize=(12, 6))
            plt.bar(ordered_distribution.keys(),
                    ordered_distribution.values(),
                    color=green_shades)
            plt.title('Distribution of Partners by Success Rate Ranges')
            plt.xlabel('Success Rate Range')
            plt.ylabel('Number of Partners')
            plt.xticks(rotation=45)

            # Save the chart
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error creating partners rate chart: {str(e)}")
            return False
        finally:
            plt.close('all')

    def _create_partners_rate_plot(self, partner_success_rates):
        """Create line plot showing success rate distribution across partners"""
        plt.figure(figsize=(12, 6))

        # Sort success rates for better visualization
        sorted_rates = sorted(partner_success_rates.values())
        x_values = range(1, len(sorted_rates) + 1)

        plt.plot(x_values, sorted_rates, 'b-', linewidth=2)
        plt.title('Partners Success Rate Distribution')
        plt.xlabel('Number of Partners')
        plt.ylabel('Success Rate (%)')
        plt.grid(True)

        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        plt.close()

        return base64.b64encode(buffer.getvalue())

    def _compute_monthly_charts(self):
        for record in self:
            if not record.data_file:
                record.monthly_analysis_chart = False
                continue

            # Read CSV data
            data = record._read_csv_data()
            if not data:
                continue

            # Initialize data arrays
            monthly_data = defaultdict(lambda: {'orders': 0, 'successful': 0, 'rate': 0})

            # Process data
            for row in data:
                if not row['date_order']:
                    continue

                month_key = row['date_order'].strftime('%m/%Y')
                monthly_data[month_key]['orders'] += 1
                if row['state'] == 'sale':
                    monthly_data[month_key]['successful'] += 1

            # Calculate success rate for each month
            for month_data in monthly_data.values():
                month_data['rate'] = (month_data['successful'] / month_data['orders'] * 100) if month_data['orders'] > 0 else 0

            # Sort months chronologically
            sorted_months = sorted(monthly_data.keys(),
                                   key=lambda x: datetime.strptime(x, '%m/%Y'))

            # Create data arrays in chronological order
            months = sorted_months
            orders_data = [monthly_data[month]['orders'] for month in months]
            successful_data = [monthly_data[month]['successful'] for month in months]
            rate_data = [monthly_data[month]['rate'] for month in months]

            if not months:
                record.monthly_analysis_chart = False
                continue

            # Create combined chart
            record.monthly_analysis_chart = record._create_chart(
                months, orders_data, successful_data, rate_data)

    @staticmethod
    def _create_chart(months, orders_data, successful_data, rate_data):
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

            plt.title('Monthly Orders Analysis')

            # Set x-axis labels
            months_display = [datetime.strptime(m, '%m/%Y').strftime('%B %Y') for m in months]
            plt.xticks(x, months_display, rotation=45, ha='right')

            # Add grid
            ax1.grid(True, axis='y', linestyle='--', alpha=0.7)

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
            print(f"Error creating chart: {str(e)}")
            return False
        finally:
            plt.close('all')

    @staticmethod
    def _create_distribution_chart(data, title, xlabel, ylabel, colors):
        """Helper function for creating distribution charts"""
        try:
            # Create figure
            fig, ax = plt.subplots(figsize=(12, 6))

            # Get data
            labels = list(data.keys())
            values = list(data.values())

            # Create bars with specific colors
            x = np.arange(len(labels))
            bars = ax.bar(x, values, color=colors)

            # Customize chart
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            ax.set_title(title)

            # Set x-axis labels
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha='right')

            # Add grid
            ax.grid(True, axis='y', linestyle='--', alpha=0.7)

            # Add values above bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
                        ha='center', va='bottom')

            # Adjust layout
            plt.tight_layout()

            # Save to buffer
            buffer = BytesIO()
            fig.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error creating distribution chart: {str(e)}")
            return False
        finally:
            plt.close('all')

    def _create_weekday_success_chart(self, weekday_stats):
        """Creating success rate chart by weekday"""
        try:
            plt.figure(figsize=(12, 6))

            # Weekday names
            weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            success_rates = []
            total_orders = []

            # Calculate success rate
            for day in range(7):
                stats = weekday_stats[day]
                success_rate = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
                success_rates.append(success_rate)
                total_orders.append(stats['total'])

            # Create main bars
            bars = plt.bar(weekdays, success_rates, color='#4CAF50', alpha=0.7)

            # Add order count labels
            for i, (bar, orders) in enumerate(zip(bars, total_orders)):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2, height + 1,
                         f'{orders}',
                         ha='center', va='bottom',
                         rotation=0,
                         fontsize=10,
                         color='green')

            plt.title('Success Rate by Weekday\n(numbers show total orders)',
                      pad=20, fontsize=12)
            plt.xlabel('Weekday')
            plt.ylabel('Success Rate (%)')

            # Add grid
            plt.grid(True, linestyle='--', alpha=0.7, zorder=0)

            # Configure X axis labels
            plt.xticks(rotation=45, ha='right')

            # Set Y axis limits
            plt.ylim(0, max(success_rates) * 1.15)

            # Configure layout
            plt.tight_layout()

            # Save chart
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error creating weekday success chart: {str(e)}")
            return False

    def _create_month_success_chart(self, month_stats):
        """Creating success rate chart by month"""
        try:
            plt.figure(figsize=(12, 6))

            # Month names
            months = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
            success_rates = []
            total_orders = []

            # Calculate success rate
            for month in range(1, 13):
                stats = month_stats[month]
                success_rate = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
                success_rates.append(success_rate)
                total_orders.append(stats['total'])

            # Create main bars
            bars = plt.bar(months, success_rates, color='#2196F3', alpha=0.7)

            # Add order count labels
            for i, (bar, orders) in enumerate(zip(bars, total_orders)):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2, height + 1,
                         f'{orders}',
                         ha='center', va='bottom',
                         rotation=0,
                         fontsize=10,
                         color='blue')

            plt.title('Success Rate by Month\n(numbers show total orders)',
                      pad=20, fontsize=12)
            plt.xlabel('Month')
            plt.ylabel('Success Rate (%)')

            # Add grid
            plt.grid(True, linestyle='--', alpha=0.7, zorder=0)

            # Configure X axis labels
            plt.xticks(rotation=45, ha='right')

            # Set Y axis limits
            plt.ylim(0, max(success_rates) * 1.15)

            # Configure layout
            plt.tight_layout()

            # Save chart
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error creating month success chart: {str(e)}")
            return False

    def _compute_weekday_charts(self):
        for record in self:
            if not record.data_file:
                record.weekday_success_chart = False
                continue

            # Read CSV data
            data = record._read_csv_data()
            if not data:
                continue

            # Initialize weekday data
            weekday_data = defaultdict(lambda: {'total': 0, 'successful': 0})

            # Process data
            for row in data:
                if not row['date_order']:
                    continue

                weekday = row['date_order'].weekday()
                weekday_data[weekday]['total'] += 1
                if row['state'] == 'sale':
                    weekday_data[weekday]['successful'] += 1

            # Create weekday success chart
            record.weekday_success_chart = record._create_weekday_success_chart(weekday_data)

    def _compute_month_charts(self):
        for record in self:
            if not record.data_file:
                record.month_success_chart = False
                continue

            # Read CSV data
            data = record._read_csv_data()
            if not data:
                continue

            # Initialize month data
            month_data = defaultdict(lambda: {'total': 0, 'successful': 0})

            # Process data
            for row in data:
                if not row['date_order']:
                    continue

                month = row['date_order'].month
                month_data[month]['total'] += 1
                if row['state'] == 'sale':
                    month_data[month]['successful'] += 1

            # Create month success chart
            record.month_success_chart = record._create_month_success_chart(month_data)

    def _compute_partner_orders_charts(self):
        """Compute success rate based on total number of partner orders"""
        for record in self:
            if not record.data_file:
                record.partner_orders_success_chart = False
                continue

            try:
                # Read CSV data
                data = record._read_csv_data()
                if not data:
                    continue

                # Calculate statistics per partner
                partner_stats = {}
                for row in data:
                    partner_id = row['partner_id']
                    if partner_id not in partner_stats:
                        partner_stats[partner_id] = {'total': 0, 'successful': 0}

                    partner_stats[partner_id]['total'] += 1
                    if row['state'] == 'sale':
                        partner_stats[partner_id]['successful'] += 1

                # Create chart
                record.partner_orders_success_chart = record._create_partner_orders_success_chart(partner_stats)

            except Exception as e:
                print(f"Error computing partner orders success chart: {str(e)}")
                record.partner_orders_success_chart = False

    def _create_partner_orders_success_chart(self, partner_stats):
        """Create chart showing success rate by total number of partner orders"""
        try:
            plt.figure(figsize=(12, 6))

            # Calculate success rates and total orders
            success_data = []
            for partner_id, stats in partner_stats.items():
                if stats['total'] > 0:
                    success_rate = (stats['successful'] / stats['total']) * 100
                    success_data.append((stats['total'], success_rate))

            # Sort by total orders
            success_data.sort(key=lambda x: x[0])

            # Group data by order count ranges
            ranges = [1, 2, 3, 5, 10, 20, 50, 100, float('inf')]
            range_stats = {i: {'total': 0, 'sum_rate': 0} for i in range(len(ranges))}

            for total_orders, success_rate in success_data:
                for i, upper_bound in enumerate(ranges):
                    if total_orders <= upper_bound:
                        range_stats[i]['total'] += 1
                        range_stats[i]['sum_rate'] += success_rate
                        break

            # Calculate average success rate for each range
            x_labels = []
            success_rates = []
            partners_count = []

            for i in range(len(ranges)):
                if range_stats[i]['total'] > 0:
                    if i == len(ranges) - 1:
                        x_labels.append(f'>{ranges[i-1]}')
                    elif i == 0:
                        x_labels.append(f'1')
                    else:
                        x_labels.append(f'{ranges[i-1]+1}-{ranges[i]}')

                    avg_rate = range_stats[i]['sum_rate'] / range_stats[i]['total']
                    success_rates.append(avg_rate)
                    partners_count.append(range_stats[i]['total'])

            # Create bar chart
            bars = plt.bar(x_labels, success_rates, color='#9C27B0', alpha=0.7)

            # Add value labels
            for i, (bar, count) in enumerate(zip(bars, partners_count)):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2, height + 1,
                         f'{count}',
                         ha='center', va='bottom',
                         rotation=0,
                         fontsize=10,
                         color='purple')

            plt.title('Success Rate by Number of Orders per Partner\n(numbers show partners count in each range)',
                      pad=20, fontsize=12)
            plt.xlabel('Number of Orders')
            plt.ylabel('Average Success Rate (%)')

            # Add grid
            plt.grid(True, linestyle='--', alpha=0.7, zorder=0)

            # Configure X axis labels
            plt.xticks(rotation=45, ha='right')

            # Set Y axis limits
            plt.ylim(0, max(success_rates) * 1.15)

            # Configure layout
            plt.tight_layout()

            # Save chart
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error creating partner orders success chart: {str(e)}")
            return False

    def _compute_amount_success_charts(self):
        """Compute success rate based on different amount metrics"""
        for record in self:
            if not record.data_file:
                record.total_amount_success_chart = False
                record.success_amount_success_chart = False
                record.avg_amount_success_chart = False
                record.avg_success_amount_success_chart = False
                continue

            try:
                # Read CSV data
                data = record._read_csv_data()
                if not data:
                    continue

                # Calculate statistics per partner
                partner_stats = {}
                for row in data:
                    partner_id = row['partner_id']
                    amount = float(row['amount_total'])

                    if partner_id not in partner_stats:
                        partner_stats[partner_id] = {
                            'total_orders': 0,
                            'successful_orders': 0,
                            'total_amount': 0,
                            'success_amount': 0
                        }

                    partner_stats[partner_id]['total_orders'] += 1
                    partner_stats[partner_id]['total_amount'] += amount

                    if row['state'] == 'sale':
                        partner_stats[partner_id]['successful_orders'] += 1
                        partner_stats[partner_id]['success_amount'] += amount

                # Calculate success rates and averages
                for partner_id, stats in partner_stats.items():
                    stats['success_rate'] = (stats['successful_orders'] / stats['total_orders'] * 100) if stats['total_orders'] > 0 else 0
                    stats['avg_amount'] = stats['total_amount'] / stats['total_orders'] if stats['total_orders'] > 0 else 0
                    stats['avg_success_amount'] = stats['success_amount'] / stats['successful_orders'] if stats['successful_orders'] > 0 else 0

                # Create charts
                record.total_amount_success_chart = record._create_amount_based_chart(
                    partner_stats, 'total_amount',
                    'Success Rate by Total Orders Amount',
                    'Total Orders Amount'
                )

                record.success_amount_success_chart = record._create_amount_based_chart(
                    partner_stats, 'success_amount',
                    'Success Rate by Successful Orders Amount',
                    'Successful Orders Amount'
                )

                record.avg_amount_success_chart = record._create_amount_based_chart(
                    partner_stats, 'avg_amount',
                    'Success Rate by Average Order Amount',
                    'Average Order Amount'
                )

                record.avg_success_amount_success_chart = record._create_amount_based_chart(
                    partner_stats, 'avg_success_amount',
                    'Success Rate by Average Successful Order Amount',
                    'Average Successful Order Amount'
                )


            except Exception as e:
                print(f"Error computing amount success charts: {str(e)}")
                record.total_amount_success_chart = False
                record.success_amount_success_chart = False
                record.avg_amount_success_chart = False
                record.avg_success_amount_success_chart = False

    def _create_amount_based_chart(self, partner_stats, amount_field, title, xlabel):
        """Create chart showing success rate by specified amount metric"""
        try:
            plt.figure(figsize=(15, 8))

            # Prepare data
            data_points = []
            for partner_id, stats in partner_stats.items():
                amount = stats[amount_field]
                if amount > 0:  # Виключаємо записи з нульовою сумою
                    data_points.append((amount, stats['success_rate']))

            if not data_points:
                return False

            # Sort by amount
            data_points.sort(key=lambda x: x[0])

            total_points = len(data_points)
            if total_points == 0:
                return False

            # Визначаємо кількість груп (зменшуємо якщо партнерів мало)
            num_groups = min(30, total_points // 50)  # Мінімум 50 партнерів на групу
            if num_groups < 5:  # Якщо груп менше 5, встановлюємо мінімум 5 груп
                num_groups = 5

            # Розраховуємо розмір кожної групи
            group_size = total_points // num_groups
            remainder = total_points % num_groups

            # Ініціалізуємо результат
            result = {
                'ranges': [],
                'rates': [],
                'orders_count': []
            }

            # Розбиваємо на групи
            start_idx = 0
            for i in range(num_groups):
                # Додаємо +1 до розміру групи для перших remainder груп
                current_group_size = group_size + (1 if i < remainder else 0)
                if current_group_size == 0:
                    break

                end_idx = start_idx + current_group_size
                group_points = data_points[start_idx:end_idx]

                # Рахуємо статистику для групи
                min_amount = group_points[0][0]
                max_amount = group_points[-1][0]
                avg_success_rate = sum(rate for _, rate in group_points) / len(group_points)

                # Форматуємо діапазон
                if max_amount >= 1000000:
                    range_str = f'{min_amount/1000000:.1f}M-{max_amount/1000000:.1f}M'
                elif max_amount >= 1000:
                    range_str = f'{min_amount/1000:.0f}K-{max_amount/1000:.0f}K'
                else:
                    range_str = f'{min_amount:.0f}-{max_amount:.0f}'

                # Додаємо дані до результату
                result['ranges'].append(range_str)
                result['rates'].append(avg_success_rate)
                result['orders_count'].append(len(group_points))

                start_idx = end_idx

            # Створюємо точковий графік
            x_points = []
            y_points = []
            counts = []
            for i, (rate, count) in enumerate(zip(result['rates'], result['orders_count'])):
                if count > 0:
                    x_points.append(i)
                    y_points.append(rate)
                    counts.append(count)

            # Створюємо градієнт кольорів від червоного до зеленого в залежності від success rate
            colors = ['#ff4d4d' if rate < 50 else '#00cc00' for rate in y_points]
            sizes = [max(80, min(150, count/2)) for count in counts]  # Розмір точки залежить від кількості партнерів

            # Малюємо точки
            scatter = plt.scatter(x_points, y_points, s=sizes, alpha=0.6, c=colors)

            # Розраховуємо середню кількість партнерів на точку
            avg_partners = sum(counts) // len(counts) if counts else 0

            plt.title(f'{title}\n(each point represents ~{avg_partners} partners, point size shows relative number in range)',
                      pad=20, fontsize=12)
            plt.xlabel(xlabel)
            plt.ylabel('Success Rate (%)')

            # Налаштовуємо осі
            plt.ylim(-5, 105)

            # Показуємо всі мітки, якщо їх менше 10, інакше кожну другу
            if len(result['ranges']) <= 10:
                plt.xticks(range(len(result['ranges'])), result['ranges'],
                           rotation=45, ha='right')
            else:
                plt.xticks(range(len(result['ranges']))[::2], [result['ranges'][i] for i in range(0, len(result['ranges']), 2)],
                           rotation=45, ha='right')

            plt.grid(True, linestyle='--', alpha=0.7)

            # Додаємо горизонтальні лінії
            plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
            plt.axhline(y=50, color='gray', linestyle='--', alpha=0.3)
            plt.axhline(y=100, color='gray', linestyle='-', alpha=0.3)

            # Додаємо легенду
            legend_elements = [
                plt.Line2D([0], [0], marker='o', color='w',
                           markerfacecolor='#ff4d4d', markersize=10,
                           label='Success Rate < 50%'),
                plt.Line2D([0], [0], marker='o', color='w',
                           markerfacecolor='#00cc00', markersize=10,
                           label='Success Rate ≥ 50%')
            ]
            plt.legend(handles=legend_elements, loc='upper right')

            # Зберігаємо графік
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight',
                        dpi=100, pad_inches=0.2)
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error creating amount based chart: {str(e)}")
            return False

    def _format_amount(self, amount):
        """Format amount for display in chart labels"""
        if amount >= 1000000:
            return f'{amount/1000000:.1f}M'
        elif amount >= 1000:
            return f'{amount/1000:.0f}K'
        else:
            return f'{amount:.0f}'
