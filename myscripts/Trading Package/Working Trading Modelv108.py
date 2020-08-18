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

***FOR LIVE TRADING, MAKE SURE 'TICK-NYSE' DATA does not operate same time as FOREX data.

"""
#IMPORT MODULES
import backtrader as bt
import backtrader.indicators as btind
from backtrader.feeds import mysql
from datetime import date, time, datetime, timedelta
import pytz
from collections import defaultdict


class UserInputs():
	#This class is designed so runstrat() method can pick up these parameters (can use self.p.whatever to pass parameters for some reason)
	def __init__():
		pass
		
	def datalist(data_req):
		#Create list of tickers to load data for.  Market Breadth indicators need to be removed from initiliazation and next() so they are not traded
		#Data Notes - 'EMB' and 'SHY' data starts 8/3/2017, 'DBA' has almost double the amount of records the other tickers do for some reason.
		#TICK is # of NYSE stocks trading on an uptick vs # of stocks trading on downtick.  About 2800 stocks total, usually oscillates between -500 to +500.  Readings above 1000 or below -1000 considered extreme.  #TRIN is ratio of (# of Advance/Decliners)/(Advance/Decline Volume).  Below 1 is strong rally, Above 1 is strong decline.#VIX is 30 day expectation of volatility for S&P 500 options.  VIX spikes correlate to market declines because more people buying options to protect themselves from declines
		#'A', 'AAL', 'AAPL', 'ABBV', 'ABT', 'ACN', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP', 'AFL', 'AGG', 'AGN', 'ALGN', 'ALL', 'ALXN', 'AMAT', 'AMGN', 'AMT', 'AMZN', 'ANTM', 'AON', 'APD', 'APH', 'ASML', 'ATVI', 'AVGO', 'AWK', 'AXP', 'AZO', 'BA', 'BABA', 'BAC', 'BAX', 'BDX', 'BIDU', 'BIIB', 'BK', 'BKNG', 'BLK', 'BMRN', 'BMY', 'BSX', 'C', 'CAT', 'CB', 'CCI', 'CDNS', 'CERN', 'CHKP', 'CHTR', 'CI', 'CL', 'CLX', 'CMCSA', 'CME', 'CNC', 'COF', 'COP', 'COST', 'CRM', 'CSCO', 'CSX', 'CTAS', 'CTSH', 'CTXS', 'CVS', 'CVX', 'D', 'DBA', 'DD', 'DE', 'DG', 'DHR', 'DIS', 'DLR', 'DLTR', 'DOW', 'DUK', 'EA', 'EBAY', 'ECL', 'ED', 'EL', 'EMB', 'EMR', 'EQIX', 'EQR', 'ES', 'ETN', 'EW', 'EWH', 'EWW', 'EXC', 'EXPE', 'FAST', 'FB', 'FDX', 'FE', 'FIS', 'FISV', 'GD', 'GE', 'GILD', 'GIS', 'GM', 'GOOG', 'GPN', 'GS', 'HAS', 'HCA', 'HD', 'HON', 'HPQ', 'HSIC', 'HUM', 'HYG', 'IAU', 'IBM', 'ICE', 'IDXX', 'ILMN', 'INCY', 'INFO', 'INTC', 'INTU', 'ISRG', 'ITW', 'JBHT', 'JD', 'JNJ', 'JPM', 'KHC', 'KLAC', 'KMB', 'KMI', 'KO', 'KR', 'LBTYA', 'LBTYK', 'LHX', 'LLY', 'LMT', 'LOW', 'LQD', 'LRCX', 'LULU', 'MA', 'MAR', 'MCD', 'MCHP', 'MCO', 'MDLZ', 'MDT', 'MELI', 'MET', 'MMC', 'MMM', 'MNST', 'MO', 'MRK', 'MS', 'MSCI', 'MSFT', 'MSI', 'MU', 'MXIM', 'MYL', 'NEE', 'NEM', 'NFLX', 'NKE', 'NLOK', 'NOC', 'NOW', 'NSC', 'NTAP', 'NTES', 'NVDA', 'NXPI', 'ORCL', 'ORLY', 'PAYX', 'PCAR', 'PEG', 'PEP', 'PFE', 'PG', 'PGR', 'PLD', 'PM', 'PNC', 'PSA', 'PSX', 'PYPL', 'QCOM', 'REGN', 'RMD', 'ROKU', 'ROP', 'ROST', 'RTX', 'SBAC', 'SBUX', 'SCHW', 'SHOP', 'SHW', 'SHY', 'SIRI', 'SNPS', 'SO', 'SPGI', 'SPY', 'SRE', 'STZ', 'SWKS', 'SYK', 'SYY', 'T', 'TCOM', 'TFC', 'TGT', 'TIP', 'TJX', 'TMO', 'TMUS', 'TROW', 'TRV', 'TSLA', 'TTWO', 'TWLO', 'TXN', 'UAL', 'ULTA', 'UNH', 'UNP', 'UPS', 'USB', 'V', 'VNQ', 'VRSK', 'VRSN', 'VRTX', 'VZ', 'WBA', 'WDAY', 'WDC', 'WEC', 'WFC', 'WLTW', 'WM', 'WMT', 'WYNN', 'XEL', 'XHB', 'XLK', 'XLNX', 'XLU', 'XLV', 'XOM', 'XRT', 'YUM', 'ZTS'
			
		#datalist = ['VIX','TICK-NYSE','TRIN-NYSE','SPY','XLU','IAU']
		datalist = ['SPY','XLU','TICK-NYSE','XHB','XLK','A', 'AAL','AAPL', 'ABBV', 'ABT', 'ACN', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP', 'AFL', 'AGG', 'AGN', 'ALGN', 'ALL', 'ALXN', 'AMAT', 'AMGN', 'AMT', 'AMZN', 'ANTM']
		#datalist = ['TICK-NYSE','A', 'AAL', 'AAPL', 'ABBV', 'ABT', 'ACN', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP', 'AFL', 'AGG', 'AGN', 'ALGN', 'ALL', 'ALXN', 'AMAT', 'AMGN', 'AMT', 'AMZN', 'ANTM', 'AON', 'APD', 'APH', 'ASML', 'ATVI', 'AVGO', 'AWK', 'AXP', 'AZO', 'BA', 'BABA', 'BAC', 'BAX', 'BDX', 'BIDU', 'BIIB', 'BK', 'BKNG', 'BLK', 'BMRN', 'BMY', 'BSX', 'C', 'CAT', 'CB', 'CCI', 'CDNS', 'CERN', 'CHKP', 'CHTR', 'CI', 'CL', 'CLX', 'CMCSA', 'CME', 'CNC', 'COF', 'COP', 'COST', 'CRM', 'CSCO', 'CSX', 'CTAS', 'CTSH', 'CTXS', 'CVS', 'CVX', 'D', 'DBA', 'DD', 'DE', 'DG', 'DHR', 'DIS', 'DLR', 'DLTR','DUK', 'EA', 'EBAY', 'ECL', 'ED', 'EL', 'EMB', 'EMR', 'EQIX', 'EQR', 'ES', 'ETN', 'EW', 'EWH', 'EWW', 'EXC', 'EXPE', 'FAST', 'FB', 'FDX', 'FE', 'FIS', 'FISV', 'GD', 'GE', 'GILD', 'GIS', 'GM', 'GOOG', 'GPN', 'GS', 'HAS', 'HCA', 'HD', 'HON', 'HPQ', 'HSIC', 'HUM', 'HYG', 'IAU', 'IBM', 'ICE', 'IDXX', 'ILMN', 'INCY', 'INFO', 'INTC', 'INTU', 'ISRG', 'ITW', 'JBHT', 'JD', 'JNJ', 'JPM', 'KHC', 'KLAC']
		#datalist = ['SPY','XHB','XLU','MCD','XLK','XLV','XRT','TICK-NYSE','IAU','TIP','AGG','VNQ','XOM','LQD','EWW','HYG','DBA']
		ibdatalist = ['SPY','XHB','XLU','MCD','XLK']
		#ibdatalist = ['EUR.USD','GBP.USD']  #Make sure not to include comma after last ticker or program won't read in live trading
		
		if data_req == 'ib':
			return ibdatalist
		elif data_req == 'hist':
			return datalist

	def model_params():
		params = dict(
			live_status = False,  #Flip between live trading (True) and backtesting (False)
			start_date = date(2018,1,2), #Dates for backtesting
			end_date = date(2018,3,30),
			timeframe0 = 5, #MINUTES
			timeframe1 = 15, #MINUTES
			timeframe2 = 60, #MINUTES
			timeframe1on = True,
			timeframe2on = True,
			sessionstart = time(8,30),
			sessionend = time(23,55),
			start_cash=100000,  #For backtesting only, live trading calls broker for available cash
			)
		return params
		
				
class Strategy(bt.Strategy):
	params = dict(
			printlines = False,
			dollars_risked_per_trade = 300,
			total_dollars_risked = 20000,
			target=2,  #multiple of dollars risks per trade, to determine profit target per trade.  "2" represents target that is double dollars risked
			min_touches=2,#Support/Resistance - # of times price has to hit expected levels
			tolerance_perc=20, #how far most recent high(low) can be from period maximum(minimum) - if this spread is within this tolerance, represents a "touch".  Expressed as % of total max-min move range over period
			bounce_perc=0,#Keep at 0 - use only if you want to influence when support/resistance is calculated, as opposed to always calculating when touchpoints are hit (preferable)
			timer='off', #time program, 'on' or 'off', returns number of seconds
			writer='off', #export results to CSV output report 'on' or 'off'
			position = 5,
			ohlc = 5,
			sma1 = 5,
			sma2 = 3,
			ema1= 5,  #8
			ema2= 3, #20
			obv=5,
			atrperiod= 5,
			atrdist= 2,   
			slope_period=5,
			breakout_per=5, 
			avg_per=5,
			adx = 14,
			stoch_per=5,
			stoch_fast=3,
			bollinger_period=10,
			bollinger_dist=2,
			lookback=10,
			rank = 3, #How many tickers to select from ticker list
			)
		
	
	def __init__(self):
			
		#Set program start time
		start_time=datetime.now().time()
		print(f'Program start at {start_time}')
		print(f'Program time period: {UserInputs.model_params().get("start_date")} to {UserInputs.model_params().get("end_date")}')
		#print(f'Program Parameters: {self.params._getitems()}')
		
		#initialize counters for prenext/next
		self.nextcounter = 0	
		self.counter = 0	
		self.prenext_done = False
		self.pos = 0
		self.cash_avail = 0
		self.data_live = False
		self.tick_close = 0
		self.spy_close = 0
		self.sortflag = 0

		#Define dictionaries and lists to be accessed from all timeframes
		self.inds = dict()
		self.size_dict = defaultdict(list)
		self.inorder_dict = defaultdict(list)
		self.long_stop_dict = defaultdict(list)
		self.short_stop_dict = defaultdict(list)
		self.target_long_dict = defaultdict(list)
		self.target_short_dict = defaultdict(list)
		self.gap_dict = defaultdict(list)
		self.combosorted_dict = defaultdict(list)
	
		#Create/Instantiate objects to access user input parameters
		self.modelp = UserInputs.model_params()
		
		#Determine interval for timeframe looping
		if not self.modelp.get('live_status'):
			datalist = UserInputs.datalist('hist')
			self.data_feed_count = len(self.datas)
			self.ticker_count = len(datalist)
			self.number_timeframes = int(self.data_feed_count/self.ticker_count) #Needs to be an integer
		elif self.modelp.get('live_status'):
			ibdatalist = UserInputs.datalist('ib')
			self.data_feed_count = len(self.datas)
			self.ticker_count = len(ibdatalist)
			self.number_timeframes = int(self.data_feed_count/self.ticker_count) #Needs to be an integer
		
		self.minimum_data = int(self.ticker_count * self.modelp.get('timeframe2')/self.modelp.get('timeframe0'))  #since iterating over 5 min periods, and longest timeframe is 1 hour, there are 12 5 min periods in an hour
	
		#Determine # of base timeframe periods within trading day
		self.intraday_periods = int(390/self.modelp.get('timeframe0'))
		
		#************************INITITIALIZE INDICATORS*********************************************************

		#Initialize dictionary's	
		for i, d in enumerate(self.datas):	
			#print(f'**DATA IN STRATEGY** -  {d._name}')
			
			self.name_t0 = d._name[:-1]+'0'
			self.name_t1 = d._name[:-1]+'1'
			self.name_t2 = d._name[:-1]+'2'			
			
			#Initialize dictionaries by appending 0 value
			self.inds[d._name] = dict()  #Dict for all indicators


			#Get available cash
			self.cash_avail = self.broker.getcash()


			#Instantiate exact data references (can't loop or will only spit out last value)
			if d._name == 'TICK-NYSE0':
				self.tick_close = d.close
			
			if d._name == 'SPY0':
				self.spy_close = d.close
			
			
			#Calculate VWAP																			
			self.inds[d._name]['vwap'] = btind.vwap(d,
													plot=False)
													
			#Determine on balance volume
			self.inds[d._name]['obv'] = btind.obv(d,
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
											
			#Slope indicators
			self.inds[d._name]['slope']= btind.Slope(d.close,
													period=self.p.slope_period,
													plot=False)
													
			self.inds[d._name]['slope_obv'] = 	btind.Slope(self.inds[d._name]['obv'],
												period=self.p.slope_period,
												plot=False)
												
		print('Start preloading data to meet minimum data requirements')	
	
	
	#*********************************************************************************************************************
	
	def next(self):
			
		#Convert backtrader float date to datetime so i can see time on printout and manipulate time variables
		self.hourmin = datetime.strftime(self.data.num2date(),'%H:%M')
		self.dt = self.datetime.date()
				
		for i, d in enumerate(self.datas):  #Need to iterate over all datas so atr and sizing can be adjusted for multiple time frame user parameters

	
			#Stock Selection - collect data to be ranked at start of trading day and put in dictionary
			if self.hourmin=='08:30' and d._name!='TICK-NYSE0' and d._name==d._name[:-1]+'0':
				self.gap_dict[d._name] = round(self.inds.get(d._name).get('gap').lines.gap[0],3)  #get open gaps, put in dict
				
			#Stock Selection - once data is collected at 8:30, sort it.  Only do the sort 1 time (equal to one data - picked data0- since all data collected previous bar
			if self.hourmin=='08:35' and self.gap_dict is not None and d._name==self.data0._name: 
				self.rank_gap(d)	
			
			#EXIT TRADES IF CRITERIA MET
			self.eod_exit(d._name)
			self.short_exit(d,d._name)
			self.long_exit(d,d._name)

			#DEFINE OVERALL ENTRY LOGIC FOR LONG AND SHORT
			if self.entry_rules(d,d._name):  #Check that entry rules are met
				
				#Check if long and short signals are true - if so, submit trade
				if self.signal_morn_break(d,d._name,'long'):
					self.buyorder(d,d._name,self.trade_size(d._name),d.open[0])
					
				if self.signal_morn_break(d,d._name,'short'):
					self.sellorder(d,d._name,self.trade_size(d._name),d.open[0])

	#*********************************************************************************************************************

	def short_exit(self,d,dname):
		#EXIT LOGIC FOR INTRADAY SHORTS
		if d._name == 'TICK-NYSE0':
			self.tick_close = d.close[0]
		
		if(d._name == dname==d._name[:-1]+'0'
			#and not (d._name[:-1]=='VIX' or d._name[:-1]=='TICK-NYSE' or d._name[:-1]=='TRIN-NYSE' or d._name[:-1]=='SPY')	
			and self.pos
			and self.prenext_done  #Start trading after all prenext loads (live and backtest modes) 
			and self.tick_close > 1000
			):
		
			#CANCEL ASSOCIATED STOP AND TARGET ORDERS
			if self.short_stop_dict.get(dname) is not None:
				self.cancel(self.short_stop_dict.get(dname)[-1])
				#self.cancel(self.target_short_dict.get(d._name)[-1])


			#SHORT EXIT ORDER - closes existing position and cancels outstanding stop-loss ord	
			self.exit_short_name = f'{dname} - Exit Short Trade'        
			self.exit_short = self.close(dname,
										size=self.size_dict.get(dname)[-1],
										name=self.exit_short_name)
			
			print(f'{self.dt} {self.hourmin} EXIT SHORT {dname} - {self.size_dict.get(dname)[-1]} shares at {d.close[0]}')
			self.size_dict[dname].append(0)
			
			#For Bracket Trading if desired
			#print(self.inorder_dict.get(d._name)[-1][1])  #dictionary holds list of backtrader orders since its bracket trade
			#print(self.inorder_dict.get(d._name)[-1][1].status)
			
		
	def long_exit(self,d,dname):
		#EXIT LOGIC FOR INTRADAY LONGS
		if d._name == 'TICK-NYSE0':
			self.tick_close = d.close[0]
		
		if(d._name == dname==d._name[:-1]+'0'
			#and not (d._name[:-1]=='VIX' or d._name[:-1]=='TICK-NYSE' or d._name[:-1]=='TRIN-NYSE' or d._name[:-1]=='SPY')	
			and self.pos
			and self.prenext_done  #Start trading after all prenext loads (live and backtest modes) 
			and self.tick_close<-1000
			):
			
			#CANCEL ASSOCIATED STOP AND TARGET ORDERS
			if self.long_stop_dict.get(dname) is not None:
				self.cancel(self.long_stop_dict.get(dname)[-1])
				#self.cancel(self.target_long_dict.get(d._name)[-1])
			
			#LONG EXIT ORDER - closes existing position and cancels outstanding stop-loss order
			print(f'{self.dt} {self.hourmin} EXIT LONG {dname} - {self.size_dict.get(dname)[-1]} shares at {d.close[0]}')
			self.exit_long_name = f'{d._name} - Exit Long Trade'
			
			self.exit_long = self.close(dname,
										size=self.size_dict.get(dname)[-1],
										name=self.exit_long_name)
			self.size_dict[dname].append(0)
		

	def eod_exit(self,dname):
		#EXIT LOGIC FOR EOD EXITS
		if self.hourmin=='14:50' and self.pos != 0 and d._name==d._name[:-1]+'0' and self.size_dict:

			#CANCEL ALL ORDERS AT END OF DAY (STOPS AND TARGETS)
			if self.long_stop_dict.get(dname) is not None:
				self.cancel(self.long_stop_dict.get(dname)[-1])
				#self.cancel(self.target_long_dict.get(dname)[-1])
			
			if self.short_stop_dict.get(dname) is not None:
				self.cancel(self.short_stop_dict.get(dname)[-1])
				#self.cancel(self.target_short_dict.get(dname)[-1])
			
			self.eod_name = f'{dname} - EXIT ALL TRADES AT EOD'
			self.eod_close = self.close(dname,
										size=self.size_dict.get(dname)[-1],
										name=self.eod_name)
			
			self.size_dict[dname].append(0)	
		

	def trade_size(self,dname):
		#Calculate Sizing
		self.size = int(self.inds.get(dname).get('atr_stop').lines.size[0])
		#print(d._name, self.dt, self.hourmin, self.long_stop,self.short_stop,self.size)
	
	
	def entry_rules(self,d,dname):
		if not self.modelp.get('live_status'):
			pos = self.getposition(d).size
		else:
			pos = self.getposition(d).size
			self.cash_avail = self.broker.getcash()
			print(d._name,self.dt,self.hourmin,d.open[0],d.high[0],d.low[0],d.close[0],d.volume[0],self.cash_avail)
	
		if (pos==0
			and not d._name[:-1]=='TICK-NYSE'
			and (self.hourmin>='09:00'and self.hourmin<='11:00')
			and self.cash_avail > self.p.total_dollars_risked
			and self.prenext_done #Start trading after all prenext data loads
			and self.sortflag == 1
			):
				
			return True
		else:
			return False

	def sellorder(self,d,dname,mysize,myopen):
		"""Places sell order and apends size and stops to dictionary"""
		date = self.datetime.date()
		
		if dname==d._name[:-1]+'0':
			#Calculate STOP (ATR BASED)
			self.short_stop = self.inds.get(dname).get('atr_stop').lines.short_stop[0]
			
			#Calculate Target Price
			if mysize:
				self.target_short = round(myopen - ((self.p.dollars_risked_per_trade*self.p.target)/mysize),2)
			
			#SHORT ENTRY ORDER
			#Create Short Entry Order
			short_name = '{} - Enter Short Trade'.format(dname)
			self.short_ord = self.sell(data=dname,
				 size=mysize,
				 exectype=bt.Order.Market,
				 transmit=False,
				 name=short_name,
				 )
												
			#Create Fixed Short Stop Loss	 
			short_stop_name = f'{dname} - Submit STOP for Short Entry'
			self.short_stop_ord = self.buy(data=dname,
				size=mysize,
				exectype=bt.Order.Stop,
				price=self.short_stop,
				transmit=True,
				parent=self.short_ord,
				name = short_stop_name,
				)

			self.short_stop_dict[dname].append(self.short_stop_ord)
			self.size_dict[dname].append(mysize)
			print(f'{date} SELL SELL SELL {dname} - {mysize} shares at {d.close[0]}.  Stop price @ {self.short_stop}')
		


	def buyorder(self,d,dname,mysize,myopen):
		"""Places buy order and apends size and stops to dictionary"""		
		if dname==dname[:-1]+'0':
			#Calculate STOP (ATR BASED)
			self.long_stop = self.inds.get(dname).get('atr_stop').lines.long_stop[0]
			 
			#Create Target Price
			if mysize:
				self.target_long = round(myopen +((self.p.dollars_risked_per_trade*self.p.target)/mysize),2)
		
			#CREATE LONG ORDER
			long_name = f'{dname} - Enter Long Trade'
			self.long_ord = self.buy(data=dname,
								size=mysize,
								exectype=bt.Order.Market,
								transmit=False,
								name = long_name)
		
			#Create Fixed Long Stop Loss
			long_stop_name = f'{dname} - Submit STOP for Long Entry'
			self.long_stop_ord = self.sell(data=dname,
								size=mysize,
								exectype=bt.Order.Stop,
								price=self.long_stop,
								transmit=True,
								parent=self.long_ord,
								name=long_stop_name)
								

			#Create size dictionary so same size can be referenced when you exit trade
			self.size_dict[dname].append(mysize)
			#Track if currently in an order or not
			self.long_stop_dict[d._name].append(self.long_stop_ord)
			print(f'{self.dt} {self.hourmin} BUY BUY BUY {dname} - {mysize} shares at {d.close[0]}.  Stop price @ {self.long_stop}')

			"""
			#Create Long Order
			#FOR BRACKET TRADING
			long_name = f'{d._name} - Enter Long Trade, Stop price: {self.long_stop}, Target: {self.target_long}'
			self.long_ord = self.buy_bracket(data=d._name,size=self.size,limitprice=self.target_long,stopprice=self.long_stop, name=long_name)
			print(self.inorder_dict.get(d._name)[-1][1])
			"""

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
		
			
	def signal_morn_break(self,d,dname,direction):
		
		if dname==dname[:-1]+'0':
			self.slope_obv_t0 = self.inds.get(dname).get('slope_obv')[0] #Get OBV
			
		if dname==dname[:-1]+'1':
			self.slope_t1 = self.inds.get(dname).get('slope')[0]  #Calc slope for time1
			
		if dname==dname[:-1]+'2':
			self.slope_t2 = self.inds.get(dname).get('slope')[0]  #Calc slope for time2
		
		#Determine open 15 minute range
		self.rng_high = round(self.inds[dname]['gap'].lines.rng_high[0],2)
		self.rng_low = round(self.inds[dname]['gap'].lines.rng_low[0],2)	
		
		if direction =='long':
			#print(dname)
			if(dname in self.topsorted_dict.keys()	
				and dname==d._name[:-1]+'0'
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
				and dname==d._name[:-1]+'0'
				and d.close[0] >= self.rng_high
				and self.tick_close > 0
				and self.slope_obv_t0 > 0
				and self.slope_t1 > 0					
				and self.slope_t2 > 0
				):
				return True
			else:
				return False
	
	
	def notify_order(self, order):

		if not order.status == order.Completed:
			return  # discard any other notification

	
		if order.status == order.Completed:
			if order.isbuy():
				print('-'*80)
				print(f"BUY EXECUTED, Date: {self.dt} {self.hourmin} Price: {round(order.executed.price,2)}, Cost: {round(order.executed.value),2}, Size {order.executed.size}, Name: {order.info['name']}")
			
			elif order.issell():
				print('-'*80)
				print(f"SELL EXECUTED, Date: {self.dt} {self.hourmin} Price: {round(order.executed.price,2)}, Cost: {round(order.executed.value,2)}, Size {order.executed.size}, Name: {order.info['name']}")


	def notify_trade(self, trade):

		if trade.isclosed:
			print('-'*80)
			print(f"{self.dt} {self.hourmin} TRADE CLOSED - Price: {round(trade.price,2)}, Net Profit: {round(trade.pnl,2)}")
	
	def notify_data(self, data, status):
		#To notify us when delayed backfilled data becomes live data during live trading
		print('*' * 5, 'DATA NOTIF:', data._getstatusname(status))
		if status == self.data.LIVE:
			self.data_live = True
			
	def prenext(self):
		#pre-loads all indicator data for all timeframes before strategy starts executing
		self.counter += 1
		
		#If you want to see full set of data
		"""
		for i, d in enumerate(self.datas):
			if d._name == d._name[:-1]+'0':
				print('{} {} prenext len {} - counter {} {} {} {} {} {}'.format(d._name,d.datetime.datetime().strftime('%Y-%m-%d %H:%M:%S'),len(self), self.counter,d.open[0],d.high[0],d.low[0],d.close[0],d.volume[0]))
		"""
				
	def nextstart(self):
		#There is a nextstart method which is called exactly once, to mark the switch from prenext to next. 
		self.prenext_done = True
		print('---------------------------------------------------------------------------------------------------------------')
		print(f'NEXTSTART called with strategy length {len(self)} - Pre Data has loaded, backtesting can start')
		print('---------------------------------------------------------------------------------------------------------------')

		#print('Strategy: {}'.format(len(self)))
		
		super(Strategy, self).nextstart()
	
			
	def regime_early_bullish(self,d,dname):
		close = self.inds.get(d.name).get('ohlc').lines.c[0]


	def regime_late_bullish(self,d):
		pass
		
		
	def regime_early_bearish(self,d):
		pass
		
	
	def regime_early_bearish(self,d):
		pass
		
			
#********************************************RUN STRATEGY**************************************************************************
def runstrat():
	
	#Create an instance of cerebro
	cerebro = bt.Cerebro(exactbars=-1)  #exactbars True reduces memory usage significantly, but change to '-1' for partial memory savings (keeping indicators in memory) or 'false' to turn off completely if having trouble accessing bars beyond max indicator paramaters.  
	cerebro.broker.set_coc(False)    #allows you to buy/sell close price of previous bar, vs. default behavior of open on next bar.
	cerebro.broker.set_coo(False)    #default is False, meaning assuming day bars,orders are put in at end of previous day (end of previous bar) and order execution happens at open of today's bar (at open of current bar).  Cheat on open puts order in same day before bar opens, and executes at open price.  Such a use case fails when the opening price gaps (up or down, depending on whether buy or sell is in effect) and the cash is not enough for an all-in operation. This forces the broker to reject the operation.
	cerebro.broker.set_shortcash(True) #False means decrease cash available when you short, True means increase it
	
	#Add our strategy
	cerebro.addstrategy(Strategy)
	
	#Create/Instantiate objects to access parameters from UserInput Class
	#Can NOT create object referencing Strategy class as per backtrader
	modelp = UserInputs.model_params()
	
	if modelp.get('live_status'):
		ibdatalist = UserInputs.datalist('ib')
		#Ensure stock lists have no duplicates - duplicates will BREAK program
		if len(ibdatalist) != len(set(ibdatalist)):
			print("*****You have duplicates in stock list - FIX LIST*****")
	else:
		datalist = UserInputs.datalist('hist')
		if len(datalist) != len(set(datalist)):
			print("*****You have duplicates in stock list - FIX LIST*****")
	
	#GET THE DATA
	session_start = modelp.get('sessionstart')
	session_end = modelp.get('sessionend')	
	
#*******************************************************************************************************************************
	if not modelp.get('live_status'):
		#******BACTESTING ONLY - MYSQL DATABASE*********
		
		#mysql configuration items for connection
		host = '127.0.0.1'
		user = 'root'
		password = 'EptL@Rl!1'
		database = 'Stock_Prices'
		table = '5_min_prices'
		
		#Determine data range to run
		start_date = modelp.get('start_date')
		end_date = modelp.get('end_date')
	
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
		
#*****************************************************************************************************************************
	elif modelp.get('live_status'):
		#*****  LIVE TRADING PARAMETERS*******
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
								rtbar=True,
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
							
		
		
		forexdatalist = ['EUR','GBP'] #'GBP','AUD','NZD' MAKE SURE NO COMMAS AFTER LAST TICKER
		for i,j in enumerate(forexdatalist):
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
		
		
		#ADD MARKET BREADTH DATA LIKE TICK
		indexdatalist = ['TICK-NYSE']  #MAKE SURE NO COMMAS AFTER LAST TICKER
		for i,j in enumerate(indexdatalist):
			tickdata = store.getdata(dataname=j,
									sectype='IND',
									exchange='NYSE',
									currency='USD',
									timeframe=bt.TimeFrame.Minutes,
									what = 'TRADES',  #Needs to be 'TRADES' for TICK-NYSE to pull data
									rtbar = False,
									sessionstart = session_start,
									sessionend = session_end,
									)
									
			cerebro.resampledata(tickdata, name="{}0".format(j),
								timeframe=bt.TimeFrame.Minutes, 
								compression=modelp.get('timeframe0'))
			
		
			#Apply resamplings
			if modelp.get('timeframe1on'):
				tickdata_Timeframe1 = cerebro.resampledata(tickdata,name="{}1".format(j),
															timeframe=bt.TimeFrame.Minutes,
															compression = modelp.get('timeframe1'))
				
			if modelp.get('timeframe2on'):
				tickdata_Timeframe2 = cerebro.resampledata(tickdata,name="{}2".format(j),
															timeframe=bt.TimeFrame.Minutes,
															compression = modelp.get('timeframe2'))
		
			
			
		cerebro.broker = store.getbroker()  #*****Critical line of code to access broker so you can trade*****
#**********************************************************************************************************************************
	# Add SQN to qualify the trades (rating to analyze quality of trading system: 2.5-3 good, above 3 excellent.  SquareRoot(NumberTrades) * Average(TradesProfit) / StdDev(TradesProfit).  Need at least 30 trades to be reliable
	cerebro.addanalyzer(bt.analyzers.SQN)
	
	#Add Sharpe Ratio - configured for daily returns
	cerebro.addanalyzer(bt.analyzers.SharpeRatio)
	
	#Adding my own custom analyzer - when creating analyzer, make sure to include file in _init_.py within backtrader.analyzer folder so it runs
	cerebro.addanalyzer(bt.analyzers.AcctStats)
	
	#Adding analyzer for drawdown
	cerebro.addanalyzer(bt.analyzers.DrawDown)
	
	# Add TradeAnalyzer to output trade statistics - THESE ARE THE TRADE NOTIFICATIONS THAT ARE PRINTED WHEN PROGRAM IS RUN
	cerebro.addanalyzer(bt.analyzers.Transactions)
	
	#Adds just buy/sell observer to chart (assuming stdstats is set to false)
	cerebro.addobservermulti(bt.observers.BuySell,)
	
	#Adds custom observers
	cerebro.addobserver(bt.observers.AcctValue) #reports trade statistics in command prompt at end of program run
	#cerebro.addobserver(bt.observers.OrderObserver) #reports trades in command prompt when program is run
	
	#Generate output report in csv format
	if UserInputs.model_params().get('writer')=='on':
		current_time = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.csv") 
		csv_file = 'C:/Program Files (x86)/Python36-32/Lib/site-packages/backtrader/out/'
		csv_file += 'Strategy'
		csv_file += current_time
		cerebro.addwriter(bt.WriterFile, csv = True, out=csv_file)
		print("Writer CSV Report On")

#************************************************************************************************************************************
	#RUN EVERYTHING
	if modelp.get('live_status'):

		results = cerebro.run(preload=False,
						stdstats=False, #enables some additional chart information like profit/loss, buy/sell, etc, but tends to clutter chart
						runonce=False,
						)
	
		#To access results (strategy dictionaries, parameters, etc. after program runs)
		thestrat = results[0]	
		#print(dir(thestrat))  #returns list of all attributes and methods associated with results object
		"""
		for i,d in enumerate(thestrat.datas):
			print(d._name,thestrat.sorted_dict)
			print(d.open.array)
		"""
		
	if not modelp.get('live_status'):
		
		results = cerebro.run(preload=False,
						stdstats=False, #enables some additional chart information like profit/loss, buy/sell, etc, but tends to clutter chart
						runonce=False,
						)
#************************************************************************************************************************************		
		#Print analyzers
		for alyzer in results[0].analyzers:
			alyzer.print()
		
		#Calculate Program end time
		end_time = datetime.now().time()
		print('Program end at {}'.format(end_time))
		
		"""
		#PLOT TRADING RESULTS - **Ensure trading session ends at 2:55 (if it ends at 3, some tickers only go up to 2:55, creating data length mismatches between tickers that doesn't allow plotting)
		plot_end = modelp.get('end_date')-timedelta(hours=8, minutes=0, seconds=.01) #Hack to prevent errors with plotting, specifically x and y shape different error
		
		#Chart 5 minute timeframes only, 1 by 1
		
		for i in range (0,len(results[0].datas),3):
			for j, d in enumerate(results[0].datas):
				d.plotinfo.plot = i ==j
			
			cerebro.plot(end = plot_end, barup='olive', bardown='lightpink',volup = 'lightgreen',voldown='crimson')
		"""
				
if __name__ == '__main__':
	
	#Run strategy
	runstrat()



"""
def signal_placeholder(self,d,dname):
		pass
		
		#INITIALIZATION
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
			
												
			self.inds[d._name]['slope_of_slope_obv'] = 	btind.Slope(self.inds[d._name]['slope_obv'],
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
"""	















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







