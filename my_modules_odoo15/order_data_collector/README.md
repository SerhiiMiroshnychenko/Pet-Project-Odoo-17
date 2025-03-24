# Order Data Collector

Модуль Odoo для збору та аналізу даних про замовлення клієнтів з фокусом на показники успішності.

## Опис

Модуль `order_data_collector` призначений для збору та аналізу даних про замовлення (sale.order) в Odoo. Він дозволяє відстежувати успішність замовлень та аналізувати історичні дані про поведінку клієнтів.

## Основні функції

### 1. Збір даних (Collect Data)

Модуль збирає наступні дані про замовлення:
- **ID замовлення** (з префіксом) - унікальний ідентифікатор замовлення
- **Успішність замовлення** (0/1) - 1 якщо замовлення успішне (state == 'sale'), 0 в іншому випадку
- **Дата створення** - дата та час створення замовлення
- **ID партнера** (з префіксом) - унікальний ідентифікатор клієнта
- **Сума замовлення** - сума поточного замовлення
- **Кількість повідомлень** - кількість повідомлень в поточному замовленні
- **Кількість змін** - кількість змін в поточному замовленні
- **Відсоток успішності клієнта** - відсоток успішних замовлень клієнта на момент створення поточного замовлення
- **Загальна кількість замовлень** - кількість попередніх замовлень клієнта
- **Вік клієнта в днях** - різниця між датою поточного та першого замовлення клієнта
- **Середня сума замовлень** - середня сума всіх попередніх замовлень клієнта
- **Середня сума успішних замовлень** - середня сума успішних попередніх замовлень клієнта
- **Середня сума неуспішних замовлень** - середня сума неуспішних попередніх замовлень клієнта
- **Загальна кількість повідомлень** - загальна кількість повідомлень у попередніх замовленнях клієнта
- **Середня кількість повідомлень в успішних замовленнях** - середня кількість повідомлень в успішних попередніх замовленнях клієнта
- **Середня кількість повідомлень в неуспішних замовленнях** - середня кількість повідомлень в неуспішних попередніх замовленнях клієнта
- **Середня кількість змін** - середня кількість змін на одне попереднє замовлення клієнта
- **Середня кількість змін в успішних замовленнях** - середня кількість змін в успішних попередніх замовленнях клієнта
- **Середня кількість змін в неуспішних замовленнях** - середня кількість змін в неуспішних попередніх замовленнях клієнта

Дані зберігаються у CSV файл з назвою `{database_name}_{prefix_number}.csv`.

### 2. Розрахунок статистики (Compute Statistics)

Після збору даних можна розрахувати статистику натиснувши кнопку "Compute Statistics". Обчислюються наступні показники:

- Загальна кількість замовлень
- Кількість успішних замовлень
- Кількість неуспішних замовлень
- Кількість унікальних клієнтів
- Середній показник успішності замовлень

## Технічні деталі

### Структура даних

#### Формат DataFrame
```
******************************
DataFrame columns: ['order_id', 'is_successful', 'create_date', 'partner_id', 'order_amount', 'order_messages', 'order_changes', 'partner_success_rate', 'partner_total_orders', 'partner_order_age_days', 'partner_avg_amount', 'partner_success_avg_amount', 'partner_fail_avg_amount', 'partner_total_messages', 'partner_success_avg_messages', 'partner_fail_avg_messages', 'partner_avg_changes', 'partner_success_avg_changes', 'partner_fail_avg_changes']

First few rows of DataFrame:
   order_id  is_successful                 create_date  partner_id  order_amount  order_messages  order_changes  partner_success_rate  partner_total_orders  partner_order_age_days  partner_avg_amount  partner_success_avg_amount  partner_fail_avg_amount  partner_total_messages  partner_success_avg_messages  partner_fail_avg_messages  partner_avg_changes  partner_success_avg_changes  partner_fail_avg_changes
0   1000001              1  2017-07-29 07:48:26.812523     1024555       5235.66              25             22                   0.0                     0                       0                 0.0                         0.0                      0.0                       0                           0.0                        0.0                  0.0                          0.0                       0.0
1   1000002              1  2017-07-29 07:54:09.954757     1026247        876.96              10              5                   0.0                     0                       0                 0.0                         0.0                      0.0                       0                           0.0                        0.0                  0.0                          0.0                       0.0
2   1000003              1  2017-07-29 08:04:13.162858     1024797       3012.77               7              4                   0.0                     0                       0                 0.0                         0.0                      0.0                       0                           0.0                        0.0                  0.0                          0.0                       0.0
3   1000004              1  2017-07-29 08:11:38.086709     1024943        621.34              10              6                   0.0                     0                       0                 0.0                         0.0                      0.0                       0                           0.0                        0.0                  0.0                          0.0                       0.0
4   1000005              1  2017-07-29 08:15:05.548616     1024776        813.12               6              3                   0.0                     0                       0                 0.0                         0.0                      0.0                       0                           0.0                        0.0                  0.0                          0.0                       0.0
******************************                  
```

