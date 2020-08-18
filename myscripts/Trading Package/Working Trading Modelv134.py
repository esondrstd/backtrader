"""
Trading model that can use multiple symbols, multiple timeframes, multiple indicators, and different start/end dates and analytics.
1 primary data feed (5 min timeframe) is sourced from mysql (but can be sourced elsewhere), and then 2 additional data feeds(resampled datafeeds)
created for 3 additional higher timeframes.  Data feeds are as follows:  data0 = 5min, data1= 15min, data2 = 60min, data3 = 1day.
Each symbol can be accessed in each timeframe.  For example, MSFT and XOM would be appear as:
data0 MSFT (base timeframe), data0 XOM(base timeframe), data1 MSFT(next higher timeframe), data1 XOM, data2 MSFT, data2 XOM, data3 MSFT(highest timeframe), data3 XOM - a total of 8 'datas'.
Indicators can also be treated as a datafeed input, i.e. slope of ema indicator.
Each data produces a "line" of data that includes everything from the data feed, i.e. Open, high, low, close etc.  System iterates over each line via next() function to produce its results.

Strategies:
1.  Mean Reversion (from double top/bottom - price breaks through prior day high/low than short/buy when price falls back just below/above prior day high/low to average like sma, vwap, etc.) - more opportunities than trending
2.  Trending (buy first oversold cycle of trend when stochastic falls under 20) - account for distance and angle of pullback (small pullback at slight angle more bullish than deeper pullback at sharp angle).  Shape of pullback important - is it intermittant staircase move with sellers pushing prices down (bad, think 2 or 3 big red candle moves on pullback mixed with small green bars), or is it multiple long candle tails with small green bodies which is more bullish) Also, less volume on pullback better.
 -for trending strategies, wider stop = more profits (no stop is best, but most risky)
3.  VWAP trading - use as support/resistance/target for above 2 strategies

Pairs Trading: 
1.  Determine optimal hedge ratio via linear regression(use Beta, i.e. slope)
2.  Use regression equation just created (hedge ratio and constant) to see how model predict performance of "portfolio" of 2 stocks (a pair)
3.  Take errors generated from predictive model vs actual prices and feed into ADF test to see if "portfolio" is stationary and cointegrated
4.  if p value from ADF test is less than signficance level (usually .05 for 95% significance), than pair is cointegrating
5.  **Result could change if you switch dependent and independent variables, however Johansen test hedge ratio provides both in test.  Johansen test also tests for cointegration
6.  Johansen test can also test your entire pairs portfolio (to create a mean reverting portfolio), and optimize weights of each pair position across portfolio
"""

#IMPORT MODULES
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

