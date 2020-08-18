import mysql.connector
import pandas as pd
from pandas import Series, DataFrame
from collections import defaultdict
from datetime import date, time, datetime
import matplotlib.pyplot as plt
#import mplfinance as mpf
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
import numpy as np

"""
Allows you to query stock database and perform research/analysis.
"Lines" are provided in the dictionary format (most recent value as 0, next recent as 1, etc.)
"""
#*****************GET CONNECTION AND DEFINE PARAMETERS**********************************
mydb = mysql.connector.connect(
	host="127.0.0.1",           
	user="root",           
	password="EptL@Rl!1",       
	database = "Stock_Prices", 
)
table='5_min_prices'
ticker_list = []
ticker_list =['A', 'AAL', 'AAPL', 'ABBV', 'ABT', 'ACN', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP', 'AFL', 'AGG', 'AGN', 'ALGN', 'ALL', 'ALXN', 'AMAT', 'AMGN', 'AMT', 'AMZN', 'ANTM', 'AON', 'APD', 'APH', 'ASML', 'ATVI', 'AVGO', 'AWK', 'AXP', 'AZO', 'BA', 'BABA', 'BAC', 'BAX', 'BDX', 'BIDU', 'BIIB', 'BK', 'BKNG', 'BLK', 'BMRN', 'BMY', 'BSX', 'C', 'CAT', 'CB', 'CCI', 'CDNS', 'CERN', 'CHKP', 'CHTR', 'CI', 'CL', 'CLX', 'CMCSA', 'CME', 'CNC', 'COF', 'COP', 'COST', 'CRM', 'CSCO', 'CSX', 'CTAS', 'CTSH', 'CTXS', 'CVS', 'CVX', 'D', 'DBA', 'DE', 'DG', 'DHR', 'DIS', 'DLR', 'DLTR', 'DUK', 'EA', 'EBAY', 'ECL', 'ED', 'EL', 'EMR', 'EQIX', 'EQR', 'ES', 'ETN', 'EW', 'EWH', 'EWW', 'EXC', 'EXPE', 'FAST', 'FB', 'FDX', 'FE', 'FIS', 'FISV', 'GD', 'GE', 'GILD', 'GIS', 'GM', 'GOOG', 'GPN', 'GS', 'HAS', 'HCA', 'HD', 'HON', 'HPQ', 'HSIC', 'HUM', 'HYG', 'IAU', 'IBM', 'ICE', 'IDXX', 'ILMN', 'INCY', 'INFO', 'INTC', 'INTU', 'ISRG', 'ITW', 'JBHT', 'JD', 'JNJ', 'JPM', 'KHC', 'KLAC', 'KMB', 'KMI', 'KO', 'KR', 'LBTYA', 'LBTYK', 'LHX', 'LLY', 'LMT', 'LOW', 'LQD', 'LRCX', 'LULU', 'MA', 'MAR', 'MCD', 'MCHP', 'MCO', 'MDLZ', 'MDT', 'MELI', 'MET', 'MMC', 'MMM', 'MNST', 'MO', 'MRK', 'MS', 'MSCI', 'MSFT', 'MSI', 'MU', 'MXIM', 'MYL', 'NEE', 'NEM', 'NFLX', 'NKE', 'NLOK', 'NOC', 'NOW', 'NSC', 'NTAP', 'NTES', 'NVDA', 'NXPI', 'ORCL', 'ORLY', 'PAYX', 'PCAR', 'PEG', 'PFE', 'PG', 'PGR', 'PLD', 'PM', 'PNC', 'PSA', 'PSX', 'PYPL', 'QCOM', 'REGN', 'RMD', 'ROP', 'ROST', 'RTX', 'SBAC', 'SBUX', 'SCHW', 'SHOP', 'SHW', 'SIRI', 'SNPS', 'SO', 'SPGI', 'SPY', 'SRE', 'STZ', 'SWKS', 'SYK', 'SYY', 'T', 'TCOM', 'TFC', 'TGT', 'TIP', 'TJX', 'TMO', 'TMUS', 'TROW', 'TRV', 'TSLA', 'TTWO', 'TWLO', 'TXN', 'ULTA', 'UNH', 'UNP', 'UPS', 'USB', 'V', 'VNQ', 'VRSK', 'VRSN', 'VRTX', 'VZ', 'WBA', 'WDC', 'WEC', 'WFC', 'WLTW', 'WM', 'WMT', 'WYNN', 'XHB', 'XLK', 'XLNX', 'XLU', 'XLV', 'XOM', 'XRT', 'YUM', 'ZTS']
#ticker_list = ['SPY','VIX']
start_date = date(2015,1,2)
end_date = date(2020,3,30)
sessionstart = time(8,30)
sessionend = time(14,55)
lookback = 30
ago = 0
myresult = defaultdict(list)
mynewresult = defaultdict(list)
closelist = defaultdict(list)
highlist = defaultdict(list)
lowlist = defaultdict(list)
datelist = defaultdict(list)
k = 0
i = 0
j = 0
x = 0


#***************************************************************************************************************************************
#CREATE COMBINED DATAFRAME OF RETURNS AND GET CORRELATIONS, COVARIANCES, and PORTFOLIO VARIANCE



#Code to combine multiple tickers into 1 dataframe of just close prices
main_df = pd.DataFrame()
for t in ticker_list:
	print("Loading {} ".format(t))
	result = "SELECT date,open,high,low,close,volume FROM {} WHERE ticker = '{}' and date >= '{}' and date <='{}' ORDER BY date DESC".format(table,t,start_date.strftime("%Y-%m-%d"),end_date.strftime("%Y-%m-%d"))   
	myohlc=pd.read_sql(result,con=mydb)
	ohlc = myohlc.loc[:, ['date', 'open', 'high', 'low', 'close','volume']]
	ohlc.rename(columns={'date':'Date','open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'}, inplace=True)
	
	df = pd.read_sql(result,con=mydb)
	df.set_index('date', inplace=True)
	df.rename(columns={'close':t}, inplace=True)
	df.drop(['open','high','low','volume'],1,inplace=True)
	#print(df)
	#print(df[t])

	if main_df.empty:
		main_df = df
	else:
		main_df = main_df.join(df, how='outer')

returns = main_df.pct_change()  ##**NEED TO CONVERT 5 MIN BARS TO DAILY CHARTS TO DO THIS**
#Print out useful stats on returns
#print(returns.describe())

#Generate Correlation Table of all stocks
corr = returns.corr()
corr.to_csv("C:\\Users\\Erik\\Desktop\\correlations.csv")  #OUTPUT TO CSV ON DESKTOP
print("Correlations =  ",corr)

#Generate covariances
cov_matrix = returns.cov()
cov_matrix_a = cov_matrix * 252 #to annualise the daily covariance matrix with the standard 250 trading days
print("Covariance Matrix ",cov_matrix_a)