#### Формат CSV файлу
CSV файл має такий же формат як і DataFrame. Приклад перших рядків файлу:

```csv
order_id,is_successful,create_date,partner_id,order_amount,order_messages,order_changes,partner_success_rate,partner_total_orders,partner_order_age_days,partner_avg_amount,partner_success_avg_amount,partner_fail_avg_amount,partner_total_messages,partner_success_avg_messages,partner_fail_avg_messages,partner_avg_changes,partner_success_avg_changes,partner_fail_avg_changes
1000001,1,2017-07-29 07:48:26.812523,1024555,100.0,2,1,0.0,0,0,0.0,0.0,0.0,0,0.0,0.0,0.0,0.0,0.0
1000002,1,2017-07-29 07:54:09.954757,1026247,150.0,3,2,0.0,0,0,0.0,0.0,0.0,0,0.0,0.0,0.0,0.0,0.0
1000003,1,2017-07-29 08:04:13.162858,1024797,200.0,1,0,0.0,0,0,0.0,0.0,0.0,0,0.0,0.0,0.0,0.0,0.0
1000004,1,2017-07-29 08:11:38.086709,1024943,75.0,4,3,0.0,0,0,0.0,0.0,0.0,0,0.0,0.0,0.0,0.0,0.0
1000005,1,2017-07-29 08:15:05.548616,1024776,125.0,2,1,0.0,0,0,0.0,0.0,0.0,0,0.0,0.0,0.0,0.0,0.0
```

Де:
- `order_id` - ID замовлення з префіксом (prefix_number * 1000000 + order.id)
- `is_successful` - індикатор успішності (1 = успішне, 0 = неуспішне)
- `create_date` - дата та час створення замовлення
- `partner_id` - ID партнера з префіксом (prefix_number * 1000000 + partner.id)
- `order_amount` - сума поточного замовлення
- `order_messages` - кількість повідомлень в поточному замовленні
- `order_changes` - кількість змін в поточному замовленні
- `partner_success_rate` - відсоток успішних замовлень клієнта на момент створення (0-100)
- `partner_total_orders` - загальна кількість замовлень клієнта до поточного замовлення
- `partner_order_age_days` - вік клієнта в днях (різниця між датою поточного та першого замовлення клієнта)
- `partner_avg_amount` - середня сума всіх попередніх замовлень клієнта
- `partner_success_avg_amount` - середня сума успішних попередніх замовлень клієнта
- `partner_fail_avg_amount` - середня сума неуспішних попередніх замовлень клієнта
- `partner_total_messages` - загальна кількість повідомлень у попередніх замовленнях клієнта
- `partner_success_avg_messages` - середня кількість повідомлень в успішних попередніх замовленнях клієнта
- `partner_fail_avg_messages` - середня кількість повідомлень в неуспішних попередніх замовленнях клієнта
- `partner_avg_changes` - середня кількість змін на одне попереднє замовлення клієнта
- `partner_success_avg_changes` - середня кількість змін в успішних попередніх замовленнях клієнта
- `partner_fail_avg_changes` - середня кількість змін в неуспішних попередніх замовленнях клієнта

### SQL запит

Для збору даних використовується SQL запит з CTE (Common Table Expression):

