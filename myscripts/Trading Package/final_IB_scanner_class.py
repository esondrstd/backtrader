from ib.ext.Contract import Contract
from ib.ext.Order import Order
from ib.opt import ibConnection, message
from ib.ext.ScannerSubscription import ScannerSubscription
import time


class mystore():
	def __init__(self):
		self.gapup = []
		self.gapdown = []
		self.orderid = []
	
	
	def get_valid_order_id(self, msg): 
		print(msg.orderId)  
		self.orderid.append(msg.orderId)
		

	def scan_results(self,msg):
		#print (f'Server Response: {msg.typeName}, {msg}')
		
		if msg.reqId == self.gappingup_id:
			self.gapup.append(msg.contractDetails.m_summary.m_symbol)
		else:
			self.gapdown.append(msg.contractDetails.m_summary.m_symbol)


	def error_handler(self,msg):
		"""Handles the capturing of error messages"""
		print (f'Server Error: {msg}')
	  

	def scanDataEnd(self):
		global gappingup_id
		global gappingdown_id
		con.cancelScannerSubscription(gappingup_id)
		con.cancelScannerSubscription(gappingdown_id)
		con.disconnect()
		print ("DISCONNECTED")
		
		
	def run_prog(self):
		con = ibConnection(host='127.0.0.1', port=7497, clientId=100)
		con.connect()
			
		# Assign the error handling function defined above
		# to the TWS connection
		con.register(self.error_handler, 'Error')

		# Assign all of the server reply messages to the
		# reply_handler function defined above
		#con.registerAll(reply_handler)
		con.register(self.scan_results, message.scannerData)
		con.register(self.get_valid_order_id,'NextValidId')
		#con.reqIds(-1) 
		time.sleep(1)
		print("Order ID",self.orderid[0])
		
		
		self.gappingup_id = self.orderid[0]
		gappingup = ScannerSubscription()
		gappingup.numberOfRows(5)
		gappingup.m_scanCode = 'HIGH_OPEN_GAP'
		gappingup.m_instrument = 'STK'
		gappingup.m_averageOptionVolumeAbove ='0'
		gappingup.m_abovePrice = '5'
		gappingup.m_aboveVolume = '100000'

		self.gappingdown_id = self.gappingup_id + 1
		gappingdown = ScannerSubscription()
		gappingdown.numberOfRows(5)
		gappingdown.m_scanCode = 'LOW_OPEN_GAP'
		gappingdown.m_instrument = 'STK'
		gappingdown.m_averageOptionVolumeAbove ='0'
		gappingdown.m_abovePrice = '5'
		gappingdown.m_aboveVolume = '100000'

		con.reqScannerSubscription(self.gappingup_id,gappingup)
		time.sleep(5)
		con.reqScannerSubscription(self.gappingdown_id,gappingdown)
		time.sleep(5)

		print(self.gapup)
		print(self.gapdown)
		

myobj = mystore()
myobj.run_prog()



