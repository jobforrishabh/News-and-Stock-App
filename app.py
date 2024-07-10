from flask import Flask, render_template, request
import requests
import pandas as pd
from datetime import datetime, timedelta
from tabulate import tabulate

app = Flask(__name__)

class FinancialData:
    def __init__(self, stock_api_key, news_api):
        self.stock_api_key = stock_api_key #Get API from https://www.alphavantage.co
        self.news_api = news_api  #Get API from https://newsapi.org

    def fetch_news_data(self, company, date):
        api_key = self.news_api
        url = f"https://newsapi.org/v2/everything?q={company}&from={date}&sortBy=publishedAt&apiKey={api_key}"

        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])
            return articles[:10]  # Return only top 10 articles
        else:
            return []

    def get_stock_data(self, symbol, days=365):
        start_date = datetime.now() - timedelta(days=days)
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "apikey": self.stock_api_key
        }
        try:
            response = requests.get(url, params=params, verify= False)
            response.raise_for_status()  # Raise exception for bad responses (e.g., 404)
            data = response.json()
            time_series = data.get("Time Series (Daily)", {})
            if time_series:
                df = pd.DataFrame.from_dict(time_series, orient='index')
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                df = df.apply(pd.to_numeric)
                df = df[df.index >= start_date]
                return df
            else:
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None

    def calculate_averages(self, df):
        if df is None:
            return None

        monthly_avg = df['4. close'].resample('M').mean()
        quarterly_avg = df['4. close'].resample('Q').mean()
        yearly_avg = df['4. close'].resample('A').mean()

        monthly_high = df['2. high'].resample('M').max()
        monthly_low = df['3. low'].resample('M').min()

        monthly_data = pd.DataFrame({
            'Date': monthly_avg.index,
            'High': monthly_high.values,
            'Low': monthly_low.values,
            'Average': monthly_avg.values
        })

        quarterly_high = df['2. high'].resample('Q').max()
        quarterly_low = df['3. low'].resample('Q').min()
        quarterly_data = pd.DataFrame({
            'Date': quarterly_avg.index,
            'High': quarterly_high.values,
            'Low': quarterly_low.values,
            'Average': quarterly_avg.values
        })

        yearly_high = df['2. high'].resample('A').max()
        yearly_low = df['3. low'].resample('A').min()
        yearly_data = pd.DataFrame({
            'Date': yearly_avg.index,
            'High': yearly_high.values,
            'Low': yearly_low.values,
            'Average': yearly_avg.values
        })

        return {
            'monthly_data': tabulate(monthly_data, headers='keys', tablefmt='html', showindex=False),
            'quarterly_data': tabulate(quarterly_data, headers='keys', tablefmt='html', showindex=False),
            'yearly_data': tabulate(yearly_data, headers='keys', tablefmt='html', showindex=False)
        }


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        company_name = request.form['company_name']
        date = request.form['date']
        symbol = request.form['symbol']

        financial_data = FinancialData(stock_api_key="USE_YOUR_API",
        news_api="USE_YOUR_API")

        # Fetch news data
        news_data = financial_data.fetch_news_data(company_name, date)

        # Fetch stock data
        stock_data_df = financial_data.get_stock_data(symbol, 365)

        if stock_data_df is not None:
            averages_data = financial_data.calculate_averages(stock_data_df)
        else:
            averages_data = None

        return render_template('index.html', news_data=news_data, averages_data=averages_data)

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
