import csv
import base64
import logging
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.patheffects as PathEffects

matplotlib.use('Agg')
import numpy as np
import pandas as pd
import seaborn as sns
from io import StringIO, BytesIO
from collections import defaultdict

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DataProcessor(models.Model):
    _name = 'data.processor'
    _description = 'Data Processor'

    name = fields.Char(required=True)
    prefix_number = fields.Integer(required=True)
    date_from = fields.Date(readonly=True)
    date_to = fields.Date(readonly=True)
    date_range_display = fields.Char(string='Analysis Period', compute='_compute_date_range_display', store=True)
    date_partner_from = fields.Date(readonly=True)
    date_partner_to = fields.Date(readonly=True)
    date_partner_display = fields.Char(string="Partner's Period", compute='_compute_date_range_display', store=True)

    # Data file fields
    data_file = fields.Binary(string='Data File (CSV)', attachment=True)
    data_filename = fields.Char(string='Data Filename')

    # Statistics fields
    total_partners = fields.Integer(string='Total number of clients')
    total_orders = fields.Integer(string='Total number of orders')
    orders_by_state = fields.Text(string='Distribution of orders by status')
    partners_by_success_rate = fields.Text(string='Distribution of customers by success_rate')

    # Chart fields
    partners_by_rate_chart = fields.Binary('Partners by Rate Chart', attachment=True)
    customer_history_graph = fields.Binary('Customer History Graph', attachment=True)
    partner_orders_success_chart = fields.Binary('Partner Orders Success Chart', attachment=True)
    customer_relationship_graph = fields.Binary('Customer Relationship Graph', attachment=True)
    partner_age_success_chart = fields.Binary('Partner Age Success Chart', attachment=True)
    customer_avg_messages_graph = fields.Binary('Customer Average Messages Graph', attachment=True)
    customer_avg_changes_graph = fields.Binary('Customer Average Changes Graph', attachment=True)
    customer_relationship_distribution_graph = fields.Binary('Customer Relationship Distribution Graph',
                                                             attachment=True)
    customer_amount_success_distribution_plot = fields.Binary('Customer Amount Success Distribution Plot',
                                                              attachment=True)
    customer_amount_success_distribution_graph = fields.Binary('Розподіл успішності за сумою замовлення',
                                                               attachment=True)
    customer_order_dependency = fields.Binary('Customer Order Dependency Graph', attachment=True)
    customer_age_dependency = fields.Binary('Customer Age Dependency Graph', attachment=True)
    customer_messages_dependency = fields.Binary('Customer Messages Dependency Graph', attachment=True)
    customer_changes_dependency = fields.Binary('Customer Changes Dependency Graph', attachment=True)

    @api.depends('date_from', 'date_to', 'date_partner_from', 'date_partner_to')
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

                # Build the display string
                parts = []
                if years > 0:
                    parts.append(f"{years} {'year' if years == 1 else 'years'}")
                if months > 0:
                    parts.append(f"{months} {'month' if months == 1 else 'months'}")

                record.date_range_display = f"{' '.join(parts)} (from {record.date_from.strftime('%d.%m.%Y')} to {record.date_to.strftime('%d.%m.%Y')})"
            else:
                record.date_range_display = "Period not defined"

            if record.date_partner_from and record.date_partner_to:
                # Calculate the difference in days
                delta = (record.date_partner_to - record.date_partner_from).days

                # Convert to years and months
                years = delta // 365
                remaining_days = delta % 365
                months = remaining_days // 30

                # Build the display string
                parts = []
                if years > 0:
                    parts.append(f"{years} {'year' if years == 1 else 'years'}")
                if months > 0:
                    parts.append(f"{months} {'month' if months == 1 else 'months'}")

                record.date_partner_display = f"{' '.join(parts)} (from {record.date_from.strftime('%d.%m.%Y')} to {record.date_to.strftime('%d.%m.%Y')})"
            else:
                record.date_partner_display = "Period not defined"

    def action_collect_data(self):
        """Collect all necessary data and save to CSV"""
        self.ensure_one()
        try:
            # Get all orders without date restriction
            query = """
                        WITH partner_stats AS (
                            SELECT 
                                %s * 1000000 + p.id as partner_id,
                                p.create_date as partner_create_date,
                                COUNT(DISTINCT so.id) as total_orders,
                                COUNT(DISTINCT CASE WHEN so.state = 'sale' THEN so.id END) as successful_orders,
                                AVG(so.amount_total) as avg_amount,
                                COUNT(DISTINCT m.id) as total_messages,
                                CAST(
                                    CAST(COUNT(DISTINCT CASE 
                                        WHEN EXISTS (
                                            SELECT 1 FROM mail_tracking_value mtv 
                                            WHERE mtv.mail_message_id = m2.id
                                        ) THEN m2.id 
                                    END) AS DECIMAL(10,2)) / 
                                    NULLIF(COUNT(DISTINCT so.id), 0)
                                    AS DECIMAL(10,2)
                                ) as changes_count,
                                CAST(
                                    CAST(COUNT(DISTINCT CASE WHEN so.state = 'sale' THEN so.id END) AS DECIMAL(10,1)) * 100.0 / 
                                    NULLIF(COUNT(DISTINCT so.id), 0)
                                    AS DECIMAL(10,1)
                                ) as success_rate,
                                MIN(so.date_order::date) as first_order_date,
                                MAX(so.date_order::date) as last_order_date,
                                (MAX(so.date_order::date) - MIN(so.date_order::date)) as partner_order_age_days
                            FROM res_partner p
                            INNER JOIN sale_order so ON so.partner_id = p.id
                            LEFT JOIN mail_message m ON m.res_id = so.id AND m.model = 'sale.order'
                            LEFT JOIN mail_message m2 ON m2.res_id = so.id AND m2.model = 'sale.order'
                            GROUP BY p.id, p.create_date
                        )
                        SELECT 
                            partner_id,
                            partner_create_date,
                            total_orders,
                            successful_orders,
                            success_rate,
                            avg_amount,
                            total_messages,
                            changes_count,
                            first_order_date,
                            last_order_date,
                            partner_order_age_days
                        FROM partner_stats
                    """

            self.env.cr.execute(query, (self.prefix_number,))
            results = self.env.cr.dictfetchall()
            for result in results[:10]:
                print(result)

            if not results:
                raise UserError(_("No data found"))

            # Find min and max dates from sale orders
            date_query = """
                SELECT MIN(date_order)::date as min_date, 
                       MAX(date_order)::date as max_date
                FROM sale_order
            """
            self.env.cr.execute(date_query)
            date_result = self.env.cr.dictfetchone()

            # Convert to CSV
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

            self.write({
                'date_from': date_result['min_date'],
                'date_to': date_result['max_date'],
                'data_file': base64.b64encode(output.getvalue().encode('utf-8')),
                'data_filename': f"{self.env.cr.dbname}_{self.prefix_number}.csv"
            })

            return True

        except Exception as e:
            raise UserError(_("Error collecting data: %s") % str(e))

    def action_compute_statistics(self):
        """Compute basic statistics from the collected data"""
        self.ensure_one()
        if not self.data_file:
            raise UserError(_("Please collect data first"))

        try:
            # Read CSV data
            csv_data = StringIO(base64.b64decode(self.data_file).decode())
            df = pd.read_csv(csv_data)

            # Get min and max dates
            df['partner_create_date'] = pd.to_datetime(df['partner_create_date'])
            min_date = df['partner_create_date'].min()
            max_date = df['partner_create_date'].max()

            # Compute basic statistics
            total_orders = df['total_orders'].sum()
            successful_orders = df['successful_orders'].sum()
            unsuccessful_orders = total_orders - successful_orders

            # Calculate success rate ranges
            success_rate_ranges = defaultdict(int)
            for success_rate in df['success_rate']:
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

            # Format success rate ranges
            success_rate_text = []
            for rate_range in ['100%', '80-99%', '60-79%', '40-59%', '20-39%', '0-19%']:
                if rate_range in success_rate_ranges:
                    success_rate_text.append(f"{rate_range}: {success_rate_ranges[rate_range]} partners")

            stats = {
                'date_partner_from': min_date.date(),
                'date_partner_to': max_date.date(),
                'total_partners': len(df),
                'total_orders': total_orders,
                'orders_by_state': f"""Total Orders: {total_orders}
Successful: {successful_orders} ({(successful_orders / total_orders * 100 if total_orders else 0):.1f}%)
Unsuccessful: {unsuccessful_orders} ({(unsuccessful_orders / total_orders * 100 if total_orders else 0):.1f}%)""",
                'partners_by_success_rate': '\n'.join(success_rate_text)
            }

            self.write(stats)

        except Exception as e:
            raise UserError(_("Error computing statistics: %s") % str(e))

    def action_create_charts(self):
        """Create all charts from the collected data"""
        self.ensure_one()
        if not self.data_file:
            raise UserError(_("Please collect data first"))

        try:
            # Read CSV data
            csv_data = StringIO(base64.b64decode(self.data_file).decode())
            df = pd.read_csv(csv_data)

            print("\nDataFrame columns:")
            print(df.columns)
            print("\nFirst few rows:")
            print(df.head())

            # Create all charts
            charts_data = {
                'partners_by_rate_chart': self._create_partners_by_rate_chart,
                'customer_history_graph': self._create_customer_history_graph,
                'partner_orders_success_chart': self._create_partner_orders_success_chart,
                'customer_relationship_graph': self._create_customer_relationship_graph,
                'partner_age_success_chart': self._create_partner_age_success_chart,
                'customer_avg_messages_graph': self._create_customer_avg_messages_graph,
                'customer_avg_changes_graph': self._create_customer_avg_changes_graph,
                'customer_relationship_distribution_graph': self._create_customer_relationship_distribution_graph,
                'customer_amount_success_distribution_plot': self._create_customer_amount_success_distribution_plot,
                'customer_amount_success_distribution_graph': self._create_customer_amount_success_distribution_graph,
                'customer_order_dependency': self._create_customer_order_dependency,
                'customer_age_dependency': self._create_customer_age_dependency,
                'customer_messages_dependency': self._create_customer_messages_dependency,
                'customer_changes_dependency': self._create_customer_changes_dependency,

            }

            update_vals = {}
            for field_name, chart_function in charts_data.items():
                plt.figure(figsize=(12, 6))
                chart_function(df)
                update_vals[field_name] = self._save_plot_to_binary()
                plt.close()

            self.write(update_vals)

        except Exception as e:
            raise UserError(_("Error creating charts: %s") % str(e))

    def _save_plot_to_binary(self):
        """Save current plot to binary field"""
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
        plt.close()
        return base64.b64encode(buffer.getvalue())

    def _create_partners_by_rate_chart(self, df):
        """Create distribution of partners by success rate"""
        # Створюємо групи для success rate
        bins = [0, 20, 40, 60, 80, 100]
        labels = ['0-19%', '20-39%', '40-59%', '60-79%', '80-99%', '100%']

        # Групуємо дані
        df['success_rate_group'] = pd.cut(df['success_rate'],
                                          bins=[-float('inf')] + bins,
                                          labels=labels,
                                          include_lowest=True)

        # Рахуємо кількість партнерів в кожній групі
        success_rate_counts = df['success_rate_group'].value_counts().sort_index()

        # Створюємо графік
        plt.figure(figsize=(15, 8))
        colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC', '#99CCFF']
        bars = plt.bar(range(len(success_rate_counts)), success_rate_counts, color=colors)

        # Додаємо підписи
        plt.title('Distribution of Partners by Success Rate')
        plt.xlabel('Success Rate Range')
        plt.ylabel('Number of Partners')
        plt.xticks(range(len(success_rate_counts)), success_rate_counts.index, rotation=45)

        # Додаємо значення над стовпчиками
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2., height,
                     f'{int(height):,}',
                     ha='center', va='bottom')

        # Додаємо сітку
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()

    def _create_customer_relationship_distribution_graph(self, df):
        """Create distribution of customer relationship duration"""
        print("\n=== Аналіз даних для графіку ===")
        print("\n1. Початкові дані:")
        print(f"Кількість рядків: {len(df)}")
        print("\nПерші 5 рядків:")
        print(df[['partner_id', 'partner_order_age_days', 'total_orders', 'success_rate']].head())

        # Конвертуємо дні в місяці та забезпечуємо числовий формат
        df['relationship_months'] = pd.to_numeric(df['partner_order_age_days'],
                                                errors='coerce').fillna(0) / 30

        print("\n2. Після конвертації в місяці:")
        print("\nСтатистика relationship_months:")
        print(df['relationship_months'].describe())

        # Створюємо власні межі для груп на основі процентилів
        percentiles = np.percentile(df['relationship_months'].unique(),
                                    np.linspace(0, 100, 11))  # 11 точок для 10 інтервалів

        print("\n3. Процентилі для груп:")
        print(percentiles)

        # Переконуємося, що межі унікальні
        percentiles = np.unique(percentiles)
        if len(percentiles) < 11:
            # Якщо у нас менше унікальних значень, додаємо невеликі відступи
            missing = 11 - len(percentiles)
            step = (percentiles[-1] - percentiles[0]) / (10 * 100)
            for i in range(missing):
                percentiles = np.insert(percentiles, -1, percentiles[-1] + step)

        def format_duration(months):
            months = int(months)
            if months < 12:
                return f"{months}м"
            years = months // 12
            months = months % 12
            if months == 0:
                return f"{years}р"
            return f"{years}р {months}м"

        # Створюємо групи з унікальними межами
        labels = [f"{format_duration(left)}-{format_duration(right)}"
                  for left, right in zip(percentiles[:-1], percentiles[1:])]

        df['relationship_group'] = pd.cut(df['relationship_months'],
                                          bins=percentiles,
                                          labels=labels,
                                          include_lowest=True)

        # Рахуємо статистику для кожної групи
        group_stats = df.groupby('relationship_group').agg({
            'partner_id': 'nunique',  # кількість унікальних клієнтів
            'total_orders': 'sum',    # сума всіх замовлень
            'success_rate': 'mean'    # середня успішність
        }).reset_index()

        # Перейменовуємо колонки для зручності
        group_stats.columns = ['group', 'customers', 'total_orders', 'success_rate']

        print("\n4. Статистика по групах:")
        print(group_stats)

        # Додаємо середню кількість замовлень на клієнта
        group_stats['avg_orders'] = group_stats['total_orders'] / group_stats['customers']

        print("\n5. Фінальна статистика з середніми замовленнями:")
        print(group_stats[['group', 'customers', 'total_orders', 'avg_orders', 'success_rate']])

        # Створення графіку з двома осями
        fig, ax = plt.subplots(figsize=(15, 8))
        x = np.arange(len(group_stats))

        # Основні стовпці - середня кількість замовлень на клієнта
        bars = ax.bar(x, group_stats['avg_orders'], color='#1f77b4', alpha=0.7)
        ax.set_xlabel('Тривалість співпраці з клієнтом')
        ax.set_ylabel('Середня кількість замовлень на клієнта', color='#1f77b4')
        ax.tick_params(axis='y', labelcolor='#1f77b4')

        # Додаємо другу вісь для успішності
        ax2 = ax.twinx()
        success_line = ax2.plot(x, group_stats['success_rate'], 'o-',
                                color='gold', linewidth=2, markersize=8)
        ax2.set_ylabel('Відсоток успішності (%)', color='gold')
        ax2.tick_params(axis='y', labelcolor='gold')
        ax2.set_ylim(0, 100)

        # Налаштовуємо мітки осі X
        ax.set_xticks(x)
        ax.set_xticklabels(group_stats['group'], rotation=45, ha='right')

        # Додаємо підписи значень
        max_height = max(group_stats['avg_orders'])
        spacing = max_height * 0.05  # фіксований відступ 5% від максимальної висоти

        for i, (avg_orders, customers, total_orders) in enumerate(zip(group_stats['avg_orders'],
                                                                      group_stats['customers'],
                                                                      group_stats['total_orders'])):
            # Середня кількість замовлень (блакитним)
            ax.text(i, avg_orders + spacing * 3, f'~{avg_orders:.1f}',
                    ha='center', va='bottom',
                    color='#1f77b4',  # блакитний колір
                    path_effects=[
                        PathEffects.withStroke(linewidth=3, foreground='white')
                    ])

            # Кількість клієнтів (чорним)
            ax.text(i, avg_orders + spacing * 2, f'n={customers}',
                    ha='center', va='bottom',
                    color='black',
                    path_effects=[
                        PathEffects.withStroke(linewidth=3, foreground='white')
                    ])

            # Загальна кількість замовлень (синім)
            ax.text(i, avg_orders + spacing, f'({int(total_orders)})',
                    ha='center', va='bottom',
                    color='#1f77b4',  # синій колір
                    path_effects=[
                        PathEffects.withStroke(linewidth=3, foreground='white')
                    ])

        # Збільшуємо верхню межу графіка для підписів
        ax.set_ylim(0, max_height * 1.4)

        # Додаємо підписи успішності
        for i, success in enumerate(group_stats['success_rate']):
            ax2.text(i, success + 2, f'{success:.1f}%',
                     ha='center', va='bottom', color='black',
                     path_effects=[
                         PathEffects.withStroke(linewidth=3, foreground='white')
                     ])

        # Додаємо легенду
        custom_lines = [
            bars.patches[0],  # стовпчики для середньої кількості замовлень
            Line2D([0], [0], color='gold', marker='o', linewidth=2, markersize=8),  # лінія успішності
            Line2D([0], [0], color='black', marker='s', linewidth=0, markersize=8),  # маркер для кількості клієнтів
            Line2D([0], [0], color='#1f77b4', marker='s', linewidth=0, markersize=8)  # маркер для кількості замовлень
        ]
        ax.legend(custom_lines, [
            'Середня кількість замовлень',
            'Відсоток успішності',
            'Кількість клієнтів (n=X)',
            'Кількість замовлень (Y)'
        ], loc='upper left')

        plt.title('Залежність кількості замовлень від тривалості співпраці з клієнтом\n' +
                  'n=X - кількість унікальних клієнтів, (Y) - загальна кількість замовлень')
        plt.tight_layout()

    def _create_customer_amount_success_distribution_plot(self, df):
        """Create distribution of customer amount success"""
        print("\n=== Starting customer amount success distribution analysis ===")
        print("DataFrame columns:", df.columns.tolist())
        print("\nFirst few rows of DataFrame:")
        print(df.head())

        # Конвертуємо суму в числовий формат
        print("\nConverting avg_amount to numeric...")
        df['avg_amount'] = pd.to_numeric(df['avg_amount'], errors='coerce')
        print("Unique values in avg_amount after conversion:", df['avg_amount'].unique()[:10])

        # Відфільтруємо від'ємні значення
        df = df[df['avg_amount'] >= 0]
        print("\nNumber of rows after filtering negative values:", len(df))

        # Форматуємо мітки груп
        def format_amount(interval):
            left = int(interval.left)
            right = int(interval.right)

            def format_number(num):
                if num >= 1000000:
                    return f"{num / 1000000:.1f}M"
                elif num >= 1000:
                    return f"{num / 1000:.0f}K"
                return str(int(num))

            return f'{format_number(left)}-{format_number(right)}'

        # Створюємо 20 груп з приблизно однаковою кількістю клієнтів
        print("\nGrouping data...")
        customer_stats = df.groupby('partner_id').agg({
            'avg_amount': 'mean',
            'success_rate': 'mean'  # відсоток успішності
        }).reset_index()

        # Створюємо групи
        customer_stats['amount_group'] = pd.qcut(customer_stats['avg_amount'],
                                               q=20,
                                               duplicates='drop')

        # Отримуємо межі інтервалів та створюємо нові лейбли
        intervals = customer_stats['amount_group'].cat.categories
        labels = [format_amount(interval) for interval in intervals]

        # Застосовуємо нові лейбли
        customer_stats['amount_group'] = pd.qcut(customer_stats['avg_amount'],
                                               q=20,
                                               labels=labels,
                                               duplicates='drop')

        print("\nCalculating group statistics...")
        # Рахуємо статистику для кожної групи
        group_stats = customer_stats.groupby('amount_group').agg({
            'partner_id': 'count',  # кількість клієнтів
            'success_rate': 'mean',  # середній відсоток успішності
            'avg_amount': 'mean'  # середня сума замовлення
        }).reset_index()

        print("\nGroup statistics:")
        print(group_stats)

        # Створення графіку з двома осями
        fig, ax = plt.subplots(figsize=(15, 8))
        x = np.arange(len(group_stats))

        # Основні стовпці - середня сума замовлення
        bars = ax.bar(x, group_stats['avg_amount'], color='#1f77b4', alpha=0.7)
        ax.set_xlabel('Середня сума замовлення, грн')
        ax.set_ylabel('Середня сума замовлення, грн', color='#1f77b4')
        ax.tick_params(axis='y', labelcolor='#1f77b4')

        # Додаємо другу вісь для успішності
        ax2 = ax.twinx()
        success_line = ax2.plot(x, group_stats['success_rate'], 'o-',
                              color='gold', linewidth=2, markersize=8)
        ax2.set_ylabel('Середній відсоток успішності (%)', color='gold')
        ax2.tick_params(axis='y', labelcolor='gold')
        ax2.set_ylim(0, 100)

        # Налаштовуємо мітки осі X
        ax.set_xticks(x)
        ax.set_xticklabels(group_stats['amount_group'], rotation=45)

        # Додаємо підписи значень
        for i, (amount, partners) in enumerate(zip(group_stats['avg_amount'],
                                                 group_stats['partner_id'])):
            # Підпис середньої суми
            ax.text(i, amount, f'~{amount / 1000:.0f}K',
                   ha='center', va='bottom', color='#1f77b4')
            # Підпис кількості клієнтів
            ax.text(i, 0, f'n={partners}',
                   ha='center', va='top', color='gray')

        # Додаємо підписи успішності
        for i, success in enumerate(group_stats['success_rate']):
            ax2.text(i, success + 2, f'{success:.1f}%',
                     ha='center', va='bottom', color='black')

        # Додаємо легенду
        from matplotlib.lines import Line2D
        custom_lines = [bars.patches[0], Line2D([0], [0], color='gold', marker='o', linewidth=2, markersize=8)]
        ax.legend(custom_lines, ['Середня сума замовлення', 'Середній % успішності'], loc='upper left')

        plt.title('Залежність успішності від середньої суми замовлення клієнта')
        plt.tight_layout()

    def _create_customer_history_graph(self, df):
        """Create customer history analysis"""
        # Створюємо групи за кількістю замовлень
        conditions = [
            (df['total_orders'] == 1),
            (df['total_orders'].between(2, 5)),
            (df['total_orders'].between(6, 10)),
            (df['total_orders'].between(11, 20)),
            (df['total_orders'] >= 21)
        ]
        categories = ['Нові', '2-5 замовлень', '6-10 замовлень', '11-20 замовлень', '20+ замовлень']
        df['category'] = np.select(conditions, categories)

        # Рахуємо статистику по групах
        group_stats = df.groupby('category').agg(
            partners_count=('partner_id', 'count'),
            total_orders_sum=('total_orders', 'sum'),
            success_rate=('success_rate', 'mean')
        ).reindex(categories)

        # Створюємо графік з двома осями
        fig, ax1 = plt.subplots(figsize=(15, 8))

        # Налаштовуємо відступи для графіка
        plt.subplots_adjust(right=0.85)

        # Створюємо другу вісь
        ax2 = ax1.twinx()
        ax3 = ax1.twinx()
        ax3.spines["right"].set_position(("axes", 1.1))

        # Ширина стовпців
        width = 0.35
        x = np.arange(len(categories))

        # Створюємо стовпці для кількості партнерів (темно-синій)
        partners_bars = ax1.bar(x - width / 2, group_stats['partners_count'], width,
                                label='Кількість клієнтів', color='#1f77b4')

        # Створюємо стовпці для кількості замовлень (світло-синій)
        orders_bars = ax2.bar(x + width / 2, group_stats['total_orders_sum'], width,
                              label='Кількість замовлень', color='#63a7e6')

        # Додаємо лінію успішності
        success_line = ax3.plot(x, group_stats['success_rate'], 'o-',
                                color='gold', label='Відсоток успішності',
                                linewidth=2, markersize=8, zorder=5)

        # Налаштовуємо осі
        ax1.set_xlabel('Категорія', fontsize=10, labelpad=10)
        ax1.set_ylabel('Кількість клієнтів', color='#1f77b4', fontsize=10)
        ax2.set_ylabel('Кількість замовлень', color='#63a7e6', fontsize=10)
        ax3.set_ylabel('Відсоток успішності (%)', color='gold', fontsize=10)

        # Встановлюємо межі для осей
        ax3.set_ylim(0, 100)

        # Встановлюємо кольори для міток осей
        ax1.tick_params(axis='y', labelcolor='#1f77b4')
        ax2.tick_params(axis='y', labelcolor='#63a7e6')
        ax3.tick_params(axis='y', labelcolor='gold')

        # Встановлюємо мітки осі X
        ax1.set_xticks(x)
        ax1.set_xticklabels(categories, rotation=0)

        # Додаємо значення над стовпцями та точками
        for i, v in enumerate(group_stats['partners_count']):
            ax1.text(i - width / 2, v, f'{int(v):,}',
                     ha='center', va='bottom', fontsize=10)

        for i, v in enumerate(group_stats['total_orders_sum']):
            ax2.text(i + width / 2, v, f'{int(v):,}',
                     ha='center', va='bottom', fontsize=10)

        for i, v in enumerate(group_stats['success_rate']):
            ax3.text(i, v + 2, f'{v:.1f}%',
                     ha='center', va='bottom', color='black', fontsize=10)

        # Налаштовуємо легенду
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        lines3, labels3 = ax3.get_legend_handles_labels()

        ax1.legend(lines1 + lines2 + lines3,
                   labels1 + labels2 + labels3,
                   loc='upper right', bbox_to_anchor=(1.25, 1))

        # Встановлюємо заголовок
        plt.title('Розподіл клієнтів та замовлень за кількістю попередніх замовлень',
                  pad=20, fontsize=12)

        # Додаємо сітку
        ax1.grid(True, linestyle='--', alpha=0.3, zorder=0)

        # Налаштовуємо відступи
        plt.tight_layout()

    def _create_partner_orders_success_chart(self, df):
        """Create partner orders vs success rate chart"""
        plt.figure(figsize=(12, 6))

        # Підготовка даних
        data = df[['total_orders', 'success_rate']].copy()
        total_partners = len(data)

        # Сортуємо за кількістю замовлень
        data = data.sort_values('total_orders')

        # Визначаємо кількість груп (зменшуємо якщо партнерів мало)
        num_groups = min(30, total_partners // 20)  # Мінімум 20 партнерів на групу
        if num_groups < 5:  # Якщо груп менше 5, встановлюємо мінімум 5 груп
            num_groups = 5

        # Розраховуємо розмір кожної групи
        group_size = total_partners // num_groups
        remainder = total_partners % num_groups

        # Ініціалізуємо результат
        result = {
            'ranges': [],
            'rates': [],
            'partners_count': [],
            'orders_count': []
        }

        # Розбиваємо на групи
        start_idx = 0
        for i in range(num_groups):
            current_group_size = group_size + (1 if i < remainder else 0)
            if current_group_size == 0:
                break

            end_idx = start_idx + current_group_size
            group_data = data.iloc[start_idx:end_idx]

            # Рахуємо статистику для групи
            min_orders = group_data['total_orders'].min()
            max_orders = group_data['total_orders'].max()
            avg_success_rate = group_data['success_rate'].mean()
            total_orders = group_data['total_orders'].sum()

            # Форматуємо діапазон
            range_str = f'{int(min_orders)}-{int(max_orders)}'

            # Додаємо дані до результату
            result['ranges'].append(range_str)
            result['rates'].append(avg_success_rate)
            result['partners_count'].append(len(group_data))
            result['orders_count'].append(total_orders)

            start_idx = end_idx

        # Створюємо точковий графік
        x_points = []
        y_points = []
        counts = []
        orders = []
        for i, (rate, count, order_count) in enumerate(
                zip(result['rates'], result['partners_count'], result['orders_count'])):
            if count > 0:
                x_points.append(i)
                y_points.append(rate)
                counts.append(count)
                orders.append(order_count)

        # Створюємо градієнт кольорів від червоного до зеленого в залежності від success rate
        colors = ['#ff4d4d' if rate < 50 else '#00cc00' for rate in y_points]
        sizes = [max(80, min(150, count / 2)) for count in counts]  # Розмір точки залежить від кількості партнерів

        # Малюємо точки
        plt.scatter(x_points, y_points, s=sizes, alpha=0.6, c=colors)

        # Додаємо анотації для кожної точки
        for i, (x, y) in enumerate(zip(x_points, y_points)):
            # Кількість замовлень зверху точки (чорний колір)
            plt.annotate(f'{int(orders[i])}',
                         xy=(x, y),
                         xytext=(0, 10),  # 10 пікселів вгору
                         textcoords='offset points',
                         ha='center',
                         va='bottom',
                         fontsize=8,
                         color='black')

            # Кількість партнерів знизу точки (синій колір)
            plt.annotate(f'{int(counts[i])}',
                         xy=(x, y),
                         xytext=(0, -10),  # 10 пікселів вниз
                         textcoords='offset points',
                         ha='center',
                         va='top',
                         fontsize=8,
                         color='blue')

        plt.title(
            'Успішність замовлень за кількістю замовлень партнера\n' +
            '(розмір точки показує відносну кількість партнерів,\n' +
            'чорне число - кількість замовлень, синє число - кількість партнерів)',
            pad=20, fontsize=12)
        plt.xlabel('Діапазон кількості замовлень', fontsize=10)
        plt.ylabel('Успішність (%)', fontsize=10)

        # Налаштовуємо осі
        plt.ylim(-5, 105)

        # Показуємо всі мітки, якщо їх менше 10, інакше кожну другу
        if len(result['ranges']) <= 10:
            plt.xticks(range(len(result['ranges'])), result['ranges'],
                       rotation=45, ha='right')
        else:
            plt.xticks(range(len(result['ranges']))[::2],
                       [result['ranges'][i] for i in range(0, len(result['ranges']), 2)],
                       rotation=45, ha='right')

        plt.grid(True, linestyle='--', alpha=0.7)

        # Додаємо легенду
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w',
                       markerfacecolor='#ff4d4d', markersize=10,
                       label='Успішність < 50%'),
            plt.Line2D([0], [0], marker='o', color='w',
                       markerfacecolor='#00cc00', markersize=10,
                       label='Успішність ≥ 50%'),
            plt.Line2D([0], [0], marker='s', color='black',
                       markersize=8, linestyle='none',
                       label='Кількість замовлень'),
            plt.Line2D([0], [0], marker='s', color='blue',
                       markersize=8, linestyle='none',
                       label='Кількість партнерів')
        ]
        plt.legend(handles=legend_elements, loc='upper right')

        plt.tight_layout()

    def _create_customer_relationship_graph(self, df):
        """Create customer relationship duration analysis"""
        # Встановлюємо відображення всіх стовпців
        pd.set_option('display.max_columns', None)
        # Можна також налаштувати ширину виводу
        pd.set_option('display.width', None)

        # Тепер виводимо дані
        print('DATA FRAME PROCESSOR')
        print(df.head(10))
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # Конвертуємо дні в місяці
        df['relationship_months'] = df['partner_order_age_days'] / 30

        # Функція для категоризації терміну співпраці
        def get_relationship_category(months):
            if months < 2:
                return 'Нові'
            elif 2 <= months < 6:
                return '2-6 місяців'
            elif 6 <= months < 12:
                return '6-12 місяців'
            elif 12 <= months < 24:
                return '1-2 роки'
            else:
                return '2+ роки'

        # Визначаємо порядок категорій
        category_order = ['Нові', '2-6 місяців', '6-12 місяців', '1-2 роки', '2+ роки']

        # Застосовуємо категоризацію
        df['relationship_category'] = df['relationship_months'].apply(get_relationship_category)

        # Створюємо DataFrame для клієнтів (беремо тільки унікальних клієнтів)
        clients_df = df.drop_duplicates('partner_id', keep='last')

        # Рахуємо кількість клієнтів в кожній категорії
        category_counts = clients_df['relationship_category'].value_counts()
        category_counts = category_counts.reindex(category_order)

        # Рахуємо кількість замовлень в кожній категорії
        # Використовуємо агрегацію для підрахунку total_orders для кожної категорії
        orders_counts = df.groupby('relationship_category')['total_orders'].sum()
        orders_counts = orders_counts.reindex(category_order)

        # Рахуємо відсоток успішності для кожної категорії
        success_by_category = df.groupby('relationship_category').agg(
            successful=('successful_orders', 'sum'),
            total=('total_orders', 'sum')
        )
        success_by_category['success_rate'] = (success_by_category['successful'] / success_by_category['total']) * 100
        success_by_category = success_by_category['success_rate'].reindex(category_order)

        # Створюємо позиції для стовпчиків
        x = np.arange(len(category_counts))
        width = 0.35

        # Створюємо стовпчики для клієнтів (зліва від центру)
        bars1 = ax1.bar(x - width / 2, category_counts.values, width,
                        color='#1f77b4', label='Кількість клієнтів')
        ax1.set_xlabel('Термін співпраці')
        ax1.set_ylabel('Кількість клієнтів', color='#1f77b4')
        ax1.tick_params(axis='y', labelcolor='#1f77b4')

        # Створюємо другу вісь для замовлень
        ax3 = ax1.twinx()
        ax3.spines['right'].set_position(('outward', 60))
        bars2 = ax3.bar(x + width / 2, orders_counts.values, width,
                        color='skyblue', label='Кількість замовлень')
        ax3.set_ylabel('Кількість замовлень', color='blue')
        ax3.tick_params(axis='y', labelcolor='blue')

        # Створюємо третю вісь для відсотка успішності
        ax2 = ax1.twinx()
        success_line = ax2.plot(x, success_by_category.values, 'o-',
                                color='gold', linewidth=2, markersize=8)
        ax2.set_ylabel('Відсоток успішності (%)', color='black')
        ax2.tick_params(axis='y', labelcolor='black')
        ax2.set_ylim(0, 100)

        # Налаштовуємо мітки осі X
        ax1.set_xticks(x)
        ax1.set_xticklabels(category_order, rotation=45)
        ax1.set_title('Розподіл клієнтів та замовлень відносно терміну співпраці')

        # Додаємо підписи значень для клієнтів
        for i, v in enumerate(category_counts.values):
            ax1.text(x[i] - width / 2, v, f'{int(v):,}',
                     ha='center', va='bottom', color='#1f77b4')

        # Додаємо підписи значень для замовлень
        for i, v in enumerate(orders_counts.values):
            ax3.text(x[i] + width / 2, v, f'{int(v):,}',
                     ha='center', va='bottom', color='blue')

        # Додаємо підписи для відсотка успішності
        for i, v in enumerate(success_by_category.values):
            ax2.text(i, v, f'{v:.1f}%',
                     ha='center', va='bottom', color='black')

        # Додаємо легенду
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax3.get_legend_handles_labels()
        lines3 = [Line2D([0], [0], color='gold', marker='o', linestyle='-')]
        ax1.legend(lines1 + lines2 + lines3,
                   labels1 + labels2 + ['Відсоток успішності'],
                   loc='upper right')

        plt.tight_layout()


    def _create_partner_age_success_chart(self, df):
        """Create partner age vs success rate chart"""

        # Функція для створення міток вікових діапазонів
        def get_age_range(days):
            if days < 30:
                return f"{days}d"
            elif days < 365:
                months = days // 30
                return f"{months}m"
            else:
                years = days // 365
                return f"{years}y"

        # Створюємо діапазони для групування
        df['age_range'] = df['partner_order_age_days'].apply(get_age_range)

        # Групуємо дані
        grouped = df.groupby('age_range').agg({
            'success_rate': 'mean',
            'total_orders': 'sum',
            'partner_id': 'nunique'  # Додаємо підрахунок унікальних партнерів
        }).reset_index()

        # Створюємо допоміжну колонку для сортування
        def get_sort_key(x):
            value = int(x[:-1])
            unit = x[-1]
            if unit == 'd':
                return value
            elif unit == 'm':
                return value * 30
            else:  # 'y'
                return value * 365

        grouped['sort_key'] = grouped['age_range'].apply(get_sort_key)
        grouped = grouped.sort_values('sort_key')

        # Виводимо статистику для кожної точки
        print("\nСтатистика по точках:")
        print("Діапазон | Замовлення | Партнери | Успішність")
        print("-" * 50)
        for _, row in grouped.iterrows():
            print(
                f"{row['age_range']:8} | {int(row['total_orders']):10} | {int(row['partner_id']):8} | {row['success_rate']:.1f}%")

        grouped = grouped.drop('sort_key', axis=1)

        plt.figure(figsize=(15, 8))

        # Фільтруємо точки з нульовою кількістю ордерів
        mask = grouped['total_orders'] > 0
        x_points = range(len(grouped[mask]))
        y_points = grouped[mask]['success_rate'].values
        counts = grouped[mask]['total_orders'].values
        ranges = grouped[mask]['age_range'].values

        # Створюємо градієнт кольорів від червоного до зеленого в залежності від success rate
        colors = ['#ff4d4d' if rate < 50 else '#00cc00' for rate in y_points]
        sizes = [max(80, min(150, count / 2)) for count in counts]

        # Малюємо точки
        scatter = plt.scatter(x_points, y_points, s=sizes, alpha=0.6, c=colors)

        # Додаємо анотації для кожної точки
        for i, (x, y) in enumerate(zip(x_points, y_points)):
            # Кількість замовлень зверху точки (чорний колір)
            plt.annotate(f'{int(counts[i])}',
                         xy=(x, y),
                         xytext=(0, 10),  # 10 пікселів вгору
                         textcoords='offset points',
                         ha='center',
                         va='bottom',
                         fontsize=8,
                         color='black')

            # Кількість клієнтів знизу точки (синій колір)
            plt.annotate(f'{int(grouped[mask]["partner_id"].iloc[i])}',
                         xy=(x, y),
                         xytext=(0, -10),  # 10 пікселів вниз
                         textcoords='offset points',
                         ha='center',
                         va='top',
                         fontsize=8,
                         color='blue')

        plt.title(
            'Успішність замовлень за віком партнера\n' +
            '(розмір точки показує відносну кількість замовлень,\n' +
            'чорне число - кількість замовлень, синє число - кількість клієнтів)',
            pad=20, fontsize=12)
        plt.xlabel('Вік партнера (d=дні, m=місяці, y=роки)', fontsize=10)
        plt.ylabel('Успішність (%)', fontsize=10)

        # Налаштовуємо осі
        plt.ylim(-5, 105)

        # Показуємо всі мітки, якщо їх менше 10, інакше кожну другу
        if len(ranges) <= 10:
            plt.xticks(x_points, ranges, rotation=45, ha='right')
        else:
            plt.xticks(x_points[::2], ranges[::2], rotation=45, ha='right')

        plt.grid(True, linestyle='--', alpha=0.7)

        # Додаємо горизонтальні лінії
        plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
        plt.axhline(y=50, color='gray', linestyle='--', alpha=0.3)
        plt.axhline(y=100, color='gray', linestyle='-', alpha=0.3)

        # Додаємо легенду
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w',
                       markerfacecolor='#ff4d4d', markersize=10,
                       label='Успішність < 50%'),
            plt.Line2D([0], [0], marker='o', color='w',
                       markerfacecolor='#00cc00', markersize=10,
                       label='Успішність ≥ 50%'),
            plt.Line2D([0], [0], marker='s', color='black',
                       markersize=8, linestyle='none',
                       label='Кількість замовлень'),
            plt.Line2D([0], [0], marker='s', color='blue',
                       markersize=8, linestyle='none',
                       label='Кількість клієнтів')
        ]
        plt.legend(handles=legend_elements, loc='upper right')

    def _create_customer_avg_messages_graph(self, df):
        """Create average messages analysis"""
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # Конвертуємо total_messages в числовий формат
        df['total_messages'] = pd.to_numeric(df['total_messages'], errors='coerce').fillna(0)

        # Функція категоризації
        def get_message_category(avg_messages):
            if pd.isna(avg_messages) or avg_messages == 0:
                return 'Без повідомлень'
            elif 0 < avg_messages <= 3:
                return '1-3 повідомлення'
            elif 3 < avg_messages <= 7:
                return '4-7 повідомлень'
            elif 7 < avg_messages <= 15:
                return '8-15 повідомлень'
            elif 15 < avg_messages <= 20:
                return '15-20 повідомлень'
            elif 20 < avg_messages <= 50:
                return '20-50 повідомлень'
            elif 50 < avg_messages <= 75:
                return '50-75 повідомлень'
            else:
                return '75+ повідомлень'

        # Визначаємо порядок категорій
        category_order = ['Без повідомлень', '1-3 повідомлення', '4-7 повідомлень',
                         '8-15 повідомлень', '15-20 повідомлень', '20-50 повідомлень',
                         '50-75 повідомлень', '75+ повідомлень']

        # Категоризуємо клієнтів
        df['message_category'] = df['total_messages'].apply(get_message_category)

        # Рахуємо статистику по категоріях
        category_stats = df.groupby('message_category').agg({
            'partner_id': 'count',  # кількість клієнтів
            'total_orders': 'sum',  # кількість замовлень
            'success_rate': 'mean'  # середній відсоток успішності
        }).reindex(category_order)

        # Замінюємо NaN на 0
        category_stats = category_stats.fillna(0)

        # Створюємо позиції для стовпчиків
        x = np.arange(len(category_order))
        width = 0.35

        # Створюємо стовпчики для клієнтів
        bars1 = ax1.bar(x - width / 2, category_stats['partner_id'], width,
                       color='#1f77b4', label='Кількість клієнтів')
        ax1.set_ylabel('Кількість клієнтів', color='#1f77b4')
        ax1.tick_params(axis='y', labelcolor='#1f77b4')

        # Створюємо другу вісь для замовлень
        ax3 = ax1.twinx()
        ax3.spines['right'].set_position(('outward', 60))
        bars2 = ax3.bar(x + width / 2, category_stats['total_orders'], width,
                       color='skyblue', label='Кількість замовлень')
        ax3.set_ylabel('Кількість замовлень', color='blue')
        ax3.tick_params(axis='y', labelcolor='blue')

        # Створюємо третю вісь для відсотка успішності
        ax2 = ax1.twinx()
        success_line = ax2.plot(x, category_stats['success_rate'], 'o-',
                              color='gold', linewidth=2, markersize=8,
                              label='Відсоток успішності')
        ax2.set_ylabel('Відсоток успішності (%)')
        ax2.set_ylim(0, 100)

        # Налаштовуємо мітки осі X
        ax1.set_xticks(x)
        ax1.set_xticklabels(category_order, rotation=45, ha='right')

        # Додаємо підписи значень для клієнтів
        for i, v in enumerate(category_stats['partner_id']):
            if not pd.isna(v):  # перевіряємо на NaN
                ax1.text(x[i] - width / 2, v, f'{int(v):,}',
                        ha='center', va='bottom', color='#1f77b4')

        # Додаємо підписи значень для замовлень
        for i, v in enumerate(category_stats['total_orders']):
            if not pd.isna(v):  # перевіряємо на NaN
                ax3.text(x[i] + width / 2, v, f'{int(v):,}',
                        ha='center', va='bottom', color='blue')

        # Додаємо підписи для відсотка успішності
        for i, v in enumerate(category_stats['success_rate']):
            if not pd.isna(v):  # перевіряємо на NaN
                ax2.text(x[i], v + 1, f'{v:.1f}%',
                        ha='center', va='bottom', color='black')

        # Налаштовуємо заголовок та легенду
        plt.title('Аналіз клієнтів за середньою кількістю повідомлень')
        fig.tight_layout()

    def _create_customer_avg_changes_graph(self, df):
        """Create average changes analysis"""
        fig, ax1 = plt.subplots(figsize=(15, 8))

        # Конвертуємо changes_count в числовий формат
        df['changes_count'] = pd.to_numeric(df['changes_count'], errors='coerce').fillna(0)

        # Створення категорій на основі середньої кількості змін на замовлення
        def get_changes_category(changes):
            if changes == 0:
                return '0. Без змін'
            elif changes <= 0.5:
                return '1. 0.1-0.5 змін'
            elif changes <= 1:
                return '2. 0.5-1 зміна'
            elif changes <= 2:
                return '3. 1-2 зміни'
            elif changes <= 3:
                return '4. 2-3 зміни'
            elif changes <= 4:
                return '5. 3-4 зміни'
            elif changes <= 5:
                return '6. 4-5 змін'
            else:
                return '7. 5+ змін'

        # Словник для відображення категорій без номерів
        display_categories = {
            '0. Без змін': 'Без змін',
            '1. 0.1-0.5 змін': '0.1-0.5 змін',
            '2. 0.5-1 зміна': '0.5-1 зміна',
            '3. 1-2 зміни': '1-2 зміни',
            '4. 2-3 зміни': '2-3 зміни',
            '5. 3-4 зміни': '3-4 зміни',
            '6. 4-5 змін': '4-5 змін',
            '7. 5+ змін': '5+ змін'
        }

        df['category'] = df['changes_count'].apply(get_changes_category)

        # Агрегація даних за категоріями
        category_stats = df.groupby('category').agg({
            'partner_id': 'count',
            'changes_count': 'mean',
            'success_rate': 'mean',
            'total_orders': 'sum'
        }).reset_index()

        # Сортування категорій у правильному порядку
        category_order = ['0. Без змін', '1. 0.1-0.5 змін', '2. 0.5-1 зміна', '3. 1-2 зміни',
                          '4. 2-3 зміни', '5. 3-4 зміни', '6. 4-5 змін', '7. 5+ змін']
        category_stats['category'] = pd.Categorical(category_stats['category'],
                                                    categories=category_order,
                                                    ordered=True)
        category_stats = category_stats.sort_values('category')

        # Створення графіку
        x = np.arange(len(category_stats))
        width = 0.35  # ширина стовпчиків

        # Створюємо стовпчики для клієнтів
        bars1 = ax1.bar(x - width / 2, category_stats['partner_id'], width,
                        color='#1f77b4', label='Кількість клієнтів')
        ax1.set_ylabel('Кількість клієнтів', color='#1f77b4')
        ax1.tick_params(axis='y', labelcolor='#1f77b4')

        # Створюємо другу вісь для замовлень
        ax3 = ax1.twinx()
        ax3.spines['right'].set_position(('outward', 60))
        bars2 = ax3.bar(x + width / 2, category_stats['total_orders'], width,
                        color='skyblue', label='Кількість замовлень')
        ax3.set_ylabel('Кількість замовлень', color='blue')
        ax3.tick_params(axis='y', labelcolor='blue')

        # Створюємо третю вісь для відсотка успішності
        ax2 = ax1.twinx()
        success_line = ax2.plot(x, category_stats['success_rate'], 'o-',
                                color='gold', linewidth=2, markersize=8,
                                label='Відсоток успішності')
        ax2.set_ylabel('Відсоток успішності (%)')
        ax2.set_ylim(0, 100)

        # Налаштовуємо мітки осі X
        ax1.set_xticks(x)
        ax1.set_xticklabels([display_categories[cat] for cat in category_stats['category']], rotation=45, ha='right')

        # Додаємо підписи значень для клієнтів
        for i, v in enumerate(category_stats['partner_id']):
            percentage = v / category_stats['partner_id'].sum() * 100
            ax1.text(i - width / 2, v, f'{int(v):,}\n({percentage:.1f}%)',
                     ha='center', va='bottom', color='#1f77b4')

        # Додаємо підписи значень для замовлень
        for i, v in enumerate(category_stats['total_orders']):
            ax3.text(i + width / 2, v, f'{int(v):,}',
                     ha='center', va='bottom', color='blue')

        # Додаємо підписи для відсотка успішності
        for i, v in enumerate(category_stats['success_rate']):
            ax2.text(i, v + 1, f'{v:.1f}%',
                     ha='center', va='bottom', color='black')

        # Додаємо середню кількість змін на замовлення для кожної категорії
        for i, avg_changes in enumerate(category_stats['changes_count']):
            ax1.text(i, 0, f'~{avg_changes:.2f}', ha='center', va='top')

        plt.title('Аналіз клієнтів за середньою кількістю змін на одне замовлення')
        fig.tight_layout()

    def _create_customer_amount_success_distribution_graph(self, df):
        print("\n=== Starting analysis ===")

        # Закриваємо всі відкриті фігури перед створенням нової
        plt.close('all')

        fig, ax = plt.subplots(figsize=(15, 8))

        # Конвертуємо суму в числовий формат
        df['avg_amount'] = pd.to_numeric(df['avg_amount'], errors='coerce')

        # Відфільтруємо від'ємні значення
        df = df[df['avg_amount'] >= 0]

        # Розраховуємо середню суму замовлень для кожного клієнта
        customer_stats = df.groupby('partner_id').agg({
            'avg_amount': 'mean',
            'success_rate': 'mean'  # відсоток успішності
        }).reset_index()

        # Видаляємо викиди (суми більше 99-го перцентиля)
        amount_99th = np.percentile(customer_stats['avg_amount'], 99)
        customer_stats = customer_stats[customer_stats['avg_amount'] <= amount_99th]

        # Створюємо власні межі для груп
        amount_bins = [
            0,  # мінімум
            100,  # до 100 грн
            500,  # до 500 грн
            1000,  # до 1000 грн
            2000,  # до 2000 грн
            5000,  # до 5000 грн
            10000,  # до 10000 грн
            20000,  # до 20000 грн
            float('inf')  # решта
        ]

        # Створюємо мітки для груп
        labels = [
            '0-100',
            '100-500',
            '500-1K',
            '1K-2K',
            '2K-5K',
            '5K-10K',
            '10K-20K',
            '20K+'
        ]

        # Застосовуємо групування
        customer_stats['amount_group'] = pd.cut(
            customer_stats['avg_amount'],
            bins=amount_bins,
            labels=labels,
            include_lowest=True
        )

        # Рахуємо статистику для кожної групи
        group_stats = customer_stats.groupby('amount_group').agg({
            'partner_id': 'count',  # кількість клієнтів
            'success_rate': 'mean',  # середній відсоток успішності
            'avg_amount': 'mean'  # середня сума замовлення
        }).reset_index()

        # Створення графіку з двома осями
        x = np.arange(len(group_stats))

        # Основні стовпці - середня сума замовлення
        bars = ax.bar(x, group_stats['avg_amount'], color='#1f77b4', alpha=0.7)
        ax.set_xlabel('Середня сума замовлення, грн')
        ax.set_ylabel('Середня сума замовлення, грн', color='#1f77b4')
        ax.tick_params(axis='y', labelcolor='#1f77b4')

        # Додаємо другу вісь для успішності
        ax2 = ax.twinx()
        success_line = ax2.plot(x, group_stats['success_rate'], 'o-',
                                color='gold', linewidth=2, markersize=8)
        ax2.set_ylabel('Середній відсоток успішності (%)', color='gold')
        ax2.tick_params(axis='y', labelcolor='gold')
        ax2.set_ylim(0, 100)

        # Налаштовуємо мітки осі X
        ax.set_xticks(x)
        ax.set_xticklabels(group_stats['amount_group'], rotation=45)

        # Додаємо підписи значень
        for i, (amount, customers) in enumerate(zip(group_stats['avg_amount'],
                                                    group_stats['partner_id'])):
            # Підпис середньої суми
            if amount >= 1000:
                amount_text = f'~{amount / 1000:.0f}K'
            else:
                amount_text = f'~{amount:.0f}'
            ax.text(i, amount, amount_text,
                    ha='center', va='bottom', color='#1f77b4')
            # Підпис кількості клієнтів
            ax.text(i, 0, f'n={customers}',
                    ha='center', va='top', color='gray')

        # Додаємо підписи успішності
        for i, success in enumerate(group_stats['success_rate']):
            ax2.text(i, success + 2, f'{success:.1f}%',
                     ha='center', va='bottom', color='black')

        # Додаємо легенду
        custom_lines = [bars.patches[0], Line2D([0], [0], color='gold', marker='o', linewidth=2, markersize=8)]
        ax.legend(custom_lines, ['Середня сума замовлення', 'Середній % успішності'], loc='upper left')

        plt.title('Залежність успішності від середньої суми замовлення клієнта')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()


    def _create_customer_order_dependency(self, df):
        """Create a scatter plot showing dependency between success rate and total orders"""
        plt.figure(figsize=(10, 6))
        plt.scatter(df['total_orders'], df['success_rate'], s=3, alpha=0.5)
        plt.xlabel('Total Orders')
        plt.ylabel('Success Rate (%)')
        plt.title('Customer Success Rate vs Total Orders')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()


    def _create_customer_age_dependency(self, df):
        plt.figure(figsize=(10, 6))
        df['partner_order_age_months'] = df['partner_order_age_days'] // 30
        plt.scatter(df['partner_order_age_months'], df['success_rate'], s=3, alpha=0.5)
        plt.xlabel('Partner Age (months)')
        plt.ylabel('Success Rate (%)')
        plt.title('Customer Success Rate vs Partner Age')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()

    def _create_customer_messages_dependency(self, df):
        plt.figure(figsize=(10, 6))
        plt.scatter(df['total_messages'], df['success_rate'], s=3, alpha=0.5)
        plt.xlabel('Messages')
        plt.ylabel('Success Rate (%)')
        plt.title('Customer Success Rate vs Messages')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()


    def _create_customer_changes_dependency(self, df):
        plt.figure(figsize=(10, 6))

        plt.scatter(df['changes_count'], df['success_rate'], s=3, alpha=0.5)
        plt.xlabel('Changes')
        plt.ylabel('Success Rate (%)')
        plt.title('Customer Success Rate vs Changes')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
