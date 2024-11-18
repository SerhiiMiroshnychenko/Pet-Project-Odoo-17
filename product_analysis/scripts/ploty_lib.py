import plotly.graph_objects as go
import datetime


def plot_step_quantity_with_labels(dates, quantities, dates_formatted):
    """
    Будує ступінчастий графік із простором нижче 0 по осі Y за допомогою Plotly.
    Додає точки на місцях зламу графіка та підписи дат біля них.

    :param dates: Список об'єктів datetime.date для осі X.
    :param quantities: Список числових значень для осі Y.
    :param dates_formatted: Список рядків у форматі 'YYYY-MM-DD' для підписів точок на графіку.
    """
    # Перетворюємо дати у формат, сумісний із Plotly
    dates = [date.isoformat() for date in dates]

    # Створюємо ступінчастий графік
    fig = go.Figure()

    # Додаємо лінію графіка
    fig.add_trace(go.Scatter(
        x=dates,
        y=quantities,
        mode='lines+markers',
        line=dict(shape='hv', color='green'),
        marker=dict(size=8, color='red'),
        name='Кількість'
    ))

    # Додаємо підписи для точок
    for x, y, label in zip(dates, quantities, dates_formatted):
        fig.add_trace(go.Scatter(
            x=[x],
            y=[y],
            mode='text',
            text=[label],
            textposition="top center",
            textfont=dict(color='blue', size=10),
            showlegend=False
        ))

    # Налаштування осей
    fig.update_layout(
        title="Графік кількості за датами (ступінчастий)",
        xaxis=dict(
            title="Дати",
            tickformat="%b %Y",
            tickangle=45
        ),
        yaxis=dict(
            title="Кількість",
            range=[min(quantities) - 10, max(quantities) + 10]
        ),
        plot_bgcolor='white',
        legend=dict(yanchor="top", y=1, xanchor="left", x=0),
        margin=dict(l=50, r=50, t=50, b=50)
    )

    # Додаємо сітку
    fig.update_xaxes(showgrid=True, gridcolor='lightgrey')
    fig.update_yaxes(showgrid=True, gridcolor='lightgrey')

    # Відображаємо графік
    fig.show()


# Виклик функції через конструкцію if __name__ == "__main__":
if __name__ == "__main__":
    dates = [datetime.date(2023, 11, 19), datetime.date(2024, 6, 30), datetime.date(2024, 11, 18)]
    quantities = [0.0, 65.0, 65.0]
    dates_formatted = [date.strftime('%Y.%m.%d') for date in dates]
    plot_step_quantity_with_labels(dates, quantities, dates_formatted)
