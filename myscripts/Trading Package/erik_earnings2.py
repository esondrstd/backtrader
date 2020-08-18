import datetime
from collections import defaultdict
from yahoo_earnings_calendar import YahooEarningsCalendar
import pandas as pd
from datetime import date, time, datetime, timedelta
import sqlalchemy
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from datetime import datetime

mydict = dict()
alldict = defaultdict(list)
my_custom_delay_s = 0.1

yec = YahooEarningsCalendar(my_custom_delay_s)
tickers = ['EBAY','EA','ECL']
#tickers = ['A', 'AAL', 'AAPL', 'ABBV', 'ABT', 'ACN', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP', 'AFL', 'AGG', 'AGN', 'ALGN', 'ALL', 'ALXN', 'AMAT', 'AMGN', 'AMT', 'AMZN', 'ANTM', 'AON', 'APD', 'APH', 'ASML', 'ATVI', 'AVGO', 'AWK', 'AXP', 'AZO', 'BA', 'BABA', 'BAC', 'BAX', 'BDX', 'BIDU', 'BIIB', 'BK', 'BKNG', 'BLK', 'BMRN', 'BMY', 'BSX', 'C', 'CAT', 'CB', 'CCI', 'CDNS', 'CERN', 'CHKP', 'CHTR', 'CI', 'CL', 'CLX', 'CMCSA', 'CME', 'CNC', 'COF', 'COP']
#tickers = ['A', 'AAL', 'AAPL', 'ABBV', 'ABT', 'ACN', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP', 'AFL', 'AGG', 'AGN', 'ALGN', 'ALL', 'ALXN', 'AMAT', 'AMGN', 'AMT', 'AMZN', 'ANTM', 'AON', 'APD', 'APH', 'ASML', 'ATVI', 'AVGO', 'AWK', 'AXP', 'AZO', 'BA', 'BABA', 'BAC', 'BAX', 'BDX', 'BIDU', 'BIIB', 'BK', 'BKNG', 'BLK', 'BMRN', 'BMY', 'BSX', 'C', 'CAT', 'CB', 'CCI', 'CDNS', 'CERN', 'CHKP', 'CHTR', 'CI', 'CL', 'CLX', 'CMCSA', 'CME', 'CNC', 'COF', 'COP', 'COST', 'CRM', 'CSCO', 'CSX', 'CTAS', 'CTSH', 'CTXS', 'CVS', 'CVX', 'D', 'DBA', 'DD', 'DE', 'DG', 'DHR', 'DIS', 'DLR', 'DLTR', 'DUK', 'EA', 'EBAY', 'ECL', 'ED', 'EL', 'EMB', 'EMR', 'EQIX', 'EQR', 'ES', 'ETN', 'EW', 'EWH', 'EWW', 'EXC', 'EXPE', 'FAST', 'FB', 'FDX', 'FE', 'FIS', 'FISV', 'GD', 'GE', 'GILD', 'GIS', 'GM', 'GOOG', 'GPN', 'GS', 'HAS', 'HCA', 'HD', 'HON', 'HPQ', 'HSIC', 'HUM', 'HYG', 'IAU', 'IBM', 'ICE', 'IDXX', 'ILMN', 'INCY', 'INFO', 'INTC', 'INTU', 'ISRG', 'ITW', 'JBHT', 'JD', 'JNJ', 'JPM', 'KHC', 'KLAC', 'KMB', 'KMI', 'KO', 'KR', 'LBTYA', 'LBTYK', 'LHX', 'LLY', 'LMT', 'LOW', 'LQD', 'LRCX', 'LULU', 'MA', 'MAR', 'MCD', 'MCHP', 'MCO', 'MDLZ', 'MDT', 'MELI', 'MET', 'MMC', 'MMM', 'MNST', 'MO', 'MRK', 'MS', 'MSCI', 'MSFT', 'MSI', 'MU', 'MXIM', 'MYL', 'NEE', 'NEM', 'NFLX', 'NKE', 'NLOK', 'NOC', 'NOW', 'NSC', 'NTAP', 'NTES', 'NVDA', 'NXPI', 'ORCL', 'ORLY', 'PAYX', 'PCAR', 'PEG', 'PEP', 'PFE', 'PG', 'PGR', 'PLD', 'PM', 'PNC', 'PSA', 'PSX', 'PYPL', 'QCOM', 'REGN', 'RMD', 'ROKU', 'ROP', 'ROST', 'RTX', 'SBAC', 'SBUX', 'SCHW', 'SHOP', 'SHW', 'SHY', 'SIRI', 'SNPS', 'SO', 'SPGI', 'SPY', 'SRE', 'STZ', 'SWKS', 'SYK', 'SYY', 'T', 'TCOM', 'TFC', 'TGT', 'TIP', 'TJX', 'TMO', 'TMUS', 'TROW', 'TRV', 'TSLA', 'TTWO', 'TWLO', 'TXN', 'ULTA', 'UNH', 'UNP', 'UPS', 'USB', 'V', 'VNQ', 'VRSK', 'VRSN', 'VRTX', 'VZ', 'WBA', 'WDAY', 'WDC', 'WEC', 'WFC', 'WLTW', 'WM', 'WMT', 'WYNN', 'XHB', 'XLK', 'XLNX', 'XLU', 'XLV', 'XOM', 'XRT', 'YUM', 'ZTS']
	
# Returns a list of all available earnings of BOX
for i in tickers:
	mydict[i] = yec.get_earnings_of(i)
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
alldf['date'] = pd.to_datetime(alldf['date'])  #convert date to datetime format
#alldf.set_index('date', inplace=True)
alldf.sort_values(by=['date'], inplace=True, ascending=True)
pd.set_option('display.max_rows', None)
print(alldf)


#GET READY TO SEND TO MYSQL DATABASE
"""
#configuration
host = '127.0.0.1'
user = 'root'
password = 'EptL@Rl!1'
database = 'Stock_Prices'

print('Connected')

# configure Session class with desired options
Session = sessionmaker()

#The following lines create engine which connect to mysql database
engine = sqlalchemy.create_engine( "mysql+pymysql://{}:{}@{}/{}".format(user,password,host,database))

# associate it with our custom Session class
Session.configure(bind=engine)

# work with the session
session = Session()
metadata = MetaData()

#ONLY USE IF TABLE NOT CREATED ALREADY!!!!  create table called intraday prices and define column types
intraday_prices = Table('fundamentals',metadata,
	Column('ticker',String(32), nullable=False),
	Column('date',DateTime,nullable=False),
	Column('eps_estimate',Numeric(19,4), nullable=True),
	Column('eps_actual',Numeric(19,4), nullable=True),
	Column('eps_diff',Numeric(19,4), nullable=True),
	Column('source',String(32), nullable=False),
	Column('key',String(64), nullable=False,primary_key=True)
)

#execute creation of table
metadata.create_all(engine)


alldf.to_sql('fundamentals', engine, index=False,if_exists='append')

# Commit the changes
session.commit()
print('Congrats - table updated in mysql')

# Close the session
session.close()
"""
