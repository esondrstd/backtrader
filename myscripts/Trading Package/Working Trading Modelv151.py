"""
Trading model that can use multiple symbols, multiple timeframes, multiple indicators, and different start/end dates and analytics.
1 primary data feed (5 min timeframe) is sourced from mysql (but can be sourced elsewhere), and then 2 additional data feeds(resampled datafeeds)
created for 3 additional higher timeframes.  Data feeds are as follows:  data0 = 5min, data1= 15min, data2 = 60min, data3 = 1day.
Each symbol can be accessed in each timeframe.  For example, MSFT and XOM would be appear as:
data0 MSFT (base timeframe), data0 XOM(base timeframe), data1 MSFT(next higher timeframe), data1 XOM, data2 MSFT, data2 XOM, data3 MSFT(highest timeframe), data3 XOM - a total of 8 'datas'.
Indicators can also be treated as a datafeed input, i.e. slope of ema indicator.
Each data produces a "line" of data that includes everything from the data feed, i.e. Open, high, low, close etc.  System iterates over each line via next() function to produce its results.
 
Strategies:
1.  Mean Reversion - PAIRS and spread trading
2.  Trending (buy first oversold cycle of trend when stochastic falls under 20) - account for distance and angle of pullback (small pullback at slight angle more bullish than deeper pullback at sharp angle).  Shape of pullback important - is it intermittant staircase move with sellers pushing prices down (bad, think 2 or 3 big red candle moves on pullback mixed with small green bars), or is it multiple long candle tails with small green bodies which is more bullish) Also, less volume on pullback better.
 -for trending strategies, wider stop = more profits (no stop is best, but most risky)
3.  VWAP trading - use as support/resistance/target for above 2 strategies
**ALWAYS USE VECTOR MULTIPLICATION/ADDITION etc - speeds up program tremendously
"""

#IMPORT MODULES
import sys
print(sys.version,sys.executable)
import backtrader as bt
import backtrader.indicators as btind
from backtrader.utils import flushfile  # win32 quick stdout flushing
from backtrader.feeds import mysql
from datetime import date, time, datetime, timedelta
import pytz
from collections import defaultdict
import numpy as np
import statsmodels.tsa.stattools as ts
from statsmodels.tsa.vector_ar.vecm import coint_johansen
import matplotlib.pyplot as plt
import itertools
from scipy import stats
from sqlalchemy import *