"""
twsScannerSubscription(numberOfRows = -1, 
                       instrument = "", 
                       locationCode = "", 
                       scanCode = "", 
                       abovePrice = "", 
                       belowPrice = "", 
                       aboveVolume = "",
                       averageOptionVolumeAbove = "",
                       marketCapAbove = "", 
                       marketCapBelow = "", 
                       moodyRatingAbove = "", 
                       moodyRatingBelow = "", 
                       spRatingAbove = "", 
                       spRatingBelow = "", 
                       maturityDateAbove = "", 
                       maturityDateBelow = "", 
                       couponRateAbove = "", 
                       couponRateBelow = "", 
                       excludeConvertible = "TRUE", 
                       scannerSettingPairs = "", 
                       stockTypeFilter = "CORP")

               
                       
scanCodes:
"LOW_OPT_VOL_PUT_CALL_RATIO",
"HIGH_OPT_IMP_VOLAT_OVER_HIST",
"LOW_OPT_IMP_VOLAT_OVER_HIST",
"HIGH_OPT_IMP_VOLAT",
"TOP_OPT_IMP_VOLAT_GAIN",
"TOP_OPT_IMP_VOLAT_LOSE",
"HIGH_OPT_VOLUME_PUT_CALL_RATIO",
"LOW_OPT_VOLUME_PUT_CALL_RATIO",
"OPT_VOLUME_MOST_ACTIVE",
"HOT_BY_OPT_VOLUME",
"HIGH_OPT_OPEN_INTEREST_PUT_CALL_RATIO",
"LOW_OPT_OPEN_INTEREST_PUT_CALL_RATIO",
"TOP_PERC_GAIN",
"MOST_ACTIVE",
"TOP_PERC_LOSE",
"HOT_BY_VOLUME",
"TOP_PERC_GAIN",
"HOT_BY_PRICE",
"TOP_TRADE_COUNT",
"TOP_TRADE_RATE",
"TOP_PRICE_RANGE",
"HOT_BY_PRICE_RANGE",
"TOP_VOLUME_RATE",
"LOW_OPT_IMP_VOLAT",
"OPT_OPEN_INTEREST_MOST_ACTIVE",
"NOT_OPEN",
"HALTED",
"TOP_OPEN_PERC_GAIN",
"TOP_OPEN_PERC_LOSE",
"HIGH_OPEN_GAP",
"LOW_OPEN_GAP",
"LOW_OPT_IMP_VOLAT",
"TOP_OPT_IMP_VOLAT_GAIN",
"TOP_OPT_IMP_VOLAT_LOSE",
"HIGH_VS_13W_HL",
"LOW_VS_13W_HL",
"HIGH_VS_26W_HL",
"LOW_VS_26W_HL",
"HIGH_VS_52W_HL",
"LOW_VS_52W_HL",
"HIGH_SYNTH_BID_REV_NAT_YIELD",
"LOW_SYNTH_BID_REV_NAT_YIELD"
"""
"""
Low Opt Volume P/C Ratio 
(LOW_OPT_VOL_PUT_CALL_RATIO)*         Put option volumes are divided by call option volumes and the top underlying symbols with the lowest ratios are displayed. 
High Option Imp Vol Over Historical 
(HIGH_OPT_IMP_VOLAT_OVER_HIST)*         Shows the top underlying contracts (stocks or indices) with the largest divergence between implied and historical volatilities. 
Low Option Imp Vol Over Historical 
(LOW_OPT_IMP_VOLAT_OVER_HIST)*         Shows the top underlying contracts (stocks or indices) with the smallest divergence between implied and historical volatilities. 
Highest Option Imp Vol 
(HIGH_OPT_IMP_VOLAT)*         Shows the top underlying contracts (stocks or indices) with the highest vega-weighted implied volatility of near-the-money options with an expiration date in the next two months. 
Top Option Imp Vol % Gainers 
(TOP_OPT_IMP_VOLAT_GAIN)*         Shows the top underlying contracts (stocks or indices) with the largest percent gain between current implied volatility and yesterday's closing value of the 15 minute average of implied volatility. 
Top Option Imp Vol % Losers 
(TOP_OPT_IMP_VOLAT_LOSE)*         Shows the top underlying contracts (stocks or indices) with the largest percent loss between current implied volatility and yesterday's closing value of the 15 minute average of implied volatility. 
High Opt Volume P/C Ratio 
(HIGH_OPT_VOLUME_PUT_CALL_ 
RATIO)         Put option volumes are divided by call option volumes and the top underlying symbols with the highest ratios are displayed. 
Low Opt Volume P/C Ratio 
(LOW_OPT_VOLUME_PUT_CALL_ 
RATIO)         Put option volumes are divided by call option volumes and the top underlying symbols with the lowest ratios are displayed. 
Most Active by Opt Volume 
(OPT_VOLUME_MOST_ACTIVE)         Displays the most active contracts sorted descending by options volume. 
Hot by Option Volume 
(HOT_BY_OPT_VOLUME)         Shows the top underlying contracts for highest options volume over a 10-day average. 
High Option Open Interest P/C Ratio 
(HIGH_OPT_OPEN_INTEREST_PUT_CALL_RATIO)         Returns the top 50 contracts with the highest put/call ratio of outstanding option contracts. 
Low Option Open Interest P/C Ratio 
(LOW_OPT_OPEN_INTEREST_PUT_ 
CALL_RATIO)         Returns the top 50 contracts with the lowest put/call ratio of outstanding option contracts. 
Top % Gainers 
(TOP_PERC_GAIN)         Contracts whose last trade price shows the highest percent increase from the previous night's closing price. 
Most Active 
(MOST_ACTIVE)         

Contracts with the highest trading volume today, based on units used by TWS (lots for US stocks; contract for derivatives and non-US stocks). 

The sample spreadsheet includes two Most Active scans: Most Active List, which displays the most active contracts in the NASDAQ, NYSE and AMEX markets, and Most Active US, which displays the most active stocks in the United States. 
Top % Losers 
(TOP_PERC_LOSE)         Contracts whose last trade price shows the lowest percent increase from the previous night's closing price. 
Hot Contracts by Volume 
(HOT_BY_VOLUME)         

Contracts where: 

    today's Volume/avgDailyVolume is highest. 
    avgDailyVolume is a 30-day exponential moving average of the contract's daily volume. 

Top % Futures Gainers 
(TOP_PERC_GAIN)         Futures whose last trade price shows the highest percent increase from the previous night's closing price. 
Hot Contracts by Price 
(HOT_BY_PRICE)         

Contracts where: 

    (lastTradePrice-prevClose)/avgDailyChange is highest in absolute value (positive or negative). 
    The avgDailyChange is defined as an exponential moving average of the contract's (dailyClose-dailyOpen) 

Top Trade Count 
(TOP_TRADE_COUNT)         The top trade count during the day. 
Top Trade Rate 
(TOP_TRADE_RATE)         Contracts with the highest number of trades in the past 60 seconds (regardless of the sizes of those trades). 
Top Price Range 
(TOP_PRICE_RANGE)         The largest difference between today's high and low, or yesterday's close if outside of today's range. 
Hot by Price Range 
(HOT_BY_PRICE_RANGE)         The largest price range (from Top Price Range calculation) over the volatility. 
Top Volume Rate 
(TOP_VOLUME_RATE)         The top volume rate per minute. 
Lowest Option Imp Vol 
(LOW_OPT_IMP_VOLAT)         Shows the top underlying contracts (stocks or indices) with the lowest vega-weighted implied volatility of near-the-money options with an expiration date in the next two months. 
Most Active by Opt Open Interest 
(OPT_OPEN_INTEREST_MOST_ 
ACTIVE)         Returns the top 50 underlying contracts with the (highest number of outstanding call contracts) + (highest number of outstanding put contracts) 
Not Open 
(NOT_OPEN)         Contracts that have not traded today. 
Halted 
(HALTED)         Contracts for which trading has been halted. 
Top % Gainers Since Open 
(TOP_OPEN_PERC_GAIN)         Shows contracts with the highest percent price INCREASE between the last trade and opening prices. 
Top % Losers Since Open 
(TOP_OPEN_PERC_LOSE)         Shows contracts with the highest percent price DECREASE between the last trade and opening prices. 
Top Close-to-Open % Gainers 
(HIGH_OPEN_GAP)         Shows contracts with the highest percent price INCREASE between the previous close and today's opening prices. 
Top Close-to-Open % Losers 
(LOW_OPEN_GAP)         Shows contracts with the highest percent price DECREASE between the previous close and today's opening prices. 
Lowest Option Imp Vol 
(LOW_OPT_IMP_VOLAT)         Shows the top underlying contracts (stocks or indices) with the lowest vega-weighted implied volatility of near-the-money options with an expiration date in the next two months. 
Top Option Imp Vol % Gainers 
(TOP_OPT_IMP_VOLAT_GAIN)         Shows the top underlying contracts (stocks or indices) with the largest percent gain between current implied volatility and yesterday's closing value of the 15 minute average of implied volatility. 
Top Option Imp Vol % Losers 
(TOP_OPT_IMP_VOLAT_LOSE)*         Shows the top underlying contracts (stocks or indices) with the largest percent loss between current implied volatility and yesterday's closing value of the 15 minute average of implied volatility. 
13-Week High 
(HIGH_VS_13W_HL)         The highest price for the past 13 weeks. 
13-Week Low 
(LOW_VS_13W_HL)         The lowest price for the past 13 weeks. 
26-Week High 
(HIGH_VS_26W_HL)         The highest price for the past 26 weeks. 
26-Week Low 
(LOW_VS_26W_HL)         The lowest price for the past 26 weeks. 
52-Week High 
(HIGH_VS_52W_HL)         The highest price for the past 52 weeks. 
52-Week Low 
(LOW_VS_52W_HL)         The lowest price for the past 52 weeks. 
EFP - High Synth Bid Rev Yield 
(HIGH_SYNTH_BID_REV_NAT_ 
YIELD)         Highlights the highest synthetic EFP interest rates available. These rates are computed by taking the price differential between the SSF and the underlying stock and netting dividends to calculate an annualized synthetic implied interest rate over the period of the SSF. The High rates may present an investment opportunity. 
EFP - Low Synth Bid Rev Yield 
(LOW_SYNTH_BID_REV_NAT_ 
YIELD)         Highlights the lowest synthetic EFP interest rates available. These rates are computed by taking the price differential between the SSF and the underlying stock and netting dividends to calculate an annualized synthetic implied interest rate over the period of the SSF. The Low rates may present a borrowing opportunity. 

WSH_NEXT_ANALYST_MEETING, 
WSH_NEXT_EARNINGS, 
WSH_NEXT_EVENT, 
WSH_NEXT_MAJOR_EVENT, 
WSH_PREV_ANALYST_MEETING, 
WSH_PREV_EARNINGS, 
WSH_PREV_EVENT, 
"""

	