class UserInputs():
	#This class is designed so runstrat() method can pick up these parameters (can use self.p.whatever to pass parameters for some reason)

	def datalist(data_req):
		#Create list of tickers to load data for.  Market Breadth indicators need to be removed from initiliazation and next() so they are not traded
		#Data Notes - 'EMB' and 'SHY' data starts 8/3/2017, 'DBA' has almost double the amount of records the other tickers do for some reason.
		#TICK is # of NYSE stocks trading on an uptick vs # of stocks trading on downtick.  About 2800 stocks total, usually oscillates between -500 to +500.  Readings above 1000 or below -1000 considered extreme.  #TRIN is ratio of (# of Advance/Decliners)/(Advance/Decline Volume).  Below 1 is strong rally, Above 1 is strong decline.#VIX is 30 day expectation of volatility for S&P 500 options.  VIX spikes correlate to market declines because more people buying options to protect themselves from declines
		#'A', 'AAL', 'AAPL', 'ABBV', 'ABT', 'ACN', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP', 'AFL', 'AGG', 'AGN', 'ALGN', 'ALL', 'ALXN', 'AMAT', 'AMGN', 'AMT', 'AMZN', 'ANTM', 'AON', 'APD', 'APH', 'ASML', 'ATVI', 'AVGO', 'AWK', 'AXP', 'AZO', 'BA', 'BABA', 'BAC', 'BAX', 'BDX', 'BIDU', 'BIIB', 'BK', 'BKNG', 'BLK', 'BMRN', 'BMY', 'BSX', 'C', 'CAT', 'CB', 'CCI', 'CDNS', 'CERN', 'CHKP', 'CHTR', 'CI', 'CL', 'CLX', 'CMCSA', 'CME', 'CNC', 'COF', 'COP', 'COST', 'CRM', 'CSCO', 'CSX', 'CTAS', 'CTSH', 'CTXS', 'CVS', 'CVX', 'D', 'DBA', 'DD', 'DE', 'DG', 'DHR', 'DIS', 'DLR', 'DLTR', 'DOW', 'DUK', 'EA', 'EBAY', 'ECL', 'ED', 'EL', 'EMB', 'EMR', 'EQIX', 'EQR', 'ES', 'ETN', 'EW', 'EWH', 'EWW', 'EXC', 'EXPE', 'FAST', 'FB', 'FDX', 'FE', 'FIS', 'FISV', 'GD', 'GE', 'GILD', 'GIS', 'GM', 'GOOG', 'GPN', 'GS', 'HAS', 'HCA', 'HD', 'HON', 'HPQ', 'HSIC', 'HUM', 'HYG', 'IAU', 'IBM', 'ICE', 'IDXX', 'ILMN', 'INCY', 'INFO', 'INTC', 'INTU', 'ISRG', 'ITW', 'JBHT', 'JD', 'JNJ', 'JPM', 'KHC', 'KLAC', 'KMB', 'KMI', 'KO', 'KR', 'LBTYA', 'LBTYK', 'LHX', 'LLY', 'LMT', 'LOW', 'LQD', 'LRCX', 'LULU', 'MA', 'MAR', 'MCD', 'MCHP', 'MCO', 'MDLZ', 'MDT', 'MELI', 'MET', 'MMC', 'MMM', 'MNST', 'MO', 'MRK', 'MS', 'MSCI', 'MSFT', 'MSI', 'MU', 'MXIM', 'MYL', 'NEE', 'NEM', 'NFLX', 'NKE', 'NLOK', 'NOC', 'NOW', 'NSC', 'NTAP', 'NTES', 'NVDA', 'NXPI', 'ORCL', 'ORLY', 'PAYX', 'PCAR', 'PEG', 'PEP', 'PFE', 'PG', 'PGR', 'PLD', 'PM', 'PNC', 'PSA', 'PSX', 'PYPL', 'QCOM', 'REGN', 'RMD', 'ROKU', 'ROP', 'ROST', 'RTX', 'SBAC', 'SBUX', 'SCHW', 'SHOP', 'SHW', 'SHY', 'SIRI', 'SNPS', 'SO', 'SPGI', 'SPY', 'SRE', 'STZ', 'SWKS', 'SYK', 'SYY', 'T', 'TCOM', 'TFC', 'TGT', 'TIP', 'TJX', 'TMO', 'TMUS', 'TROW', 'TRV', 'TSLA', 'TTWO', 'TWLO', 'TXN', 'UAL', 'ULTA', 'UNH', 'UNP', 'UPS', 'USB', 'V', 'VNQ', 'VRSK', 'VRSN', 'VRTX', 'VZ', 'WBA', 'WDAY', 'WDC', 'WEC', 'WFC', 'WLTW', 'WM', 'WMT', 'WYNN', 'XEL', 'XHB', 'XLK', 'XLNX', 'XLU', 'XLV', 'XOM', 'XRT', 'YUM', 'ZTS'
			
		#datalist = ['VIX','TICK-NYSE','TRIN-NYSE','SPY','XLU','IAU']
		datalist = ['SPY','XLU','TICK-NYSE','XHB','AAPL','INTC','ACN','ADBE', 'AMZN', 'ANTM', 'ADI', 'AGN', 'ALGN', 'ALL', 'ALXN']
		#datalist = ['SPY','TICK-NYSE','A', 'AAL', 'AAPL', 'ABBV', 'ABT', 'ACN', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP', 'AFL', 'AGG', 'AGN', 'ALGN', 'ALL', 'ALXN', 'AMAT', 'AMGN', 'AMT', 'AMZN', 'ANTM', 'AON', 'APD', 'APH', 'ASML', 'ATVI', 'AVGO', 'AWK', 'AXP', 'AZO', 'BA', 'BABA', 'BAC', 'BAX', 'BDX', 'BIDU', 'BIIB', 'BK', 'BKNG', 'BLK', 'BMRN', 'BMY', 'BSX', 'C', 'CAT', 'CB', 'CCI', 'CDNS', 'CERN', 'CHKP', 'CHTR', 'CI', 'CL', 'CLX', 'CMCSA', 'CME', 'CNC', 'COF', 'COP', 'COST', 'CRM', 'CSCO', 'CSX', 'CTAS', 'CTSH', 'CTXS', 'CVS', 'CVX', 'D', 'DBA', 'DD', 'DE', 'DG', 'DHR', 'DIS', 'DLR', 'DLTR','DUK', 'EA', 'EBAY', 'ECL', 'ED', 'EL', 'EMB', 'EMR', 'EQIX', 'EQR', 'ES', 'ETN', 'EW', 'EWH', 'EWW', 'EXC', 'EXPE', 'FAST', 'FB', 'FDX', 'FE', 'FIS', 'FISV', 'GD', 'GE', 'GILD', 'GIS', 'GM', 'GOOG', 'GPN', 'GS', 'HAS', 'HCA', 'HD', 'HON', 'HPQ', 'HSIC', 'HUM', 'HYG', 'IAU', 'IBM', 'ICE', 'IDXX', 'ILMN', 'INCY', 'INFO', 'INTC', 'INTU', 'ISRG', 'ITW', 'JBHT', 'JD', 'JNJ', 'JPM', 'KHC', 'KLAC']
		#datalist = ['SPY','XHB','XLU','MCD','XLK','XLV','XRT','TICK-NYSE','IAU','TIP','AGG','VNQ','XOM','LQD','EWW','HYG','DBA']
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
			start_date = date(2018,1,1), #Dates for backtesting
			end_date = date(2018,3,30),
			nysetick_on = False,
			timeframe0 = 5, #MINUTES
			timeframe1 = 15, #MINUTES
			timeframe2 = 60, #MINUTES  5,30,240
			timeframe1on = True,
			timeframe2on = True,
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
			timer = 'on', #time program, 'on' or 'off', returns number of seconds
			writer = 'off', #export results to CSV output report 'on' or 'off'
			sma1 = 5,
			sma2 = 3,
			ema1 = 5,  #8
			ema2 = 10, #20
			signif = .05, #(.10, .05, and .01 available) for statistical tests: .01 ideal
			pairs_lookback = 30,
			obv = 10,
			atrper = 5,
			atrdist = 2,   
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
			rank = 2, #How many tickers to select from ticker list
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
		self.hedge_ratio_t1 = 0
		self.hedge_ratio_t2  = 0
		self.first_run_complete = False

		self.inds = dict()
		self.long_stop_dict = defaultdict(list)
		self.short_stop_dict = defaultdict(list)
		self.gap_dict = defaultdict(list)
		self.close_dict = defaultdict(list)
		self.justclose_dict = defaultdict(list)
		self.cointegrating_pairs = []
		self.adfpval = []
		self.errors = []
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
		
		#Create/Instantiate objects to access UserInputs class
		self.modelp = UserInputs.model_params()

		#Calc data feed metrics
		if not self.modelp.get('live_status'):
			datalist = UserInputs.datalist('hist')
		elif self.modelp.get('live_status'):
			ibdatalist = UserInputs.datalist('ib')
        
		#Initialize dictionary's	
		for i, d in enumerate(self.datas):	
			#Initialize dictionaries by appending 0 value
			self.inds[d._name] = dict()  #Dict for all indicators
			
			#Instantiate exact data references (can't loop or will only spit out last value)
			if d._name == 'TICK-NYSE0':
				self.tick_close = d.close
			
