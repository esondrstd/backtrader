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

"""



#IMPORT MODULES
import backtrader as bt
import backtrader.indicators as btind
from backtrader.feeds import mysql
from datetime import date, time, datetime, timedelta
import pytz
import timeit
import copy
import math
from collections import defaultdict


#***************************************************DEVELOP STRATEGY********************************************************************
#DEFINE ALL STRATEGY USER INPUTS
class UserInputs():
	
	def __init__():
		pass
	
	def datalist(data_req):
		#Create list of tickers to load data for.  Market Breadth indicators need to be removed from initiliazation and next() so they are not traded
		
		#TICK is # of NYSE stocks trading on an uptick vs # of stocks trading on downtick.  About 2800 stocks total, usually oscillates between -500 to +500.  Readings above 1000 or below -1000 considered extreme
		#TRIN is ratio of (# of Advance/Decliners)/(Advance/Decline Volume).  Below 1 is strong rally, Above 1 is strong decline.
		#VIX is 30 day expectation of volatility for S&P 500 options.  VIX spikes correlate to market declines because more people buying options to protect themselves from declines
		
		#datalist = ['VIX','TICK-NYSE','TRIN-NYSE','SPY','XLU','IAU']
		datalist = ['SPY','IAU','XLU',]
		#datalist = ['SPY','IAU','TIP','AGG','XHB','DBA','VNQ','LQD','EWZ','XLU','MCD','XLK',]
		#datalist = ['IAU','TIP','AGG','EMB','VNQ','XLU','SPY','XOM','LQD','EWZ','MCD','DBA','EWH','EWW','HYG','XLV','XRT','XLK','SHY','XHB']
		ibdatalist = ['SPY-STK-SMART-USD','AAPL-STK-SMART-USD']
		#ibdatalist = ['EUR.USD-CASH-IDEALPRO',]
		
		if data_req == 'ib':
			return ibdatalist
		elif data_req == 'hist':
			return datalist
	
	def model_params():
		params = dict(
			live_status = False,  #Flip between live trading (True) and backtesting (False)
			start_date = date(2017, 1, 2), #Dates for backtesting
			end_date = date(2017,4,1),
			timeframe0 = 5, #MINUTES
			timeframe1 = 15, #MINUTES
			timeframe2 = 60, #MINUTES
			timeframe1on = True,
			timeframe2on = True,
			printlines = False,
			sessionstart = time(8,30),
			sessionend = time(14,55),
			TrailingStop = False,
			start_cash=100000,
			dollars_risked_per_trade = 300,
			total_dollars_risked = 20000,
			target=3,  #multiple of dollars risks per trade, to determine profit target per trade.  "2" represents target that is double dollars risked
			min_touches=2,#Support/Resistance
			tolerance_perc=1.5,#Support/Resistance
			bounce_perc=5,#Support/Resistance
			timer='off', #time program, 'on' or 'off', returns number of seconds
			writer='off', #export results to CSV output report 'on' or 'off'
			)
		return params
			
	#make sure these are NUMBERS ONLY, NOT STRINGS
	def ind_params():
		params = dict(
			position = 5,
			ohlc = 5,
			sma1 = 10,
			sma2 = 20,
			ema1= 10,
			ema2= 20,
			atrperiod= 14,
			atrdist= 2,   
			slope_period=14,
			breakout_per=5, 
			avg_per=10,
			adx = 14,
			stoch_per=14,
			stoch_fast=3,
			bollinger_period=20,
			bollinger_dist=2,
			avgvolume = 40,  #Needs to be at least 350 (at highest calculation) to calculate 5 periods of avg intraday volume (period over period)
			lookback=10,
			priorday=40,
			vwap_lookback=40,#Support/Resistance calcs
			)
		return params
	
	def max_ind():	
		indicator_dict = UserInputs.ind_params()
		maxind = max(indicator_dict.values()) 
		return maxind
		
	def ib_backfill_start(maxind):
		#sometimes IB backfill does not collect enough data for live trading - this creates new start date for backfill to guarantee enough data collected for longest indicator lookback period
		today_date = datetime.now()
		backfill_days = -(maxind)
		ib_start_date = today_date + timedelta(days=backfill_days)
		return ib_start_date
	
class Strategy(bt.Strategy,UserInputs):
	#Due to backtrader convention, any strategy arguments should be defined inside `params` dictionary or passed via bt.Cerebro() class via .addstrategy() method.
	params = copy.deepcopy(UserInputs.ind_params()) #Access parameters from other class so params can be referenced outside Strategy class.  'Deep copy' copies all dictionary keys and values, vs. regular(shallow) copy which just creates reference back to old dictionary
	
	def __init__(self):
		
		#Set program start time
		start_time=datetime.now().time()
		print('Program start at {}'.format(start_time))
	
		#print(self.params.sma1, self.p.ema1, self.params.atrperiod) #Proof deep copy worked for params
		
		#initialize counters for prenext/next
		self.dayperiod = 0
		self.nextcounter = 0	
		self.counter = 0
		self.counttostop = 0
		self.datastatus = 0
		self.prenext_done = False
		self.bought = 0
		self.sold = 0
		self.long_exit_price = 0
		self.short_exit_price = 0
		self.trade_open_counter = 0
		self.trade_close_counter = 0	
		self.trade_total_counter = 0
		self.lost_counter = 0 
		self.won_counter = 0
		
		
		#Define dictionaries and lists to be accessed from all timeframes
		self.atr_list =[]
		self.inds = dict()
		self.gap_dict=dict()
		self.rnghigh_dict = dict()
		self.rnglow_dict= dict()
		self.longstop_dict = dict()
		self.shortstop_dict = dict()
		self.target_long_dict = defaultdict(list)
		self.target_short_dict = defaultdict(list)
		self.size_dict = defaultdict(list)
		self.inorder_dict = defaultdict(list)	
		self.pos_dict = defaultdict(list)	

				
		#Create/Instantiate objects to access user input parameters
		modelp = UserInputs.model_params()
		indp = UserInputs.ind_params()
		datalist = UserInputs.datalist('hist')
		ibdatalist = UserInputs.datalist('ib')
		
		#Determine interval for timeframe looping
		if not modelp.get('live_status'):
			self.data_feed_count = len(self.datas)
			self.ticker_count = len(datalist)
			self.number_timeframes = int(self.data_feed_count/self.ticker_count) #Needs to be an integer
		elif modelp.get('live_status'):   
			self.data_feed_count = len(self.datas)
			self.ticker_count = len(ibdatalist)
			self.number_timeframes = int(self.data_feed_count/self.ticker_count) #Needs to be an integer
		
		#Determine # of base timeframe periods within trading day
		self.intraday_periods = int(390/modelp.get('timeframe0'))
		
		#************************INITITIALIZE INDICATORS*********************************************************
		#Initialize dictionary's
		for i, d in enumerate(self.datas):
			
			self.name_t0 = d._name[:-1]+'0'
			self.name_t1 = d._name[:-1]+'1'
			self.name_t2 = d._name[:-1]+'2'
			
			print('Datas included in Strategy: {}'.format(d._name))
				
			#Initialize dictionaries by appending 0 value
			self.target_long_dict[d._name].append(0)
			self.target_short_dict[d._name].append(0)
			self.size_dict[d._name].append(0)
			self.pos_dict[d._name].append(0)
			self.pos_dict[d._name].append(0) #Need to append twice to reference 2nd to last value
			self.inorder_dict[d._name].append(False)
			
			#For all indicators
			self.inds[d._name] = dict()
			
			
			#Determine current and prior day bars
			self.inds[d._name]['ohlc'] = btind.OHLC(d,
											period=indp.get('ohlc'),
											plot=False)
											
			self.inds[d._name]['prior_ohlc'] = btind.priorday(d,
											period=indp.get('ohlc'),
											plot=False)
			
			#AVERAGE TRUE RANGE INDICATOR
			self.inds[d._name]['atr'] = btind.ATR(d,
											period=indp.get('atrperiod'),
											plot=False)
											
			#Moving Average Indicators - FAST, SLOW, and CROSS
			self.inds[d._name]['sma1'] = btind.SMA(d,
													period=indp.get('sma1'),
													plot=True)
													
			self.inds[d._name]['sma2'] = btind.SMA(d,
													period=indp.get('sma2'),
													plot=True)										
			
			"""
			self.inds[d._name]['ema1'] = btind.EMA(d,
													period=indp.get('ema1'),
													plot=False)
														
			self.inds[d._name]['ema2'] = btind.EMA(d,
													period=indp.get('ema2'),
													plot=False)
												
			
			#This will double pre-next 												
			self.inds[d._name]['cross'] = btind.CrossOver(self.inds[d._name]['ema1'],
													self.inds[d._name]['ema2'],
													plot=False)
			
			#RSI
			self.inds[d._name]['rsi']= btind.RSI(d,
												safediv=True,
												plot=False)
					
			
			#Bollinger Band
			self.inds[d._name]['bollinger'] = btind.BollingerBands(d,
														period=indp.get('bollinger_period'),
														devfactor = indp.get('bollinger_dist'),
														plot=False)
			"""
			
			#Stochastics - just prints Slow %d line (not %K also which would be "StochasticFast")
			self.inds[d._name]['stochastic'] = btind.StochasticSlow(d,
														period=indp.get('stoch_per'),
														period_dfast= indp.get('stoch_fast'),
														safediv=True,
														plot=True)
			
			#ADX
			self.inds[d._name]['adx'] = btind.ADX(d,
												period=indp.get('adx'),
												plot=True)
			"""												
			#Pivots
			self.inds[d._name]['pivots'] = btind.pivotpoint.PivotPoint(d,
														plot=False)
			"""											
		
			#Highest and Lowest Values of Period Indicator
			self.inds[d._name]['highest'] = btind.Highest(d.high,
														period=indp.get('breakout_per'),
														plot=False)
																							
			self.inds[d._name]['lowest'] = btind.Lowest(d.low,
														period=indp.get('breakout_per'),
														plot=False)
			
			#Slope indicators
			self.inds[d._name]['slope']= btind.Slope(d,
													period=indp.get('slope_period'),
													plot=False)
			"""					
			self.inds[d._name]['slope_sma1'] = 	btind.Slope(self.inds[d._name]['sma1'],
													period=indp.get('slope_period'),
													plot=False)
													
			self.inds[d._name]['slope_of_slope_sma1'] = 	btind.Slope(self.inds[d._name]['slope_sma1'],
													period=indp.get('slope_period'),
													plot=False)
													
			self.inds[d._name]['slope_sma_width'] = btind.Slope(self.inds[d._name]['sma1']-self.inds[d._name]['sma2'],
													period=indp.get('slope_period'),
													plot=False)											
													
			self.inds[d._name]['slope_adx'] = 	btind.Slope(self.inds[d._name]['adx'],
													period=indp.get('slope_period'),
													plot=False)	
													
			self.inds[d._name]['slope_of_slope_adx'] = 	btind.Slope(self.inds[d._name]['slope_adx'],
													period=indp.get('slope_period'),
													plot=False)	
													
			self.inds[d._name]['slope_rsi'] = 	btind.Slope(self.inds[d._name]['rsi'],
													period=indp.get('slope_period'),
													plot=False,
													plotname = 'Slope_RSI')
													
			self.inds[d._name]['slope_of_slope_rsi'] = 	btind.Slope(self.inds[d._name]['slope_rsi'],
													period=indp.get('slope_period'),
													plot=False,
													plotname = 'Slope_of_Slope_RSI')									
													
			self.inds[d._name]['slope_ema1'] = 	btind.Slope(self.inds[d._name]['ema1'],
													period=indp.get('slope_period'),
													plot=False,
													plotname = 'Slope_EMA1')
			self.inds[d._name]['slope_ema2'] = 	btind.Slope(self.inds[d._name]['ema2'],
													period=indp.get('slope_period'),
													plot=False,
													plotname = 'Slope_EMA2')
			"""
															
			self.inds[d._name]['resistance'] = btind.Resistance(d,
															period=indp.get('lookback'),
															plot=True)	
			
			self.inds[d._name]['support'] = btind.Support(d,
															period=indp.get('lookback'),
															plot=True)
			
	
			if d._name == d._name[:-1]+'0' or d._name == d._name[:-1]+'1':
				self.inds[d._name]['avgvolume'] = btind.avgvolume(d,
															period=indp.get('avgvolume'),
															plot=False)
			
			if d._name == d._name[:-1]+'0':
				self.inds[d._name]['priorday'] = btind.priorday(d,
															period=indp.get('priorday'),
															plot=False)
																									
			if d._name == d._name[:-1]+'0' or d._name == d._name[:-1]+'1':
				self.inds[d._name]['vwap'] = btind.vwap(d,
															period=indp.get('vwap_lookback'),
															plot=True)
																								
			#Plot ADX and Stochastic on same subplot as stochastic							
			#self.inds[d._name]['adx'].plotinfo.plotmaster = self.inds[d._name]['stochastic']
		
		print('Start preloading data to meet minimum data requirements')	
		
	def prenext(self):
		#pre-loads all indicator data for all timeframes before strategy starts executing
		self.counter += 1
		#If you want to see full set of data
		"""
		for i, d in enumerate(self.datas):
			if d._name == d._name[:-1]+'0':
				print('{} {} prenext len {} - counter {} {} {} {} {} {}'.format(d._name,d.datetime.datetime().strftime('%Y-%m-%d %H:%M:%S'),len(self), self.counter,d.open[0],d.high[0],d.low[0],d.close[0],d.volume[0]))
		"""
		self.next()
				
	def nextstart(self):
		#There is a nextstart method which is called exactly once, to mark the switch from prenext to next. 
		self.prenext_done = True
		print('--------------------------------------------------')
		print('nextstart called with len {} - Minimal amout of data has been loaded to start backtesting'.format(len(self)))
		print('--------------------------------------------------')
		
		super(Strategy, self).nextstart()
		
	def next(self):

		#Start Timer
		if UserInputs.model_params().get('timer')=='on':
			self.t0 = datetime.utcnow() 		
		#print('Strategy: {}'.format(len(self)))
		
		#Create/Instantiate objects to access user input parameters
		modelp = UserInputs.model_params()
		indp = UserInputs.ind_params()
		
		#Convert backtrader float date to datetime so i can see time on printout and manipulate time variables
		dt = datetime.strftime(self.data.num2date(),'%Y-%m-%d')
		self.datadate=datetime.strftime(self.data.num2date(),'%H:%M:%S')
		self.hourmin = datetime.strftime(self.data.num2date(),'%H:%M')
		
		if UserInputs.model_params().get('timer')=='on':
			self.nextcounter += 1
		
		#Get available cash
		cash_avail = round(self.broker.getcash(),2)
		
#-------------------------------------------------------------------------------------------------------------------------	
		#SETUP TRADING ENTRY/EXIT TIMEFRAME 
		if self.maxtimeframe() >  self.max_ind_period():
			for i, d in enumerate(self.datas):  #Need to iterate over all datas so atr and sizing can be adjusted for multiple time frame user parameters
				self.counter += 1
				#print('{} {} next len {} - counter {} {} {} {} {} {}'.format(d._name,d.datetime.datetime().strftime('%Y-%m-%d %H:%M:%S'),len(self), self.counter,d.open[0],d.high[0],d.low[0],d.close[0],d.volume[0]))
			
				#Create naming convention so other timeframe data can be accessed via dictionary (i.e. support/resistance data)	
				#If other timeframes needed, just change data name within calculation to one of the names below
				self.name_t0 = d._name[:-1]+'0'
				self.name_t1 = d._name[:-1]+'1'
				self.name_t2 = d._name[:-1]+'2'
				
		
				#Determine OHLC for current bar and prior day for each timeframe
				self.open_t0 = round(self.inds.get(self.name_t0).get('ohlc').lines.open[0],3)
				self.high_t0 = round(self.inds.get(self.name_t0).get('ohlc').lines.high[0],3)
				self.low_t0 = round(self.inds.get(self.name_t0).get('ohlc').lines.low[0],3)
				self.close_t0 = round(self.inds.get(self.name_t0).get('ohlc').lines.close[0],3)
				self.volume_t0 = round(self.inds.get(self.name_t0).get('ohlc').lines.volume[0],3)
				self.pbar_open_t0_ = round(self.inds.get(self.name_t0).get('prior_ohlc').lines.prior_open[0],3)
				self.pbar_high_t0 =  round(self.inds.get(self.name_t0).get('prior_ohlc').lines.prior_high[0],3)
				self.pbar_low_t0 =  round(self.inds.get(self.name_t0).get('prior_ohlc').lines.prior_low[0],3)
				self.pbar_close_t0 =  round(self.inds.get(self.name_t0).get('prior_ohlc').lines.prior_close[0],3)
				self.pbar_volume_t0 =  round(self.inds.get(self.name_t0).get('prior_ohlc').lines.prior_volume[0],3)
				
				self.open_t1 = round(self.inds.get(self.name_t1).get('ohlc').lines.open[0],3)
				self.high_t1 = round(self.inds.get(self.name_t1).get('ohlc').lines.high[0],3)
				self.low_t1 = round(self.inds.get(self.name_t1).get('ohlc').lines.low[0],3)
				self.close_t1 = round(self.inds.get(self.name_t1).get('ohlc').lines.close[0],3)
				self.volume_t1 = round(self.inds.get(self.name_t1).get('ohlc').lines.volume[0],3)
				self.pbar_open_t1_ = round(self.inds.get(self.name_t1).get('prior_ohlc').lines.prior_open[0],3)
				self.pbar_high_t1 =  round(self.inds.get(self.name_t1).get('prior_ohlc').lines.prior_high[0],3)
				self.pbar_low_t1 =  round(self.inds.get(self.name_t1).get('prior_ohlc').lines.prior_low[0],3)
				self.pbar_close_t1 =  round(self.inds.get(self.name_t1).get('prior_ohlc').lines.prior_close[0],3)
				self.pbar_volume_t1 =  round(self.inds.get(self.name_t1).get('prior_ohlc').lines.prior_volume[0],3)
			
				self.open_t2 = round(self.inds.get(self.name_t2).get('ohlc').lines.open[0],3)
				self.high_t2 = round(self.inds.get(self.name_t2).get('ohlc').lines.high[0],3)
				self.low_t2 = round(self.inds.get(self.name_t2).get('ohlc').lines.low[0],3)
				self.close_t2 = round(self.inds.get(self.name_t2).get('ohlc').lines.close[0],3)
				self.volume_t2 = round(self.inds.get(self.name_t2).get('ohlc').lines.volume[0],3)
				self.pbar_open_t2_ = round(self.inds.get(self.name_t2).get('prior_ohlc').lines.prior_open[0],3)
				self.pbar_high_t2 =  round(self.inds.get(self.name_t2).get('prior_ohlc').lines.prior_high[0],3)
				self.pbar_low_t2 =  round(self.inds.get(self.name_t2).get('prior_ohlc').lines.prior_low[0],3)
				self.pbar_close_t2 =  round(self.inds.get(self.name_t2).get('prior_ohlc').lines.prior_close[0],3)
				self.pbar_volume_t2 =  round(self.inds.get(self.name_t2).get('prior_ohlc').lines.prior_volume[0],3)


				#Set support and resistance levels - MAKE SURE TO DEFINE CONDITION THAT PRICE IS ABOVE SUPPORT AND BELOW RESISTANCE
				self.resistance_t0 = round(self.inds.get(self.name_t0).get('resistance')[0],3)
				self.resistance_t1 = round(self.inds.get(self.name_t1).get('resistance')[0],3)
				self.resistance_t2 = round(self.inds.get(self.name_t2).get('resistance')[0],3)
				self.support_t0 = round(self.inds.get(self.name_t0).get('support')[0],3)
				self.support_t1 = round(self.inds.get(self.name_t1).get('support')[0],3)
				self.support_t2 = round(self.inds.get(self.name_t2).get('support')[0],3)
				
			
				#Calculate VWAP	
				self.vwap_t0 = round(self.inds.get(self.name_t0).get('vwap').lines.vwap[0],3)
				self.vwap_t1 = round(self.inds.get(self.name_t1).get('vwap').lines.vwap[0],3)
				#print(d._name, self.hourmin, d.close[0], d.volume[0],self.vwap_t0)
					
					
				#Calculate Average Volume (intraday over intraday time period)
				self.intraday_volume_t0 = round(self.inds.get(self.name_t0).get('avgvolume').lines.avgvolume_5min[0],3)
				self.intraday_volume_t1 = round(self.inds.get(self.name_t0).get('avgvolume').lines.avgvolume_15min[0],3)	
				#print(d._name,dt, self.hourmin, self.volume_t1, self.intraday_volume_t1)

				
				#Calculate Moving Averages
				self.sma1_t1 = round(self.inds.get(self.name_t1).get('sma1')[0],3)
				self.sma2_t1 = round(self.inds.get(self.name_t1).get('sma1')[0],3)
				self.sma1_t2 = round(self.inds.get(self.name_t2).get('sma2')[0],3)
				self.sma2_t2 = round(self.inds.get(self.name_t2).get('sma2')[0],3)
				#self.cross_t1 = self.inds.get(self.name_t1).get('cross')[0]
				
				#self.vixsma_t0 = round(self.inds.get('VIX0').get('sma1')[0],3) #holds just VIX0 sma data
				#self.spysma_t0 = round(self.inds.get('SPY0').get('sma1')[0],3) #holds just SPY0 sma data
				#self.ticksma_t0 = round(self.inds.get('TICK-NYSE0').get('sma1')[0],3)  #holds just TICK0 sma data
				#self.trinsma_t0 = round(self.inds.get('TRIN-NYSE0').get('sma1')[0],3)  #holds just TRIN0 sma data
									
				#self.ema1_t1 = round(self.inds.get(self.name_t1).get('ema1')[0],3)

					
				#Calculate slopes
				self.slope_t0 = round(self.inds.get(self.name_t0).get('slope')[0],3)
				self.slope_t1 = round(self.inds.get(self.name_t1).get('slope')[0],3)
				self.slope_t2 = round(self.inds.get(self.name_t2).get('slope')[0],3)
				
				
				#Determine if space between SMA1 and SMA2 is widening or contracting 
				#self.slope_sma_width_t1 = round(self.inds.get(self.name_t1).get('slope_sma_width')[0],3)
				
				#self.slope_sma1_t1 = round(self.inds.get(self.name_t1).get('slope_sma1')[0],3)
				#self.slope_of_slope_sma1_t1 = round(self.inds.get(self.name_t1).get('slope_of_slope_sma1')[0],3)
				
				#self.slope_adx_t1 = round(self.inds.get(self.name_t1).get('slope_adx')[0],3)
				#self.slope_of_slope_adx_t1 = round(self.inds.get(self.name_t1).get('slope_of_slope_adx')[0],3)
				
				#self.slope_rsi_t1 = round(self.inds.get(self.name_t1).get('slope_rsi')[0],3)
				#self.slope_of_slope_rsi_t1 = round(self.inds.get(self.name_t1).get('slope_of_slope_rsi')[0],3)
			
				#Calculate RSI
				#self.rsi_t1 = round(self.inds.get(self.name_t1).get('rsi')[0],2)
				
				#Calculate Bollinger Bands
				#self.boll_top_t1 = self.inds.get(self.name_t1).get('bollinger').lines.top[0]
				#self.boll_bot_t1 = self.inds.get(self.name_t1).get('bollinger').lines.bot[0]
				#self.boll_mid_t1 = self.inds.get(self.name_t1).get('bollinger').lines.mid[0]
				
				#Calculate Stochastic lines
				self.percK_t0 = round(self.inds.get(self.name_t0).get('stochastic').lines.percK[0],3)
				self.percK_t1 = round(self.inds.get(self.name_t1).get('stochastic').lines.percK[0],3)
				#self.percD_t1 = round(self.inds.get(self.name_t1).get('stochastic').lines.percD[0],3)
				
				#Calculate ADX - Average Directional Movement Index to measure trend strength
				self.adx_t1 = round(self.inds.get(self.name_t1).get('adx')[0],3)
				self.adx_t2 = round(self.inds.get(self.name_t2).get('adx')[0],3)
				
				#Calculate highest and lowest indicators
				self.highest_t1 = round(self.inds.get(self.name_t1).get('highest')[0],3) 
				self.lowest_t1 = round(self.inds.get(self.name_t1).get('lowest')[0],3) 
				
				"""
				#Determine open gap
				self.gap = self.open_gap(self.name_t0,d)	
					
				#Determine open 15 minute range
				self.range_high = self.open_range('high',self.name_t0)
				self.range_low = self.open_range('low',self.name_t0)
				"""
				
				#Calculate Candlestick Patterns
				if d._name == d._name[:-1]+'0': #For a single timeframe only (timeframe 1)
					self.bullish_three_line_strike_pattern_t0= self.bullish_three_line_strike(d)
					self.bearish_three_line_strike_pattern_t0= self.bearish_three_line_strike(d)
					self.bullish_engulfing_pattern_t0= self.bullish_engulfing(d,self.slope_t0)
					self.bearish_engulfing_pattern_t0= self.bearish_engulfing(d,self.slope_t0)
					
				if d._name == d._name[:-1]+'1': #For a single timeframe only (timeframe 1)
					#Determine if candlestick patterns exist
					self.bullish_engulfing_pattern_t1= self.bullish_engulfing(d,self.slope_t1)
					self.bearish_engulfing_pattern_t1= self.bearish_engulfing(d,self.slope_t1)	
					self.bullish_three_line_strike_pattern_t1= self.bullish_three_line_strike(d)
					self.bearish_three_line_strike_pattern_t1= self.bearish_three_line_strike(d)
					
				if d._name == d._name[:-1]+'1':  #THIS IS TIMEFRAME THAT IS BEING TRADED
					#Calc Average ATR
					self.avg_atr_t1 = round(self.inds.get(self.name_t1).get('atr')[0],3)
					
					#Calculate ATR Stop Loss for Long and Short Positions
					self.stop_atr = self.avg_atr_t1
					self.atr_target_dist = indp.get('atrdist')
					self.stop_dist = self.stop_atr*self.atr_target_dist
					
					self.long_stop = d.close[0] - self.stop_dist
					self.short_stop = d.close[0] + self.stop_dist
					
					#Calculate Sizing
					self.maxsize = modelp.get('total_dollars_risked')/d.close[0]
					self.atrsize = modelp.get('dollars_risked_per_trade')/self.stop_dist
					self.size = int(min(self.maxsize,self.atrsize))  #Needs to be integer for IB to process
					self.cost = self.size * d.close[0]  #Need intermidiary step to avoid method/float multiplication error
					#Ensure we have the cash to afford next position
					pos_cost = self.cost
					
					#Calculate exit prices for base trading timeframe
					self.short_exit_price = self.target_short_dict.get(self.name_t1)[-1]
					self.long_exit_price = self.target_long_dict.get(self.name_t1)[-1] 
				

					#Get Positions and toggle inorder status to false if stop-loss was executed (when position size becomes '0').  Used default dict to collect multiple values for each key in dictionary									
					self.pos = self.getposition(d).size
					self.pos_dict[d._name].append(self.pos)
					
					if (self.pos_dict.get(d._name)[-2]!=0 and self.pos_dict.get(d._name)[-1] == 0 and self.inorder_dict.get(d._name)[-1] == True):
						self.inorder_dict[d._name].append(False)
						self.size_dict[d._name].append(0)
				
				print(d._name, dt, self.hourmin, cash_avail, self.pos_dict.get(d._name)[-1], self.size_dict.get(d._name)[-1], self.inorder_dict[d._name], self.percK_t0, self.long_exit_price, self.close_t0, self.short_exit_price,self.hourmin=='14:50')
				
				#DEFINE OVERALL ENTRY LOGIC FOR LONG AND SHORT
				if (
					d._name == d._name[:-1]+'1'  #Trade timeframe 1 only
					and cash_avail > pos_cost
					and self.pos_dict.get(d._name)[-1] == 0
					and self.size_dict.get(d._name)[-1] == 0
					and self.inorder_dict.get(d._name)[-1] == False
					and self.prenext_done #Start trading after all prenext data loads
					and (self.hourmin>='08:55'and self.hourmin<='10:30')
					):  	
					#DEFINE LONG ENTRY LOGIC
					if(	#Timeframe 0 signals
						self.percK_t0 < 20
						#and self.slope_t0 < 0
						#and self.volume_t0 > self.intraday_volume_t0
						#Timeframe 1 signals
						#and (self.bullish_engulfing_pattern_t1 or self.bullish_three_line_strike_pattern_t1)
						#and self.slope_t1 < 0
						#self.close_t1>self.low_t1
						and self.percK_t1 < 20
						and self.volume_t1 > self.intraday_volume_t1
						#and self.low_t1 < self.support_t1
						#and self.pbar_close_t1> self.support_t1
						#and self.slope_t1 > 0
						#and self.sma1_t1 > self.sma2_t1
						#and self.adx_t1 > 20
						#and self.volume_t1 > self.intraday_volume_t1
						#Timeframe 2 signals						
						and self.slope_t2 > 0
						#and self.adx_t2 > 20
						#and self.sma1_t2 > self.sma2_t2
						#and self.adx_t2 < 40
					  ):
						
						#CREATE LONG ENTRY ORDER
						#if not (d._name[:-1]=='VIX' or d._name[:-1]=='TICK-NYSE' or d._name[:-1]=='TRIN-NYSE' or d._name[:-1]=='SPY'):
						if not modelp.get('live_status'):
							
							#Create Long Order
							long_name = '{} - Enter Long Trade'.format(d._name)
							self.long_ord = self.buy(data=d._name,
												size=self.size,
												exectype=bt.Order.Market,
												transmit=False,
												name = long_name)
							
							
							#Create size dictionary so same size can be referenced when you exit trade
							self.size_dict[d._name].append(self.size)
							#Track if currently in an order or not
							self.inorder_dict[d._name].append(True)
							#Set target prices to be referenced when you exit trade
							self.long_exit_price = round((d.open[0]+(modelp.get('dollars_risked_per_trade')*modelp.get('target'))/self.size),3)
							self.target_long_dict[d._name].append(self.long_exit_price)
							
							if modelp.get('TrailingStop'):
								#Create Trailing Long Stop Loss
								long_stop_name = '{} - Trailing StopLoss for Long Entry'.format(d._name)
								self.long_stop_ord = self.sell(data=d._name,
													size=self.size,
													exectype=bt.Order.StopTrail,
													price=self.long_stop,
													trailamount = self.stop_dist,
													transmit=True,
													parent=self.long_ord,
													name=long_stop_name)
													
							elif not modelp.get('TrailingStop'):
								#Create Fixed Long Stop Loss
								long_stop_name = '{} - Fixed StopLoss for Long Entry'.format(d._name)
								self.long_stop_ord = self.sell(data=d._name,
													size=self.size,
													exectype=bt.Order.Stop,
													price=self.long_stop,
													transmit=True,
													parent=self.long_ord,
													name=long_stop_name)
										
							self.longstop_dict[d._name] = self.long_stop_ord
	
						elif modelp.get('live_status') and self.data_live:
							#Create Long Entry Order
							long_name = '{} - Enter Long Trade'.format(d._name)
							self.long_ord = self.buy(data=d._name,
												size=self.size,
												exectype=bt.Order.Market,
												transmit=False,
												)

							self.inorder_dict[d._name].append(True)
							self.size_dict[d._name].append(self.size)
							self.long_exit_price = round((d.open[0]+(modelp.get('dollars_risked_per_trade')*modelp.get('target'))/self.size),3)
							self.target_long_dict[d._name].append(self.long_exit_price)
							
							if modelp.get('TrailingStop'):
								#Create Trailing Long Stop Loss
								long_stop_name = '{} - Trailing StopLoss for Long Entry'.format(d._name)
								self.long_stop_ord = self.sell(data=d._name,
													size=self.size,
													exectype=bt.Order.StopTrail,
													price=self.long_stop,
													trailamount = self.stop_dist,
													transmit=True,
													parent=self.long_ord,
													name=long_stop_name)
													
							elif not modelp.get('TrailingStop'):
								#Create Fixed Long Stop Loss
								long_stop_name = '{} - Fixed StopLoss for Long Entry'.format(d._name)
								self.long_stop_ord = self.sell(data=d._name,
													size=self.size,
													exectype=bt.Order.Stop,
													price=self.long_stop,
													transmit=True,
													parent=self.long_ord,
													name=long_stop_name)
														
							self.longstop_dict[d._name] = self.long_stop_ord
							self.bought = len(self)  #stores bar number when trade was entered
		
					#DEFINE SHORT ENTRY LOGIC
					elif (	#Timeframe 0 signals
							self.percK_t0 > 80
							#(self.high_t0 >= self.resistance_t0 and self.pbar_high_t0< self.resistance_t0))
							#and self.slope_t0 > 0
							#and self.volume_t0 > self.intraday_volume_t0
							#and self.volume_t0 < self.intraday_volume_t0
							#Timeframe 1 signals
							#and (self.bearish_engulfing_pattern_t1 or self.bearish_three_line_strike_pattern_t1)
							#and self.slope_t1 > 0
							#and self.close_t1<self.high_t1
							and self.percK_t1 > 80
							and self.volume_t1 > self.intraday_volume_t1
							#and self.high_t1 >= self.resistance_t1
							#and self.pbar_close_t1< self.resistance_t1
							#and self.volume_t1 > self.intraday_volume_t1
							#and self.slope_t1 < 0
							#and self.adx_t1 > 20
							#and self.adx_t1 < 40
							#and self.sma1_t1 < self.sma2_t1
							#Timeframe 2 signals						
							and self.slope_t2 < 0
							#and self.adx_t2 > 20
							#and self.sma1_t2 < self.sma2_t2
							#and self.adx_t2 < 40
						  ):
							
							
							#SHORT ENTRY ORDER
							#if not (d._name[:-1]=='VIX' or d._name[:-1]=='TICK-NYSE' or d._name[:-1]=='TRIN-NYSE' or d._name[:-1]=='SPY'):
								if not modelp.get('live_status'):
									#Create Short Entry Order
									short_name = '{} - Enter Short Trade'.format(d._name)
									self.short_ord = self.sell(data=d._name,
										 size=self.size,
										 exectype=bt.Order.Market,
										 transmit=False,
										 name=short_name,
										 )
									
									self.size_dict[d._name].append(-self.size)
									self.inorder_dict[d._name].append(True)
									self.short_exit_price = round((d.open[0]-(modelp.get('dollars_risked_per_trade')*modelp.get('target'))/self.size),3)
									self.target_short_dict[d._name].append(self.short_exit_price)
										
									if modelp.get('TrailingStop'):
										#Create Trailing Short Stop Loss	 
										short_stop_name = '{} - Trailing StopLoss for Short Entry'.format(d._name)
										self.short_stop_ord = self.buy(data=d._name,
											size=self.size,
											exectype=bt.Order.StopTrail,
											price=self.short_stop,
											trailamount = self.stop_dist,
											transmit=True,
											parent=self.short_ord,
											name = short_stop_name,
											)
									elif not modelp.get('TrailingStop'):
										#Create Fixed Short Stop Loss	 
										short_stop_name = '{} - Fixed StopLoss for Short Entry'.format(d._name)
										self.short_stop_ord = self.buy(data=d._name,
											size=self.size,
											exectype=bt.Order.Stop,
											price=self.short_stop,
											transmit=True,
											parent=self.short_ord,
											name = short_stop_name,
											)							
											
									self.shortstop_dict[d._name] = self.short_stop_ord #dictionary needed by cancel order to access all symbols instead of last symbol
									self.sold = len(self)  #stores bar number when trade was entered
									
								elif modelp.get('live_status') and self.data_live:
									#Create Short Entry Order
									short_name = '{} - Short Entry'.format(d._name)
									self.short_ord = self.sell(data=d._name,
														size=self.size,
														exectype=bt.Order.Market,
														transmit=False,
														)
												
									self.inorder_dict[d._name].append(True)
									self.size_dict[d._name].append(-self.size)
									self.short_exit_price = round((d.open[0]-(modelp.get('dollars_risked_per_trade')*modelp.get('target'))/self.size),3)
									self.target_short_dict[d._name].append(self.short_exit_price)
									
									if modelp.get('TrailingStop'):
										#Create Trailing Short Stop Loss	 
										short_stop_name = '{} - Trailing StopLoss for Short Entry'.format(d._name)
										self.short_stop_ord = self.buy(data=d._name,
											size=self.size,
											exectype=bt.Order.StopTrail,
											price=self.short_stop,
											trailamount = self.stop_dist,
											transmit=True,
											parent=self.short_ord,
											name = short_stop_name,
											)
									elif not modelp.get('TrailingStop'):
										#Create Fixed Short Stop Loss	 
										short_stop_name = '{} - Fixed StopLoss for Short Entry'.format(d._name)
										self.short_stop_ord = self.buy(data=d._name,
											size=self.size,
											exectype=bt.Order.Stop,
											price=self.short_stop,
											transmit=True,
											parent=self.short_ord,
											name = short_stop_name,
											)
									
									self.shortstop_dict[d._name] = self.short_stop_ord #dictionary needed by cancel order to access all symbols instead of last symbol
		
				#********************************EXIT LOGIC/ORDERS*********************************************
				else:
					#EXIT LOGIC FOR SHORTS
					if (d._name == d._name[:-1]+'1' 
						#and not (d._name[:-1]=='VIX' or d._name[:-1]=='TICK-NYSE' or d._name[:-1]=='TRIN-NYSE' or d._name[:-1]=='SPY')	
						and self.size_dict.get(d._name)[-1] < 0
						and self.inorder_dict.get(d._name)[-1] == True
						and self.prenext_done #Start trading after all prenext data loads 
						and (self.low_t1 <= self.short_exit_price or self.low_t1 <= self.vwap_t1 or self.hourmin=='14:45')  
						):		
	
						#SHORT EXIT ORDER - closes existing position and cancels outstanding stop-loss ord	
						self.exit_short_name = '{} - Exit Short Trade'.format(d._name)        
						self.exit_short = self.close(d._name,
													size=self.pos,
													name=self.exit_short_name)
	
						self.inorder_dict[d._name].append(False)
						short_stop_ord = self.shortstop_dict.get(d._name) #Need dictionary or else self.cancel_shortstop will only call the last symbol returned for short_stop_ord (not all symbols)
						self.cancel_shortstop = self.cancel(short_stop_ord) 
	
					#EXIT LOGIC FOR LONGS
					elif (d._name == d._name[:-1]+'1' 
						#and not (d._name[:-1]=='VIX' or d._name[:-1]=='TICK-NYSE' or d._name[:-1]=='TRIN-NYSE' or d._name[:-1]=='SPY')	
						and self.size_dict.get(d._name)[-1] > 0
						and self.inorder_dict.get(d._name)[-1] == True
						and self.prenext_done  #Start trading after all prenext loads (live and backtest modes) 
						and (self.high_t1 >= self.long_exit_price or self.high_t1 >= self.vwap_t1 or self.hourmin=='14:45')
						):
						
						#LONG EXIT ORDER - closes existing position and cancels outstanding stop-loss order
						self.exit_long_name = '{} - Exit Long Trade'.format(d._name)
						
						self.exit_long = self.close(d._name,
													size=self.pos,
													name=self.exit_long_name)
						
						self.inorder_dict[d._name].append(False)					
						long_stop_ord = self.longstop_dict.get(d._name)
						self.cancel_longstop = self.cancel(long_stop_ord)				
							
				#-------------------------------OUTPUT RESULTS--------------------------------------------
				#PRINT RESULTS
				if UserInputs.model_params().get('printlines') or modelp.get('live_status'):  #need to ensure all data has loaded for longest indicators
					out = [ 'Strategy: {}'.format(len(self)),
							'{}'.format(str(i)), 
							d._name,
							d.datetime.datetime().strftime('%Y-%m-%d %H:%M:%S'),
							d.open[0],
							d.high[0],
							d.low[0],
							d.close[0],
							d.volume[0],
							self.slope_t0,
							self.slope_t1,
							self.slope_t2,
							self.adx_t1,
							self.adx_t2,
							self.percK_t0,
							]					
					print(','.join(str(x) for x in out))
								
				#TIMER (to determine code speed)
				if UserInputs.model_params().get('timer')=='on':
					self.nextcounter=0
					t1 = datetime.utcnow() 
					diff = t1-self.t0
					print(d._name,self.hourmin,round(diff.total_seconds(),5))

	#-------------------------------Key Strategy Methods-------------------------------------------------------------------
	def maxtimeframe(self):
		#Determine max timeframe used by program, and return its length - ensures enough data has loaded to start calc.
		time1 = UserInputs.model_params().get('timeframe1on')
		time2 = UserInputs.model_params().get('timeframe2on')
		if time1 and time2:
			for x in range(2, len(self.datas)):
					d = self.datas[x]
					if len(d)>0:
						break
			return(len(d))
		if time1 and not time2:
			for x in range(1, len(self.datas)):
					d = self.datas[x]
					if len(d)>0:
						break
			return(len(d))
		else:
			for x in range(0, len(self.datas)):
					d = self.datas[x]
					if len(d)>0:
						break
			return(len(d))
			
	def max_ind_period(self):
		#Determine lookback period of longest indicator
		indicator_dict = UserInputs.ind_params()
		max_ind = max(indicator_dict.values()) 
		return max_ind
		

	def open_gap(self,ticker,mydata):
		#Determine opening gap from yesterday's close
		if self.hourmin == '08:30':
			gap = (mydata.open[0]-mydata.close[-1])/mydata.close[0]*100
			#Add self.gap to dictionary, with key name as stock name and value as self.gap, so we can access all stocks instead of just last one		
			self.gap_dict[ticker] = round(gap,3)
			
		#lookup up symbol name within gap dictionary you just created above and return gap as self.open_gap
		open_gap = self.gap_dict.get(ticker)
		return open_gap

	def open_range(self,direction,data_name):
		#Determines high and low opening range for day
		if self.hourmin == '08:50':
			rng_high = round(self.inds[data_name]['highest'][0],2)
			rng_low = round(self.inds[data_name]['lowest'][0],2)
			self.rnghigh_dict[data_name] = round(rng_high,3)
			self.rnglow_dict[data_name] = round(rng_low,3)
	
		if direction=='high':
			open_range =  self.rnghigh_dict.get(data_name)
		elif direction=='low':
			open_range =  self.rnglow_dict.get(data_name)
		return open_range
			
		
	def bullish_engulfing(self,mydata,slope):
		#Candlestick reversal pattern - long signal
		
		if (slope < 0
			and mydata.close[-1]< mydata.open[-1]
			and mydata.close[0] > mydata.open[0]
			and mydata.close[0] > mydata.open[-1]
			and mydata.open[0] < mydata.close[-1]
			):
			signal = True
		else:
			signal = False
		return signal
		
	def bearish_engulfing(self,mydata,slope):
		#Candlestick reversal pattern - short signal
		if (slope > 0
			and mydata.close[-1]> mydata.open[-1]
			and mydata.close[0] < mydata.open[0]
			and mydata.close[0] < mydata.open[-1]
			and mydata.open[0] > mydata.close[-1]
			):
			signal = True
		else:
			signal = False
		return signal
			
	def bullish_three_line_strike(self,mydata):
		#Candlestick pattern
		if (mydata.close[-2]< mydata.close[-3]
			and mydata.close[-1]< mydata.close[-2]
			and mydata.open[-2] < mydata.open[-3]
			and mydata.open[-1] < mydata.open[-2]
			and mydata.open[0] < mydata.open[-1]
			and mydata.open[0] <= mydata.close[-1]
			and mydata.close[0] > mydata.open[-3]
			):
			signal = True
		else:
			signal = False
		return signal

	def bearish_three_line_strike(self,mydata):
		#Candlestick pattern
		if (mydata.close[-2]> mydata.close[-3]
			and mydata.close[-1]> mydata.close[-2]
			and mydata.open[-2] > mydata.open[-3]
			and mydata.open[-1] > mydata.open[-2]
			and mydata.open[0] > mydata.open[-1]
			and mydata.open[0] >= mydata.close[-1]
			and mydata.close[0] < mydata.open[-3]
			):
			signal = True
		else:
			signal = False
		return signal
			
	data_live = False
	def notify_data(self, data, status):
		#To notify us when delayed backfilled data becomes live data during live trading
		print('*' * 5, 'DATA NOTIF:', data._getstatusname(status))
		if status == data.LIVE:
			self.data_live = True
			self.datastatus = 1	
						
	def log(self, txt, dt=None):
		''' Logging function for this strategy'''
		dt = self.datetime.date()
		mystring = '  {},{}'.format(dt.isoformat(), txt)
		return mystring
		
#********************************************RUN STRATEGY*******************************************************	
def runstrat():
	
	#Create an instance of cerebro
	cerebro = bt.Cerebro(exactbars=-1)  #exactbars True reduces memory usage significantly, but change to '-1' for partial memory savings (keeping indicators in memory) or 'false' to turn off completely if having trouble accessing bars beyond max indicator paramaters.  
	cerebro.broker.set_coc(False)    #cheat on close allows you to buy the close price of the current bar in which order was made.  cheat on open allows you to simulate a market order on the open price of the next bar
	cerebro.broker.set_coo(False)    #cheat on open allows you to buy the close price of the current bar in which order was made.  cheat on open allows you to simulate a market order on the open price of the next bar
	cerebro.broker.set_shortcash(True) #False means decrease cash available when you short, True means increase it
	
	#Add our strategy
	cerebro.addstrategy(Strategy)
	
	#Create/Instantiate objects to access parameters from UserInput Class
	#Can NOT create object referencing Strategy class as per backtrader
	modelp = UserInputs.model_params()
	indp = UserInputs.ind_params()
	datalist = UserInputs.datalist('hist')
	ibdatalist = UserInputs.datalist('ib')
	
	#Ensure stock lists have no duplicates - duplicates will BREAK program
	if len(datalist) != len(set(datalist)) or len(ibdatalist) != len(set(ibdatalist)):
		print("*****You have duplicates in stock list - FIX LIST*****")
	
	#GET THE DATA
	session_start = modelp.get('sessionstart')
	session_end = modelp.get('sessionend')	
	
	if modelp.get('live_status'):
		#*****  LIVE TRADING PARAMETERS*******
		store = bt.stores.IBStore(host='127.0.0.1',
								port=7497,
								clientId = 100)
		
		#get number of tickers
		indicator_dict = UserInputs.ind_params()
		max_ind = max(indicator_dict.values()) 
							
		#Data set for live trading IB
		for i,j in enumerate(ibdatalist):
			
			#Data for live IB trading
			data = store.getdata(dataname=j,
								timeframe=bt.TimeFrame.Minutes,
								tz = pytz.timezone('US/Central'),
								#historical = True, 
								backfill_start = True,  #true enables maximum allowable backfill in single request
								useRTH = True, 
								rtbar=True,
								fromdate = UserInputs.ib_backfill_start(UserInputs.max_ind()),#from date determined by today - max period paramater 
								sessionstart = session_start,
								sessionend = session_end,
								notifyall=True,
								qcheck=2.0,
								debug=True)
			
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
										
			cerebro.broker = store.getbroker()
			
		
	elif not modelp.get('live_status'):
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
									timeframe=bt.TimeFrame.Minutes,
									compression = modelp.get('timeframe0'),
									)
									
			data_BaseTimeframe = cerebro.adddata(data=data, 
												name="{}0".format(j),
												)
			data_BaseTimeframe.csv=True #Report this data to csv file (true) or not (false)	
			#data_BaseTimeframe.plotinfo.plot = False
			
			if modelp.get('timeframe1on'):
				#Apply resamplings			
				data_Timeframe1 = cerebro.resampledata(data,
										name="{}1".format(j),
										timeframe=bt.TimeFrame.Minutes,
										compression = modelp.get('timeframe1'),
										)
				data_Timeframe1.csv=False #Report this data to csv file (true) or not (false)				
				#data_Timeframe1.plotinfo.plot = False
				#data_Timeframe1.plotinfo.plotmaster = data_BaseTimeframe
	
			if modelp.get('timeframe2on'):
				data_Timeframe2 = cerebro.resampledata(data,
										name="{}2".format(j),
										timeframe=bt.TimeFrame.Minutes,
										compression = modelp.get('timeframe2'),
										)
				data_Timeframe2.csv=False #Report this data to csv file (true) or not (false)	
				#data_Timeframe2.plotinfo.plot = False
				#data_Timeframe2.plotinfo.plotmaster = data_BaseTimeframe
			
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
		
	# Add SQN to qualify the trades (rating to analyze quality of trading system: 2.5-3 good, above 3 excellent.  SquareRoot(NumberTrades) * Average(TradesProfit) / StdDev(TradesProfit).  Need at least 30 trades to be reliable
	cerebro.addanalyzer(bt.analyzers.SQN)
	
	#Adding my own custom analyzer - when creating analyzer, make sure to include file in _init_.py within backtrader.analyzer folder so it runs
	cerebro.addanalyzer(bt.analyzers.AcctStats)
	
	#Adding analyzer for drawdown
	cerebro.addanalyzer(bt.analyzers.DrawDown)
	
	# Add TradeAnalyzer to output trade statistics - THESE ARE THE TRADE NOTIFICATIONS THAT ARE PRINTED WHEN PROGRAM IS RUN
	cerebro.addanalyzer(bt.analyzers.Transactions)
	
	#Adds just buy/sell observer to chart (assuming stdstats is set to false)
	cerebro.addobservermulti(bt.observers.BuySell)
	
	#Adds custom observers
	cerebro.addobserver(bt.observers.AcctValue) #reports trade statistics in command prompt at end of program run
	cerebro.addobserver(bt.observers.OrderObserver) #reports trades in command prompt when program is run
	
	#Generate output report in csv format
	if UserInputs.model_params().get('writer')=='on':
		current_time = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.csv") 
		csv_file = 'C:/Program Files (x86)/Python36-32/Lib/site-packages/backtrader/out/'
		csv_file += 'Strategy'
		csv_file += current_time
		cerebro.addwriter(bt.WriterFile, csv = True, out=csv_file)
		print("Writer CSV Report On")

	
	#RUN EVERYTHING
	results = cerebro.run(stdstats=False, #enables some additional chart information like profit/loss, buy/sell, etc, but tends to clutter chart
						runonce=True,
						)
	

	if not modelp.get('live_status'):
	
		#Print analyzers
		for alyzer in results[0].analyzers:
			alyzer.print()
		
		#Calculate Program end time
		end_time = datetime.now().time()
		print('Program end at {}'.format(end_time))
		
		#PLOT TRADING RESULTS - **Ensure trading session ends at 2:55 (if it ends at 3, some tickers only go up to 2:55, creating data length mismatches between tickers that doesn't allow plotting)
	
		#Chart each ticker and timeframe in separate plots
		for i in range (len(results[0].datas)):
			for j, d in enumerate(results[0].datas):
				d.plotinfo.plot = i ==j
			cerebro.plot(fmt_x_ticks = '%Y-%b-%d %H:%M', fmt_x_data = '%Y-%b-%d %H:%M', volume = True, style='candlestick',barup='olive', bardown='lightpink',volup = 'lightgreen',voldown='crimson')
		
		"""
		#Chart only 15 min timeframe for each ticker
		for i in range (1,len(results[0].datas),3):   #Assumes 3 timeframes used
			for j, d in enumerate(results[0].datas):
				d.plotinfo.plot = i ==j	
			cerebro.plot(style='candlestick',barup='olive', bardown='lightpink',volup = 'lightgreen',voldown='crimson')
		"""
		
		
if __name__ == '__main__':
	
	#Run strategy
	runstrat()
