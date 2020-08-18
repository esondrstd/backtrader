import pandas as pd
import sqlalchemy
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import xlrd

#configuration
host = '127.0.0.1'
user = 'root'
password = 'EptL@Rl!1'
database = 'Stock_Prices'

print('Connected')

# configure Session class with desired options
Session = sessionmaker()

#The following lines create engine which connect to mysql database ********ERIK CHANGED ON 6/1/2020 - check code
#engine = create_engine( "mysql+pymysql://{}:{}@{}/{}".format(user,password,host,database))
engine = sqlalchemy.create_engine( "mysql+pymysql://{}:{}@{}/{}".format(user,password,host,database))


# associate it with our custom Session class
Session.configure(bind=engine)

# work with the session
session = Session()

metadata = MetaData()

"""
#ONLY USE IF TABLE NOT CREATED ALREADY!!!!  create table called intraday prices and define column types
intraday_prices = Table('5_min_prices',metadata,
	Column('ticker',String(32), nullable=False),
	Column('date',DateTime, nullable=False),
	Column('open',Numeric(19,4), nullable=True),
	Column('high',Numeric(19,4), nullable=True),
	Column('low',Numeric(19,4), nullable=True),
	Column('close',Numeric(19,4), nullable=True),
	Column('volume',BigInteger, nullable=True),
	Column('created',DateTime, nullable=False),
	Column('source',String(32), nullable=False),
	Column('key',String(64), nullable=False,primary_key=True)
)

#execute creation of table
metadata.create_all(engine)
"""

contractlist = ('TICK-NYSE','TRIN-NYSE',)#'VIX','TICK-NYSE','TRIN-NYSE','A',	 'AAL',	 'AAPL',	 'ABBV',	 'ABT',	 'ACN',	 'ADBE',	 'ADI',	 'ADP',	 'ADSK',	 'AEP',	 'AFL',	 'AGG',	 'AGN',	 'ALGN',	 'ALL',	 'ALXN',	 'AMAT',	 'AMGN',	 'AMT',	 'AMZN',	 'ANTM',	 'AON',	 'APD',	 'APH',	 'ASML',	 'ATVI',	 'AVGO',	 'AWK',	 'AXP',	 'AZO',	 'BA',	 'BABA',	 'BAC',	 'BAX',	 'BDX',	 'BIDU',	 'BIIB',	 'BK',	 'BKNG',	 'BLK',	 'BMRN',	 'BMY',	 'BSX',	 'C',	 'CAT',	 'CB',	 'CCI',	 'CDNS',	 'CERN',	 'CHKP',	 'CHTR',	 'CI',	 'CL',	 'CLX',	 'CMCSA',	 'CME',	 'CNC',	 'COF',	 'COP',	 'COST',	 'CRM',	 'CSCO',	 'CSX',	 'CTAS',	 'CTSH',	 'CTXS',	 'CVS',	 'CVX',	 'D',	 'DBA',	 'DD',	 'DE',	 'DG',	 'DHR',	 'DIS',	 'DLR',	 'DLTR',	 'DOW',	 'DUK',	 'EA',	 'EBAY',	 'ECL',	 'ED',	 'EL',	 'EMB',	 'EMR',	 'EQIX',	 'EQR',	 'ES',	 'ETN',	 'EW',	 'EWH',	 'EWW',	 'EXC',	 'EXPE',	 'FAST',	 'FB',	 'FDX',	 'FE',	 'FIS',	 'FISV',	 'GD',	 'GE',	 'GILD',	 'GIS',	 'GM',	 'GOOG',	 'GPN',	 'GS',	 'HAS',	 'HCA',	 'HD',	 'HON',	 'HPQ',	 'HSIC',	 'HUM',	 'HYG',	 'IAU',	 'IBM',	 'ICE',	 'IDXX',	 'ILMN',	 'INCY',	 'INFO',	 'INTC',	 'INTU',	 'ISRG',	 'ITW',	 'JBHT',	 'JD',	 'JNJ',	 'JPM',	 'KHC',	 'KLAC',	 'KMB',	 'KMI',	 'KO',	 'KR',	 'LBTYA',	 'LBTYK',	 'LHX',	 'LLY',	 'LMT',	 'LOW',	 'LQD',	 'LRCX',	 'LULU',	 'MA',	 'MAR',	 'MCD',	 'MCHP',	 'MCO',	 'MDLZ',	 'MDT',	 'MELI',	 'MET',	 'MMC',	 'MMM',	 'MNST',	 'MO',	 'MRK',	 'MS',	 'MSCI',	 'MSFT',	 'MSI',	 'MU',	 'MXIM',	 'MYL',	 'NEE',	 'NEM',	 'NFLX',	 'NKE',	 'NLOK',	 'NOC',	 'NOW',	 'NSC',	 'NTAP',	 'NTES',	 'NVDA',	 'NXPI',	 'ORCL',	 'ORLY',	 'PAYX',	 'PCAR',	 'PEG',	 'PEP',	 'PFE',	 'PG',	 'PGR',	 'PLD',	 'PM',	 'PNC',	 'PSA',	 'PSX',	 'PYPL',	 'QCOM',	 'REGN',	 'RMD',	 'ROKU',	 'ROP',	 'ROST',	 'RTX',	 'SBAC',	 'SBUX',	 'SCHW',	 'SHOP',	 'SHW',	 'SHY',	 'SIRI',	 'SNPS',	 'SO',	 'SPGI',	 'SPY',	 'SRE',	 'STZ',	 'SWKS',	 'SYK',	 'SYY',	 'T',	 'TCOM',	 'TFC',	 'TGT',	 'TIP',	 'TJX',	 'TMO',	 'TMUS',	 'TROW',	 'TRV',	 'TSLA',	 'TTWO',	 'TWLO',	 'TXN',	 'UAL',	 'ULTA',	 'UNH',	 'UNP',	 'UPS',	 'USB',	 'V',	 'VNQ',	 'VRSK',	 'VRSN',	 'VRTX',	 'VZ',	 'WBA',	 'WDAY',	 'WDC',	 'WEC',	 'WFC',	 'WLTW',	 'WM',	 'WMT',	 'WYNN',	 'XEL',	 'XHB',	 'XLK',	 'XLNX',	 'XLU',	 'XLV',	 'XOM',	 'XRT',	 'YUM',	 'ZTS',


for s in contractlist:
	#location of file to load
	file_path = 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/{}.csv'.format(s)

	#This will read select columns only from file
	df = pd.read_csv(file_path,usecols=['ticker','date','open','high','low', 'close','volume','created','source','key'])
	
	#Populate table with dataframe
	df.to_sql('5_min_prices', engine, index=False,if_exists='append')

	# Commit the changes
	session.commit()
	print('Congrats - {} table updated in mysql'.format(s))


# Close the session
session.close()


#TO READ ECONOMIC DATA INTO DATABASE
"""
#location of file to load
file_path = 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/econ.xlsx'

#This will read select columns only from file
for i in range(1,15):
	df = pd.read_excel(file_path,sheet_name = i,usecols=['date','econ','close'])

	#Populate table with dataframe
	df.to_sql('econ', engine, index=False,if_exists='append')

	# Commit the changes
	session.commit()
	print('Congrats - {} table updated in mysql')


# Close the session
session.close()
"""