class UserInputs():
	#This class is designed so runstrat() method can pick up these parameters (can use self.p.whatever to pass parameters for some reason)

	def datalist(data_req):
		#Create list of tickers to load data for.  Market Breadth indicators need to be removed from initiliazation and next() so they are not traded
		#Data Notes - 'EMB' and 'SHY' data starts 8/3/2017, 'DBA' has almost double the amount of records the other tickers do for some reason.
		#TICK is # of NYSE stocks trading on an uptick vs # of stocks trading on downtick.  About 2800 stocks total, usually oscillates between -500 to +500.  Readings above 1000 or below -1000 considered extreme.  #TRIN is ratio of (# of Advance/Decliners)/(Advance/Decline Volume).  Below 1 is strong rally, Above 1 is strong decline.#VIX is 30 day expectation of volatility for S&P 500 options.  VIX spikes correlate to market declines because more people buying options to protect themselves from declines
		#'A', 'AAL', 'AAPL', 'ABBV', 'ABT', 'ACN', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP', 'AFL', 'AGG', 'AGN', 'ALGN', 'ALL', 'ALXN', 'AMAT', 'AMGN', 'AMT', 'AMZN', 'ANTM', 'AON', 'APD', 'APH', 'ASML', 'ATVI', 'AVGO', 'AWK', 'AXP', 'AZO', 'BA', 'BABA', 'BAC', 'BAX', 'BDX', 'BIDU', 'BIIB', 'BK', 'BKNG', 'BLK', 'BMRN', 'BMY', 'BSX', 'C', 'CAT', 'CB', 'CCI', 'CDNS', 'CERN', 'CHKP', 'CHTR', 'CI', 'CL', 'CLX', 'CMCSA', 'CME', 'CNC', 'COF', 'COP', 'COST', 'CRM', 'CSCO', 'CSX', 'CTAS', 'CTSH', 'CTXS', 'CVS', 'CVX', 'D', 'DBA', 'DD', 'DE', 'DG', 'DHR', 'DIS', 'DLR', 'DLTR', 'DOW', 'DUK', 'EA', 'EBAY', 'ECL', 'ED', 'EL', 'EMB', 'EMR', 'EQIX', 'EQR', 'ES', 'ETN', 'EW', 'EWH', 'EWW', 'EXC', 'EXPE', 'FAST', 'FB', 'FDX', 'FE', 'FIS', 'FISV', 'GD', 'GE', 'GILD', 'GIS', 'GM', 'GOOG', 'GPN', 'GS', 'HAS', 'HCA', 'HD', 'HON', 'HPQ', 'HSIC', 'HUM', 'HYG', 'IAU', 'IBM', 'ICE', 'IDXX', 'ILMN', 'INCY', 'INFO', 'INTC', 'INTU', 'ISRG', 'ITW', 'JBHT', 'JD', 'JNJ', 'JPM', 'KHC', 'KLAC', 'KMB', 'KMI', 'KO', 'KR', 'LBTYA', 'LBTYK', 'LHX', 'LLY', 'LMT', 'LOW', 'LQD', 'LRCX', 'LULU', 'MA', 'MAR', 'MCD', 'MCHP', 'MCO', 'MDLZ', 'MDT', 'MELI', 'MET', 'MMC', 'MMM', 'MNST', 'MO', 'MRK', 'MS', 'MSCI', 'MSFT', 'MSI', 'MU', 'MXIM', 'MYL', 'NEE', 'NEM', 'NFLX', 'NKE', 'NLOK', 'NOC', 'NOW', 'NSC', 'NTAP', 'NTES', 'NVDA', 'NXPI', 'ORCL', 'ORLY', 'PAYX', 'PCAR', 'PEG', 'PEP', 'PFE', 'PG', 'PGR', 'PLD', 'PM', 'PNC', 'PSA', 'PSX', 'PYPL', 'QCOM', 'REGN', 'RMD', 'ROKU', 'ROP', 'ROST', 'RTX', 'SBAC', 'SBUX', 'SCHW', 'SHOP', 'SHW', 'SHY', 'SIRI', 'SNPS', 'SO', 'SPGI', 'SPY', 'SRE', 'STZ', 'SWKS', 'SYK', 'SYY', 'T', 'TCOM', 'TFC', 'TGT', 'TIP', 'TJX', 'TMO', 'TMUS', 'TROW', 'TRV', 'TSLA', 'TTWO', 'TWLO', 'TXN', 'UAL', 'ULTA', 'UNH', 'UNP', 'UPS', 'USB', 'V', 'VNQ', 'VRSK', 'VRSN', 'VRTX', 'VZ', 'WBA', 'WDAY', 'WDC', 'WEC', 'WFC', 'WLTW', 'WM', 'WMT', 'WYNN', 'XEL', 'XHB', 'XLK', 'XLNX', 'XLU', 'XLV', 'XOM', 'XRT', 'YUM', 'ZTS'
		
		#datalist = ['VIX','TICK-NYSE','TRIN-NYSE','SPY','XLU','IAU']
		#datalist = ['TICK-NYSE','SPY','INTC','AAPL','ABBV']
		#datalist = ['SPY','TICK-NYSE','AMT', 'AMZN', 'ANTM', 'AON', 'APD', 'APH', 'ASML', 'ATVI', 'AVGO', 'AWK', 'AXP', 'AZO', 'BA', 'BABA', 'BAC', 'BAX', 'BDX', 'BIDU', 'BIIB', 'BK', 'BKNG', 'BLK', 'BMRN', 'BMY', 'BSX', 'C', 'CAT', 'CB', 'CCI', 'CDNS', 'CERN', 'CHKP', 'CHTR', 'CI', 'CL', 'CLX', 'CMCSA', 'CME', 'CNC', 'COF', 'COP', 'COST', 'CRM', 'CSCO', 'CSX', 'CTAS', 'CTSH', 'CTXS', 'CVS', 'CVX', 'D', 'DBA', 'DD', 'DE', 'DG', 'DHR', 'DIS', 'DLR', 'DLTR','DUK', 'EA', 'EBAY', 'ECL', 'ED', 'EL', 'EMB', 'EMR', 'EQIX', 'EQR', 'ES', 'ETN', 'EW', 'EWH', 'EWW', 'EXC']
		datalist = ['SPY','TICK-NYSE','A', 'AAL', 'AAPL', 'ABBV', 'ABT', 'ACN', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP', 'AFL', 'AGG', 'AGN', 'ALGN', 'ALL', 'ALXN', 'AMAT', 'AMGN', 'AMT', 'AMZN', 'ANTM', 'AON', 'APD', 'APH', 'ASML', 'ATVI', 'AVGO', 'AWK', 'AXP', 'AZO', 'BA', 'BABA', 'BAC', 'BAX', 'BDX', 'BIDU', 'BIIB', 'BK', 'BKNG', 'BLK', 'BMRN', 'BMY', 'BSX', 'C', 'CAT', 'CB', 'CCI', 'CDNS', 'CERN', 'CHKP', 'CHTR', 'CI', 'CL', 'CLX', 'CMCSA', 'CME', 'CNC', 'COF', 'COP', 'COST', 'CRM', 'CSCO', 'CSX', 'CTAS', 'CTSH', 'CTXS', 'CVS', 'CVX', 'D', 'DBA', 'DD', 'DE', 'DG', 'DHR', 'DIS', 'DLR', 'DLTR','DUK', 'EA', 'EBAY', 'ECL', 'ED', 'EL', 'EMB', 'EMR', 'EQIX', 'EQR', 'ES', 'ETN', 'EW', 'EWH', 'EWW', 'EXC', 'EXPE', 'FAST', 'FB', 'FDX', 'FE', 'FIS', 'FISV', 'GD', 'GE', 'GILD', 'GIS', 'GM', 'GOOG', 'GPN', 'GS', 'HAS', 'HCA', 'HD', 'HON', 'HPQ', 'HSIC', 'HUM', 'HYG', 'IAU', 'IBM', 'ICE', 'IDXX', 'ILMN', 'INCY', 'INFO', 'INTC', 'INTU', 'ISRG', 'ITW', 'JBHT', 'JD', 'JNJ', 'JPM', 'KHC', 'KLAC']
		#datalist = ['TICK-NYSE','A', 'AAL', 'AAPL', 'ABBV', 'ABT', 'ACN', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP', 'AFL', 'AGG', 'AGN', 'ALGN', 'ALL', 'ALXN', 'AMAT', 'AMGN', 'AMT', 'AMZN', 'ANTM', 'AON', 'APD', 'APH', 'ASML', 'ATVI', 'AVGO', 'AWK', 'AXP', 'AZO', 'BA', 'BABA', 'BAC', 'BAX', 'BDX', 'BIDU', 'BIIB', 'BK', 'BKNG', 'BLK', 'BMRN', 'BMY', 'BSX', 'C', 'CAT', 'CB', 'CCI', 'CDNS', 'CERN', 'CHKP', 'CHTR', 'CI', 'CL', 'CLX', 'CMCSA', 'CME', 'CNC', 'COF', 'COP', 'COST', 'CRM', 'CSCO', 'CSX', 'CTAS', 'CTSH', 'CTXS', 'CVS', 'CVX', 'D', 'DBA', 'DD', 'DE', 'DG', 'DHR', 'DIS', 'DLR', 'DLTR', 'DUK', 'EA', 'EBAY', 'ECL', 'ED', 'EL', 'EMB', 'EMR', 'EQIX', 'EQR', 'ES', 'ETN', 'EW', 'EWH', 'EWW', 'EXC', 'EXPE', 'FAST', 'FB', 'FDX', 'FE', 'FIS', 'FISV', 'GD', 'GE', 'GILD', 'GIS', 'GM', 'GOOG', 'GPN', 'GS', 'HAS', 'HCA', 'HD', 'HON', 'HPQ', 'HSIC', 'HUM', 'HYG', 'IAU', 'IBM', 'ICE', 'IDXX', 'ILMN', 'INCY', 'INFO', 'INTC', 'INTU', 'ISRG', 'ITW', 'JBHT', 'JD', 'JNJ', 'JPM', 'KHC', 'KLAC', 'KMB', 'KMI', 'KO', 'KR', 'LBTYA', 'LBTYK', 'LHX', 'LLY', 'LMT', 'LOW', 'LQD', 'LRCX', 'LULU', 'MA', 'MAR', 'MCD', 'MCHP', 'MCO', 'MDLZ', 'MDT', 'MELI', 'MET', 'MMC', 'MMM', 'MNST', 'MO', 'MRK', 'MS', 'MSCI', 'MSFT', 'MSI', 'MU', 'MXIM', 'MYL', 'NEE', 'NEM', 'NFLX', 'NKE', 'NLOK', 'NOC', 'NOW', 'NSC', 'NTAP', 'NTES', 'NVDA', 'NXPI', 'ORCL', 'ORLY', 'PAYX', 'PCAR', 'PEG', 'PEP', 'PFE', 'PG', 'PGR', 'PLD', 'PM', 'PNC', 'PSA', 'PSX', 'PYPL', 'QCOM', 'REGN', 'RMD', 'ROKU', 'ROP', 'ROST', 'RTX', 'SBAC', 'SBUX', 'SCHW', 'SHOP', 'SHW', 'SHY', 'SIRI', 'SNPS', 'SO', 'SPGI', 'SPY', 'SRE', 'STZ', 'SWKS', 'SYK', 'SYY', 'T', 'TCOM', 'TFC', 'TGT', 'TIP', 'TJX', 'TMO', 'TMUS', 'TROW', 'TRV', 'TSLA', 'TTWO', 'TWLO', 'TXN', 'ULTA', 'UNH', 'UNP', 'UPS', 'USB', 'V', 'VNQ', 'VRSK', 'VRSN', 'VRTX', 'VZ', 'WBA', 'WDAY', 'WDC', 'WEC', 'WFC', 'WLTW', 'WM', 'WMT', 'WYNN', 'XHB', 'XLK', 'XLNX', 'XLU', 'XLV', 'XOM', 'XRT', 'YUM', 'ZTS']
		ibdatalist = ['MCD','AAPL','SPY','XHB','XLU','ABBV', 'ABT', 'ACN', 'ADBE', 'ADI']  #'AAPL-STK-SMART-USD'
		ibforex_datalist = []  #'EUR','GBP','AUD'
		#ibdatalist = ['EUR.USD','GBP.USD']  #Make sure not to include comma after last ticker or program won't read in live trading
		
		if data_req == 'ib':
			return ibdatalist
		elif data_req == 'hist':
			return datalist
		elif data_req == 'forex': 
			return ibforex_datalist

	def model_params():
		params = dict(
			live_status = False,  #Flip between live trading (True) and backtesting (False)
			start_date = date(2019,1,1), #Dates for backtesting
			end_date = date(2019,4,1),
			nysetick_on = False,
			t0_on = True,
			t1_on = True,
			t2_on = True,
			timeframe0 = 5, #MINUTES
			timeframe1 = 15, #MINUTES
			timeframe2 = 60, #MINUTES 
			sessionstart = time(8,30),
			sessionend = time(14,55),
			start_cash=100000,  #For backtesting only, live trading calls broker for available cash
			)
		return params
		
				
class Strategy(bt.Strategy):
	 
	params = dict(
			printlines = True,
			dollars_risked_per_trade = 300,
			total_dollars_risked = 20000,
			target = 2,  #multiple of dollars risks per trade, to determine profit target per trade.  "2" represents target that is double dollars risked
			min_touches = 2,#Support/Resistance - # of times price has to hit expected levels
			tol_perc = 20, #how far most recent high(low) can be from period maximum(minimum) - if this spread is within this tolerance, represents a "touch".  Expressed as % of total max-min move range over period
			bounce_perc = 0,#Keep at 0 - use only if you want to influence when support/resistance is calculated, as opposed to always calculating when touchpoints are hit (preferable)
			writer = 'off', #export results to CSV output report 'on' or 'off'
			sma1 = 5,
			sma2 = 3,
			ema1 = 5,  #8
			ema2 = 10, #20
			signif = .05, #(.10, .05, and .01 available) for statistical tests: .01 ideal
			pairs_lookback = 10,
			obv = 10,
			atrper = 5,
			atrdist = 3,   
			slope_per = 5,
			breakout_per = 5, 
			avg_per = 5,
			rsi = 10,
			adx = 10,
			stoch_per = 5,
			stoch_fast = 3,
			boll_per = 10,
			boll_dist = 2,
			lookback = 10,
			rank = 10, #How many tickers to select from ticker list
			)
			
	def __init__(self):
		"""initialize parameters and variables for Strategy Class"""
		
		#Set program start time
		self.start_time=datetime.now().time()
		print(f'Program start at {self.start_time}')
		print(f'Program time period: {UserInputs.model_params().get("start_date")} to {UserInputs.model_params().get("end_date")}')
		print(self.getdatanames())
		
		#print(f'Program Parameters: {self.params._getitems()}')
		
		#initialize variables and dicts
		self.nextcounter = 0
		self.cor_counter = 0		
		self.prenext_done = False
		self.pos = 0
		self.cash_avail = 0
		self.data_live = False
		self.tick_close = 0
		self.sortflag = 0
		self.first_run_complete = False
		self.pair_count = 0

		self.inds = dict()
		self.rtop_dict = dict()
		self.rbot_dict = dict()
		self.merged_dict = dict()
		self.long_stop_dict = defaultdict(list)
		self.short_stop_dict = defaultdict(list)
		self.gap_dict = defaultdict(list)
		self.perc_chg_dict = defaultdict(list)
		self.cointegrating_pairs = []
		self.adfpval = []
		self.errors = []
		self.all_tickers = []
		self.pair_spread = defaultdict(list)
		self.pair_zscore= defaultdict(list)
		self.date_dict = defaultdict(list)
		self.pair_close_dict = defaultdict(list)
		self.pair_spread_dict = defaultdict(list)
		self.pair_zscore_dict = defaultdict(list)
		self.long_pair_dict = defaultdict(list)
		self.short_pair_dict = defaultdict(list)
		self.exit_pair_dict = defaultdict(list)
		self.hratio_close_dict = defaultdict(list)
		self.justdate_dict = defaultdict(list)
		self.plotdict = defaultdict(list)
		self.inorder_dict = defaultdict(list)
		self.stop_dict = defaultdict(list)
		self.size_dict = defaultdict(lambda: defaultdict(list))
		self.pair_long_stop_dict = defaultdict(lambda: defaultdict(list))
		self.pair_short_stop_dict = defaultdict(lambda: defaultdict(list))
		self.eps_dict=defaultdict(lambda: defaultdict(list))
		#self.inorder_dict = defaultdict(lambda: defaultdict(list))  #allows you to keep nesting lists within dictionary
		
		#Create/Instantiate objects to access UserInputs class
		self.modelp = UserInputs.model_params()
	
		#Calc data feed metrics
		if not self.modelp.get('live_status'):
			datalist = UserInputs.datalist('hist')
		elif self.modelp.get('live_status'):
			ibdatalist = UserInputs.datalist('ib')
		
		"""
		#---------------------------------------------------------------------------------------------------------------------
		#PULL FUNDAMENTALS SQL TABLE INTO A DICTIONARY
		#Define connection configuration
		startd = UserInputs.model_params().get("start_date")
		endd = UserInputs.model_params().get("end_date")

		host = '127.0.0.1'
		user = 'root'
		password = 'EptL@Rl!1'
		database = 'Stock_Prices'
		table = 'fundamentals'
		start_date = startd.strftime("%Y-%m-%d")
		end_date = endd.strftime("%Y-%m-%d")

		#Establish SQL connection
		engine = create_engine('mysql+pymysql://'+user+':'+ password +'@'+ host +'/'+ database +'?charset=utf8mb4', echo=False)
		conn = engine.connect()
		
		#Get data from SQL DB
		mytest = conn.execute(f"SELECT * FROM {table} where datetime >= '{start_date}' and datetime <= '{end_date}'")
		eps_set = mytest.fetchall()

		#Get dictionary from SQL results
		d, a = {}, []
		for rowproxy in eps_set:
			# rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
			for column, value in rowproxy.items():
				# build up the dictionary
				d = {**d, **{column: str(value)}}
			a.append(d)
		
		for i in a:
			self.eps_dict[f"{i['ticker']}"]['date'] = i['datetime']
			if i['eps_estimate'] != 'None':
				self.eps_dict[f"{i['ticker']}"]['eps_estimate'] = float(i['eps_estimate'])
			if i['eps_actual'] != 'None':
				self.eps_dict[f"{i['ticker']}"]['eps_actual'] = float(i['eps_actual'])
			if i['eps_diff'] != 'None':
				self.eps_dict[f"{i['ticker']}"]['eps_diff%'] = float(i['eps_diff'])

		#Close DB connection
		conn.close()
		engine.dispose()
		"""
		
		#---------------------------------------------------------------------------------------------------------------------------
		#Initialize dictionary's
		for i, d in enumerate(self.datas):	
			#Initialize dictionaries by appending 0 value
			self.inds[d._name] = dict()  #Dict for all indicators
			
			#Instantiate exact data references (can't loop or will only spit out last value)
			if d._name == 'TICK-NYSE0':
				self.tick_close = d.close
			
			if d._name[:-1] != 'TICK-NYSE':
#*********************************************INITITIALIZE INDICATORS*********************************************************				
				self.inds[d._name]['close'] = btind.close(d.close,period=self.p.pairs_lookback,plot=False)	#history of closing prices
				self.inds[d._name]['slope'] = btind.Slope(d,period=self.p.slope_per,plot=False)							
				self.inds[d._name]['slope_of_slope'] = btind.Slope(self.inds[d._name]['slope'],period=self.p.slope_per,plot=False)
				self.inds[d._name]['obv'] = btind.obv(d,period=self.p.obv,plot=True)
				self.inds[d._name]['slope_obv'] = btind.Slope(self.inds[d._name]['obv'],period=self.p.obv,plot=False)
				#self.inds[d._name]['gap'] = btind.gap(d,period=self.p.breakout_per,plot=False)
				self.inds[d._name]['vwap'] = btind.vwap(d,plot=False)
				self.inds[d._name]['atr'] = btind.ATR(d,period=self.p.atrper,plot=False)
				self.inds[d._name]['perc_chg'] = btind.PercentChange(d.open,period=6,plot=False)
				self.inds[d._name]['atr_stop'] = btind.atr_stop(d,self.inds[d._name]['atr'],atrdist = self.p.atrdist,dollars_risked = self.p.total_dollars_risked,dollars_per_trade = self.p.dollars_risked_per_trade,plot=False)
				#self.inds[d._name]['hammer'] = btind.HammerCandles(d,plot=False)											
				#self.inds[d._name]['three_line_strike'] = btind.three_line_strike(d,plot=True)										
				#self.inds[d._name]['ema1'] = btind.EMA(d,period=self.p.ema1,plot=True)
				#self.inds[d._name]['ema2'] = btind.EMA(d,period=self.p.ema2,plot=True)
				#self.inds[d._name]['adx'] = btind.ADX(d,period=self.p.adx,plot=True)	
				#self.inds[d._name]['slope_adx'] = 	btind.Slope(self.inds[d._name]['adx'],period=self.p.slope_per,plot=False)																		
				#self.inds[d._name]['bollinger'] = btind.BollingerBands(d.close,period=self.p.boll_per,devfactor = self.p.boll_dist,plot=True)						
				#self.inds[d._name]['slope_ema1'] = 	btind.Slope(self.inds[d._name]['ema1'],period=self.p.slope_per,plot=False)	
				#self.inds[d._name]['slope_ema2'] = 	btind.Slope(self.inds[d._name]['ema2'],period=self.p.slope_per,plot=False)			
				#self.inds[d._name]['slope_ema_width'] = btind.Slope(self.inds[d._name]['ema1']-self.inds[d._name]['ema2'],period=self.p.slope_per,plot=False)											
				#self.inds[d._name]['rsi']= btind.RSI(d,period=self.p.rsi,safediv=True,plot=True)								
				self.inds[d._name]['stochastic'] = btind.StochasticSlow(d,period=self.p.stoch_per,period_dfast= self.p.stoch_fast,safediv=True,plot=False)
				#self.inds[d._name]['adx'].plotinfo.plotmaster = self.inds[d._name]['rsi']   #Plot ADX on same subplot as RSI
				#self.inds[d._name]['support'] = btind.Support(d,period=self.p.lookback,min_touches = self.p.min_touches,tol_perc = self.p.tol_perc,bounce_perc = self.p.bounce_perc,plot=False)
				#self.inds[d._name]['resistance'] = btind.Resistance(d,period=self.p.lookback,min_touches = self.p.min_touches,tol_perc = self.p.tol_perc,bounce_perc = self.p.bounce_perc,plot=False)	
													
				#Initialize target size, target long, and target short prices
				self.inds[d._name]['target_size'] = self.inds[d._name]['atr_stop']().lines.size			
				self.inds[d._name]['target_long'] = d.open +(self.p.dollars_risked_per_trade*self.p.target)/self.inds[d._name]['target_size']																	
				self.inds[d._name]['target_short'] = d.open -(self.p.dollars_risked_per_trade*self.p.target)/self.inds[d._name]['target_size']																	
			
		if d._name==d._name[:-1]+'1'and not d._name == 'TICK-NYSE1':
				self.all_tickers.append(d._name)	
		self.all_pairs = list(itertools.combinations(self.all_tickers, 2))  #return list of all pair combinations of tickers
		
		print('Start preloading data to meet minimum data requirements')	
		
#**************************************************************************************************************************************
	"""
	def start(self):
		for i, d in enumerate(self.datas): 
			if self.modelp.get('live_status') and d.contractdetails is not None:
				print(f'ContractDetails: {d.contractdetails.m_longName} {d.contractdetails.m_marketName} {d.contractdetails.m_timeZoneId}')
	"""

	def notify_order(self, order):
		if order.status == order.Completed:
			if order.isbuy() and self.pos==0:
				print(f"{order.data._name} ENTER LONG POSITION, Date: {self.dt} {self.hourmin} Price: {round(order.executed.price,2)}, Cost: {round(order.executed.value,2)}, Size {order.executed.size}, Type {order.getordername()}")
			
			if order.isbuy() and self.pos < 0:
				print(f"{order.data._name} EXIT SHORT POSITION, Date: {self.dt} {self.hourmin} Price: {round(order.executed.price,2)}, Cost: {round(order.executed.value,2)}, Size {order.executed.size}, Type {order.getordername()}")
			
			if order.issell() and self.pos==0:
				print(f"{order.data._name} ENTER SHORT POSITION, Date: {self.dt} {self.hourmin} Price: {round(order.executed.price,2)}, Cost: {round(order.executed.value,2)}, Size {order.executed.size}, Type {order.getordername()}")
			
			if order.issell() and self.pos > 0:
				print(f"{order.data._name} EXIT LONG POSITION, Date: {self.dt} {self.hourmin} Price: {round(order.executed.price,2)}, Cost: {round(order.executed.value,2)}, Size {order.executed.size}, Type {order.getordername()}")
		
	
	def notify_store(self, msg, *args, **kwargs):
		print('*' * 5, 'STORE NOTIF:', msg)


	def notify_trade(self, trade):
		if trade.isclosed:
			print(f"{trade.data._name} POSITION CLOSED {self.dt} {self.hourmin} Price: {round(trade.price,2)}, Net Profit: {round(trade.pnl,2)}")
		
	
	def notify_data(self, data, status):
		#To notify us when delayed backfilled data becomes live data during live trading
		print('*' * 5, 'DATA NOTIF:', data._getstatusname(status))
		if status == self.data.LIVE:
			self.data_live = True
			
	def prenext(self):
		pass
		#pre-loads all indicator data for all timeframes before strategy starts executing
		#print(f"Prenext len {len(self)}")
		
				
	def nextstart(self):
		#There is a nextstart method which is called exactly once, to mark the switch from prenext to next. 
		self.prenext_done = True
		print('---------------------------------------------------------------------------------------------------------------')	
		print(f'NEXTSTART called with strategy length {len(self)} - Pre Data has loaded, backtesting can start')
		print('---------------------------------------------------------------------------------------------------------------')
		super(Strategy, self).nextstart()		

	#*****************************************************************************************************************************
	#WHERE ALL 
	def next(self):
		"""Iterates over each "line" of data (date and ohlcv) provided by data feed"""
		#mystart=datetime.now()
		#Convert backtrader float date to datetime so i can see time on printout and manipulate time variables
		self.hourmin = datetime.strftime(self.data.num2date(),'%H:%M')
		self.dt = self.data.num2date()
		print(self.dt)
		
		"""
		#PAIRS TRADING - Get correlations, rank them, and store correlations pairs and value in dctionary
		if self.hourmin=='08:30':
			#Pairs Trading Strategy
			self.clear_pairs()
			self.create_pairs(self.data,self.p.signif)  #get initial pairs list using Johansen test
			self.calc_spread_zscore()
			
		if self.first_run_complete:
			self.pairs_entry_exit()
		"""
		#-------------------STOCK SELECTION BASED ON OPEN CRITERIA-----------------------------------------
		if self.hourmin=='09:05' and self.perc_chg_dict is not None and self.data._name==self.data0._name:
			self.rank_perc(self.data)
		
		for i, d in enumerate(self.datas):  #Need to iterate over all datas so atr and sizing can be adjusted for multiple time frame user parameters	
		
			if self.hourmin=='09:00' and d._name==d._name[:-1]+'0' and d._name!='TICK-NYSE0':
				self.perc_chg_dict[d._name] = self.inds.get(d._name[:-1]+'0').get('perc_chg')[0]*100
	
			#if self.hourmin=='08:30' and d._name!='TICK-NYSE0' and d._name==d._name[:-1]+'0':
				#self.gap_dict[d._name] = self.inds.get(d._name).get('gap').lines.gap[0]  #get open gaps, put in dict
			
			#-------------------------------- EXIT TRADES IF CRITERIA MET------------------------------------------
			if d._name==d._name[:-1]+'0':
			#if d._name==d._name[:-1]+'1':
				self.pos = self.getposition(d).size
				
			if self.hourmin=='14:50' and self.pos:  #can't exit at 14:55 because cerebro submits at order at open of next bar
				self.eod_exit(d)
			
			"""
			if self.pos and self.tick_close[0]<=-1000 and d._name == d._name[:-1]+'0':
				self.exit_trade(d,'long')
			
			if self.pos and self.tick_close[0]>=1000 and d._name == d._name[:-1]+'0':
				self.exit_trade(d,'short')
			"""
	
			#---------------------------------ENTRY LOGIC FOR LONG AND SHORT-----------------------------------------
			if d._name==d._name[:-1]+'0' and d._name in self.merged_dict.keys() and self.pos==0 and self.entry_rules(d) and d._name!='TICK-NYSE0':  #Check that entry rules are met: 		
			#if d._name==d._name[:-1]+'1' and self.pos==0 and self.entry_rules(d):  #Check that entry rules are met: 
				#sig = self.sup_res(d):
				sig = self.pull_back(d)
				if sig=='buy':
					self.buyorder(d)
				elif sig=='sell':
					self.sellorder(d)
				
			#-----------------------------------------------------------------------------------------------------------

		#end_time = datetime.now()  #Timer to analyze code
		#diff = end_time-mystart 
		#print(f'Timer {diff}')
	
	#*********************************************************************************************************************
	
	def sellorder(self,d):
		"""Places sell order and apends size and stops to dictionary"""
		#Calculate Size
		target_size = int(self.inds.get(d._name).get('target_size')[0])
		
		#Calculate STOP (ATR BASED)
		self.short_stop = self.inds.get(d._name).get('atr_stop').lines.short_stop[0]
		
		#Calculate Target Price
		if target_size:
			self.target_short = round(self.inds.get(d._name).get('target_short')[0],2)
		
		#SHORT ENTRY ORDER
		#Create Short Entry Order
		short_name = f'{d._name} - Enter Short Trade'
		self.short_ord = self.sell(data=d._name,
					 size=target_size,
					 exectype=bt.Order.Market,
					 transmit=False,
					 )
											
		#Create Fixed Short Stop Loss	 
		short_stop_name = f'{d._name} - Submit STOP for Short Entry'
		self.short_stop_ord = self.buy(data=d._name,
					size=target_size,
					exectype=bt.Order.Stop,
					price = self.short_stop,
					transmit=True,
					parent=self.short_ord,
					)
		
		self.short_stop_dict[d._name].append(self.short_stop_ord)
		print(f'{self.dt} {self.hourmin} SELL SELL SELL {d._name} - {target_size} shares at {d.close[0]}.  Stop price @ {self.short_stop}')


	def buyorder(self,d):
		"""Places buy order and apends size and stops to dictionary"""		
		#Calculate Size
		target_size = int(self.inds.get(d._name).get('target_size')[0])
		
		#Calculate STOP (ATR BASED) - **** NEEDS TO BE MULTIPLE OF $.005 for IB to accepts
		self.long_stop = self.inds.get(d._name).get('atr_stop').lines.long_stop[0]
		
		#Create Target Price
		if target_size:
			self.target_long = round(self.inds.get(d._name).get('target_long')[0],2)
		
		#CREATE LONG ORDER
		long_name = f'{d._name} - Enter Long Trade'
		self.long_ord = self.buy(data=d._name,
							size=target_size,
							exectype=bt.Order.Market,
							transmit=False,
							)
		
		#Create Fixed Long Stop Loss
		long_stop_name = f'{d._name} - Submit STOP for Long Entry'
		self.long_stop_ord = self.sell(data=d._name,
							size=target_size,
							exectype=bt.Order.Stop,
							price = self.long_stop,
							transmit=True,
							parent=self.long_ord,
							)
								
		#Track if currently in an order or not
		self.long_stop_dict[d._name].append(self.long_stop_ord)
		print(f'{self.dt} {self.hourmin} BUY BUY BUY {d._name} - {target_size} shares at {d.close[0]}.  Stop price @ {self.long_stop}')
	
	def exit_trade(self,d,direction):
		#EXIT LOGIC FOR INTRADAY SHORTS
		if(	direction == 'short'
			and d._name==d._name[:-1]+'0'
			#and not (d._name[:-1]=='VIX' or d._name[:-1]=='TICK-NYSE' or d._name[:-1]=='TRIN-NYSE' or d._name[:-1]=='SPY')	
			and self.pos < 0):
		
			#CANCEL ASSOCIATED STOP AND TARGET ORDERS
			if self.short_stop_dict.get(d._name) is not None:
				self.cancel(self.short_stop_dict.get(d._name)[-1])
				print(f'{d._name} {self.dt} {self.hourmin} Short Stop Order CANCELLED - Exit Criteria Met')
				#self.cancel(self.target_short_dict.get(d._name)[-1])
				
			#SHORT EXIT ORDER - closes existing position and cancels outstanding stop-loss ord	
			print(f'{d._name} {self.dt} {self.hourmin} EXIT Criteria Met - Exit Short Trade')       
			self.exit_short = self.close(d._name)
			
			#print(f'{self.dt} {self.hourmin} EXIT SHORT {d._name} - {self.pos} shares at {d.close[0]}')
				
		elif(direction == 'long'
			and d._name==d._name[:-1]+'0'
			#and not (d._name[:-1]=='VIX' or d._name[:-1]=='TICK-NYSE' or d._name[:-1]=='TRIN-NYSE' or d._name[:-1]=='SPY')	
			and self.pos > 0):
			
			#CANCEL ASSOCIATED STOP AND TARGET ORDERS
			if self.long_stop_dict.get(d._name) is not None:
				self.cancel(self.long_stop_dict.get(d._name)[-1])
				print(f'{d._name} {self.dt} {self.hourmin} Long Stop Order CANCELLED - Exit Criteria Met')
			
			#LONG EXIT ORDER - closes existing position and cancels outstanding stop-loss order
			print(f'{d._name} {self.dt} {self.hourmin} EXIT Criteria Met - Exit Long Trade')
			self.exit_long = self.close(d._name)
			
	def eod_exit(self,d):
		#EXIT LOGIC FOR EOD EXITS
		#CANCEL ALL ORDERS AT END OF DAY (STOPS AND TARGETS)
		if self.long_stop_dict.get(d._name) is not None:
			self.cancel(self.long_stop_dict.get(d._name)[-1])
			print(f'{d._name} All Stop Orders Cancelled EOD')
		
		if self.short_stop_dict.get(d._name) is not None:
			self.cancel(self.short_stop_dict.get(d._name)[-1])
			#self.cancel(self.target_short_dict.get(d._name)[-1])
		
		self.eod_name = f'{d._name} - EXIT ALL TRADES AT EOD'
		self.eod_close = self.close(d._name,
									name=self.eod_name)

	def entry_rules(self,d):	
		#Get available cash
		self.cash_avail = self.broker.getcash()
		if not self.modelp.get('live_status'):	
			if (not d._name[:-1]=='TICK-NYSE'
				and (self.hourmin>='09:05'and self.hourmin<='14:00')
				and self.cash_avail > self.p.total_dollars_risked
				and self.prenext_done 	#start trading after all prenext data loads
				and self.sortflag == 1	#start trading after sort has happened and stocks have been selected
				):
				return True
				
			else:
				return False
				
		elif self.modelp.get('live_status'):
			self.cash_avail = self.broker.getcash()
			print(d._name,self.dt,self.hourmin)	
			
			if (not d._name[:-1]=='TICK-NYSE'
				and (self.hourmin>='09:00'and self.hourmin<='14:00')
				and self.cash_avail > self.p.total_dollars_risked
				and self.prenext_done #Start trading after all prenext data loads
				and self.data_live
				):
				return True
			else:
				return False	
		print(d._name,self.dt,self.hourmin,d.open[0],d.high[0],d.low[0],d.close[0],d.volume[0],self.cash_avail,self.pos)
			
	
	def eps(self,d):
		if d._name[:-1] in self.eps_dict.keys() and str(self.dt) in self.eps_dict.get(d._name[:-1]).get('date'):
			if self.eps_dict.get(d._name[:-1]).get('eps_diff%') > 0:
				return 'buy'
			elif self.eps_dict.get(d._name[:-1]).get('eps_diff%') < 0:
				return 'sell'
			else:
				return False
		else:
			return False
		
		
	def tick_trade(self):
		if self.tick_close[0] >= 100:
			return 'buy'
		elif self.tick_close[0] <= -1000:
			return 'sell'
		else:
			return False
			
	
	def create_pairs(self,d,signif):
		"""
		Get list of all tickers defined, perform Johansen test for cointigration and cointegrated stocks
		Cointegration test helps to establish the presence of a statistically significant connection 
		between two or more time series.  Order of integration(d) is the number of differencing required 
		to make a non-stationary time series stationary.  Now, when you have two or more time series, 
		and there exists a linear combination of them that has an order of integration (d) less than that of 
		the individual series, then the collection of series is said to be cointegrated.  When two or more 
		time series are cointegrated, it means they have a long run, statistically significant relationship.
		"""	
		if len(d) > self.p.pairs_lookback * (self.modelp.get('timeframe1')/self.modelp.get('timeframe0')):  #ensure enough data has loaded for lookback period
		#Loop through all pairs, run Johansen test, and pick out cointegrated stocks
			for i, (ticker1, ticker2) in enumerate(self.all_pairs): 	
				t1_data = np.array(self.inds.get(ticker1).get('close').get(size=self.p.pairs_lookback)) 	#Y variable
				t2_data = np.array(self.inds.get(ticker2).get('close').get(size=self.p.pairs_lookback))	#X variable
				combined_data = np.vstack((t1_data, t2_data)).T
				
				# The second and third parameters indicate constant term, with a lag of 1. 
				result = coint_johansen(combined_data, 0, 1)  #Inputted as Y Variable first, X Var second.  testing only 2 tickers at a time.  Can not conduct test with more than 12 tickers
				hedge_ratio = result.evec[:, 0]	#The first column of eigenvectors contains the best weights (shortest half life for mean reversion).  This determine shares of each instrument.
				hedge_ratio_t1 = hedge_ratio[0]
				hedge_ratio_t2 = hedge_ratio[1]
								
				# the 90%, 95%, and 99% confidence levels for the trace statistic and maximum eigenvalue statistic are stored in the first, second, and third column of cvt and cvm, respectively
				confidence_level_cols = {90: 0, 95: 1,99: 2}
				confidence_level_col = confidence_level_cols[(1-signif)*100]
				trace_crit_value = result.cvt[:, confidence_level_col]
				eigen_crit_value = result.cvm[:, confidence_level_col]
				#t1_trace = trace_crit_value[0]
				#t2_trace = trace_crit_value[1]
				#t1_eigen = eigen_crit_value[0]
				#t2_eigen = eigen_crit_value[1]
				#t1_lr1 = result.lr1[0]
				#t2_lr1 = result.lr1[1]
				#t1_lr2 = result.lr2[0]
				#t2_lr2 = result.lr2[1]
			
				# The trace statistic and maximum eigenvalue statistic are stored in lr1 and lr2 - see if they exceeded the confidence threshold
				if np.all(result.lr1 >= trace_crit_value) and np.all(result.lr2 >= eigen_crit_value):			
					#self.cointegrating_pairs.append(dict(t1=ticker1,t2=ticker2,hratio_t1=hedge_ratio_t1,hratio_t2=hedge_ratio_t2))
					#print(f'{self.dt} {self.hourmin} Johansen: Pair:{ticker1}/{ticker2} , {ticker1} - Trace Stat: {t1_lr1} is > Crit Val {t1_trace} Max Eigen Stat {t1_lr2} > {t1_eigen} Crit Val, Hedge: {hedge_ratio[0]}')
					#print(f'{self.dt} {self.hourmin} Johansen: Pair:{ticker1}/{ticker2} , {ticker2} - Trace Stat: {t2_lr1} is > Crit Val {t2_trace} Max Eigen Stat {t2_lr2} > {t2_eigen} Crit Val, Hedge: {hedge_ratio[1]}')
					self.adfpval.append(dict(t1=ticker1,t2=ticker2,hratio1 = hedge_ratio_t1,hratio2=hedge_ratio_t2))

					"""
					#Perform regression on pairs
					beta_set = np.array(t2_data)
					beta = beta_set.reshape((len(beta_set), 1))
					Y_set = np.array(t1_data)
					Y = Y_set.reshape((len(Y_set), 1))
					(m, c, rvalue, pvalue, stderr) = stats.mstats.linregress(beta, Y)  #input as linregress(x,y)
			
					#Create residual series for ADF test (i.e. errors)
					coef_price = np.multiply(m,beta_set)
					projected = np.add(coef_price,c) #vector approach to solve project = m * beta[n][0] + c
					error = np.subtract(Y_set,projected)  #error = value - projected for n,value in enumberate(Y)
					
					#Perform ADF test on pairs
					r = ts.adfuller(error, autolag='AIC')
					#output = {'test_statistic':round(r[0], 4), 'pvalue':round(r[1], 4), 'n_lags':round(r[2], 4), 'n_obs':r[3]}
					p_value = r[1]	
					
					if p_value <= signif and self.pair_count <= 10:
						self.adfpval.append(dict(t1=ticker1,t2=ticker2,hratio1 = hedge_ratio_t1,hratio2=hedge_ratio_t2))
						self.pair_count += 1	
						#self.pval_dict[f'{t1}/{t2}'].append(p_value)			
						print(f" ADF Test => P-Value {p_value} <= Significance Level {signif}. Rejecting Null Hypothesis that Data has unit root (non-stationary).")
						#print(f" ADF Test => Series is Stationary.")
					else:
						print(f" ADF Test => P-Value {p_value} > Significance Level {signif}. Weak evidence to reject the Null Hypothesis.")
						#print(f" ADF Test => Series is Non-Stationary.") 
					"""
					
	def calc_spread_zscore(self):
		print (f'Number of ADF PAIRS: {len(self.adfpval)}')
		print(self.adfpval)		
		#sorted_pval = sorted(pval_dict.items(), key = lambda x: x[1], reverse=True)  #Create sorted list -  key accepts a function (lambda), and every item (x) will be passed to the function individually, and return a value x[1] by which it will be sorted.
		#self.rtop_dict = dict(sorted_pval[-5:])  #Choose subset of tickers with highest rank (i.e. top 3)

		for i in self.adfpval:		
			t1 = i['t1'] 	#Y Variable
			t2 = i['t2']	#X Variable
			name = f'{t1}/{t2}'
			hratio_t1 = i['hratio1']
			hratio_t2 = i['hratio2']
			t1_data = self.inds.get(t1).get('close').get(size=self.p.pairs_lookback)
			t2_data = self.inds.get(t2).get('close').get(size=self.p.pairs_lookback)
			pos_t1 = self.getpositionbyname(t1).size
			pos_t2 = self.getpositionbyname(t2).size
			
			arrt1 = np.multiply(hratio_t1,np.array(t1_data)) #create array of hedge ratio * close price
			arrt2 = np.multiply(hratio_t2,np.array(t2_data)) 
			#spread = np.round(np.add(arrt1,arrt2),2)
			spread = np.add(arrt1,arrt2)
			#zscore = np.round(stats.zscore(spread),4)
			zscore = stats.zscore(spread)
			self.pair_zscore_dict[f'zscore {t1}/{t2}'] = [x for x in zscore]	#unpack numpy array vales
			self.pair_spread_dict[f'spread {t1}/{t2}'] = [x for x in spread]	#unpack numpy array vales			
			self.inorder_dict[f'{t1}/{t2} inorder'].append(False) #initialize inorder dictionary
			self.pair_long_stop_dict[name][t1].append(0)
			self.pair_long_stop_dict[name][t2].append(0)
			self.pair_short_stop_dict[name][t1].append(0)
			self.pair_short_stop_dict[name][t2].append(0)
			self.stop_dict[name].append(0)
	
		#if self.pair_spread_dict and not self.first_run_complete:
			#self.plot_pair()
			#self.plot_spread()
			#self.plot_zscore()
			#print(self.inorder_dict)
		
		self.first_run_complete = True
		#print(self.hourmin)
		
				
	def pairs_entry_exit(self,z_entry_threshold=2.0, z_exit_threshold=0):
		"""Create the entry/exit signals based on the exceeding of 
		z_enter_threshold for entering a position and falling below
		z_exit_threshold for exiting a position."""	
		for i in self.adfpval:
			t1 = i['t1'] 	#Y Variable
			t2 = i['t2']	#X Variable
			name = f'{t1}/{t2}'
			hratio_t1 = i['hratio1']
			hratio_t2 = i['hratio2']
			t1_data = self.inds.get(t1).get('close')[0]
			t2_data = self.inds.get(t2).get('close')[0]
			
			cash_avail = self.broker.getcash()	
			spread_now = hratio_t1 * t1_data + hratio_t2 * t2_data #create array of hedge ratio * close price
			self.pair_spread_dict[f'spread {t1}/{t2}'].append(spread_now)
			self.pair_spread_dict[f'spread {t1}/{t2}'].pop(0)	#remove first item in dictionary (keep length to lookback period)
			zscore_now = stats.zscore(self.pair_spread_dict.get(f'spread {t1}/{t2}')[-self.p.pairs_lookback:])[0]
			long_signal = zscore_now <= -z_entry_threshold*1.0
			short_signal = -1*(zscore_now >= z_entry_threshold*1.0)
			total_entry_signals = long_signal + short_signal
			exit_signal = abs(zscore_now) <= z_exit_threshold*1.0
			pair_stop_signal = zscore_now >= self.stop_dict.get(name)[-1]
			t1_long_stop_sig = t1_data < self.pair_long_stop_dict.get(name).get(t1)[-1]
			t2_long_stop_sig = t2_data < self.pair_long_stop_dict.get(name).get(t2)[-1]
			t1_short_stop_sig = t1_data > self.pair_short_stop_dict.get(name).get(t1)[-1]
			t2_short_stop_sig = t2_data > self.pair_short_stop_dict.get(name).get(t2)[-1]
			
			print(t1_long_stop_sig,t2_long_stop_sig,t1_short_stop_sig,t2_short_stop_sig)
			print(self.pair_long_stop_dict.get(name).get(t1),self.pair_long_stop_dict.get(name).get(t2),self.pair_short_stop_dict.get(name).get(t1),self.pair_short_stop_dict.get(name).get(t2))
			
			if self.inorder_dict.get(f'{t1}/{t2} inorder')[-1] and (exit_signal or t1_long_stop_sig or t2_long_stop_sig or t1_short_stop_sig or t2_short_stop_sig or pair_stop_signal or self.hourmin=='14:45'):
				self.close(t1,size=self.size_dict.get(name).get(t1)[-1])	#exit on 5 min bar	
				self.close(t2,size=self.size_dict.get(name).get(t2)[-1])	#exit on 5 min bar
				print(f'EXIT pair {t1}/{t2} zscore: {zscore_now} <= z exit of {z_exit_threshold}')
				if zscore_now >= self.stop_dict.get(name)[-1] or t1_long_stop_sig or t2_long_stop_sig or t1_short_stop_sig or t2_short_stop_sig:
					print(f'STOPPED OUT')
				self.inorder_dict[f'{t1}/{t2} inorder'].append(False)
					
			if total_entry_signals !=0 and not self.inorder_dict.get(f'{t1}/{t2} inorder')[-1] and self.hourmin<'11:00' and cash_avail > self.p.total_dollars_risked:
				# Calculate weights and position size
				hratio_weights_t1 = hratio_t1 * t1_data
				hratio_weights_t2 = hratio_t2 * t2_data
				weights_t1_set = total_entry_signals * hratio_weights_t1
				weights_t2_set = total_entry_signals * hratio_weights_t2
				total_weights = abs(weights_t1_set) + abs(weights_t2_set)
				weights_t1 = weights_t1_set/total_weights
				weights_t2 = weights_t2_set/total_weights
				cash_size_t1 = self.p.total_dollars_risked * weights_t1
				cash_size_t2 = self.p.total_dollars_risked * weights_t2
				size_t1 = int(cash_size_t1/t1_data)
				size_t2 = int(cash_size_t2/t2_data)
				
				if weights_t1>0:
					#long stock 1 of pair
					long_name = f'For Pair {name}: - Enter LONG Trade for leg {t1}'
					self.long_ord = self.buy(data=t1,
					size= size_t1,
					exectype=bt.Order.Market,
					transmit=True)
					self.size_dict[name][t1].append(size_t1)
					self.pair_long_stop_dict[name][t1].append(self.inds.get(t1).get('atr_stop').lines.long_stop[0])
					print(f"{self.dt} {self.hourmin} For Pair {name} - Enter LONG Trade for leg {t1} at price {t1_data} zscore: {zscore_now} >= z entry of {z_entry_threshold}")
				if weights_t2>0:
					#long stock 1 of pair
					long_name = f'For Pair {name}: - Enter LONG Trade for leg {t2}'
					self.long_ord = self.buy(data=t2,
					size= size_t2,
					exectype=bt.Order.Market,
					transmit=True)
					self.size_dict[name][t2].append(size_t2)
					self.pair_long_stop_dict[name][t2].append(self.inds.get(t2).get('atr_stop').lines.long_stop[0])
					print(f"{self.dt} {self.hourmin} For Pair {name} - Enter LONG Trade for leg {t2} at price {t2_data} zscore: {zscore_now} >= z entry of {z_entry_threshold}")
				if weights_t1<0:
					#Short stock 1 of pair
					short_name = f'For Pair {name}: - Enter SHORT Trade for leg {t1}'
					self.short_ord = self.sell(data=t1,
					size= size_t1,
					exectype=bt.Order.Market,
					transmit=True)
					self.size_dict[name][t1].append(size_t1)
					self.pair_short_stop_dict[name][t1].append(self.inds.get(t1).get('atr_stop').lines.short_stop[0])
					print(f"{self.dt} {self.hourmin} For Pair {name} - Enter SHORT Trade for leg {t1} at price {t1_data} zscore: {zscore_now} >= z entry of {z_entry_threshold}")
				if weights_t2<0:
					#Short stock 2 of pair
					short_name = f'For Pair {name}: - Enter SHORT Trade for leg {t2}'
					self.short_ord = self.sell(data=t2,
					size= size_t2,
					exectype=bt.Order.Market,
					transmit=True)
					self.size_dict[name][t2].append(size_t2)
					self.pair_short_stop_dict[name][t1].append(self.inds.get(t2).get('atr_stop').lines.short_stop[0])
					print(f"{self.dt} {self.hourmin} For Pair {name} - Enter Short Trade for leg {t2} at price {t2_data} zscore: {zscore_now} >= z entry of {z_entry_threshold}")
				
				spread_stop = abs(zscore_now) + .5
				self.stop_dict[name].append(spread_stop)
				self.inorder_dict[f'{name} inorder'].append(True)	

		#print(self.adfpval)	
		#print(self.pair_zscore_dict)
		#print(self.pair_spread_dict)

			
	def clear_pairs(self):
		self.adfpval.clear()
		self.cointegrating_pairs.clear()
		self.pair_close_dict.clear()
		self.pair_spread_dict.clear()
		self.pair_zscore_dict.clear()
		self.long_pair_dict.clear()
		self.short_pair_dict.clear()
		self.exit_pair_dict.clear()
		self.hratio_close_dict.clear()
		self.errors.clear()
		self.first_run_complete = False
		self.inorder_dict.clear()
		self.pair_long_stop_dict.clear()
		self.pair_short_stop_dict.clear()
		self.stop_dict.clear()
		self.size_dict.clear()
		
		
	def plot_pair(self):
		if self.adfpval:
			fig = plt.figure()
			cols = 2
			rows = int(len(self.adfpval)/cols)	#define number of rows in multi-chart plot

			for i, pair in enumerate(self.adfpval):
				if i <= (rows*cols)-1:
					t1_name = pair.get('t1')
					t2_name = pair.get('t2')
					t1_data= self.inds.get(t1_name).get('close').get(size=self.p.pairs_lookback)
					t2_data = self.inds.get(t2_name).get('close').get(size=self.p.pairs_lookback)

					ax = fig.add_subplot(rows, cols, i+1)
					ax2 = ax.twinx()
					ax.plot(t1_data,'r-')
					ax2.plot(t2_data, 'b-')
					#ax.set_ylabel(f'{t1_name} data', color='g')
					#ax2.set_ylabel(f'{t2_name} data', color='b')
					ax.set_title(f'{t1_name} and {t2_name} Close Prices')
			
			plt.tight_layout()			
			plt.show()

				
	def plot_spread(self):
		if self.pair_spread_dict:
			fig = plt.figure()
			cols = 2
			rows = int(len(self.adfpval)/cols)

			for i, pair in enumerate(self.adfpval):
				if i <= (rows*cols)-1:
					t1_name = pair.get('t1')
					t2_name = pair.get('t2')
					spread_data= self.pair_spread_dict.get(f'spread {t1_name}/{t2_name}')
					
					ax = fig.add_subplot(rows, cols, i+1)
					ax.plot(spread_data,'g-')
					#ax.set_ylabel(f'{t1_name}/{t2_name} spread', color='b')
					ax.set_title(f'{t1_name}/{t2_name} spread')
			
			plt.tight_layout()		
			plt.show()
	
	
	def plot_zscore(self):
		if self.pair_spread_dict:
			fig = plt.figure()
			cols = 2
			rows = int(len(self.adfpval)/cols)

			for i, pair in enumerate(self.adfpval):
				if i <= (rows*cols)-1:
					t1_name = pair.get('t1')
					t2_name = pair.get('t2')

					spread_data= self.pair_zscore_dict.get(f'zscore {t1_name}/{t2_name}')
					ax = fig.add_subplot(rows, cols, i+1)
					ax.plot(spread_data,'g-')
					ax.axhline(y=0, color='r', linestyle='-')
					#ax.set_ylabel(f'{t1_name}/{t2_name} zscore', color='r')
					ax.set_title(f'{t1_name}/{t2_name} zscore')
			
			plt.tight_layout()		
			plt.show()
			
	
	def hammer(self,d):
		self.hammer_t0= self.inds.get(d._name[:-1]+'0').get('hammer')[0]
		
		if self.hammer_t0==1:
				return 'buy'
		elif self.hammer_t0==-1:
				return 'sell'
		else:
			return False
				
				
	def three_line(self,d):
		self.three_strike_t0= self.inds.get(d._name[:-1]+'0').get('three_line_strike')[0]

		if self.three_strike_t0==1:
			return 'buy'
		elif self.three_strike_t0==-1:
			return 'sell'
		else:
			return False
	
	
	def pull_back(self,d):
		#Get timeframe 0 values
		self.percK_t0 = self.inds.get(d._name[:-1]+'0').get('stochastic').lines.percK[0]
		self.slope_obv_t0 = self.inds.get(d._name[:-1]+'0').get('slope_obv')[0] #Get OBV
		self.slope_t0 = self.inds.get(d._name[:-1]+'0').get('slope')[0]  
		self.vwap_t0 = self.inds.get(d._name[:-1]+'0').get('vwap')[0]  
		#Get Timeframe 1 Values
		self.slope_t1 = self.inds.get(d._name[:-1]+'1').get('slope')[0]  #Calc slope for time1
		
		#Get Timeframe 2 Values
		self.slope_t2 = self.inds.get(d._name[:-1]+'2').get('slope')[0]  #Calc slope for time2

		#Signal Logic for BUY
		if(#d._name in self.rtop_dict.keys()
			self.tick_close > 0
			and self.slope_obv_t0 > 0
			and d.close[0]>self.vwap_t0
			and self.slope_t1 > 0
			and self.slope_t2 > 0			
			and self.percK_t0 < 30):
			return 'buy'		
		#Signal Logic for SELL	
		elif (#d._name in self.rbot_dict.keys()
			self.tick_close < 0
			and self.slope_obv_t0 < 0
			and d.close[0] < self.vwap_t0
			and self.slope_t1 < 0	
			and self.slope_t2 < 0	
			and self.percK_t0 > 70):
			return 'sell'
		else:
			return False
				
		
	def sup_res(self,d):
		#Calc timeframe 0
		self.slope_obv_t0 = self.inds.get(d._name[:-1]+'0').get('slope_obv')[0] #Get OBV
		self.slope_t0 = self.inds.get(d._name[:-1]+'0').get('slope')[0]  
		self.vwap_t0 = self.inds.get(d._name[:-1]+'0').get('vwap')[0]  
		
		#Calculate timeframe 1
		self.resistance_t1 = self.inds.get(d._name).get('resistance')[0]
		self.support_t1 = self.inds.get(d._name).get('support')[0]
		self.slope_t1 = self.inds.get(d._name[:-1]+'1').get('slope')[0]  #Calc slope for time1
		
		#Calculate timeframe 2
		self.resistance_t2 = self.inds.get(d._name).get('resistance')[0]
		self.support_t2 = self.inds.get(d._name).get('support')[0]
		self.slope_t2 = self.inds.get(d._name[:-1]+'2').get('slope')[0]  #Calc slope for time1
	
		#Signal Logic
		if(self.tick_close > 0
			and self.slope_obv_t0 > 0
			and d.close[0] > self.vwap_t0
			and self.slope_t1 > 0					
			and self.slope_t2 > 0
			and d.low[0] < self.support_t1):
			return 'buy'
		elif (self.tick_close < 0
			and self.slope_obv_t0 < 0
			and d.close[0] < self.vwap_t0
			and self.slope_t1 < 0					
			and self.slope_t2 < 0
			and d.high[0] > self.resistance_t1):
			return 'sell'
		else:
			return False
	
	
	def rank_perc(self,d):
		"""Create % change ranking across stock universe and return top X and bottom Y as per paramaters"""
		sorted_res = sorted(self.perc_chg_dict.items(), key = lambda x: x[1], reverse=True)  #Create sorted list -  key accepts a function (lambda), and every item (x) will be passed to the function individually, and return a value x[1] by which it will be sorted.
		self.rtop_dict = dict(sorted_res[:self.p.rank])  #Choose subset of tickers with highest rank (i.e. top 3)
		self.rbot_dict = dict(sorted_res[-self.p.rank:])  #Choose subset of tickers with lowest rank (i.e. bottom 3)
		self.merged_dict = {**self.rtop_dict, **self.rbot_dict} 
		self.sortflag = 1
		print(f'{d._name} {self.dt} {self.hourmin} Top Sort: {self.rtop_dict}, Bottom Sort: {self.rbot_dict}')
	

	def rank_gap(self,d):
		"""Create gap ranks across stock universe and return top X and bottom Y as per paramaters"""
		sorted_res = sorted(self.gap_dict.items(), key = lambda x: x[1], reverse=True) #Create sorted list -  key accepts a function (lambda), and every item (x) will be passed to the function individually, and return a value x[1] by which it will be sorted.
		self.rtop_dict = dict(sorted_res[:self.p.rank])  #Choose subset of tickers with highest rank (i.e. top 3)
		self.rbot_dict = dict(sorted_res[-self.p.rank:])  #Choose subset of tickers with lowest rank (i.e. bottom 3)
		self.merged_dict = {**self.rtop_dict, **self.rbot_dict} 
		self.sortflag = 1
		print(f'{d._name} {self.dt} {self.hourmin} Top Sort: {self.rtop_dict}, Bottom Sort: {self.rbot_dict}')
		
			
	def signal_morn_break(self,d,direction):
		"""Dependent upon running rank_gap function first"""
		#Calc timeframe 0 
		self.slope_obv_t0 = self.inds.get(d._name[:-1]+'0').get('slope_obv')[0] #Get OBV
		#Calc timeframe 1
		self.slope_t1 = self.inds.get(d._name[:-1]+'1').get('slope')[0]  #Calc slope for time1
		#Calc timeframe 2	
		self.slope_t2 = self.inds.get(d._name[:-1]+'2').get('slope')[0]  #Calc slope for time2
		
		#Determine open 15 minute range
		self.rng_high = self.inds[d._name]['gap'].lines.rng_high[0]
		self.rng_low = self.inds[d._name]['gap'].lines.rng_low[0]
		#Signal Logic
		if(d._name in self.rtop_dict.keys()
			and d.close[0] >= self.rng_high
			and self.tick_close > 0
			and self.slope_obv_t0 > 0
			and self.slope_t1 > 0					
			and self.slope_t2 > 0):
			return 'buy'
		elif(d._name in self.rbot_dict.keys()
			and d.close[0] <= self.rng_low
			and self.tick_close < 0
			and self.slope_obv_t0 < 0
			and self.slope_t1 < 0					
			and self.slope_t2 < 0):
			return 'sell'
		else:
			return False
	
	
	def regime_early_bull(self,d):
		#Trend underway, getting stronger
		#Get timeframe 0 values
		self.percK_t0 = self.inds.get(d._name).get('stochastic').lines.percK[0]
		
		#Get Timeframe 1 Values
		self.slope_obv_t1 = self.inds.get(d._name[:-1]+'1').get('slope_obv')[0] #Get OBV slope	
		self.slope_t1 = self.inds.get(d._name[:-1]+'1').get('slope')[0]  #Calc slope for time1
		self.slope_of_slope_t1 = self.inds.get(d._name[:-1]+'1').get('slope_of_slope')[0]  #Calc slope for time1
		self.ema1_t1 = self.inds.get(d._name[:-1]+'1').get('ema1')[0]
		self.ema2_t1 = self.inds.get(d._name[:-1]+'1').get('ema2')[0]
		self.slope_ema1_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema1')[0]
		self.slope_ema2_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema1')[0]
		self.adx_t1 = self.inds.get(d._name[:-1]+'1').get('adx')[0]
		self.slope_adx_t1 = self.inds.get(d._name[:-1]+'1').get('slope_adx')[0]
		self.slope_ema_width_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema_width')[0]
		self.boll_mid_t1 = self.inds.get(d._name[:-1]+'1').get('bollinger').lines.mid[0]
		
		#Get Timeframe 2 Values
		self.slope_obv_t2 = self.inds.get(d._name[:-1]+'2').get('slope_obv')[0] #Get OBV slope
		self.slope_t2 = self.inds.get(d._name[:-1]+'2').get('slope')[0]  #Calc slope for time2
		self.slope_of_slope_t2 = self.inds.get(d._name[:-1]+'2').get('slope_of_slope')[0]  #Calc slope for time1
		self.ema1_t2 = self.inds.get(d._name[:-1]+'2').get('ema1')[0]
		self.ema2_t2 = self.inds.get(d._name[:-1]+'2').get('ema2')[0]
		self.slope_ema1_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema2')[0]
		self.slope_ema2_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema2')[0]
		self.adx_t2 = self.inds.get(d._name[:-1]+'2').get('adx')[0]
		self.slope_adx_t2 = self.inds.get(d._name[:-1]+'2').get('slope_adx')[0]
		self.slope_ema_width_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema_width')[0]
		self.boll_mid_t2 = self.inds.get(d._name[:-1]+'2').get('bollinger').lines.mid[0]

		#Store in list so expressions can be 'scored' later
		mylist = [self.adx_t1 > 20,
				 self.adx_t2 > 20,
				 self.slope_adx_t1 > 0,
				 self.slope_adx_t2 > 0,
				 self.ema1_t1 > self.ema2_t1,
				 self.ema1_t2 > self.ema2_t2,
				 self.slope_ema1_t1 > 0,
				 self.slope_ema2_t1 > 0,
				 self.slope_ema_width_t1 > 0,
				 self.slope_ema_width_t2 > 0,
				 self.slope_t1 > 0,
				 self.slope_t2 > 0,
				 self.slope_of_slope_t1 > 0,
				 self.slope_of_slope_t2 > 0,
				 self.slope_obv_t1 > 0,
				 self.slope_obv_t2 > 0,
				 d.close[0] > self.boll_mid_t1,
				 d.close[0] > self.boll_mid_t2,
				 #self.percK_t0 < 30,
				 ]
		
		#Get length of list		
		mycount = len(mylist)
		#If 75% of list is true, return true
		if sum(mylist) > (mycount * .75):	#sum count true as 1, false as 0 	
			return True
		else:
			return False
		
		
	def regime_late_bull(self,d):
		#Late in trend, starting to top out - look to exit long position or initiate short position
		#Vix has -.43 correlation to SPY over last 5 years - use as indicator (Vix sloping down good for trend?)
		#Get Timeframe 1 Values
		self.slope_obv_t1 = self.inds.get(d._name[:-1]+'1').get('slope_obv')[0] #Get OBV slope	
		self.slope_t1 = self.inds.get(d._name[:-1]+'1').get('slope')[0]  #Calc slope for time1
		self.slope_of_slope_t1 = self.inds.get(d._name[:-1]+'1').get('slope_of_slope')[0]  #Calc slope for time1
		self.ema1_t1 = self.inds.get(d._name[:-1]+'1').get('ema1')[0]
		self.ema2_t1 = self.inds.get(d._name[:-1]+'1').get('ema2')[0]
		self.slope_ema1_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema1')[0]
		self.slope_ema2_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema1')[0]
		self.adx_t1 = self.inds.get(d._name[:-1]+'1').get('adx')[0]
		self.slope_adx_t1 = self.inds.get(d._name[:-1]+'1').get('slope_adx')[0]
		self.slope_ema_width_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema_width')[0]
		self.boll_mid_t1 = self.inds.get(d._name[:-1]+'1').get('bollinger').lines.mid[0]
		self.rsi_t1 = self.inds.get(d._name[:-1]+'1').get('rsi')[0]
		
		#Get Timeframe 2 Values
		self.slope_obv_t2 = self.inds.get(d._name[:-1]+'2').get('slope_obv')[0] #Get OBV slope
		self.slope_t2 = self.inds.get(d._name[:-1]+'2').get('slope')[0]  #Calc slope for time2
		self.slope_of_slope_t2 = self.inds.get(d._name[:-1]+'2').get('slope_of_slope')[0]  #Calc slope for time1
		self.ema1_t2 = self.inds.get(d._name[:-1]+'2').get('ema1')[0]
		self.ema2_t2 = self.inds.get(d._name[:-1]+'2').get('ema2')[0]
		self.slope_ema1_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema2')[0]
		self.slope_ema2_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema2')[0]
		self.adx_t2 = self.inds.get(d._name[:-1]+'2').get('adx')[0]
		self.slope_adx_t2 = self.inds.get(d._name[:-1]+'2').get('slope_adx')[0]
		self.slope_ema_width_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema_width')[0]
		self.boll_mid_t2 = self.inds.get(d._name[:-1]+'2').get('bollinger').lines.mid[0]
		self.rsi_2 = self.inds.get(d._name[:-1]+'2').get('rsi')[0]

		#Store in list so expressions can be 'scored' later
		mylist = [self.adx_t1 > 35,
				 self.adx_t2 > 35,
				 self.slope_adx_t1 < 0,
				 self.slope_adx_t2 < 0,
				 self.ema1_t1 > self.ema2_t1,
				 self.ema1_t2 > self.ema2_t2,
				 self.slope_ema1_t1 > 0,
				 self.slope_ema2_t1 > 0,
				 self.slope_ema_width_t1 < 0,
				 self.slope_ema_width_t2 < 0,
				 self.slope_t1 > 0,
				 self.slope_t2 > 0,
				 self.slope_of_slope_t1 < 0,
				 self.slope_of_slope_t2 < 0,
				 self.slope_obv_t1 < 0,
				 self.slope_obv_t2 < 0,
				 d.close[0] > self.boll_mid_t1,
				 d.close[0] > self.boll_mid_t2,
				 self.rsi_t1 < 70,
				 self.rsi_t2 < 70,
				 ]
		#Get length of list		
		mycount = len(mylist)
		#If 75% of list is true, return true
		if sum(mylist) > (mycount * .75):	#sum count true as 1, false as 0 	
			return True
		else:
			return False
	
	"""
	def mean_revert(self,d,direction):
		self.boll_top_t0 = self.inds.get(d._name[:-1]+'0').get('bollinger').lines.top[0]
		self.boll_bot_t0 = self.inds.get(d._name[:-1]+'0').get('bollinger').lines.bot[0]
		#self.boll_top_t1 = self.inds.get(d._name[:-1]+'1').get('bollinger').lines.top[0]
		#self.boll_bot_t1 = self.inds.get(d._name[:-1]+'1').get('bollinger').lines.bot[0]
		self.adx_t0 = self.inds.get(d._name).get('adx')[0]
		self.rsi_t0 = round(self.inds.get(d._name).get('rsi')[0],2)
		
		if d.close[0] >= self.boll_top_t1:
			return True
		elif d.close[0] <= 
	"""	


	def regime_neutral(self,d):
		#Define Variables
		
		#Calculate timeframe 1
		self.adx_t1 = self.inds.get(d._name[:-1]+'1').get('adx')[0]
		self.rsi_t1 = self.inds.get(d._name[:-1]+'1').get('rsi')[0]
		self.resistance_t1 = self.inds.get(d._name[:-1]+'1').get('resistance')[0]
		self.support_t1 = self.inds.get(d._name[:-1]+'1').get('support')[0]
		
		#Calculate timeframe 2
		self.adx_t2 = self.inds.get(d._name[:-1]+'2').get('adx')[0]
		self.rsi_t2 = self.inds.get(d._name[:-1]+'2').get('rsi')[0]
		self.resistance_t2 = self.inds.get(d._name[:-1]+'2').get('resistance')[0]
		self.support_t2 = self.inds.get(d._name[:-1]+'2').get('support')[0]

		#Define signal criteria
		#Store in list so expressions can be 'scored' later
		mylist = [self.adx_t1 < 20,
				 self.adx_t2 < 20,
				 self.rsi_t1 < 70,
				 self.rsi_t1 > 30,
				 self.rsi_t2 < 70,
				 self.rsi_t2 > 30,
				 d.close[0] < self.resistance_t1,
				 d.close[0] > self.support_t1,
				 d.close[0] < self.resistance_t2,
				 d.close[0] > self.support_t2,
				 ]
				 
		#Get length of list		
		mycount = len(mylist)
		#If 75% of list is true, return true
		if sum(mylist) > (mycount * .75):	#sum count true as 1, false as 0 	
			return True
		else:
			return False
		
	
	def regime_early_bear(self,d):
		#Trend underway, getting stronger
		#Get timeframe 0 values
		self.percK_t0 = self.inds.get(d._name).get('stochastic').lines.percK[0]
		
		#Get Timeframe 1 Values
		self.slope_obv_t1 = self.inds.get(d._name[:-1]+'1').get('slope_obv')[0] #Get OBV slope	
		self.slope_t1 = self.inds.get(d._name[:-1]+'1').get('slope')[0]  #Calc slope for time1
		self.slope_of_slope_t1 = self.inds.get(d._name[:-1]+'1').get('slope_of_slope')[0]  #Calc slope for time1
		self.ema1_t1 = self.inds.get(d._name[:-1]+'1').get('ema1')[0]
		self.ema2_t1 = self.inds.get(d._name[:-1]+'1').get('ema2')[0]
		self.slope_ema1_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema1')[0]
		self.slope_ema2_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema1')[0]
		self.adx_t1 = self.inds.get(d._name[:-1]+'1').get('adx')[0]
		self.slope_adx_t1 = self.inds.get(d._name[:-1]+'1').get('slope_adx')[0]
		self.slope_ema_width_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema_width')[0]
		self.boll_mid_t1 = self.inds.get(d._name[:-1]+'1').get('bollinger').lines.mid[0]
		
		#Get Timeframe 2 Values
		self.slope_obv_t2 = self.inds.get(d._name[:-1]+'2').get('slope_obv')[0] #Get OBV slope
		self.slope_t2 = self.inds.get(d._name[:-1]+'2').get('slope')[0]  #Calc slope for time2
		self.slope_of_slope_t2 = self.inds.get(d._name[:-1]+'2').get('slope_of_slope')[0]  #Calc slope for time1
		self.ema1_t2 = self.inds.get(d._name[:-1]+'2').get('ema1')[0]
		self.ema2_t2 = self.inds.get(d._name[:-1]+'2').get('ema2')[0]
		self.slope_ema1_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema2')[0]
		self.slope_ema2_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema2')[0]
		self.adx_t2 = self.inds.get(d._name[:-1]+'2').get('adx')[0]
		self.slope_adx_t2 = self.inds.get(d._name[:-1]+'2').get('slope_adx')[0]
		self.slope_ema_width_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema_width')[0]
		self.boll_mid_t2 = self.inds.get(d._name[:-1]+'2').get('bollinger').lines.mid[0]

		#Store in list so expressions can be 'scored' later
		mylist = [self.adx_t1 > 20,
				 self.adx_t2 > 20,
				 self.slope_adx_t1 < 0,
				 self.slope_adx_t2 < 0,
				 self.ema1_t1 < self.ema2_t1,
				 self.ema1_t2 < self.ema2_t2,
				 self.slope_ema1_t1 < 0,
				 self.slope_ema2_t1 < 0,
				 self.slope_ema_width_t1 < 0,
				 self.slope_ema_width_t2 < 0,
				 self.slope_t1 < 0,
				 self.slope_t2 < 0,
				 self.slope_of_slope_t1 < 0,
				 self.slope_of_slope_t2 < 0,
				 self.slope_obv_t1 < 0,
				 self.slope_obv_t2 < 0,
				 d.close[0] < self.boll_mid_t1,
				 d.close[0] < self.boll_mid_t2,
				 #self.percK_t0 > 70,
				 ]
		#Get length of list		
		mycount = len(mylist)
		#If 75% of list is true, return true
		if sum(mylist) > (mycount * .75):	#sum count true as 1, false as 0 	
			return True
		else:
			return False
	
	
	def regime_late_bear(self,d):
		#Late in trend, starting to top out - look to exit short position or initiate long position
		#Get Timeframe 1 Values
		self.slope_obv_t1 = self.inds.get(d._name[:-1]+'1').get('slope_obv')[0] #Get OBV slope	
		self.slope_t1 = self.inds.get(d._name[:-1]+'1').get('slope')[0]  #Calc slope for time1
		self.slope_of_slope_t1 = self.inds.get(d._name[:-1]+'1').get('slope_of_slope')[0]  #Calc slope for time1
		self.ema1_t1 = self.inds.get(d._name[:-1]+'1').get('ema1')[0]
		self.ema2_t1 = self.inds.get(d._name[:-1]+'1').get('ema2')[0]
		self.slope_ema1_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema1')[0]
		self.slope_ema2_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema1')[0]
		self.adx_t1 = self.inds.get(d._name[:-1]+'1').get('adx')[0]
		self.slope_adx_t1 = self.inds.get(d._name[:-1]+'1').get('slope_adx')[0]
		self.slope_ema_width_t1 = self.inds.get(d._name[:-1]+'1').get('slope_ema_width')[0]
		self.boll_mid_t1 = self.inds.get(d._name[:-1]+'1').get('bollinger').lines.mid[0]
		self.rsi_t1 = self.inds.get(d._name[:-1]+'1').get('rsi')[0]
		
		#Get Timeframe 2 Values
		self.slope_obv_t2 = self.inds.get(d._name[:-1]+'2').get('slope_obv')[0] #Get OBV slope
		self.slope_t2 = self.inds.get(d._name[:-1]+'2').get('slope')[0]  #Calc slope for time2
		self.slope_of_slope_t2 = self.inds.get(d._name[:-1]+'2').get('slope_of_slope')[0]  #Calc slope for time1
		self.ema1_t2 = self.inds.get(d._name[:-1]+'2').get('ema1')[0]
		self.ema2_t2 = self.inds.get(d._name[:-1]+'2').get('ema2')[0]
		self.slope_ema1_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema2')[0]
		self.slope_ema2_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema2')[0]
		self.adx_t2 = self.inds.get(d._name[:-1]+'2').get('adx')[0]
		self.slope_adx_t2 = self.inds.get(d._name[:-1]+'2').get('slope_adx')[0]
		self.slope_ema_width_t2 = self.inds.get(d._name[:-1]+'2').get('slope_ema_width')[0]
		self.boll_mid_t2 = self.inds.get(d._name[:-1]+'2').get('bollinger').lines.mid[0]
		self.rsi_t2 = self.inds.get(d._name[:-1]+'2').get('rsi')[0]

		#Store in list so expressions can be 'scored' later
		mylist = [self.adx_t1 > 35,
				 self.adx_t2 > 35,
				 self.slope_adx_t1 < 0,
				 self.slope_adx_t2 < 0,
				 self.ema1_t1 < self.ema2_t1,
				 self.ema1_t2 < self.ema2_t2,
				 self.slope_ema1_t1 < 0,
				 self.slope_ema2_t1 < 0,
				 self.slope_ema_width_t1 > 0,
				 self.slope_ema_width_t2 > 0,
				 self.slope_t1 < 0,
				 self.slope_t2 < 0,
				 self.slope_of_slope_t1 > 0,
				 self.slope_of_slope_t2 > 0,
				 self.slope_obv_t1 > 0,
				 self.slope_obv_t2 > 0,
				 d.close[0] < self.boll_mid_t1,
				 d.close[0] < self.boll_mid_t2,
				 self.rsi_t1 < 30,
				 self.rsi_t2 < 30,
				 ]
		#Get length of list		
		mycount = len(mylist)
		#If 75% of list is true, return true
		if sum(mylist) > (mycount * .75):	#sum count true as 1, false as 0 	
			return True
		else:
			return False
	
	
	def rank_correl(self,d,df):
		"""Returns most highly correlated pairs of stocks, and correlation value, from ticker list via 2 key, 1 value dict"""
		mycorr = df.corr(method='pearson')
		np.fill_diagonal(mycorr.values, np.nan)  #replace 1's with NA's in correlations matrix
		spy_ranked = mycorr["SPY1"].sort_values(ascending=False).dropna() #get just SPY column in dataframe, then sort
		print(f'Top Positive Correlations to SPY: {spy_ranked.nlargest(self.p.rank)} Top Negative: {spy_ranked.nsmallest(self.p.rank)}')
		print(f'Return just ticker names of top SPY correlations: {spy_ranked.nlargest(self.p.rank).index}')	#returns ticker pair list of highest ranked correlations
		"""
		rank_all = mycorr.unstack().sort_values(kind="quicksort",ascending=False).dropna().drop_duplicates()	#returns all correlations, ranked hishest to lowest
		#print(rank_all)
		print(f'Top Positive Correlations: {rank_all.nlargest(3)} Top Negative: {rank_all.nsmallest(3)}')
		print(f'Return just ticker names of top correlations: {rank_all.nlargest(3).index}')	#returns ticker pair list of highest ranked correlations
		"""
		
	def grangers_causation_matrix(self,data, variables, test='ssr_chi2test', verbose=True):    
		"""Check Granger Causality of all possible combinations of the Time series.
		Y is the response variable, X are predictors. The values in the table 
		are the P-Values. P-Values lesser than the significance level (0.05), implies 
		the Null Hypothesis that the coefficients of the corresponding past values is 
		zero, that is, the X does not cause Y can be rejected.

		data      : pandas dataframe containing the time series variables
		variables : list containing names of the time series variables.
		
		Output Example:
		Y = SPY1, X = SPY1, P Values = [1.0, 1.0, 1.0, 1.0, 1.0]
		Y = XLU1, X = SPY1, P Values = [0.5009, 0.4085, 0.3347, 0.105, 0.006]
		Y = XHB1, X = SPY1, P Values = [0.7069, 0.7361, 0.304, 0.0065, 0.0063]
		
		if you look at row 2, it refers to the p-value of SPY1(X) causing XLU1(Y). 
		If a given p-value is < significance level (0.05), then, the corresponding X series causes the Y.
		Looking at the P-Values in the above table, you can pretty much observe that all the variables (time series) in the system are interchangeably causing each other.
		if most pvalues in output are less than significance level, then system good candidate for using Vector Auto Regression models to forecast. 
		"""
		
		df = pd.DataFrame(np.zeros((len(variables), len(variables))), columns=variables, index=variables)
		maxlag=len(variables)
		for c in df.columns:
			for r in df.index:
				test_result = ts.grangercausalitytests(data[[r, c]], maxlag=maxlag, verbose=False)
				p_values = [test_result[i+1][0][test][1] for i in range(maxlag)]
				if verbose: print(f'Y = {r}, X = {c}, P Values = {p_values}')
				min_p_value = np.min(p_values)
				df.loc[r, c] = min_p_value
		df.columns = [var + '_x' for var in variables]
		df.index = [var + '_y' for var in variables]
		return df
				
		#self.grangers_causation_matrix(self.df_closes, variables = self.df_closes.columns)

#********************************************RUN STRATEGY FUNCTION*********************************************************************
def runstrat():	
	
	cerebro = bt.Cerebro(exactbars=-1) #Create an instance of cerebro.  exactbars True reduces memory usage significantly, but change to '-1' for partial memory savings (keeping indicators in memory) or 'false' to turn off completely if having trouble accessing bars beyond max indicator paramaters.  
	cerebro.broker.set_shortcash(True) #False means decrease cash available when you short, True means increase it
	cerebro.addstrategy(Strategy)	#Add our strategy to cerebro

	#Determine data and time range to run
	modelp = UserInputs.model_params()
	start_date = modelp.get('start_date')
	end_date = modelp.get('end_date')
	session_start = modelp.get('sessionstart')
	session_end = modelp.get('sessionend')	
	
	#Add data
	if not modelp.get('live_status'):
		data_backtest(cerebro,start_date,end_date,session_start,session_end)
	else:
		data_live(cerebro,session_start,session_end)

	#Add analysis to cerebro
	add_analysis(cerebro) #get all the result analysis

	results = cerebro.run(preload=False,
					stdstats=False, #enables some additional chart information like profit/loss, buy/sell, etc, but tends to clutter chart
					runonce=False
					)
	
	#Print analyzers from results			
	for n in results[0].analyzers:
		n.print()
	
	#Access Results(strategy dictionaries, parameters, etc. after program runs)
	"""
	#print(dir(results[0]))  #returns list of all attributes and methods associated with results object
	for i,d in enumerate(results[0].datas):
		print(d._name,results[0].sorted_dict)
		print(d.open.array)
	"""
	
	#csv_output(cerebro)  #output to csv
	
	#Plot results 	
	"""
	for i in range (0,len(results[0].datas),3):
		for j, d in enumerate(results[0].datas):
			d.plotinfo.plot = i ==j
		#cerebro.plot(barup='olive', bardown='lightpink',volup = 'lightgreen',voldown='crimson')
		cerebro.plot(barup='olive', bardown='lightpink',volume=False)
	"""
#************************************************************************************************************************************			
def data_live(cerebro,session_start,session_end):
	modelp = UserInputs.model_params()
	
	ibforex_datalist = UserInputs.datalist('forex')
	ibdatalist = UserInputs.datalist('ib')
	#Ensure stock lists have no duplicates - duplicates will BREAK program
	if len(ibdatalist) != len(set(ibdatalist)):
		print("*****You have duplicates in stock list - FIX LIST*****")
	
	#Determine configuration to connect to Interactive Brokers
	store = bt.stores.IBStore(host='127.0.0.1',
							port=7497,
							clientId = 100,
							indcash = True)
	
	for i,j in enumerate(ibdatalist):
		#Data for live IB trading
		data = store.getdata(dataname=j,
							sectype='STK',
							exchange='SMART',
							currency='USD',
							timeframe=bt.TimeFrame.Minutes,
							tz = pytz.timezone('US/Central'),
							sessionstart = session_start,
							sessionend = session_end,
							useRTH = True,
							)
							
							
		cerebro.resampledata(data, name="{}0".format(j),timeframe=bt.TimeFrame.Minutes, compression=modelp.get('timeframe0'))

		#Apply resamplings
		if modelp.get('t1_on'):
			data_Timeframe1 = cerebro.resampledata(data,name="{}1".format(j),
													timeframe=bt.TimeFrame.Minutes,
													compression = modelp.get('timeframe1'))
		
		if modelp.get('t2_on'):
			data_Timeframe2 = cerebro.resampledata(data,name="{}2".format(j),
													timeframe=bt.TimeFrame.Minutes,
													compression = modelp.get('timeframe2'))
						
#-----------------------------------------------------------------------------------------------------------------------------------						
	
	for i,j in enumerate(ibforex_datalist):
		#Data for live IB trading
		forexdata = store.getdata(dataname=j,
							sectype='CASH',
							exchange='IDEALPRO',
							currency='USD',
							timeframe=bt.TimeFrame.Minutes,
							what = 'MIDPOINT',  #Needs to be midpoint for FOREX or won't work
							tz = pytz.timezone('US/Central'),
							sessionstart = session_start,
							sessionend = session_end,
							)
							
		cerebro.resampledata(forexdata, name="{}0".format(j),timeframe=bt.TimeFrame.Minutes, compression=modelp.get('timeframe0'))

		#Apply resamplings
		if modelp.get('t1_on'):
			data_Timeframe1 = cerebro.resampledata(forexdata,name="{}1".format(j),
													timeframe=bt.TimeFrame.Minutes,
													compression = modelp.get('timeframe1'))
		
		if modelp.get('t2_on'):
			data_Timeframe2 = cerebro.resampledata(forexdata,name="{}2".format(j),
													timeframe=bt.TimeFrame.Minutes,
													compression = modelp.get('timeframe2'))			
	
#------------------------------------------------------------------------------------------------------------------------------------
	#ADD MARKET BREADTH DATA LIKE TICK
	if modelp.get('nysetick_on'):
		tickdata = store.getdata(dataname='TICK-NYSE',
								sectype='IND',
								exchange='NYSE',
								currency='USD',
								timeframe=bt.TimeFrame.Minutes,
								what = 'TRADES',  #Needs to be 'TRADES' for TICK-NYSE to pull data
								rtbar = False,
								sessionstart = session_start,
								sessionend = session_end,
								)
								
		cerebro.resampledata(tickdata, name="{}0".format('TICK-NYSE'),
							timeframe=bt.TimeFrame.Minutes, 
							compression=modelp.get('timeframe0'))
		
		"""
		#Apply resamplings
		if modelp.get('t1_on'):
			tickdata_Timeframe1 = cerebro.resampledata(tickdata,name="{}1".format('TICK-NYSE'),
														timeframe=bt.TimeFrame.Minutes,
														compression = modelp.get('timeframe1'))
			
		if modelp.get('t2_on'):
			tickdata_Timeframe2 = cerebro.resampledata(tickdata,name="{}2".format('TICK-NYSE'),
														timeframe=bt.TimeFrame.Minutes,
														compression = modelp.get('timeframe2'))	
		"""
													
	cerebro.broker = store.getbroker()  #*****Critical line of code to access broker so you can trade*****


def data_backtest(cerebro,start_date,end_date,session_start,session_end):
	modelp = UserInputs.model_params()
	
	datalist = UserInputs.datalist('hist')
	if len(datalist) != len(set(datalist)):
		print("*****You have duplicates in stock list - FIX LIST*****")
	
	#define mysql configuration items for connection
	host = '127.0.0.1'
	user = 'root'
	password = 'EptL@Rl!1'
	database = 'Stock_Prices'
	table = '5_min_prices'
	
	for i,j in enumerate(datalist):
		#Get data from mysql and add data to Cerebro
		data = mysql.MySQLData(dbHost = host,
								dbUser = user,
								dbPWD = password,
								dbName = database,
								table = table,
								symbol = j,  
								fromdate = start_date,
								todate= end_date,
								sessionstart = session_start,
								sessionend = session_end,
								compression = modelp.get('timeframe0'),
								)
		if modelp.get('t0_on'):	
			cerebro.adddata(data, name="{}0".format(j))

		if modelp.get('t1_on'):
			#Apply resamplings			
			data_Timeframe1 = cerebro.resampledata(data,
									name="{}1".format(j),
									timeframe=bt.TimeFrame.Minutes,
									compression = modelp.get('timeframe1'),
									)

		if modelp.get('t2_on'):
			data_Timeframe2 = cerebro.resampledata(data,
									name="{}2".format(j),
									timeframe=bt.TimeFrame.Minutes,
									compression = modelp.get('timeframe2'),
									)

	# Set our desired cash start
	cerebro.broker.setcash(modelp.get('start_cash'))
	
	# Set the commission
	cerebro.broker.setcommission(commission=0.00003,
								margin= None,
								mult=1.0,
								commtype=None,
								percabs=True,
								stocklike=True,
								leverage=1)
	
	"""
	#Set the slippage
	cerebro.broker.set_slippage_perc(0.001,
									slip_open=True, 
									slip_limit=True,
									slip_match=True,
									slip_out=False)
	"""
	
def add_analysis(cerebro):
	# Add SQN to qualify the trades (rating to analyze quality of trading system: 2.5-3 good, above 3 excellent.  SquareRoot(NumberTrades) * Average(TradesProfit) / StdDev(TradesProfit).  Need at least 30 trades to be reliable
	cerebro.addanalyzer(bt.analyzers.SQN)
	cerebro.addanalyzer(bt.analyzers.SharpeRatio)
	cerebro.addanalyzer(bt.analyzers.AcctStats)
	cerebro.addanalyzer(bt.analyzers.DrawDown)
	# Add TradeAnalyzer to output trade statistics - THESE ARE THE TRADE NOTIFICATIONS THAT ARE PRINTED WHEN PROGRAM IS RUN
	cerebro.addanalyzer(bt.analyzers.Transactions)
	cerebro.addobservermulti(bt.observers.BuySell)
	cerebro.addobserver(bt.observers.AcctValue) #reports trade statistics in command prompt at end of program run
	#cerebro.addobserver(bt.observers.OrderObserver) #reports trades in output window when program is run


def csv_output(cerebro):
	#Generate output report in csv format
	if UserInputs.model_params().get('writer')=='on':
		current_time = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.csv") 
		csv_file = 'C:/Program Files (x86)/Python36-32/Lib/site-packages/backtrader/out/'
		csv_file += 'Strategy'
		csv_file += current_time
		cerebro.addwriter(bt.WriterFile, csv = True, out=csv_file)
		print("Writer CSV Report On and report generated")

#**********************************************RUN ENTIRE PROGRAM**********************************************************************						
if __name__ == '__main__':
	
	#Run strategy
	runstrat()
	

"""

		#INITIALIZATION
			
			#Relative Volume by Bar
			self.inds[d._name]['rel_volume'] = btind.RelativeVolumeByBar(d,
											start = self.modelp.get('sessionstart'),
											end = self.modelp.get('sessionend'),
											plot=False)
					
			
			#Calculate VWAP																			
			self.inds[d._name]['vwap'] = btind.vwap(d,
													plot=False)
			
			#Determine current ohlcv bars
			self.inds[d._name]['ohlc'] = btind.ohlc(d,
											period=self.p.ohlc,
											plot=False)
			
			#Determine same bar, prior day
			self.inds[d._name]['priorday'] = btind.priorday(d,
															plot=False)
			
													
			#Moving Average Indicators - FAST, SLOW, and CROSS
			self.inds[d._name]['sma1'] = btind.SMA(d,
													period=self.p.sma1,
													plot=False)
													
			self.inds[d._name]['sma2'] = btind.SMA(d,
													period=self.p.sma2,
													plot=False)										
			
			
			self.inds[d._name]['ema1'] = btind.EMA(d,
													period=self.p.ema1,
													plot=True)
														
			self.inds[d._name]['ema2'] = btind.EMA(d,
													period=self.p.ema2,
													plot=True)
																				
			self.inds[d._name]['cross'] = btind.CrossOver(self.inds[d._name]['ema1'],
													self.inds[d._name]['ema2'],
													plot=False)
			
			#RSI
			self.inds[d._name]['rsi']= btind.RSI(d,
												period=self.p.rsi,
												safediv=True,
												plot=False)
					
		
			#Bollinger Band
			self.inds[d._name]['bollinger'] = btind.BollingerBands(d.close,
														period=self.p.bollinger_period,
														devfactor = self.p.bollinger_dist,
														plot=True)
														
	
			
			#Stochastics - just prints Slow %d line (not %K also which would be "StochasticFast")
			self.inds[d._name]['stochastic'] = btind.StochasticSlow(d,
														period=self.p.stoch_per,
														period_dfast= self.p.stoch_fast,
														safediv=True,
														plot=False)
			
			#ADX
			self.inds[d._name]['adx'] = btind.ADX(d,
												period=self.p.adx,
												plot=False)
												
			#Pivots
			self.inds[d._name]['pivots'] = btind.pivotpoint.PivotPoint(d,
														plot=False)
													
		
			#Highest and Lowest Values of Period Indicator
			self.inds[d._name]['highest'] = btind.Highest(d.high,
														period=self.p.breakout_per,
														plot=False)
																							
			self.inds[d._name]['lowest'] = btind.Lowest(d.low,
														period=self.p.breakout_per,
														plot=False)
			
			self.inds[d._name]['slope_of_slope'] = 	btind.Slope(self.inds[d._name]['slope'],
												period=self.p.slope_period,
												plot=False)	
											
			self.inds[d._name]['slope_of_slope_obv'] = 	btind.Slope(self.inds[d._name]['slope_obv'],
												period=self.p.slope_period,
												plot=False)	
				
			self.inds[d._name]['slope_ema1'] = 	btind.Slope(self.inds[d._name]['ema1'],
													period=self.p.slope_period,
													plot=False)	
			
			self.inds[d._name]['slope_ema2'] = 	btind.Slope(self.inds[d._name]['ema2'],
													period=self.p.slope_period,
													plot=False)	
			
			self.inds[d._name]['slope_sma1'] = 	btind.Slope(self.inds[d._name]['sma1'],
													period=self.p.slope_period,
													plot=False)									
													
			self.inds[d._name]['slope_of_slope_sma1'] = btind.Slope(self.inds[d._name]['slope_sma1'],
													period=self.p.slope_period,
													plot=False)										
			
													
			self.inds[d._name]['slope_of_slope_sma1'] = btind.Slope(self.inds[d._name]['slope_sma1'],
													period=self.p.slope_period,
													plot=False)
													
			self.inds[d._name]['slope_sma_width'] = btind.Slope(self.inds[d._name]['sma1']-self.inds[d._name]['sma2'],
													period=self.p.slope_period,
													plot=False)	
													
			self.inds[d._name]['slope_ema_width'] = btind.Slope(self.inds[d._name]['ema1']-self.inds[d._name]['ema2'],
													period=self.p.slope_period,
													plot=False)										
													
			self.inds[d._name]['slope_adx'] = 	btind.Slope(self.inds[d._name]['adx'],
													period=self.p.slope_period,
													plot=False)	
													
			self.inds[d._name]['slope_of_slope_adx'] = 	btind.Slope(self.inds[d._name]['slope_adx'],
													period=self.p.slope_period,
													plot=False)	
													
			self.inds[d._name]['slope_rsi'] = 	btind.Slope(self.inds[d._name]['rsi'],
													period=self.p.slope_period,
													plot=False,
													plotname = 'Slope_RSI')
													
			self.inds[d._name]['slope_of_slope_rsi'] = 	btind.Slope(self.inds[d._name]['slope_rsi'],
													period=self.p.slope_period,
													plot=False,
													plotname = 'Slope_of_Slope_RSI')									
													
			self.inds[d._name]['slope_ema1'] = 	btind.Slope(self.inds[d._name]['ema1'],
													period=self.p.slope_period,
													plot=False,
													plotname = 'Slope_EMA1')
			self.inds[d._name]['slope_ema2'] = 	btind.Slope(self.inds[d._name]['ema2'],
													period=self.p.slope_period,
													plot=False,
													plotname = 'Slope_EMA2')
			
													
			self.inds[d._name]['resistance'] = btind.Resistance(d,
															period=self.p.lookback,
															min_touches = self.p.min_touches,
															tolerance_perc = self.p.tolerance_perc,
															bounce_perc = self.p.bounce_perc,
															plot=False)	
			
			self.inds[d._name]['support'] = btind.Support(d,
															period=self.p.lookback,
															min_touches = self.p.min_touches,
															tolerance_perc = self.p.tolerance_perc,
															bounce_perc = self.p.bounce_perc,
															plot=False)
			
			#Calculate Hammer Candle Signal								
			self.inds[d._name]['hammer'] = btind.HammerCandles(d,
													plot=False)											

			#Calculate Engulfing Candle Signal								
			self.inds[d._name]['engulfing'] = btind.EngulfingCandles(d,
													plot=False)	
													
			#Calculate Engulfing Candle Signal								
			self.inds[d._name]['three_line_strike'] = btind.three_line_strike(d,
													plot=False)										

			#Plot ADX and Stochastic on same subplot as stochastic							
			#self.inds[d._name]['adx'].plotinfo.plotmaster = self.inds[d._name]['stochastic']
		
		
		
		
		#FOR TRADE SIGNALS
		self.obv_t0 = self.inds.get(d._name).get('obv')[0]
		self.slope_obv_t0 = self.inds.get(d._name).get('slope_obv')[0]
		#self.slope_of_slope_obv_t0 = self.inds.get(d._name).get('slope_of_slope_obv')[0]
		#print(d._name, self.hourmin,d.volume[0],self.obv_t0,self.slope_obv_t0)
		
		#Determine current ohlcv prices
		self.open_t0 = self.inds.get(d._name).get('ohlc').lines.o[0]
		self.high_t0 = self.inds.get(d._name).get('ohlc').lines.h[0]
		self.low_t0 = self.inds.get(d._name).get('ohlc').lines.l[0]
		self.close_t0 = self.inds.get(d._name).get('ohlc').lines.c[0]
		self.volume_t0 = self.inds.get(d._name).get('ohlc').lines.v[0]
		
		self.open_t1 = self.inds.get(self.name_t1).get('ohlc').lines.o[0]
		self.high_t1 = self.inds.get(self.name_t1).get('ohlc').lines.h[0]
		self.low_t1 = self.inds.get(self.name_t1).get('ohlc').lines.l[0]
		self.close_t1 = self.inds.get(self.name_t1).get('ohlc').lines.c[0]
		self.volume_t1 = self.inds.get(self.name_t1).get('ohlc').lines.v[0]
		
		self.open_t2 = self.inds.get(self.name_t2).get('ohlc').lines.o[0]
		self.high_t2 = self.inds.get(self.name_t2).get('ohlc').lines.h[0]
		self.low_t2 = self.inds.get(self.name_t2).get('ohlc').lines.l[0]
		self.close_t2 = self.inds.get(self.name_t2).get('ohlc').lines.c[0]
		self.volume_t2 = self.inds.get(self.name_t2).get('ohlc').lines.v[0]
		#print (d._name, self.dt, self.hourmin,self.open_t0,self.open_t1,self.open_t2)
		
		#To calculate prior day o,h,l,c - do not need other timeframes because same value across timeframes
		#self.pday_open_t0 = self.inds.get(d._name).get('priorday').lines.prior_open[0]
		self.pday_high_t0 =  self.inds.get(d._name).get('priorday').lines.prior_high[0]
		self.pday_low_t0 =  self.inds.get(d._name).get('priorday').lines.prior_low[0]
		#self.pday_close_t0 =  self.inds.get(d._name).get('priorday').lines.prior_close[0]
		#self.pday_volume_t0 =  self.inds.get(d._name).get('priorday').lines.prior_volume[0]
		#print(d._name,self.dt, self.hourmin, self.pday_open_t0,self.pday_high_t0,self.pday_low_t0,self.pday_close_t0,self.pday_volume_t0,)

		#Set support and resistance levels - MAKE SURE TO DEFINE CONDITION THAT PRICE IS ABOVE SUPPORT AND BELOW RESISTANCE
		#self.resistance_t0 = self.inds.get(d._name).get('resistance')[0]
		#self.resistance_t1 = self.inds.get(self.name_t1).get('resistance')[0]
		#self.resistance_t2 = self.inds.get(self.name_t2).get('resistance')[0]
		
		#self.support_t0 = self.inds.get(d._name).get('support')[0]
		#self.support_t1 = self.inds.get(self.name_t1).get('support')[0]
		#self.support_t2 = self.inds.get(self.name_t2).get('support')[0]
	
		#Calculate VWAP	
		self.vwap_t0 = self.inds.get(d._name).get('vwap').lines.vwap[0]
		self.vwap_t1 = self.inds.get(self.name_t1).get('vwap').lines.vwap[0]
		
		
		#Calculate Moving Averages
		#self.sma1_t0 = self.inds.get(d._name).get('sma1')[0]
		#self.sma1_t1 = self.inds.get(self.name_t1).get('sma1')[0]
		#self.sma2_t1 = self.inds.get(self.name_t1).get('sma1')[0]
		#self.sma1_t2 = self.inds.get(self.name_t2).get('sma2')[0]
		#self.sma2_t2 = self.inds.get(self.name_t2).get('sma2')[0]
		#self.ema1_t0 = self.inds.get(d._name).get('ema1')[0]
		#self.ema1_t1 = self.inds.get(self.name_t1).get('ema1')[0]
		#self.cross_t0 = self.inds.get(d._name).get('cross')[0]

		
		#self.vixsma_t0 = round(self.inds.get('VIX0').get('sma1')[0],3) #holds just VIX0 sma data
		#self.spysma_t0 = round(self.inds.get('SPY0').get('sma1')[0],3) #holds just SPY0 sma data
		#self.ticksma_t0 = round(self.inds.get('TICK-NYSE0').get('sma1')[0],3)  #holds just TICK0 sma data
		#self.trinsma_t0 = round(self.inds.get('TRIN-NYSE0').get('sma1')[0],3)  #holds just TRIN0 sma data
							
		#Calculate slopes
		self.slope_t0 = self.inds.get(d._name).get('slope')[0]
		
		
		#Determine if space between SMA1 and SMA2 is widening or contracting 
		#self.slope_sma_width_t1 = round(self.inds.get(self.name_t1).get('slope_sma_width')[0],3)
		
		#self.slope_ema1_t1 = self.inds.get(self.name_t1).get('slope_ema1')[0]
		#self.slope_ema2_t1 = self.inds.get(self.name_t1).get('slope_ema2')[0]
		
		#self.slope_sma1_t1 = self.inds.get(self.name_t1).get('slope_sma1')[0]
		#self.slope_of_slope_sma1_t1 = self.inds.get(self.name_t1).get('slope_of_slope_sma1')[0]
		#self.slope_of_slope_sma1_t2 = self.inds.get(self.name_t2).get('slope_of_slope_sma1')[0]
		
		#self.slope_adx_t1 = self.inds.get(self.name_t1).get('slope_adx')[0]
		#self.slope_of_slope_adx_t1 = self.inds.get(self.name_t1).get('slope_of_slope_adx')[0]
		
		#self.slope_rsi_t1 = self.inds.get(self.name_t1).get('slope_rsi')[0]
		#self.slope_of_slope_rsi_t1 = self.inds.get(self.name_t1).get('slope_of_slope_rsi')[0]
		
		#Calculate RSI
		#self.rsi_t1 = round(self.inds.get(self.name_t1).get('rsi')[0],2)
		
		#Calculate Bollinger Bands
		
		#self.boll_top_t0 = self.inds.get(d._name).get('bollinger').lines.top[0]
		#self.boll_bot_t0 = self.inds.get(d._name).get('bollinger').lines.bot[0]
		#self.boll_mid_t0 = self.inds.get(d._name).get('bollinger').lines.mid[0]
		#print(d._name, self.dt, self.hourmin, self.vwap_t0, d.close[0], self.boll_top_t0,self.boll_bot_t0)
		
		#Calculate Stochastic lines
		#self.percK_t0 = round(self.inds.get(d._name).get('stochastic').lines.percK[0],3)
		#self.percK_t1 = round(self.inds.get(self.name_t1).get('stochastic').lines.percK[0],3)
		#self.percD_t1 = round(self.inds.get(self.name_t1).get('stochastic').lines.percD[0],3)
		
		#Calculate ADX - Average Directional Movement Index to measure trend strength
		#self.adx_t1 = round(self.inds.get(self.name_t1).get('adx')[0],3)
		#self.adx_t2 = round(self.inds.get(self.name_t2).get('adx')[0],3)
		
		#Calculate highest and lowest indicators
		#self.highest_t1 = round(self.inds.get(self.name_t1).get('highest')[0],3) 
		#self.lowest_t1 = round(self.inds.get(self.name_t1).get('lowest')[0],3) 
		
		#Determine open gap
		#self.gap = round(self.inds.get(d._name).get('gap').lines.gap[0],3) 
		
							
		#print(self.dt, self.hourmin, d.high[0], d.low[0], self.gap,self.rng_high,self.rng_low)
		
		#Calculate Candlestick Patterns - if returns 1, bullish, -1 is bearish
		#self.engulfing_pattern_t0= self.inds.get(d._name).get('engulfing')[0]
		#self.hammer_t0= self.inds.get(d._name).get('hammer')[0]
		#self.three_line_strike_t0= self.inds.get(d._name).get('three_line_strike')[0]
		#print(d._name,self.dt,self.hourmin,self.hammer_t0)
		
		
		
		self.rel_volume_dict[d._name].append(self.rel_volume_t0) 
		
		#To optimize memory, keep dictionary size to 5 items
		if len(self.rel_volume_dict[d._name])==6:
			del self.rel_volume_dict[d._name][-6]
"""	



#****************************************************************************************************************************

"""
Primer on Classes and Objects
Example:
#*************************
class Point:

    def __init__(self):
        self.x = 0
        self.y = 0
#*************************
Every class should have a method with the special name __init__. This initializer method is automatically called whenever a new 
instance of Point is created. It gives the programmer the opportunity to set up the attributes required within the new instance 
by giving them their initial state/values. The self parameter (we could choose any other name, but self is the convention) is 
automatically set to reference the newly created object that needs to be initialized.

So let’s use our new Point class now:

p = Point()         # Instantiate an object of type Point
q = Point()         # Make a second point
   
print(p.x, p.y, q.x, q.y)  # Each point object has its own x and y

This program prints:  0 0 0 0   because during the initialization of the objects, we created two attributes called 
x and y for each, and gave them both the value 0.


Improving the initializer:
To create a point at position (7, 6) currently needs three lines of code:

p = Point()
p.x = 7
p.y = 6

We can make our class constructor more general by placing extra parameters into the __init__ method, as shown in this example:


class Point:
	#Point class represents and manipulates x,y coords.

	def __init__(self, x=0, y=0):
		#Create a new point at x, y
		self.x = x
		self.y = y

# Other statements outside the class continue below here.

The x and y parameters here are both optional. If the caller does not supply arguments, they’ll get the default values of 0. 
Here is our improved class in action:

    >>> p = Point(4, 2)
    >>> q = Point(6, 3)
    >>> r = Point()       # r represents the origin (0, 0)
    >>> print(p.x, q.y, r.x)
    4 3 0

Now lets add a method.  A method behaves like a function but it is invoked on a specific instance. 
Like a data attribute, methods are accessed using dot notation.

class Point:
    #Create a new Point, at coordinates x, y

    def __init__(self, x=0, y=0):
        #Create a new point at x, y
        self.x = x
        self.y = y

    def distance_from_origin(self):
        #Compute my distance from the origin
        return ((self.x ** 2) + (self.y ** 2)) ** 0.5

Let’s create a few point instances, look at their attributes, and call our new method on them:
>>> p = Point(3, 4)
>>> p.x
3
>>> p.y
4
>>> p.distance_from_origin()
5.0
>>> q = Point(5, 12)
>>> q.x
5
>>> q.y
12
>>> q.distance_from_origin()
13.0
>>> r = Point()
>>> r.x
0
>>> r.y
0
>>> r.distance_from_origin()
0.0

When defining a method, the first parameter refers to the instance being manipulated. As already noted, it is customary 
to name this parameter self.  Notice that the caller of distance_from_origin does not explicitly supply an argument to 
match the self parameter — this is done for us, behind our back.

Here is an example of passing a paramater through a simple function involving our new Point objects:

def print_point(pt):
    print("({0}, {1})".format(pt.x, pt.y))

print_point takes a point as an argument and formats the output in whichever way we choose. If we call print_point(p) 
with point p as defined previously, the output is (3, 4).
"""







