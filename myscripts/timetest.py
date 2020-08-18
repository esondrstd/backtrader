import pandas as pd
from datetime import date, time, datetime, timedelta
import numpy as np
import datetime
from collections import defaultdict
from yahoo_earnings_calendar import YahooEarningsCalendar
import pandas as pd
import sqlalchemy
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker


start_time = '08:30'
end_time = '15:00'
start_date = '2018-06-01 00:00:00'
end_date = '2018-09-30 11:59:00'
#yec_start = datetime.datetime.strptime('Jan 1 2019  08:00AM', '%b %d %Y %I:%M%p')
#yec_end = datetime.datetime.strptime('Jun 30 2019  11:59PM', '%b %d %Y %I:%M%p')

rng = pd.date_range(start_date, end_date, freq="5min").strftime('%m/%d/%Y %H:%M')
df = pd.DataFrame({'date': rng})
df['date'] = pd.to_datetime(df['date'])  #convert date to datetime format
df = df.set_index(['date'])
#pd.set_option('display.max_rows', None)

newdf = df.between_time(start_time,end_time)
print(newdf)


mydict = dict()
alldict = defaultdict(list)
my_custom_delay_s = 0.1

yec = YahooEarningsCalendar(my_custom_delay_s)
tickers = ['AAPL','INTC','ABBV', 'ABT', 'ACN', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP', 'AFL', 'AGG', 'AGN']
#tickers = ['A', 'AAL', 'AAPL', 'ABBV', 'ABT', 'ACN', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP', 'AFL', 'AGG', 'AGN', 'ALGN', 'ALL', 'ALXN', 'AMAT', 'AMGN', 'AMT', 'AMZN', 'ANTM', 'AON', 'APD', 'APH', 'ASML', 'ATVI', 'AVGO', 'AWK', 'AXP', 'AZO', 'BA', 'BABA', 'BAC', 'BAX', 'BDX', 'BIDU', 'BIIB', 'BK', 'BKNG', 'BLK', 'BMRN', 'BMY', 'BSX', 'C', 'CAT', 'CB', 'CCI', 'CDNS', 'CERN', 'CHKP', 'CHTR', 'CI', 'CL', 'CLX', 'CMCSA', 'CME', 'CNC', 'COF', 'COP', 'COST', 'CRM', 'CSCO', 'CSX', 'CTAS', 'CTSH', 'CTXS', 'CVS', 'CVX', 'D', 'DBA', 'DD', 'DE', 'DG', 'DHR', 'DIS', 'DLR', 'DLTR', 'DUK', 'EA', 'EBAY', 'ECL', 'ED', 'EL', 'EMB', 'EMR', 'EQIX', 'EQR', 'ES', 'ETN', 'EW', 'EWH', 'EWW', 'EXC', 'EXPE', 'FAST', 'FB', 'FDX', 'FE', 'FIS', 'FISV', 'GD', 'GE', 'GILD', 'GIS', 'GM', 'GOOG', 'GPN', 'GS', 'HAS', 'HCA', 'HD', 'HON', 'HPQ', 'HSIC', 'HUM', 'HYG', 'IAU', 'IBM', 'ICE', 'IDXX', 'ILMN', 'INCY', 'INFO', 'INTC', 'INTU', 'ISRG', 'ITW', 'JBHT', 'JD', 'JNJ', 'JPM', 'KHC', 'KLAC', 'KMB', 'KMI', 'KO', 'KR', 'LBTYA', 'LBTYK', 'LHX', 'LLY', 'LMT', 'LOW', 'LQD', 'LRCX', 'LULU', 'MA', 'MAR', 'MCD', 'MCHP', 'MCO', 'MDLZ', 'MDT', 'MELI', 'MET', 'MMC', 'MMM', 'MNST', 'MO', 'MRK', 'MS', 'MSCI', 'MSFT', 'MSI', 'MU', 'MXIM', 'MYL', 'NEE', 'NEM', 'NFLX', 'NKE', 'NLOK', 'NOC', 'NOW', 'NSC', 'NTAP', 'NTES', 'NVDA', 'NXPI', 'ORCL', 'ORLY', 'PAYX', 'PCAR', 'PEG', 'PEP', 'PFE', 'PG', 'PGR', 'PLD', 'PM', 'PNC', 'PSA', 'PSX', 'PYPL', 'QCOM', 'REGN', 'RMD', 'ROKU', 'ROP', 'ROST', 'RTX', 'SBAC', 'SBUX', 'SCHW', 'SHOP', 'SHW', 'SHY', 'SIRI', 'SNPS', 'SO', 'SPGI', 'SPY', 'SRE', 'STZ', 'SWKS', 'SYK', 'SYY', 'T', 'TCOM', 'TFC', 'TGT', 'TIP', 'TJX', 'TMO', 'TMUS', 'TROW', 'TRV', 'TSLA', 'TTWO', 'TWLO', 'TXN', 'ULTA', 'UNH', 'UNP', 'UPS', 'USB', 'V', 'VNQ', 'VRSK', 'VRSN', 'VRTX', 'VZ', 'WBA', 'WDAY', 'WDC', 'WEC', 'WFC', 'WLTW', 'WM', 'WMT', 'WYNN', 'XHB', 'XLK', 'XLNX', 'XLU', 'XLV', 'XOM', 'XRT', 'YUM', 'ZTS']
	
# Returns a list of all available earnings of BOX
for i in tickers:
	mydict[i] = yec.get_earnings_of(i)
	#mydict[i] = yec.earnings_between(yec_start,yec_end)
	print(i)
	if mydict.get(i):
		print("found")
		for k in mydict.get(i):
			tset = k.get('startdatetime')[:-5]  #remove last 5 digits in time stamp returned (weird '.000Z' value)
			tnew = tset.replace("T"," ")  #remove 'T' character in between date and time of time stamp returned
			alldict['date'].append(tnew)
			ticker = k.get('ticker')
			alldict['ticker'].append(ticker)
			alldict['eps_estimate'].append(k.get('epsestimate'))
			alldict['eps_actual'].append(k.get('epsactual'))
			alldict['eps_diff'].append(k.get('epssurprisepct'))
			alldict['source'].append('Yahoo Earnings Cal')
			alldict['key'].append(f'{ticker} {tnew}')

alldf = pd.DataFrame.from_dict(alldict)
alldf['date'] = pd.to_datetime(alldf['date']) + pd.DateOffset(1)  #convert date to datetime format and offset by 1 day for backtest
alldf['date'] = alldf['date'].dt.strftime('%Y-%m-%d 08:30:00')
alldf = alldf[(alldf['date'] > start_date) & (alldf['date'] <= end_date)]  #Filter dataframe by dates requested
alldf.set_index('date', inplace=True)
alldf.drop_duplicates(subset ="ticker", keep = 'last', inplace = True) 

#alldf.sort_values(by=['date'], inplace=True, ascending=True)
pd.set_option('display.max_rows', None)

#print(alldf)

merged_df = alldf.join(newdf,how='outer')
print(merged_df)