```sql
WITH order_data AS (
                    SELECT 
                        so.id as order_id,
                        so.create_date as create_date,
                        so.partner_id,
                        so.state,
                        so.amount_total as order_amount,
                        CASE WHEN so.state = 'sale' THEN 1 ELSE 0 END as is_successful,
                        (
                            SELECT COUNT(DISTINCT m.id)
                            FROM mail_message m 
                            WHERE m.res_id = so.id AND m.model = 'sale.order'
                        ) as order_messages,
                        (
                            SELECT COUNT(DISTINCT CASE 
                                WHEN EXISTS (
                                    SELECT 1 FROM mail_tracking_value mtv 
                                    WHERE mtv.mail_message_id = m.id
                                ) THEN m.id 
                            END)
                            FROM mail_message m
                            WHERE m.res_id = so.id AND m.model = 'sale.order'
                        ) as order_changes,
                        (
                            SELECT COALESCE(
                                CAST(COUNT(CASE WHEN s2.state = 'sale' THEN 1 END) AS DECIMAL(10,2)) /
                                NULLIF(COUNT(*), 0),
                                0
                            )
                            FROM sale_order s2
                            WHERE s2.partner_id = so.partner_id
                            AND s2.create_date < so.create_date
                        ) as partner_success_rate,
                        (
                            SELECT COUNT(*)
                            FROM sale_order s2
                            WHERE s2.partner_id = so.partner_id
                            AND s2.create_date < so.create_date
                        ) as partner_total_orders,
                        (
                            SELECT 
                                EXTRACT(DAY FROM (so.create_date - MIN(s2.create_date)))::INTEGER
                            FROM sale_order s2
                            WHERE s2.partner_id = so.partner_id
                            AND s2.create_date < so.create_date
                        ) as partner_order_age_days,
                        (
                            SELECT COALESCE(AVG(s2.amount_total), 0)
                            FROM sale_order s2
                            WHERE s2.partner_id = so.partner_id
                            AND s2.create_date < so.create_date
                        ) as partner_avg_amount,
                        (
                            SELECT COALESCE(AVG(s2.amount_total), 0)
                            FROM sale_order s2
                            WHERE s2.partner_id = so.partner_id
                            AND s2.create_date < so.create_date
                            AND s2.state = 'sale'
                        ) as partner_success_avg_amount,
                        (
                            SELECT COALESCE(AVG(s2.amount_total), 0)
                            FROM sale_order s2
                            WHERE s2.partner_id = so.partner_id
                            AND s2.create_date < so.create_date
                            AND s2.state != 'sale'
                        ) as partner_fail_avg_amount,
                        (
                            SELECT COUNT(DISTINCT m.id)
                            FROM sale_order s2
                            LEFT JOIN mail_message m ON m.res_id = s2.id AND m.model = 'sale.order'
                            WHERE s2.partner_id = so.partner_id
                            AND s2.create_date < so.create_date
                        ) as partner_total_messages,
                        (
                            SELECT COALESCE(AVG(message_count), 0)
                            FROM (
                                SELECT s2.id, COUNT(DISTINCT m.id) as message_count
                                FROM sale_order s2
                                LEFT JOIN mail_message m ON m.res_id = s2.id AND m.model = 'sale.order'
                                WHERE s2.partner_id = so.partner_id
                                AND s2.create_date < so.create_date
                                AND s2.state = 'sale'
                                GROUP BY s2.id
                            ) as t
                        ) as partner_success_avg_messages,
                        (
                            SELECT COALESCE(AVG(message_count), 0)
                            FROM (
                                SELECT s2.id, COUNT(DISTINCT m.id) as message_count
                                FROM sale_order s2
                                LEFT JOIN mail_message m ON m.res_id = s2.id AND m.model = 'sale.order'
                                WHERE s2.partner_id = so.partner_id
                                AND s2.create_date < so.create_date
                                AND s2.state != 'sale'
                                GROUP BY s2.id
                            ) as t
                        ) as partner_fail_avg_messages,
                        (
                            SELECT COALESCE(
                                CAST(COUNT(DISTINCT CASE 
                                    WHEN EXISTS (
                                        SELECT 1 FROM mail_tracking_value mtv 
                                        WHERE mtv.mail_message_id = m2.id
                                    ) THEN m2.id 
                                END) AS DECIMAL(10,2)) /
                                NULLIF(COUNT(DISTINCT s2.id), 0),
                                0
                            )
                            FROM sale_order s2
                            LEFT JOIN mail_message m2 ON m2.res_id = s2.id AND m2.model = 'sale.order'
                            WHERE s2.partner_id = so.partner_id
                            AND s2.create_date < so.create_date
                        ) as partner_avg_changes,
                        (
                            SELECT COALESCE(AVG(change_count), 0)
                            FROM (
                                SELECT s2.id,
                                COUNT(DISTINCT CASE 
                                    WHEN EXISTS (
                                        SELECT 1 FROM mail_tracking_value mtv 
                                        WHERE mtv.mail_message_id = m2.id
                                    ) THEN m2.id 
                                END) as change_count
                                FROM sale_order s2
                                LEFT JOIN mail_message m2 ON m2.res_id = s2.id AND m2.model = 'sale.order'
                                WHERE s2.partner_id = so.partner_id
                                AND s2.create_date < so.create_date
                                AND s2.state = 'sale'
                                GROUP BY s2.id
                            ) as t
                        ) as partner_success_avg_changes,
                        (
                            SELECT COALESCE(AVG(change_count), 0)
                            FROM (
                                SELECT s2.id,
                                COUNT(DISTINCT CASE 
                                    WHEN EXISTS (
                                        SELECT 1 FROM mail_tracking_value mtv 
                                        WHERE mtv.mail_message_id = m2.id
                                    ) THEN m2.id 
                                END) as change_count
                                FROM sale_order s2
                                LEFT JOIN mail_message m2 ON m2.res_id = s2.id AND m2.model = 'sale.order'
                                WHERE s2.partner_id = so.partner_id
                                AND s2.create_date < so.create_date
                                AND s2.state != 'sale'
                                GROUP BY s2.id
                            ) as t
                        ) as partner_fail_avg_changes
                    FROM sale_order so
                    ORDER BY so.create_date
                )
                SELECT
                    %s * 1000000 + order_id as order_id_with_prefix,
                    is_successful,
                    create_date,
                    %s * 1000000 + partner_id as partner_id_with_prefix,
                    order_amount,
                    order_messages,
                    order_changes,
                    COALESCE(partner_success_rate * 100, 0) as partner_success_rate,
                    COALESCE(partner_total_orders, 0) as partner_total_orders,
                    COALESCE(partner_order_age_days, 0) as partner_order_age_days,
                    COALESCE(partner_avg_amount, 0) as partner_avg_amount,
                    COALESCE(partner_success_avg_amount, 0) as partner_success_avg_amount,
                    COALESCE(partner_fail_avg_amount, 0) as partner_fail_avg_amount,
                    COALESCE(partner_total_messages, 0) as partner_total_messages,
                    COALESCE(partner_success_avg_messages, 0) as partner_success_avg_messages,
                    COALESCE(partner_fail_avg_messages, 0) as partner_fail_avg_messages,
                    COALESCE(partner_avg_changes, 0) as partner_avg_changes,
                    COALESCE(partner_success_avg_changes, 0) as partner_success_avg_changes,
                    COALESCE(partner_fail_avg_changes, 0) as partner_fail_avg_changes
                FROM order_data
```

### Залежності

- Odoo модулі:
  - sale_crm
- Python бібліотеки:
  - pandas

## Встановлення

1. Скопіюйте модуль в директорію addons вашого Odoo серверу
2. Оновіть список модулів в Odoo
3. Встановіть модуль "Order Data Collector"

## Використання

1. Перейдіть до меню "Order Data Collector"
2. Створіть новий запис, вказавши назву та префікс
3. Натисніть кнопку "Collect Data" для збору даних
4. Після успішного збору даних натисніть "Compute Statistics" для розрахунку статистики
5. Завантажте CSV файл для подальшого аналізу даних

## Автор

Serhii Miroshnychenko
https://github.com/SerhiiMiroshnychenko
