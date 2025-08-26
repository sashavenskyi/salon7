# -*- coding: utf-8 -*-
"""
Created on Tue Aug 26 16:17:26 2025

@author: olve
"""

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

# Завантаження підсумкових даних
@st.cache_data
def load_summary(file_path):
    if not os.path.exists(file_path):
        st.warning("Файл з підсумковими даними не знайдено. Будь ласка, запустіть скрипт збору даних.")
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Помилка при завантаженні підсумкових даних: {e}")
        return {}

# Завантажуємо дані
df = load_data('all_reports.csv')
summary_data = load_summary('summary.json')

if not df.empty:
    df['Date'] = pd.to_datetime(df['Date'])
    
    st.title("Аналіз звітів з Telegram-каналу")
    st.markdown("---")

    # Фінансовий підсумок дня
    st.header("Фінансовий підсумок дня")
    
    col1, col2, col3 = st.columns(3)
    
    total_revenue = df[df['Revenue'] > 0]['Revenue'].sum()
    total_expenses = df[df['Revenue'] < 0]['Revenue'].sum()
    
    col1.metric("Загальний дохід", f"{total_revenue:,.0f} грн")
    col2.metric("Загальні витрати", f"{total_expenses:,.0f} грн")
    col3.metric("Всього за день (чистий дохід)", f"{total_revenue + total_expenses:,.0f} грн")
    
    st.markdown("---")

    # Відображення підсумкових даних з файлу
    if summary_data:
        st.subheader("Показники з файлу звіту")
        st.json(summary_data)
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
        master_revenue = filtered_df.groupby('Master')['Revenue'].sum().sort_values(ascending=False)
        fig, ax = plt.subplots()
        sns.barplot(x=master_revenue.index, y=master_revenue.values, ax=ax)
        plt.xticks(rotation=45, ha='right')
        plt.ylabel("Дохід (грн)")
        st.pyplot(fig)
        
        st.markdown("---")
        
        # Аналіз доходів за послугами
        st.header("Дохід за послугами")
        service_revenue = filtered_df.groupby('Service')['Revenue'].sum().sort_values(ascending=False).head(10)
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