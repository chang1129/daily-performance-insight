# -*- coding: utf-8 -*-
"""
Created on Fri Dec 15 14:55:12 2023

@author: chang
"""

import os
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import smtplib
from email.message import EmailMessage
import pandas as pd
import numpy as np
import yfinance as yf
import logging
from logging import config
from log_config import LOGGING_CONFIG

config.dictConfig(LOGGING_CONFIG)
my_logger = logging.getLogger('custom_logger')

def get_date_available(date,data):
    date_pd = pd.to_datetime(date)
    
    if date_pd < data.index[0]:
        return np.nan
    
    while not date_pd in data.index:
        date_pd -= timedelta(days=1)
        
    return date_pd

def calculate_performance(date, data):
    
    if isinstance(date,pd.Timestamp):
        return data['Close'].iloc[-1] / data['Close'].loc[date] - 1
    else:
        return date

def get_ticker_performance(ticker):

    end_date = date.today() + timedelta(days=1)
    start_date = end_date - relativedelta(years=4)

    try:
        data = yf.download(ticker, start=start_date, end=end_date)
        
        one_day_ago = get_date_available(end_date - relativedelta(days=2), data)
        one_day_ago = data.index[-2] if one_day_ago == data.index[-1] else one_day_ago
        one_week_ago = get_date_available(end_date - relativedelta(weeks=1), data)
        one_month_ago = get_date_available(end_date - relativedelta(months=1), data)
        ytd = get_date_available(datetime(end_date.year, 12, 31) - relativedelta(years=1) , data)
        one_year_ago = get_date_available(end_date - relativedelta(years=1) + relativedelta(days=1), data)
        three_years_ago = get_date_available(end_date - relativedelta(years=3) + relativedelta(days=1), data)

        latest_price = data['Close'].iloc[-1]
        daily_performance = calculate_performance(one_day_ago, data)
        weekly_performance = calculate_performance(one_week_ago, data)
        monthly_performance = calculate_performance(one_month_ago, data)
        ytd_performance = calculate_performance(ytd, data)
        yearly_performance = calculate_performance(one_year_ago, data)
        threeyears_performance = calculate_performance(three_years_ago, data)

    except Exception as e:
        my_logger.error(f"Error fetching performance for {ticker}: {e}")
        raise

    try:
        ticker_object = yf.Ticker(ticker)
        try:
            company_name = ticker_object.info['longName']
        except KeyError:
            company_name = ticker_object.info['shortName']

    except Exception as e:
        my_logger.error(f"Error fetching company name for {ticker}: {e}")
        raise
        
    result = {
        'name': company_name,
        'ticker': ticker,
        'latest_price': latest_price,
        'daily': daily_performance,
        'weekly': weekly_performance,
        'monthly': monthly_performance,
        'YTD': ytd_performance,
        '1_year':yearly_performance,
        '3_years':threeyears_performance
    }

    return result

def color_font(number):
    if pd.isnull(number):
        return 'color: black'
    else:
        color = 'red' if float(number) < 0 else 'green'
        return f'color:{color}'

def add_style(df):
    formatting = {
        'latest_price': '{0:,.2f}',
        'daily': '{:.2%}',
        'weekly': '{:.2%}',
        'monthly': '{:.2%}',
        'YTD': '{:.2%}',
        '1_year': '{:.2%}',
        '3_years': '{:.2%}'
    }
    styled_df = df.style.format(formatting, na_rep='').applymap(color_font, subset=list(formatting.keys()))
    styled_df.set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#E2EFDA'), ('font-weight', 'bold'),('width', '100px')]},
        {'selector': 'th, td', 'props': [('border', '1px solid black'), ('text-align', 'center')]},
        {'selector': '', 'props': [('border-collapse', 'collapse')]}
    ]).hide(axis='index')

    return styled_df

def send_email(styled_df_market, styled_df_stock, styled_df_watchlist):
    EMAIL_ADDRESS = os.environ.get('EMAIL_USER')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASS')
    EMAIL_RECIPIENT = os.environ.get('EMAIL_RECEIVE')
    today_date = date.today()
    
    email_body = f"""\
    <html>
      <body>
        <h2>{today_date}</h2>
        <h2>Market</h2>
        {styled_df_market.to_html(na_rep='-')}
        <h2>Portfolio</h2>
        {styled_df_stock.to_html(na_rep='-')}
        <h2>Watchlist</h2>
        {styled_df_watchlist.to_html(na_rep='-')}
      </body>
    </html>
    """
    
    msg = EmailMessage()
    msg['Subject'] = f'Daily Performance Insight_{today_date}'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_RECIPIENT
    msg.add_alternative(email_body, subtype='html')
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        my_logger.info(f"Email sent successfully on {today_date}")
    except Exception as e:
        my_logger.error(f"Error sending email: {e}")
        raise
        
def fetch_performance(tickers):
    performances = []
    for ticker in tickers:
        try:
            performances.append(get_ticker_performance(ticker))
        except Exception as e:
            my_logger.warning(f"Skipping {ticker} due to error: {e}")
    return pd.DataFrame.from_dict(performances)

def lambda_handler(event, context):
    market = ['^GSPC', '^DJI', '^IXIC', 'BZ=F', 'GC=F', '^TNX', 'BTC-USD', 'ETH-USD']
    stock = ['AMD', 'AAPL', 'MSFT', 'TSLA', 'IVV', 'BABA', '5106.KL', '5168.KL', '7160.KL', '5211PA.KL', '5292.KL']
    watchlist = ['AMZN','GOOG', 'NVDA','ARM' , 'MU','SNOW','QCOM','META','V',
                  'D05.SI','O39.SI','U11.SI', '373220.KS', '096770.KS', '6752.T', '002594.SZ']
    
    df_market = fetch_performance(market)
    df_stock = fetch_performance(stock)
    df_watchlist = fetch_performance(watchlist)
    
    styled_df_market = add_style(df_market)
    styled_df_stock = add_style(df_stock)
    styled_df_watchlist = add_style(df_watchlist)
    send_email(styled_df_market, styled_df_stock, styled_df_watchlist)


