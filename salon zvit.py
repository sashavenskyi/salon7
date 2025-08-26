import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json

# Завантаження даних
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path):
        st.error(f"Файл '{file_path}' не знайдено. Будь ласка, запустіть скрипт 'telegram_collector.py' для збору даних.")
        return pd.DataFrame()
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        # Очищення даних від невідомих символів
        df = df.replace({r'[^\w\s\-\,\.\(\)\/\%\:]': ''}, regex=True)
        return df
    except Exception as e:
        st.error(f"Помилка при завантаженні файлу: {e}")
        return pd.DataFrame()

# Завантаження підсумкових даних з усіх файлів
@st.cache_data
def load_all_summaries(folder_path):
    summary_data = []
    for file_name in os.listdir(folder_path):
        if file_name.startswith('summary_') and file_name.endswith('.json'):
            file_path = os.path.join(folder_path, file_name)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    date_str = file_name.replace('summary_', '').replace('.json', '')
                    data['Date'] = pd.to_datetime(date_str)
                    summary_data.append(data)
            except Exception as e:
                st.warning(f"Помилка при завантаженні файлу {file_name}: {e}")
    return pd.DataFrame(summary_data)


# Завантажуємо дані
df = load_data('all_reports.csv')
summary_df = load_all_summaries('.')

if not df.empty:
    df['Date'] = pd.to_datetime(df['Date'])
    
    st.title("Аналіз звітів з Telegram-каналу")
    st.markdown("---")

    # Відображення підсумків у вигляді таблиці
    if not summary_df.empty:
        st.header("Фінансові підсумки")
        summary_df['Date'] = pd.to_datetime(summary_df['Date'])
        summary_df.set_index('Date', inplace=True)
        st.dataframe(summary_df.sort_index(ascending=False).T.style.format("{:,.0f} грн"))
        st.markdown("---")

    # Фінансовий підсумок дня
    if not summary_df.empty:
        st.header("Останній фінансовий звіт")
        latest_summary = summary_df.iloc[-1].T
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("Залишок, який був", f"{latest_summary.get('Залишок який був', 0):,.0f} грн")
        col2.metric("Всього за день", f"{latest_summary.get('Всього за день', 0):,.0f} грн")
        col3.metric("Залишок в сейфі", f"{latest_summary.get('Залишок в сейфі', 0):,.0f} грн")
        
        st.markdown("---")


    # Фільтри
    st.sidebar.header("Фільтри")
    start_date = st.sidebar.date_input("Початкова дата", df['Date'].min())
    end_date = st.sidebar.date_input("Кінцева дата", df['Date'].max())

    filtered_df = df[(df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date))]
    
    if filtered_df.empty:
        st.warning("За вибраний період дані відсутні.")
    else:
        # Виведення даних
        st.header("Огляд даних")
        st.dataframe(filtered_df)

        st.markdown("---")
        
        # Аналіз доходів за майстрами
        st.header("Дохід за майстрами")
        master_revenue = filtered_df[filtered_df['Section'] != 'Expenses'].groupby('Master')['Revenue'].sum().sort_values(ascending=False)
        fig, ax = plt.subplots()
        sns.barplot(x=master_revenue.index, y=master_revenue.values, ax=ax)
        plt.xticks(rotation=45, ha='right')
        plt.ylabel("Дохід (грн)")
        st.pyplot(fig)
        
        st.markdown("---")
        
        # Аналіз доходів за послугами
        st.header("Дохід за послугами")
        service_revenue = filtered_df[filtered_df['Section'] != 'Expenses'].groupby('Service')['Revenue'].sum().sort_values(ascending=False).head(10)
        fig, ax = plt.subplots()
        sns.barplot(x=service_revenue.index, y=service_revenue.values, ax=ax)
        plt.xticks(rotation=90, ha='right')
        plt.ylabel("Дохід (грн)")
        st.pyplot(fig)

        st.markdown("---")
        
        # Розподіл платежів
        st.header("Розподіл типів оплати")
        payment_counts = filtered_df['PaymentMethod'].value_counts()
        fig, ax = plt.subplots()
        ax.pie(payment_counts, labels=payment_counts.index, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        st.pyplot(fig)
