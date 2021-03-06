# importing the required module 
import timeit 
  
  
# code snippet whose execution time is to be measured 
mycode = ''' 
#IMPORT MODULES
import backtrader as bt
import backtrader.indicators as btind
from backtrader.utils import flushfile  # win32 quick stdout flushing
from backtrader.feeds import mysql
from datetime import date, time, datetime, timedelta
import pytz
from collections import defaultdict

class UserInputs():
	#This class is designed so runstrat() method can pick up these parameters (can use self.p.whatever to pass parameters for some reason)

	def datalist(data_req):
		#Create list of tickers to load data for.  Market Breadth indicators need to be removed from initiliazation and next() so they are not traded
		#Data Notes - 'EMB' and 'SHY' data starts 8/3/2017, 'DBA' has almost double the amount of records the other tickers do for some reason.
		#TICK is # of NYSE stocks trading on an uptick vs # of stocks trading on downtick.  About 2800 stocks total, usually oscillates between -500 to +500.  Readings above 1000 or below -1000 considered extreme.  #TRIN is ratio of (# of Advance/Decliners)/(Advance/Decline Volume).  Below 1 is strong rally, Above 1 is strong decline.#VIX is 30 day expectation of volatility for S&P 500 options.  VIX spikes correlate to market declines because more people buying options to protect themselves from declines
		#'A', 'AAL', 'AAPL', 'ABBV', 'ABT', 'ACN', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP', 'AFL', 'AGG', 'AGN', 'ALGN', 'ALL', 'ALXN', 'AMAT', 'AMGN', 'AMT', 'AMZN', 'ANTM', 'AON', 'APD', 'APH', 'ASML', 'ATVI', 'AVGO', 'AWK', 'AXP', 'AZO', 'BA', 'BABA', 'BAC', 'BAX', 'BDX', 'BIDU', 'BIIB', 'BK', 'BKNG', 'BLK', 'BMRN', 'BMY', 'BSX', 'C', 'CAT', 'CB', 'CCI', 'CDNS', 'CERN', 'CHKP', 'CHTR', 'CI', 'CL', 'CLX', 'CMCSA', 'CME', 'CNC', 'COF', 'COP', 'COST', 'CRM', 'CSCO', 'CSX', 'CTAS', 'CTSH', 'CTXS', 'CVS', 'CVX', 'D', 'DBA', 'DD', 'DE', 'DG', 'DHR', 'DIS', 'DLR', 'DLTR', 'DOW', 'DUK', 'EA', 'EBAY', 'ECL', 'ED', 'EL', 'EMB', 'EMR', 'EQIX', 'EQR', 'ES', 'ETN', 'EW', 'EWH', 'EWW', 'EXC', 'EXPE', 'FAST', 'FB', 'FDX', 'FE', 'FIS', 'FISV', 'GD', 'GE', 'GILD', 'GIS', 'GM', 'GOOG', 'GPN', 'GS', 'HAS', 'HCA', 'HD', 'HON', 'HPQ', 'HSIC', 'HUM', 'HYG', 'IAU', 'IBM', 'ICE', 'IDXX', 'ILMN', 'INCY', 'INFO', 'INTC', 'INTU', 'ISRG', 'ITW', 'JBHT', 'JD', 'JNJ', 'JPM', 'KHC', 'KLAC', 'KMB', 'KMI', 'KO', 'KR', 'LBTYA', 'LBTYK', 'LHX', 'LLY', 'LMT', 'LOW', 'LQD', 'LRCX', 'LULU', 'MA', 'MAR', 'MCD', 'MCHP', 'MCO', 'MDLZ', 'MDT', 'MELI', 'MET', 'MMC', 'MMM', 'MNST', 'MO', 'MRK', 'MS', 'MSCI', 'MSFT', 'MSI', 'MU', 'MXIM', 'MYL', 'NEE', 'NEM', 'NFLX', 'NKE', 'NLOK', 'NOC', 'NOW', 'NSC', 'NTAP', 'NTES', 'NVDA', 'NXPI', 'ORCL', 'ORLY', 'PAYX', 'PCAR', 'PEG', 'PEP', 'PFE', 'PG', 'PGR', 'PLD', 'PM', 'PNC', 'PSA', 'PSX', 'PYPL', 'QCOM', 'REGN', 'RMD', 'ROKU', 'ROP', 'ROST', 'RTX', 'SBAC', 'SBUX', 'SCHW', 'SHOP', 'SHW', 'SHY', 'SIRI', 'SNPS', 'SO', 'SPGI', 'SPY', 'SRE', 'STZ', 'SWKS', 'SYK', 'SYY', 'T', 'TCOM', 'TFC', 'TGT', 'TIP', 'TJX', 'TMO', 'TMUS', 'TROW', 'TRV', 'TSLA', 'TTWO', 'TWLO', 'TXN', 'UAL', 'ULTA', 'UNH', 'UNP', 'UPS', 'USB', 'V', 'VNQ', 'VRSK', 'VRSN', 'VRTX', 'VZ', 'WBA', 'WDAY', 'WDC', 'WEC', 'WFC', 'WLTW', 'WM', 'WMT', 'WYNN', 'XEL', 'XHB', 'XLK', 'XLNX', 'XLU', 'XLV', 'XOM', 'XRT', 'YUM', 'ZTS'
			
		#datalist = ['VIX','TICK-NYSE','TRIN-NYSE','SPY','XLU','IAU']
		datalist = ['SPY','XLU','TICK-NYSE','XHB','AAPL','INTC','ADSK']
		#datalist = ['TICK-NYSE','A', 'AAL', 'AAPL', 'ABBV', 'ABT', 'ACN', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP', 'AFL', 'AGG', 'AGN', 'ALGN', 'ALL', 'ALXN', 'AMAT', 'AMGN', 'AMT', 'AMZN', 'ANTM', 'AON', 'APD', 'APH', 'ASML', 'ATVI', 'AVGO', 'AWK', 'AXP', 'AZO', 'BA', 'BABA', 'BAC', 'BAX', 'BDX', 'BIDU', 'BIIB', 'BK', 'BKNG', 'BLK', 'BMRN', 'BMY', 'BSX', 'C', 'CAT', 'CB', 'CCI', 'CDNS', 'CERN', 'CHKP', 'CHTR', 'CI', 'CL', 'CLX', 'CMCSA', 'CME', 'CNC', 'COF', 'COP', 'COST', 'CRM', 'CSCO', 'CSX', 'CTAS', 'CTSH', 'CTXS', 'CVS', 'CVX', 'D', 'DBA', 'DD', 'DE', 'DG', 'DHR', 'DIS', 'DLR', 'DLTR','DUK', 'EA', 'EBAY', 'ECL', 'ED', 'EL', 'EMB', 'EMR', 'EQIX', 'EQR', 'ES', 'ETN', 'EW', 'EWH', 'EWW', 'EXC', 'EXPE', 'FAST', 'FB', 'FDX', 'FE', 'FIS', 'FISV', 'GD', 'GE', 'GILD', 'GIS', 'GM', 'GOOG', 'GPN', 'GS', 'HAS', 'HCA', 'HD', 'HON', 'HPQ', 'HSIC', 'HUM', 'HYG', 'IAU', 'IBM', 'ICE', 'IDXX', 'ILMN', 'INCY', 'INFO', 'INTC', 'INTU', 'ISRG', 'ITW', 'JBHT', 'JD', 'JNJ', 'JPM', 'KHC', 'KLAC']
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
			start_date = date(2018,6,1), #Dates for backtesting
			end_date = date(2018,8,30),
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
			target=2,  #multiple of dollars risks per trade, to determine profit target per trade.  "2" represents target that is double dollars risked
			min_touches=2,#Support/Resistance - # of times price has to hit expected levels
			tolerance_perc=20, #how far most recent high(low) can be from period maximum(minimum) - if this spread is within this tolerance, represents a "touch".  Expressed as % of total max-min move range over period
			bounce_perc=0,#Keep at 0 - use only if you want to influence when support/resistance is calculated, as opposed to always calculating when touchpoints are hit (preferable)
			timer='off', #time program, 'on' or 'off', returns number of seconds
			writer='off', #export results to CSV output report 'on' or 'off'
			sma1 = 5,
			sma2 = 3,
			ema1= 5,  #8
			ema2= 10, #20
			obv=10,
			atrperiod= 5,
			atrdist= 2,   
			slope_period=5,
			breakout_per=5, 
			avg_per=5,
			rsi = 10,
			adx = 10,
			stoch_per=5,
			stoch_fast=3,
			bollinger_period=10,
			bollinger_dist=2,
			lookback=10,
			rank = 3, #How many tickers to select from ticker list
			)
			
	def __init__(self):
		"""initialize parameters and variables for Strategy Class"""

		#Set program start time
		start_time=datetime.now().time()
		print(f'Program start at {start_time}')
		print(f'Program time period: {UserInputs.model_params().get("start_date")} to {UserInputs.model_params().get("end_date")}')
		print(self.getdatanames())
		#print(f'Program Parameters: {self.params._getitems()}')
		
		#initialize variables and dicts
		self.nextcounter = 0	
		self.counter = 0	
		self.prenext_done = False
		self.pos = 0
		self.cash_avail = 0
		self.data_live = False
		self.tick_close = 0
		self.sortflag = 0

		self.inds = dict()
		self.long_stop_dict = defaultdict(list)
		self.short_stop_dict = defaultdict(list)
		self.gap_dict = defaultdict(list)
		self.rtop_dict = dict()
		self.rbot_dict = dict()
		self.topsorted_dict = dict()
		self.botsorted_dict = dict()
		
	
		#Create/Instantiate objects to access UserInputs class
		self.modelp = UserInputs.model_params()
		
		#Calc data feed metrics
		if not self.modelp.get('live_status'):
			datalist = UserInputs.datalist('hist')
			#self.data_feed_count = len(self.datas)
			#self.ticker_count = len(datalist)
			#self.number_timeframes = int(self.data_feed_count/self.ticker_count) #Needs to be an integer
		elif self.modelp.get('live_status'):
			ibdatalist = UserInputs.datalist('ib')
			#self.data_feed_count = len(self.datas)
			#self.ticker_count = len(ibdatalist)
			#self.number_timeframes = int(self.data_feed_count/self.ticker_count) #Needs to be an integer
		"""
		#Determine # of base timeframe periods within trading day and minimum period of loading
		self.minimum_data = int(self.ticker_count * self.modelp.get('timeframe2')/self.modelp.get('timeframe0'))  #since iterating over 5 min periods, and longest timeframe is 1 hour, there are 12 5 min periods in an hour
		self.intraday_periods = int(390/self.modelp.get('timeframe0'))
		"""

		#Initialize dictionary's	
		for i, d in enumerate(self.datas):	
			#print(f'**DATA IN STRATEGY**-{d._name}')
			
			#Initialize dictionaries by appending 0 value
			self.inds[d._name] = dict()  #Dict for all indicators

			#Get available cash
			self.cash_avail = self.broker.getcash()

			#Instantiate exact data references (can't loop or will only spit out last value)
			if d._name == 'TICK-NYSE0':
				self.tick_close = d.close
			
#*********************************************INITITIALIZE INDICATORS*********************************************************				
			#Calculate Slope
			self.inds[d._name]['slope'] = btind.Slope(d,
											period=self.p.slope_period,
											plot=False)
											
			self.inds[d._name]['slope_of_slope'] = 	btind.Slope(self.inds[d._name]['slope'],
												period=self.p.slope_period,
												plot=False)	
											
			#Determine on balance volume			
			self.inds[d._name]['obv'] = btind.obv(d,
											period=self.p.obv,
											plot=True)
			
			self.inds[d._name]['slope_obv'] = btind.Slope(self.inds[d._name]['obv'],
											period=self.p.obv,
											plot=False)
								
			#Determine opening gap and opening hi/low range (defined by b_time parameter)
			self.inds[d._name]['gap'] = btind.gap(d,
											period=self.p.breakout_per,
											plot=False)
			
			#AVERAGE TRUE RANGE INDICATOR
			self.inds[d._name]['atr'] = btind.ATR(d,
											period=self.p.atrperiod,
											plot=False)
											
											
			self.inds[d._name]['atr_stop'] = btind.atr_stop(d,self.inds[d._name]['atr'],
											atrdist = self.p.atrdist,
											dollars_risked = self.p.total_dollars_risked,
											dollars_per_trade = self.p.dollars_risked_per_trade,
											plot=False)
									
			self.inds[d._name]['hammer'] = btind.HammerCandles(d,
													plot=False)											

			
			#self.inds[d._name]['three_line_strike'] = btind.three_line_strike(d,plot=True)
													
			self.inds[d._name]['ema1'] = btind.EMA(d,
													period=self.p.ema1,
													plot=True)
														
			self.inds[d._name]['ema2'] = btind.EMA(d,
													period=self.p.ema2,
													plot=True)
													
			self.inds[d._name]['adx'] = btind.ADX(d,
												period=self.p.adx,
												plot=True)	
												
			self.inds[d._name]['slope_adx'] = 	btind.Slope(self.inds[d._name]['adx'],
													period=self.p.slope_period,
													plot=False)	
																						
			self.inds[d._name]['bollinger'] = btind.BollingerBands(d.close,
														period=self.p.bollinger_period,
														devfactor = self.p.bollinger_dist,
														plot=True)
								
			self.inds[d._name]['slope_ema1'] = 	btind.Slope(self.inds[d._name]['ema1'],
													period=self.p.slope_period,
													plot=False)	
			
			self.inds[d._name]['slope_ema2'] = 	btind.Slope(self.inds[d._name]['ema2'],
													period=self.p.slope_period,
													plot=False)	
					
			self.inds[d._name]['slope_ema_width'] = btind.Slope(self.inds[d._name]['ema1']-self.inds[d._name]['ema2'],
													period=self.p.slope_period,
													plot=False)	
													
			self.inds[d._name]['rsi']= btind.RSI(d,
												period=self.p.rsi,
												safediv=True,
												plot=True)
												
			self.inds[d._name]['stochastic'] = btind.StochasticSlow(d,
														period=self.p.stoch_per,
														period_dfast= self.p.stoch_fast,
														safediv=True,
														plot=False)
												
			#Plot ADX on same subplot as RSI							
			#self.inds[d._name]['adx'].plotinfo.plotmaster = self.inds[d._name]['rsi']
			
			"""
			self.inds[d._name]['support'] = btind.Support(d,
															period=self.p.lookback,
															min_touches = self.p.min_touches,
															tolerance_perc = self.p.tolerance_perc,
															bounce_perc = self.p.bounce_perc,
															plot=False)
			
			self.inds[d._name]['resistance'] = btind.Resistance(d,
														period=self.p.lookback,
														min_touches = self.p.min_touches,
														tolerance_perc = self.p.tolerance_perc,
														bounce_perc = self.p.bounce_perc,
														plot=False)	
			
			#Calculate VWAP																			
			self.inds[d._name]['vwap'] = btind.vwap(d,
													plot=False)
													
			#Relative Volume by Bar
			self.inds[d._name]['rel_volume'] = btind.RelativeVolumeByBar(d,
											start = self.modelp.get('sessionstart'),
											end = self.modelp.get('sessionend'),
											plot=False)
			"""				
			
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
		#pre-loads all indicator data for all timeframes before strategy starts executing
		self.counter += 1
		
		#If you want to see full set of data
		#print(f"Prenext len {len(self)}")
		
				
	def nextstart(self):
		#There is a nextstart method which is called exactly once, to mark the switch from prenext to next. 
		self.prenext_done = True
		print('---------------------------------------------------------------------------------------------------------------')	
		print(f'NEXTSTART called with strategy length {len(self)} - Pre Data has loaded, backtesting can start')
		print('---------------------------------------------------------------------------------------------------------------')

		#print('Strategy: {}'.format(len(self)))
		
		super(Strategy, self).nextstart()		

	
	def next(self):
		"""Iterates over each "line" of data (date and ohlcv) provided by data feed"""
		#Convert backtrader float date to datetime so i can see time on printout and manipulate time variables
		self.hourmin = datetime.strftime(self.data.num2date(),'%H:%M')
		self.dt = self.datetime.date()
		
		for i, d in enumerate(self.datas):  #Need to iterate over all datas so atr and sizing can be adjusted for multiple time frame user parameters	
		
		#-------------------STOCK SELECTION BASED ON OPEN CRITERIA-----------------------------------------
			#Stock Selection - collect data to be ranked at start of trading day and put in dictionary
			if self.hourmin=='08:30' and d._name!='TICK-NYSE0' and d._name==d._name[:-1]+'0':
				self.gap_dict[d._name] = round(self.inds.get(d._name).get('gap').lines.gap[0],3)  #get open gaps, put in dict
				
			#Stock Selection - once data is collected at 8:30, sort it.  Only do the sort 1 time (equal to one data - picked data0- since all data collected previous bar
			if self.hourmin=='08:35' and self.gap_dict is not None and d._name==self.data0._name: 
				self.rank_gap(d)	
			#-----------------------------------------------------------------------------------------------------
		
				
			#-------------------------------- EXIT TRADES IF CRITERIA MET------------------------------------------
			if d._name==d._name[:-1]+'0':
				self.pos = self.getposition(d).size
				
			if self.hourmin=='14:50' and self.pos:  #can't exit at 14:55 because cerebro submits at order at open of next bar
				self.eod_exit(d)
			
			if self.tick_close > 1000 and self.pos and d._name == d._name[:-1]+'0':
				self.exit_trade(d,'long')
			
			if self.tick_close < -1000 and self.pos and d._name == d._name[:-1]+'0':
				self.exit_trade(d,'short')
			#--------------------------------------------------------------------------------------------------------			
			
						
			#---------------------------------ENTRY LOGIC FOR LONG AND SHORT-----------------------------------------
			if self.pos==0 and self.entry_rules(d):  #Check that entry rules are met
				
				#BUY SIGNAL
				if self.signal_morn_break(d,'long'):
				#if self.signal_test_long(d):
					self.buyorder(d)

				#SELL SIGNAL
				if self.signal_morn_break(d,'short'):
				#elif self.signal_test_short(d):
					self.sellorder(d)
			#-----------------------------------------------------------------------------------------------------------

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
			and self.pos < 0
			):
		
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
			and self.pos > 0
			):
			
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
			
			
	def rel_volume(self,d):
		#Get relative volume and append to dict for later reference
		if d._name==d._name[:-1]+'0' and len(self) > (self.data_feed_count * 78 * 5):  #need enough data to look back 5 days
			self.rel_volume_t0 = self.inds.get(d._name[:-1]+'0').get('rel_volume')[0] #only returns prior day 
			print(self.rel_volume_t0)
			#self.rel_volume_t0 = self.inds.get(d._name[:-1]+'0').get('rel_volume')[0]
			
			
	def rank_gap(self,d):
		"""Create gap ranks across stock universe and return top X and bottom Y as per paramaters"""
		if self.hourmin == '08:35' and d._name==self.data0._name:
		
			sorted_res = sorted(self.gap_dict.items(), key = lambda x: x[1], reverse=True)  #Create sorted list -  key accepts a function (lambda), and every item (x) will be passed to the function individually, and return a value x[1] by which it will be sorted.
			self.rtop_dict = dict(sorted_res[:self.p.rank])  #Choose subset of tickers with highest rank (i.e. top 3)
			self.rbot_dict = dict(sorted_res[-self.p.rank:])  #Choose subset of tickers with lowest rank (i.e. bottom 3)
			self.topsorted_dict = {d: v for d,v in sorted(self.rtop_dict.items(),key=lambda x:x[1],reverse=True)}  #Same as above, except converted to dictionary so we can extract ticker 'keys'.  d._name is the key, and v is the value .  Reverse = true sorts greatest first
			self.botsorted_dict = {d: v for d,v in sorted(self.rbot_dict.items(),key=lambda x:x[1])}  #Same as above, except converted to dictionary so we can extract ticker 'keys'.  d._name is the key, and v is the value .  Reverse = true sorts greatest first
			self.sortflag = 1
			print(f'{d._name} {self.dt} {self.hourmin} Top Sort: {self.topsorted_dict}, Bottom Sort: {self.botsorted_dict}')
		
	
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
		
		if d._name==d._name[:-1]+'0': 
			if direction =='long':
				if(	
					d._name in self.topsorted_dict.keys()
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
				if( d._name in self.botsorted_dict.keys()
					and d.close[0] <= self.rng_low
					and self.tick_close < 0
					and self.slope_obv_t0 < 0
					and self.slope_t1 < 0					
					and self.slope_t2 < 0
					):
					return True
				else:
					return False
	

	def volatile(self,d):
		#Need to figure this out (ATR/VIX/Volume logic of some kind)
		self.rel_volume_t0 = self.inds.get(d._name[:-1]+'0').get('rel_volume')[0]
		
			
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
	for i in range (0,len(results[0].datas),3):
		for j, d in enumerate(results[0].datas):
			d.plotinfo.plot = i ==j
		#cerebro.plot(barup='olive', bardown='lightpink',volup = 'lightgreen',voldown='crimson')
		cerebro.plot(barup='olive', bardown='lightpink',volume=False)

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
	
	#Calculate Program end time
	end_time = datetime.now().time()
	print('Program end at {}'.format(end_time))
	
'''

# timeit statement 
print(timeit.timeit(      stmt = mycode, 
                    number = 30))
                    
                    
                    
