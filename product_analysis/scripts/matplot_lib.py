import matplotlib.pyplot as plt
import datetime
from matplotlib.dates import DateFormatter


def plot_step_quantity_with_labels(dates, quantities, dates_formatted):
    """
    Будує ступінчастий графік із простором нижче 0 по осі Y.
    Додає точки на місцях зламу графіка та підписи дат біля них.

    :param dates: Список об'єктів datetime.date для осі X.
    :param quantities: Список числових значень для осі Y.
    :param dates_formatted: Список рядків у форматі 'YYYY-MM-DD' для підписів точок на графіку.
    """
    # Створюємо ступінчастий графік
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.step(dates, quantities, where='post', color='g', label='Кількість', linewidth=2)

    # Додаємо точки у місцях зламу
    ax.scatter(dates, quantities, color='red', zorder=5, label='Точки зламу')

    # Додаємо підписи біля кожної точки
    for x, y, label in zip(dates, quantities, dates_formatted):
        ax.annotate(label, xy=(x, y), xytext=(5, 5), textcoords="offset points",
                    fontsize=10, color='blue', ha='left', va='bottom')

    # Форматуємо осі
    ax.set_title("Графік кількості за датами (ступінчастий)", fontsize=14)
    ax.set_xlabel("Дати", fontsize=12)
    ax.set_ylabel("Кількість", fontsize=12)
    ax.xaxis.set_major_formatter(DateFormatter("%b %Y"))
    ax.set_ylim(min(quantities) - 10, max(quantities) + 10)  # Додаємо простір зверху і знизу
    ax.grid(True, linestyle='--', alpha=0.7)

    # Основне форматування осі X
    plt.xticks(rotation=45)
    ax.legend()

    # Відображаємо графік
    plt.tight_layout()
    plt.show()


# Виклик функції через конструкцію if __name__ == "__main__":
if __name__ == "__main__":
    dates = [datetime.date(2023, 11, 19), datetime.date(2024, 6, 30), datetime.date(2024, 11, 18)]
    quantities = [0.0, 65.0, 65.0]
    dates_formatted = [date.strftime('%Y.%m.%d') for date in dates]
    plot_step_quantity_with_labels(dates, quantities, dates_formatted)