#*********************************************INITITIALIZE INDICATORS*********************************************************				
			self.inds[d._name]['close'] = btind.close(d.close,period=self.p.pairs_lookback,plot=False)	#history of closing prices
			self.inds[d._name]['slope'] = btind.Slope(d,period=self.p.slope_per,plot=False)							
			#self.inds[d._name]['slope_of_slope'] = btind.Slope(self.inds[d._name]['slope'],period=self.p.slope_per,plot=False)
			self.inds[d._name]['obv'] = btind.obv(d,period=self.p.obv,plot=True)
			self.inds[d._name]['slope_obv'] = btind.Slope(self.inds[d._name]['obv'],period=self.p.obv,plot=False)
			self.inds[d._name]['gap'] = btind.gap(d,period=self.p.breakout_per,plot=False)
			self.inds[d._name]['vwap'] = btind.vwap(d,plot=False)
			self.inds[d._name]['atr'] = btind.ATR(d,period=self.p.atrper,plot=False)
			self.inds[d._name]['atr_stop'] = btind.atr_stop(d,self.inds[d._name]['atr'],atrdist = self.p.atrdist,dollars_risked = self.p.total_dollars_risked,dollars_per_trade = self.p.dollars_risked_per_trade,plot=False)
			#self.inds[d._name]['hammer'] = btind.HammerCandles(d,plot=False)											
			#self.inds[d._name]['three_line_strike'] = btind.three_line_strike(d,plot=True)										
			#self.inds[d._name]['ema1'] = btind.EMA(d,period=self.p.ema1,plot=True)
			#self.inds[d._name]['ema2'] = btind.EMA(d,period=self.p.ema2,plot=True)
			#self.inds[d._name]['adx'] = btind.ADX(d,period=self.p.adx,plot=True)	
			#self.inds[d._name]['slope_adx'] = 	btind.Slope(self.inds[d._name]['adx'],period=self.p.slope_per,plot=False)	/																			
			#self.inds[d._name]['bollinger'] = btind.BollingerBands(d.close,period=self.p.boll_per,devfactor = self.p.boll_dist,plot=True)						
			#self.inds[d._name]['slope_ema1'] = 	btind.Slope(self.inds[d._name]['ema1'],period=self.p.slope_per,plot=False)	
			#self.inds[d._name]['slope_ema2'] = 	btind.Slope(self.inds[d._name]['ema2'],period=self.p.slope_per,plot=False)			
			#self.inds[d._name]['slope_ema_width'] = btind.Slope(self.inds[d._name]['ema1']-self.inds[d._name]['ema2'],period=self.p.slope_per,plot=False)											
			#self.inds[d._name]['rsi']= btind.RSI(d,period=self.p.rsi,safediv=True,plot=True)								
			#self.inds[d._name]['stochastic'] = btind.StochasticSlow(d,period=self.p.stoch_per,per_dfast= self.p.stoch_fast,safediv=True,plot=False)
			#self.inds[d._name]['adx'].plotinfo.plotmaster = self.inds[d._name]['rsi']   #Plot ADX on same subplot as RSI
			self.inds[d._name]['support'] = btind.Support(d,period=self.p.lookback,min_touches = self.p.min_touches,tol_perc = self.p.tol_perc,bounce_perc = self.p.bounce_perc,plot=False)
			self.inds[d._name]['resistance'] = btind.Resistance(d,period=self.p.lookback,min_touches = self.p.min_touches,tol_perc = self.p.tol_perc,bounce_perc = self.p.bounce_perc,plot=False)	
												
			#Initialize target size, target long, and target short prices
			self.inds[d._name]['target_size'] = self.inds[d._name]['atr_stop']().lines.size			
			self.inds[d._name]['target_long'] = d.open +(self.p.dollars_risked_per_trade*self.p.target)/self.inds[d._name]['target_size']																	
			self.inds[d._name]['target_short'] = d.open -(self.p.dollars_risked_per_trade*self.p.target)/self.inds[d._name]['target_size']																	

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
				print(f"{order.data._name} ENTER LONG POSITION, Date: {self.dt} {self.hourmin} Price: {round(order.executed.price,2)}, Cost: {round(order.executed.value),2}, Size {order.executed.size}, Type {order.getordername()}")
			
			if order.isbuy() and self.pos < 0:
				print(f"{order.data._name} EXIT SHORT POSITION, Date: {self.dt} {self.hourmin} Price: {round(order.executed.price,2)}, Cost: {round(order.executed.value),2}, Size {order.executed.size}, Type {order.getordername()}")
			
			if order.issell() and self.pos==0:
				print(f"{order.data._name} ENTER SHORT POSITION, Date: {self.dt} {self.hourmin} Price: {round(order.executed.price,2)}, Cost: {round(order.executed.value),2}, Size {order.executed.size}, Type {order.getordername()}")
			
			if order.issell() and self.pos > 0:
				print(f"{order.data._name} EXIT LONG POSITION, Date: {self.dt} {self.hourmin} Price: {round(order.executed.price,2)}, Cost: {round(order.executed.value),2}, Size {order.executed.size}, Type {order.getordername()}")
		
	
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

	
	def next(self):
		"""Iterates over each "line" of data (date and ohlcv) provided by data feed"""
		#mystart=datetime.now()
		#Convert backtrader float date to datetime so i can see time on printout and manipulate time variables
		self.hourmin = datetime.strftime(self.data.num2date(),'%H:%M')
		self.dt = self.data.num2date()
		
		#Get correlations, rank them, and store correlations pairs and value in dctionary
		if self.hourmin=='08:35' and self.justclose_dict:
			
			#Pairs Trading Strategy
			print(f'{self.dt} {self.hourmin}')
			self.create_pairs(self.data,self.p.signif)  #get initial pairs list using Johansen test
			self.calc_spread_zscore(self.data)
			#if self.pair_spread_dict and not self.first_run_complete:
				#self.plot_spread()
			self.pairs_entry(self.data)
			

		if self.first_run_complete:
			self.calc_spread_zscore(self.data)
			#self.pairs_entry(self.data)

		for i, d in enumerate(self.datas):  #Need to iterate over all datas so atr and sizing can be adjusted for multiple time frame user parameters	

			#-------------------STOCK SELECTION BASED ON OPEN CRITERIA-----------------------------------------
			#Stock Selection - collect data to be ranked at start of trading day and put in dictionary
			if self.hourmin=='08:30' and d._name!='TICK-NYSE1' and d._name==d._name[:-1]+'1':		
				self.clear_pairs()
				#self.gap_dict[d._name] = round(self.inds.get(d._name).get('gap').lines.gap[0],3)  #get open gaps, put in dict

			if  d._name==d._name[:-1]+'1' and d._name!='TICK-NYSE1':
				#self.justclose_dict[d._name].append(d.close[0])
				self.closes = self.inds.get(d._name[:-1]+'1').get('close').get(size=self.p.pairs_lookback)
				self.justclose_dict[d._name] = [x for x in self.closes]
				
			#if d._name==self.data1._name:  #Just need date for 1 symbol	
				#self.dates = d.datetime.get(0,self.p.pairs_lookback)
				#self.justdate_dict[d._name] = [self.data.num2date(x) for x in self.dates]	
											
			#Stock Selection - once data is collected at 8:30, sort it.  Only do the sort 1 time (equal to one data - picked data0- since all data collected previous bar
			#if self.hourmin=='08:35' and self.gap_dict is not None and d._name==self.data0._name: 
				#self.rank_gap(d)	
			#-----------------------------------------------------------------------------------------------------
				
			#-------------------------------- EXIT TRADES IF CRITERIA MET------------------------------------------
			if d._name==d._name[:-1]+'0':
				self.pos = self.getposition(d).size
				
			if self.hourmin=='14:50' and self.pos:  #can't exit at 14:55 because cerebro submits at order at open of next bar
				self.eod_exit(d)
			
			#if self.pos and self.tick_close > 1000 and d._name == d._name[:-1]+'0':
				self.exit_trade(d,'long')
			
			#if self.pos and self.tick_close < -1000 and d._name == d._name[:-1]+'0':
				self.exit_trade(d,'short')
			#--------------------------------------------------------------------------------------------------------			
						
			#---------------------------------ENTRY LOGIC FOR LONG AND SHORT-----------------------------------------
			
			self.pairs_entry(self.data)
			
			"""
			if self.pos==0 and self.entry_rules(d):  #Check that entry rules are met
				
				#BUY SIGNAL
				#if self.signal_morn_break(d,'long'):
				#if self.signal_test_long(d):
				#if self.sup_res(d,'long'):
				#if self.hammer(d,'long'):
					self.buyorder(d)

				#SELL SIGNAL
				#if self.signal_morn_break(d,'short'):
				#if self.signal_test_short(d):
				#if self.sup_res(d,'short'):
				#if self.hammer(d,'short'):
					#self.sellorder(d)
			"""
			#-----------------------------------------------------------------------------------------------------------

		#end_time = datetime.now()  #Timer to analyze code
		#diff = end_time-mystart 
		#print(f'Timer {diff}')
	
	#*********************************************************************************************************************
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
		all_tickers = self.justclose_dict.keys()
		all_pairs = list(itertools.combinations(all_tickers, 2))  #return list of all pair combinations of tickers

		#Loop through all pairs, run Johansen test, and pick out cointegrated stocks
		for i, (ticker1, ticker2) in enumerate(all_pairs): 	
			
			t1_data = np.array(self.justclose_dict.get(ticker1)) 	#Y variable
			t2_data = np.array(self.justclose_dict.get(ticker2))	#X variable
			combined_data = np.vstack((t1_data, t2_data)).T
			
			# The second and third parameters indicate constant term, with a lag of 1. 
			result = coint_johansen(combined_data, 0, 1)  #Inputted as Y Variable first, X Var second.  testing only 2 tickers at a time.  Can not conduct test with more than 12 tickers
			hedge_ratio = result.evec[:, 0]	#The first column of eigenvectors contains the best weights (shortest half life for mean reversion).  This determine shares of each instrument.
			self.hedge_ratio_t1 = hedge_ratio[0]
			self.hedge_ratio_t2 = hedge_ratio[1]
			net_pair_val = (t1_data[-1]*self.hedge_ratio_t1) - (t2_data[-1]*self.hedge_ratio_t2)  #think market price of "spread", just like price per share for any stock
			#num_units = self.p.total_dollars_risked/net_pair_val  #this represents how many "shares" of the pair spread you can long or short
			#size_t1 = num_units*hedge_ratio_t1
			#size_t2 = num_units*hedge_ratio_t2
			#stop_price_long = net_pair_val - stop increment
			#stop_price_short = net_pair_val + stop increment
			
			# the 90%, 95%, and 99% confidence levels for the trace statistic and maximum eigenvalue statistic are stored in the first, second, and third column of cvt and cvm, respectively
			confidence_level_cols = {90: 0, 95: 1,99: 2}
			confidence_level_col = confidence_level_cols[(1-signif)*100]
			trace_crit_value = result.cvt[:, confidence_level_col]
			t1_trace = round(trace_crit_value[0],2)
			t2_trace = round(trace_crit_value[1],2)
			eigen_crit_value = result.cvm[:, confidence_level_col]
			t1_eigen = round(eigen_crit_value[0],2)
			t2_eigen = round(eigen_crit_value[1],2)
			t1_lr1 = round(result.lr1[0],2)
			t2_lr1 = round(result.lr1[1],2)
			t1_lr2 = round(result.lr2[0],2)
			t2_lr2 = round(result.lr2[1],2)
		
			# The trace statistic and maximum eigenvalue statistic are stored in lr1 and lr2 - see if they exceeded the confidence threshold
			if np.all(result.lr1 >= trace_crit_value) and np.all(result.lr2 >= eigen_crit_value):			
				print(f'{self.dt} {self.hourmin} Johansen: Pair:{ticker1}/{ticker2} , {ticker1} - Trace Stat: {t1_lr1} is > Crit Val {t1_trace} Max Eigen Stat {t1_lr2} > {t1_eigen} Crit Val, Hedge: {hedge_ratio[0]}')
				print(f'{self.dt} {self.hourmin} Johansen: Pair:{ticker1}/{ticker2} , {ticker2} - Trace Stat: {t2_lr1} is > Crit Val {t2_trace} Max Eigen Stat {t2_lr2} > {t2_eigen} Crit Val, Hedge: {hedge_ratio[1]}')
				
				self.cointegrating_pairs.append(dict(t1=ticker1,t2=ticker2))
		
		
		print("NUMBER OF COINTEGRATING PAIRS:", len(self.cointegrating_pairs))  #return number of cointegrating pairs		
		self.pair_regression(d)
		
		
	def pair_regression(self,d):
		"""Take Cointegrated pairs list from Johansen test, and run against ADF test for further refinement"""
		#Loop through Johansen cointegrating pairs and extract pair names, hedge ratios, and open price for day
		for i, pair in enumerate(self.cointegrating_pairs):
			stock1 = pair.get('t1')  #Y variable
			stock1_hratio = pair.get('hratio_t1')		
			stock2 = pair.get('t2')	#X variable
			stock2_hratio = pair.get('hratio_t2')
			
			#Perform regression on pairs
			beta_set = np.array(self.justclose_dict.get(stock2))
			beta = beta_set.reshape((len(beta_set), 1))
			Y_set = np.array(self.justclose_dict.get(stock1))
			Y = Y_set.reshape((len(Y_set), 1))

			(m, c, rvalue, pvalue, stderr) = stats.mstats.linregress(beta, Y)  #input as linregress(x,y)
			#self.hratio = m
	
			#Create residual series for ADF test (i.e. errors)
			for n, value in enumerate(Y):
				projected = m * beta[n][0] + c  #estimated series based on regression line
				error = value - projected
				self.errors.append(error)
			#Perform ADF test on pairs
			self.adfuller_test(self.errors,stock1,stock2,self.p.signif)
		
		print (f'Number of ADF PAIRS: {len(self.adfpval)} {self.adfpval}')
		if self.adfpval:
			self.plot_pair()

		
	def adfuller_test(self,ols,t1_name,t2_name,signif):
		"""Perform ADFuller to test for Stationarity of given series and print report.
		a stationary time series is one whose characteristics like mean and variance does not change over time.
		if a series is found to be non-stationary, you make it stationary by differencing the series 
		once and repeat the test again until it becomes stationary.
		
		results is an OLS regression object
		"""
		#series = df.loc[:, d._name].values
		r = ts.adfuller(ols, autolag='AIC')
		output = {'test_statistic':round(r[0], 4), 'pvalue':round(r[1], 4), 'n_lags':round(r[2], 4), 'n_obs':r[3]}
		p_value = output['pvalue']
		
		if p_value <= signif:
			print(f" ADF Test => P-Value = {p_value}. Rejecting Null Hypothesis.")
			print(f" ADF Test => Series is Stationary.")
			
			self.adfpval.append(dict(t1=t1_name,t2=t2_name))
			
			print(f"{self.dt} {self.hourmin} NUMBER OF PASSING ADF PAIRS {len(self.adfpval)}")	
			#print("ADF TESTED PAIRS:")
			print(self.adfpval)	
			
		#else:
			#print(f" ADF Test => P-Value = {p_value}. Weak evidence to reject the Null Hypothesis.")
			#print(f" ADF Test => Series is Non-Stationary.") 
		
		"""
		def adjust(val, length= 6): return str(val).ljust(length)
		# Print Summary
		print(f'    Augmented Dickey-Fuller Test"', "\n   ", '-'*47)
		print(f' Null Hypothesis: Data has unit root. Non-Stationary.')
		print(f' Significance Level    = {signif}')
		print(f' Test Statistic        = {output["test_statistic"]}')
		print(f' No. Lags Chosen       = {output["n_lags"]}')
		for key,val in r[4].items():
			print(f' Critical value {adjust(key)} = {round(val, 3)}')
		"""

	def calc_spread_zscore(self,d,z_entry_threshold=2.0,z_exit_threshold=1):
		
		
		for i in self.adfpval:
			t1 = i['t1'] 	#Y Variable
			t2 = i['t2']	#X Variable
			
			self.hratio_close_dict[t1] = [self.hedge_ratio_t1 *x for x in self.justclose_dict.get(t1)]
			self.hratio_close_dict[t2] = [self.hedge_ratio_t2 *x for x in self.justclose_dict.get(t2)]  #mutiply stock 2 array by hratio
			zip_obj = zip(self.hratio_close_dict.get(t1), self.hratio_close_dict.get(t2))
			for t1list, t2list in zip_obj:  #subtract lists to get spread
				myspread = t1list - t2list  #LONG POSITION = long1 monetary unit ostock A (Y variable) and short 'hedge ratio' monetary units of stock B (X Variable).  SHORT POSITION - sell 1 monetary unit of stock A and buy 'hedge ratio' monetary units of stock B
				spread = round(myspread,2)  #still array, just removing list of list
				self.pair_spread_dict[f'spread {t1}/{t2}'].append(spread)
			print(self.pair_spread_dict)
				
		for i in self.pair_spread_dict:
			name = i[7:]
			myzscore = stats.zscore(self.pair_spread_dict[i])
			zscore = [x for x in myzscore][0]
			self.pair_zscore_dict[f'zscore {t1}/{t2}'].append(zscore)
			self.long_pair_dict[f'long_sig {name}'].append(zscore <= -z_entry_threshold*1.0)
			self.short_pair_dict[f'short_sig {name}'].append(zscore >= z_entry_threshold*1.0)
			self.exit_pair_dict[f'exit_sig {name}'].append(abs(zscore) <= z_exit_threshold*1.0)
		print(self.pair_zscore_dict)
			
	def pairs_entry(self,d):
		"""Create the entry/exit signals based on the exceeding of 
		z_enter_threshold for entering a position and falling below
		z_exit_threshold for exiting a position."""	
		
		for i in self.pair_spread_dict:
			name = i[7:]
			if self.long_pair_dict.get(f'long_sig {name}'):
				print(f"{self.dt} {self.hourmin} {name} - long signal: {self.long_pair_dict.get(f'long_sig {name}')[0]}")
			if self.short_pair_dict.get(f'short_sig {name}'):
				print(f"{self.dt} {self.hourmin} {name} - short signal: {self.short_pair_dict.get(f'short_sig {name}')[0]}")
			if self.short_pair_dict.get(f'exit_sig {name}'):
				print(f"{self.dt} {self.hourmin} {name} - exit signal: {self.exit_pair_dict.get(f'exit_sig {name}')[0]}")
				
		self.first_run_complete = True
		self.long_pair_dict.clear()  #dict replaces itself every next statement, not needed so delete
		self.short_pair_dict.clear()
		self.exit_pair_dict.clear()
		self.pair_spread_dict.clear()
		self.pair_zscore_dict.clear()
	
	
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
		
		
	def plot_pair(self):
	
		if self.adfpval:
			fig = plt.figure()
			cols = 2
			rows = int(len(self.adfpval)/cols)

			for i, pair in enumerate(self.adfpval):
				if i <= (rows*cols)-1:
				
					t1_name = pair.get('t1')
					t2_name = pair.get('t2')
					t1_data= self.justclose_dict.get(t1_name)
					t2_data = self.justclose_dict.get(t2_name)

					ax = fig.add_subplot(rows, cols, i+1)
					ax2 = ax.twinx()
					ax.plot(t1_data,'g-')
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
					self.pair_zscore_dict
					spread_data= self.pair_zscore_dict.get(f'zscore {t1_name}/{t2_name}')
				
					ax = fig.add_subplot(rows, cols, i+1)
					ax.plot(spread_data,'g-')
					ax.set_ylabel(f'{t1_name}/{t2_name} zscore', color='g')
					ax.set_title(f'{t1_name}/{t2_name} zscore')
			
			plt.tight_layout()		
			plt.show()
	
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
		short_name = '{} - Enter Short Trade'.format(d._name)
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
			and (self.hourmin>='09:00'and self.hourmin<='14:00')
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
				and (self.hourmin>='08:30'and self.hourmin<='23:59')
				and self.cash_avail > self.p.total_dollars_risked
				and self.prenext_done #Start trading after all prenext data loads
				and self.data_live
				):
				return True
			else:
				return False	
		print(d._name,self.dt,self.hourmin,d.open[0],d.high[0],d.low[0],d.close[0],d.volume[0],self.cash_avail,self.pos)
			
			
	def signal_test_long(self,d):
		if d.close[0] > d.close[-1] and d._name==d._name[:-1]+'0':
			return True
		else:
			return False
			
	def signal_test_short(self,d):
		if d.close[0] < d.close[-1] and d._name==d._name[:-1]+'0':
			return True
		else:
			return False
	
	
	def rank_correl(self,d,df):
		"""Returns most highly correlated pairs of stocks, and correlation value, from ticker list via 2 key, 1 value dict"""
		mycorr = round(df.corr(method='pearson'),2)
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
	
	
	def rank_gap(self,d):
		"""Create gap ranks across stock universe and return top X and bottom Y as per paramaters"""
		sorted_res = sorted(self.gap_dict.items(), key = lambda x: x[1], reverse=True)  #Create sorted list -  key accepts a function (lambda), and every item (x) will be passed to the function individually, and return a value x[1] by which it will be sorted.
		self.rtop_dict = dict(sorted_res[:self.p.rank])  #Choose subset of tickers with highest rank (i.e. top 3)
		self.rbot_dict = dict(sorted_res[-self.p.rank:])  #Choose subset of tickers with lowest rank (i.e. bottom 3)
		self.sortflag = 1
		print(f'{d._name} {self.dt} {self.hourmin} Top Sort: {self.rtop_dict}, Bottom Sort: {self.rbot_dict}')
	
	
	def hammer(self,d,direction):
		self.hammer_t0= self.inds.get(d._name[:-1]+'0').get('hammer')[0]
		
		if d._name==d._name[:-1]+'0': 
			if direction =='long' and self.hammer_t0==1:
				return True
			else:
				return False
					
			if direction =='short' and self.hammer_t0==-1:
				return True
			else:
				return False
				
	def three_line(self,d,direction):
		self.three_strike_t0= self.inds.get(d._name[:-1]+'0').get('three_line_strike')[0]

		if d._name==d._name[:-1]+'0': 
			if direction =='long' and self.three_strike_t0==1:
				return True
			else:
				return False
					
			if direction =='short' and self.three_strike_t0==-1:
				return True
			else:
				return False
		

	def sup_res(self,d,direction):
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
		if d._name==d._name[:-1]+'0' and direction=='long': 
			if(	self.tick_close > 0
				and self.slope_obv_t0 > 0
				and self.vwap_t0 > 0
				and self.slope_t1 > 0					
				and self.slope_t2 > 0
				and d.low[0] < self.support_t1):
				return True
			else:
				return False
		if d._name==d._name[:-1]+'0' and direction=='short': 
			if(	self.tick_close < 0
				and self.slope_obv_t0 < 0
				and self.vwap_t0 < 0
				and self.slope_t1 < 0					
				and self.slope_t2 < 0
				and d.high[0] > self.resistance_t1):
				return True
			else:
				return False
				
	
	def signal_morn_break(self,d,direction):
		#Calc timeframe 0 
		self.slope_obv_t0 = self.inds.get(d._name[:-1]+'0').get('slope_obv')[0] #Get OBV
		#Calc timeframe 1
		self.slope_t1 = self.inds.get(d._name[:-1]+'1').get('slope')[0]  #Calc slope for time1
		#Calc timeframe 2	
		self.slope_t2 = self.inds.get(d._name[:-1]+'2').get('slope')[0]  #Calc slope for time2
		
		#Determine open 15 minute range
		self.rng_high = round(self.inds[d._name]['gap'].lines.rng_high[0],2)
		self.rng_low = round(self.inds[d._name]['gap'].lines.rng_low[0],2)	
		#Signal Logic
		if d._name==d._name[:-1]+'0': 
			if direction =='long':
				if(	d._name in self.rtop_dict.keys()
					and d.close[0] >= self.rng_high
					and self.tick_close > 0
					and self.slope_obv_t0 > 0
					and self.slope_t1 > 0					
					and self.slope_t2 > 0
					):
					return True
				else:
					return False
					
			if direction =='short':
				if( d._name in self.rbot_dict.keys()
					and d.close[0] <= self.rng_low
					and self.tick_close < 0
					and self.slope_obv_t0 < 0
					and self.slope_t1 < 0					
					and self.slope_t2 < 0
					):
					return True
				else:
					return False
	

	def regime_early_bull(self,d):
		#Trend underway, getting stronger
		#Get timeframe 0 values
		self.percK_t0 = round(self.inds.get(d._name).get('stochastic').lines.percK[0],3)
		
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
				 self.percK_t0 < 30]
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
			
		
	def regime_neutral(self,d):
		#Define Variables
		#Calculate timeframe 1
		self.adx_t1 = self.inds.get(d._name).get('adx')[0]
		self.rsi_t1 = round(self.inds.get(d._name).get('rsi')[0],2)
		self.resistance_t1 = self.inds.get(d._name).get('resistance')[0]
		self.support_t1 = self.inds.get(d._name).get('support')[0]
		
		#Calculate timeframe 2
		self.adx_t2 = self.inds.get(d._name).get('adx')[0]
		self.rsi_t2 = round(self.inds.get(d._name).get('rsi')[0],2)
		self.resistance_t2 = self.inds.get(d._name).get('resistance')[0]
		self.support_t2 = self.inds.get(d._name).get('support')[0]

		#Define signal criteria
		#Store in list so expressions can be 'scored' later
		mylist = [self.adx_t1 < 20,
				 self.adx_t2 < 20,
				 self.rsi_t1 < 60,
				 self.rsi_t1 > 40,
				 self.rsi_t2 < 60,
				 self.rsi_t2 > 40,
				 d.close[0] < self.resistance_t1,
				 d.close[0] > self.support_t1,
				 d.close[0] < self.resistance_t2,
				 d.close[0] > self.support_t2,
				 ]
				 
		#Get length of list		
		mycount = len(mylist)
		#If 75% of list is true, return true
		if sum(mylist) > (mycount * 1):	#sum count true as 1, false as 0 	
			return True
		else:
			return False
		
	
	def regime_early_bear(self,d):
		#Trend underway, getting stronger
		#Get timeframe 0 values
		self.percK_t0 = round(self.inds.get(d._name).get('stochastic').lines.percK[0],3)
		
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
				 self.percK_t0 > 70
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
				p_values = [round(test_result[i+1][0][test][1],4) for i in range(maxlag)]
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
		if modelp.get('timeframe1on'):
			data_Timeframe1 = cerebro.resampledata(data,name="{}1".format(j),
													timeframe=bt.TimeFrame.Minutes,
													compression = modelp.get('timeframe1'))
		
		if modelp.get('timeframe2on'):
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
		if modelp.get('timeframe1on'):
			data_Timeframe1 = cerebro.resampledata(forexdata,name="{}1".format(j),
													timeframe=bt.TimeFrame.Minutes,
													compression = modelp.get('timeframe1'))
		
		if modelp.get('timeframe2on'):
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
		if modelp.get('timeframe1on'):
			tickdata_Timeframe1 = cerebro.resampledata(tickdata,name="{}1".format('TICK-NYSE'),
														timeframe=bt.TimeFrame.Minutes,
														compression = modelp.get('timeframe1'))
			
		if modelp.get('timeframe2on'):
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
					
		cerebro.adddata(data, name="{}0".format(j))

		if modelp.get('timeframe1on'):
			#Apply resamplings			
			data_Timeframe1 = cerebro.resampledata(data,
									name="{}1".format(j),
									timeframe=bt.TimeFrame.Minutes,
									compression = modelp.get('timeframe1'),
									)


		if modelp.get('timeframe2on'):
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







