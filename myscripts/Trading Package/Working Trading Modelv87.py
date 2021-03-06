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
from collections import defaultdict


class UserInputs():
	#This class is designed so runstrat() method can pick up these parameters (can use self.p.whatever to pass parameters for some reason)
	def __init__():
		pass
		
	def datalist(data_req):
		#Create list of tickers to load data for.  Market Breadth indicators need to be removed from initiliazation and next() so they are not traded
		#TICK is # of NYSE stocks trading on an uptick vs # of stocks trading on downtick.  About 2800 stocks total, usually oscillates between -500 to +500.  Readings above 1000 or below -1000 considered extreme.  #TRIN is ratio of (# of Advance/Decliners)/(Advance/Decline Volume).  Below 1 is strong rally, Above 1 is strong decline.#VIX is 30 day expectation of volatility for S&P 500 options.  VIX spikes correlate to market declines because more people buying options to protect themselves from declines
		
		#datalist = ['VIX','TICK-NYSE','TRIN-NYSE','SPY','XLU','IAU']
		#datalist = ['SPY','XLU','TICK-NYSE']
		#datalist = ['SPY','XHB','XLU','MCD','XLK','XLV','XRT','TICK-NYSE',]
		#datalist = ['IAU','TIP','AGG','EMB','VNQ','XLU','SPY','XOM','LQD','EWZ','MCD','DBA','EWH','EWW','HYG','XLV','XRT','XLK','SHY','XHB']
		#ibdatalist = ['SPY','XLU','XHB',]
		#ibdatalist = ['SPY-STK-SMART-USD','XLU-STK-SMART-USD','XHB-STK-SMART-USD',]
		ibdatalist = ['EUR.USD','GBP.USD']  #Make sure not to include comma after last ticker or program won't read in live trading
		
		if data_req == 'ib':
			return ibdatalist
		elif data_req == 'hist':
			return datalist

	def model_params():
		params = dict(
			live_status = True,  #Flip between live trading (True) and backtesting (False)
			start_date = date(2016,1,2), #Dates for backtesting
			end_date = date(2016,6,30),
			timeframe0 = 5, #MINUTES
			timeframe1 = 15, #MINUTES
			timeframe2 = 60, #MINUTES
			timeframe1on = True,
			timeframe2on = True,
			sessionstart = time(8,30),
			sessionend = time(23,59),
			start_cash=100000,
			)
		return params

	def ib_backfill_start(maxind):
		#sometimes IB backfill does not collect enough data for live trading - this creates new start date for backfill to guarantee enough data collected for longest indicator lookback period
		today_date = datetime.now()
		backfill_days = -(maxind)
		ib_start_date = today_date + timedelta(days=backfill_days)
		return ib_start_date
		
		
class Strategy(bt.Strategy):
	params = dict(
			printlines = False,
			TrailingStop = False,
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
			sma1 = 10,
			sma2 = 20,
			ema1= 8,
			ema2= 20,
			obv=5,
			atrperiod= 5,
			atrdist= 2,   
			slope_period=5,
			breakout_per=5, 
			avg_per=5,
			adx = 14,
			stoch_per=5,
			stoch_fast=3,
			bollinger_period=5,
			bollinger_dist=2,
			lookback=10,
			)
		
	
	def __init__(self):
			
		#Set program start time
		start_time=datetime.now().time()
		print('Program start at {}'.format(start_time))
		print('Program time period: {} to {}'.format( UserInputs.model_params().get('start_date'),
																	UserInputs.model_params().get('end_date')))
		print('Program Parameters: {}'.format(self.params._getitems()))
		
		#initialize counters for prenext/next
		self.nextcounter = 0	
		self.counter = 0	
		self.prenext_done = False
		self.target_short_price = 0
		self.target_long_price = 0
		self.pos = 0
		self.cash_avail = 0
		self.data_live = False

		#Define dictionaries and lists to be accessed from all timeframes
		self.inds = dict()
		self.rnghigh_dict = dict()
		self.rnglow_dict= dict()
		self.longstop_dict = dict()
		self.shortstop_dict = dict()
		self.target_long_dict = defaultdict(list)
		self.target_short_dict = defaultdict(list)
		self.size_dict = defaultdict(list)
		self.inorder_dict = defaultdict(list)
	

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
			
			print("Datas in Strategy {}".format(d._name))
			
			self.name_t0 = d._name[:-1]+'0'
			self.name_t1 = d._name[:-1]+'1'
			self.name_t2 = d._name[:-1]+'2'
			
			#Initialize dictionaries by appending 0 value
			self.target_long_dict[d._name].append(0)
			self.target_short_dict[d._name].append(0)
			self.size_dict[d._name].append(0)  #Need to append twice to reference 2nd to last value
			self.size_dict[d._name].append(0) 
			self.inorder_dict[d._name].append(False)
			
			#Get available cash
			self.cash_avail = self.broker.getcash()
			
			
			#For all indicators
			self.inds[d._name] = dict()
			
	
			#Calculate VWAP																			
			self.inds[d._name]['vwap'] = btind.vwap(d,
													plot=True)
													
			#Determine on balance volume
			self.inds[d._name]['obv'] = btind.obv(d,
											period=self.p.obv,
											plot=True)
			
			#Determine current ohlcv bars
			self.inds[d._name]['ohlc'] = btind.ohlc(d,
											period=self.p.ohlc,
											plot=False)
	
			#Determine same bar, prior day
			self.inds[d._name]['priorday'] = btind.priorday(d,
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
			"""
			#RSI
			self.inds[d._name]['rsi']= btind.RSI(d,
												safediv=True,
												plot=False)
					
			
			#Bollinger Band
			self.inds[d._name]['bollinger'] = btind.BollingerBands(d,
														period=self.p.bollinger_period,
														devfactor = self.p.bollinger_dist'),
														plot=False)
	
			"""
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
			"""												
			#Pivots
			self.inds[d._name]['pivots'] = btind.pivotpoint.PivotPoint(d,
														plot=False)
			"""											
		
			#Highest and Lowest Values of Period Indicator
			self.inds[d._name]['highest'] = btind.Highest(d.high,
														period=self.p.breakout_per,
														plot=False)
																							
			self.inds[d._name]['lowest'] = btind.Lowest(d.low,
														period=self.p.breakout_per,
														plot=False)
			
			#Slope indicators
			self.inds[d._name]['slope']= btind.Slope(d.close,
													period=self.p.slope_period,
													plot=False)
													
			self.inds[d._name]['slope_obv'] = 	btind.Slope(self.inds[d._name]['obv'],
												period=self.p.slope_period,
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
													
			
			"""										
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
			"""
													
			self.inds[d._name]['resistance'] = btind.Resistance(d,
															period=self.p.lookback,
															min_touches = self.p.min_touches,
															tolerance_perc = self.p.tolerance_perc,
															bounce_perc = self.p.bounce_perc,
															plot=True)	
			
			self.inds[d._name]['support'] = btind.Support(d,
															period=self.p.lookback,
															min_touches = self.p.min_touches,
															tolerance_perc = self.p.tolerance_perc,
															bounce_perc = self.p.bounce_perc,
															plot=True)
			
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
				
	def nextstart(self):
		#There is a nextstart method which is called exactly once, to mark the switch from prenext to next. 
		self.prenext_done = True
		print('--------------------------------------------------')
		print('nextstart called with len {} - Minimal amout of data has been loaded to start backtesting'.format(len(self)))
		print('--------------------------------------------------')

		#print('Strategy: {}'.format(len(self)))
		
		super(Strategy, self).nextstart()
		
	def next(self):
			
		#Convert backtrader float date to datetime so i can see time on printout and manipulate time variables
		self.hourmin = datetime.strftime(self.data.num2date(),'%H:%M')
		self.dt = self.datetime.date()

		
		#SETUP TRADING ENTRY/EXIT TIMEFRAME 
		for i, d in enumerate(self.datas):  #Need to iterate over all datas so atr and sizing can be adjusted for multiple time frame user parameters
			#print('{} {} next len {} - counter {} {} {} {} {} {}'.format(d._name,d.datetime.datetime().strftime('%Y-%m-%d %H:%M:%S'),len(self),d.open[0],d.high[0],d.low[0],d.close[0],d.volume[0]))
			
			self.name_t0 = d._name[:-1]+'0'
			self.name_t1 = d._name[:-1]+'1'
			self.name_t2 = d._name[:-1]+'2'
			
			self.obv_t0 = self.inds.get(self.name_t0).get('obv')[0]
			self.slope_obv_t0 = self.inds.get(self.name_t0).get('slope_obv')[0]
			self.slope_of_slope_obv_t0 = self.inds.get(self.name_t0).get('slope_of_slope_obv')[0]
			#print(d._name, self.hourmin,d.volume[0],self.obv_t0,self.slope_obv_t0)
			
			#Determine current ohlcv prices
			self.open_t0 = self.inds.get(self.name_t0).get('ohlc').lines.o[0]
			self.high_t0 = self.inds.get(self.name_t0).get('ohlc').lines.h[0]
			self.low_t0 = self.inds.get(self.name_t0).get('ohlc').lines.l[0]
			self.close_t0 = self.inds.get(self.name_t0).get('ohlc').lines.c[0]
			self.volume_t0 = self.inds.get(self.name_t0).get('ohlc').lines.v[0]
			
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
			self.pday_open_t0 = self.inds.get(self.name_t0).get('priorday').lines.prior_open[0]
			self.pday_high_t0 =  self.inds.get(self.name_t0).get('priorday').lines.prior_high[0]
			self.pday_low_t0 =  self.inds.get(self.name_t0).get('priorday').lines.prior_low[0]
			self.pday_close_t0 =  self.inds.get(self.name_t0).get('priorday').lines.prior_close[0]
			self.pday_volume_t0 =  self.inds.get(self.name_t0).get('priorday').lines.prior_volume[0]
			#print(d._name,self.dt, self.hourmin, self.pday_open_t0,self.pday_high_t0,self.pday_low_t0,self.pday_close_t0,self.pday_volume_t0,)

			
			#Set support and resistance levels - MAKE SURE TO DEFINE CONDITION THAT PRICE IS ABOVE SUPPORT AND BELOW RESISTANCE
			self.resistance_t0 = self.inds.get(self.name_t0).get('resistance')[0]
			self.resistance_t1 = self.inds.get(self.name_t1).get('resistance')[0]
			self.resistance_t2 = self.inds.get(self.name_t2).get('resistance')[0]
			
			self.support_t0 = self.inds.get(self.name_t0).get('support')[0]
			self.support_t1 = self.inds.get(self.name_t1).get('support')[0]
			self.support_t2 = self.inds.get(self.name_t2).get('support')[0]
		
			#Calculate VWAP	
			self.vwap_t0 = self.inds.get(self.name_t0).get('vwap').lines.vwap[0]
			self.vwap_t1 = self.inds.get(self.name_t1).get('vwap').lines.vwap[0]

			#Calculate Moving Averages
			#self.sma1_t0 = self.inds.get(self.name_t0).get('sma1')[0]
			#self.sma1_t1 = self.inds.get(self.name_t1).get('sma1')[0]
			#self.sma2_t1 = self.inds.get(self.name_t1).get('sma1')[0]
			#self.sma1_t2 = self.inds.get(self.name_t2).get('sma2')[0]
			#self.sma2_t2 = self.inds.get(self.name_t2).get('sma2')[0]
			self.ema1_t0 = self.inds.get(self.name_t0).get('ema1')[0]
			self.ema1_t1 = self.inds.get(self.name_t1).get('ema1')[0]
			#self.cross_t0 = self.inds.get(self.name_t0).get('cross')[0]

			#Calculate Market Indicators
			if d._name == 'TICK-NYSE0':
				self.tick_close = d.close[0]
				
			#self.vixsma_t0 = round(self.inds.get('VIX0').get('sma1')[0],3) #holds just VIX0 sma data
			#self.spysma_t0 = round(self.inds.get('SPY0').get('sma1')[0],3) #holds just SPY0 sma data
			#self.ticksma_t0 = round(self.inds.get('TICK-NYSE0').get('sma1')[0],3)  #holds just TICK0 sma data
			#self.trinsma_t0 = round(self.inds.get('TRIN-NYSE0').get('sma1')[0],3)  #holds just TRIN0 sma data
								
			#Calculate slopes
			self.slope_t0 = self.inds.get(self.name_t0).get('slope')[0]
			self.slope_t1 = self.inds.get(self.name_t1).get('slope')[0]
			self.slope_t2 = self.inds.get(self.name_t2).get('slope')[0]
			
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
			#self.boll_top_t1 = self.inds.get(self.name_t1).get('bollinger').lines.top[0]
			#self.boll_bot_t1 = self.inds.get(self.name_t1).get('bollinger').lines.bot[0]
			#self.boll_mid_t1 = self.inds.get(self.name_t1).get('bollinger').lines.mid[0]
			
			#Calculate Stochastic lines
			#self.percK_t0 = round(self.inds.get(self.name_t0).get('stochastic').lines.percK[0],3)
			#self.percK_t1 = round(self.inds.get(self.name_t1).get('stochastic').lines.percK[0],3)
			#self.percD_t1 = round(self.inds.get(self.name_t1).get('stochastic').lines.percD[0],3)
			
			#Calculate ADX - Average Directional Movement Index to measure trend strength
			#self.adx_t1 = round(self.inds.get(self.name_t1).get('adx')[0],3)
			#self.adx_t2 = round(self.inds.get(self.name_t2).get('adx')[0],3)
			
			#Calculate highest and lowest indicators
			#self.highest_t1 = round(self.inds.get(self.name_t1).get('highest')[0],3) 
			#self.lowest_t1 = round(self.inds.get(self.name_t1).get('lowest')[0],3) 
			
			#Determine open gap
			#self.gap = round(self.inds.get(self.name_t0).get('gap').lines.gap[0],3) 
			
			#Determine open 15 minute range
			#self.rng_high = round(self.inds[self.name_t0]['gap'].lines.rng_high[0],2)
			#self.rng_low = round(self.inds[self.name_t0]['gap'].lines.rng_low[0],2)						
			#print(self.dt, self.hourmin, d.high[0], d.low[0], self.gap,self.rng_high,self.rng_low)
			
			"""
			#Calculate Candlestick Patterns - if returns 1, bullish, -1 is bearish
			self.engulfing_pattern_t0= self.inds.get(self.name_t0).get('engulfing')[0]
			self.hammer_t0= self.inds.get(self.name_t0).get('hammer')[0]
			self.three_line_strike_t0= self.inds.get(self.name_t0).get('three_line_strike')[0]
			#print(d._name,self.dt,self.hourmin,self.hammer_t0)
			"""
			
			#CALCULATE ORDER LOGIC FOR STOPS, SIZING, AND TARGETS
			#ATR BASED STOP
			self.long_stop = self.inds.get(self.name_t0).get('atr_stop').lines.long_stop[0]
			self.short_stop = self.inds.get(self.name_t0).get('atr_stop').lines.short_stop[0]
			
			#Calculate Sizing
			#self.size = self.inds.get(self.name_t0).get('atr_stop').lines.size[0]
			self.size = 100 #***************************************************************************************************
			#print(d._name, self.dt, self.hourmin, self.long_stop,self.short_stop,self.size)

			#Calculate Target Prices
			self.target_short = self.target_short_dict.get(d._name)[-1]
			self.target_long = self.target_long_dict.get(d._name)[-1]

			#Get Positions and toggle inorder status to false if stop-loss was executed (when position size becomes '0').  Used default dict to collect multiple values for each key in dictionary									
			if not self.modelp.get('live_status'):
				self.pos = self.getposition(d).size
			else:
				self.pos = self.broker.getvalue()
				print(d._name,self.dt,self.hourmin,d.open[0],d.high[0],d.low[0],d.close[0],d.volume[0])
			
			if (self.inorder_dict.get(d._name)[-1] == True and self.pos==0):
				self.inorder_dict[d._name].append(False)
				self.size_dict[d._name].append(0)
			#print(d._name, self.dt, self.hourmin, d.high[0],self.resistance_t0,d.low[0],self.support_t0)
			print(self.cash_avail,self.size_dict.get(d._name),self.inorder_dict.get(d._name),self.prenext_done)
			
			
			#DEFINE OVERALL ENTRY LOGIC FOR LONG AND SHORT
			if (
				d._name == d._name[:-1]+'0'  #Trade timeframe 1 only
				and self.cash_avail > self.p.total_dollars_risked
				and self.size_dict.get(d._name)[-1] == 0
				and self.inorder_dict.get(d._name)[-1] == False
				and self.prenext_done #Start trading after all prenext data loads
				#and (self.hourmin>='09:20'and self.hourmin<='15:00')
				):
				
				#DEFINE LONG ENTRY LOGIC
				if(	#Timeframe 0 signals
					d.close[0]>d.close[-1]
					#d.close[0] > self.resistance_t0
					#and d.close[-1] < self.resistance_t0
					#d.close[0] >= self.pday_high_t0
					#and d.close[-1] < self.pday_high_t0 
					#and d.close[0] > self.vwap_t0
					#and self.tick_close > 0
					#and self.tick_close < 500
					#and self.slope_obv_t0 > 0
					#Timeframe 1 signals
					#and self.slope_t1 > 0
					#Timeframe 2 signals						
					#and self.slope_t2 > 0
					):
				
					#print('**************LONG SIGNAL-FIRST**************')

					if not d._name[:-1]=='TICK-NYSE':
					#if not (d._name[:-1]=='VIX' or d._name[:-1]=='TICK-NYSE' or d._name[:-1]=='TRIN-NYSE' or d._name[:-1]=='SPY'):
							
						#CREATE LONG ORDER
						if not self.modelp.get('live_status'):
							
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
							self.target_long_price = (d.open[0]+(self.p.dollars_risked_per_trade*self.p.target)/self.size)
							self.target_long_dict[d._name].append(self.target_long_price)
							
							if self.p.TrailingStop:
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
													
							elif not self.p.TrailingStop:
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

						elif self.modelp.get('live_status') and self.data_live:
							
							#print('**************LONG SIGNAL**************')
							#Create Long Entry Order
							long_name = '{} - Enter Long Trade'.format(d._name)
							self.long_ord = self.buy(data=d._name,
												size=self.size,
												exectype=bt.Order.Market,
												transmit=False,
												)

							self.inorder_dict[d._name].append(True)
							self.size_dict[d._name].append(self.size)
							self.target_long_price = (d.open[0]+(self.p.dollars_risked_per_trade*self.p.target)/self.size)
							self.target_long_dict[d._name].append(self.target_long_price)
							
							if self.p.TrailingStop:
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
													
							elif not self.p.TrailingStop:
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
							
				#DEFINE SHORT ENTRY LOGIC
				elif (	#Timeframe 0 signals
						#self.percK_t0 > 90
						#d.close[0] < self.support_t0
						#and d.close[-1] > self.support_t0
						d.close[0]<d.close[-1]
						#d.close[0] <= self.pday_low_t0
						#and d.close[-1] > self.pday_low_t0
						#and self.slope_obv_t0 < 0
						#and self.tick_close < 0
						#and self.tick_close > -500
						#and d.close[0] < self.vwap_t0
						#Timeframe 1 signals
						#and self.slope_t1 < 0
						#Timeframe 2 signals						
						#and self.slope_t2 < 0
					  ):
						
						#print('**************SHORT SIGNAL - FIRST**************')
						
						#SHORT ENTRY ORDER
						if not d._name[:-1]=='TICK-NYSE':
						#if not (d._name[:-1]=='VIX' or d._name[:-1]=='TICK-NYSE' or d._name[:-1]=='TRIN-NYSE' or d._name[:-1]=='SPY'):
							if not self.modelp.get('live_status'):
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
								self.target_short_price =(d.open[0]-(self.p.dollars_risked_per_trade*self.p.target)/self.size)
								self.target_short_dict[d._name].append(self.target_short_price)
									
								if self.p.TrailingStop:
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
								elif not self.p.TrailingStop:
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

							elif self.modelp.get('live_status') and self.data_live:
								
								#print('**************SHORT SIGNAL**************')
								#Create Short Entry Order
								short_name = '{} - Short Entry'.format(d._name)
								self.short_ord = self.sell(data=d._name,
													size=self.size,
													exectype=bt.Order.Market,
													transmit=False,
													)

								self.inorder_dict[d._name].append(True)
								self.size_dict[d._name].append(-self.size)
								self.target_short_price = (d.open[0]-(self.p.dollars_risked_per_trade*self.p.target)/self.size)
								self.target_short_dict[d._name].append(self.target_short_price)
								
								if self.p.TrailingStop:
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
								elif not self.p.TrailingStop:
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
				if (d._name == d._name[:-1]+'0' 
					#and not (d._name[:-1]=='VIX' or d._name[:-1]=='TICK-NYSE' or d._name[:-1]=='TRIN-NYSE' or d._name[:-1]=='SPY')	
					and self.size_dict.get(d._name)[-1] < 0
					and self.inorder_dict.get(d._name)[-1] == True
					and self.prenext_done #Start trading after all prenext data loads 
					#and (d.low[0] <= self.target_short)
					and (d.low[0] <= self.target_short or self.tick_close>1000 or self.hourmin=='14:50')  
					):		

					#SHORT EXIT ORDER - closes existing position and cancels outstanding stop-loss ord	
					self.exit_short_name = '{} - Exit Short Trade'.format(d._name)        
					self.exit_short = self.close(d._name,
												size= self.size_dict.get(d._name)[-1],
												name=self.exit_short_name)

					self.inorder_dict[d._name].append(False)
					self.size_dict[d._name].append(0)
					short_stop_ord = self.shortstop_dict.get(d._name) #Need dictionary or else self.cancel_shortstop will only call the last symbol returned for short_stop_ord (not all symbols)
					self.cancel_shortstop = self.cancel(short_stop_ord) 

				#EXIT LOGIC FOR LONGS
				elif (d._name == d._name[:-1]+'0' 
					#and not (d._name[:-1]=='VIX' or d._name[:-1]=='TICK-NYSE' or d._name[:-1]=='TRIN-NYSE' or d._name[:-1]=='SPY')	
					and self.size_dict.get(d._name)[-1] > 0
					and self.inorder_dict.get(d._name)[-1] == True
					and self.prenext_done  #Start trading after all prenext loads (live and backtest modes) 
					#and (d.high[0] >= self.target_long)
					and (d.high[0] >= self.target_long or self.tick_close<-1000 or self.hourmin=='14:50')
					):
					
					#LONG EXIT ORDER - closes existing position and cancels outstanding stop-loss order
					self.exit_long_name = '{} - Exit Long Trade'.format(d._name)
					
					self.exit_long = self.close(d._name,
												size=self.size_dict.get(d._name)[-1],
												name=self.exit_long_name)
					
					self.inorder_dict[d._name].append(False)
					self.size_dict[d._name].append(0)				
					long_stop_ord = self.longstop_dict.get(d._name)
					self.cancel_longstop = self.cancel(long_stop_ord)				
						
	
	def notify_data(self, data, status):
		#To notify us when delayed backfilled data becomes live data during live trading
		print('*' * 5, 'DATA NOTIF:', data._getstatusname(status))
		if status == self.data.LIVE:
			self.data_live = True
			
	def notify_data(self, data, status, *args, **kwargs):
		print('*' * 5, 'DATA NOTIF:', data._getstatusname(status), *args)
		if status == data.LIVE:
			self.data_live = True

	def notify_order(self, order):
		if order.status == order.Completed:
			buysell = 'BUY ' if order.isbuy() else 'SELL'
			txt = '{} {}@{}'.format(buysell, order.executed.size,
									order.executed.price)
			print(txt)	
			
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
							
			data_BaseTimeframe = cerebro.adddata(data=data, 
												name="{}0".format(j),
												)
			
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
		
	
	
	
	elif modelp.get('live_status'):
		#*****  LIVE TRADING PARAMETERS*******
		store = bt.stores.IBStore(host='127.0.0.1',
								port=7497,
								clientId = 100)
		
		"""
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
													
		
		
		"""
		
		forexdatalist = ['EUR.USD','GBP.USD'] #MAKE SURE NO COMMAS AFTER LAST TICKER
		for i,j in enumerate(forexdatalist):
			#Data for live IB trading
			data = store.getdata(dataname=j,
								sectype='CASH',
								exchange='IDEALPRO',
								timeframe=bt.TimeFrame.Minutes,
								tz = pytz.timezone('US/Central'),
								sessionstart = session_start,
								sessionend = session_end,
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
													
		
		"""		
		#ADD MARKET BREADTH DATA LIKE TICK
		indexdatalist = ['TICK-NYSE']  #MAKE SURE NO COMMAS AFTER LAST TICKER
		for i,j in enumerate(indexdatalist):
			tickdata = store.getdata(dataname=j,
									sectype='IND',
									exchange='NYSE',
									currency='USD',
									timeframe=bt.TimeFrame.Minutes,
									tz = pytz.timezone('US/Central'),
									sessionstart = session_start,
									sessionend = session_end,
									)
									
			cerebro.resampledata(tickdata, name="{}0".format(j),timeframe=bt.TimeFrame.Minutes, compression=modelp.get('timeframe0'))
			
			
			#Apply resamplings
			if modelp.get('timeframe1on'):
				tickdata_Timeframe1 = cerebro.resampledata(tickdata,name="{}1".format(j),
															timeframe=bt.TimeFrame.Minutes,
															compression = modelp.get('timeframe1'))
				
			if modelp.get('timeframe2on'):
				tickdata_Timeframe2 = cerebro.resampledata(tickdata,name="{}2".format(j),
															timeframe=bt.TimeFrame.Minutes,
															compression = modelp.get('timeframe2'))
		"""
		
		
		
		cerebro.broker = store.getbroker()  #*****Critical line of code to access broker so you can trade*****
	
	
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
						runonce=False,
						
						)
	
	if not modelp.get('live_status'):
	
		#Print analyzers
		for alyzer in results[0].analyzers:
			alyzer.print()
		
		#Calculate Program end time
		end_time = datetime.now().time()
		print('Program end at {}'.format(end_time))
		
		#PLOT TRADING RESULTS - **Ensure trading session ends at 2:55 (if it ends at 3, some tickers only go up to 2:55, creating data length mismatches between tickers that doesn't allow plotting)
		plot_end = modelp.get('end_date')-timedelta(hours=8, minutes=0, seconds=.01) #Hack to prevent errors with plotting, specifically x and y shape different error
		
		#Chart 5 minute timeframes only, 1 by 1
		
		for i in range (0,len(results[0].datas),3):
			for j, d in enumerate(results[0].datas):
				d.plotinfo.plot = i ==j
			
			cerebro.plot(end = plot_end, barup='olive', bardown='lightpink',volup = 'lightgreen',voldown='crimson')
	
				
if __name__ == '__main__':
	
	#Run strategy
	runstrat()
