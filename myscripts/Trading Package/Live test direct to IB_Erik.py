from ibapi.client import EClient
from ibapi.wrapper import EWrapper
import threading
import time
from ibapi.ticktype import TickTypeEnum

from ibapi.contract import Contract
#from ibapi.ticktype import TickTypeEnum

class IBapi(EWrapper, EClient):
	def __init__(self):
		EClient.__init__(self, self)
		
	def tickPrice(self, reqId, tickType, price, attrib):
		#Wrapper that handles reqMrketData call - this is where you can filter the streamed results

		print(tickType,price)
		if tickType==4:
			print(tickType,price)
			
		
	def historicalData(self, reqId, bar):
		#Wrapper that handles reqHistoricalData call - this is where you can filter the streamed results
		print(f'Time: {bar.date} Close: {bar.close}')
		app.data.append([bar.date, bar.close])

	def updatePortfolio(self, contract: Contract, position: float,
		marketPrice: float, marketValue: float,
		averageCost: float, unrealizedPNL: float,
		realizedPNL: float, accountName: str):
		
		#Wrapper that handles reqAccountUpdates call - this is where you can filter the streamed results
		super().updatePortfolio(contract, position, marketPrice, marketValue,
				 averageCost, unrealizedPNL, realizedPNL, accountName)
		print("UpdatePortfolio.", "Symbol:", contract.symbol, "SecType:", contract.secType, "Exchange:",
			contract.exchange, "Position:", position, "MarketPrice:", marketPrice,
			"MarketValue:", marketValue, "AverageCost:", averageCost,
			"UnrealizedPNL:", unrealizedPNL, "RealizedPNL:", realizedPNL,
			"AccountName:", accountName)
		
	def accountSummary(self, reqId: int, account: str, tag: str, value: str,
						currency: str):
		#Wrapper that handles reqAccountSummary call - this is where you can filter the streamed results			
		super().accountSummary(reqId, account, tag, value, currency)
		if tag=='TotalCashBalance':
			print(tag,value)
		"""
		print("AccountSummary. ReqId:", reqId, "Account:", account,
			   "Tag: ", tag, "Value:", value, "Currency:", currency)
		"""

def run_loop():
	app.run()

app = IBapi()
app.connect('127.0.0.1', 7497, 100)

#Start the socket in a thread
api_thread = threading.Thread(target=run_loop, daemon=True)
api_thread.start()

"""
#Prints out tick types that can be used to request different kinds of market data in '' part of app.reqMktData(1, apple_contract, '', False, False, [])
for i in range(89):
     print(TickTypeEnum.to_str(i), i)
"""

time.sleep(1) #Sleep interval to allow time for connection to server

#Create contract object
contract = Contract()

"""
contract.symbol = 'TICK-NYSE'
contract.secType = 'IND'
contract.exchange = 'NYSE'
contract.currency = 'USD'
"""
contract.symbol = 'EUR'
contract.secType = 'CASH'
contract.exchange = 'IDEALPRO'
contract.currency = 'USD'

"""
contract.symbol = 'INTC'
contract.secType = 'STK'
contract.exchange = 'SMART'
contract.currency = 'USD'
"""


#The following are how you request data from Interactive Brokers Directly
#Request Market Data
app.reqMktData(1, contract, '' , False, False, [])

#id, contract, generic ticks - numbers correspond to a tick ID - 233 generic tick corresponds to 48 tick ID which corresponds to RTVolume, or 293 corresponds to tick ID 54 which is Trade Count.

#app.reqMktData(1, contract, '' , False, False, [])

#Historical Candlestick data request
app.data = [] #Initialize variable to store candle

#Incomplete - app.reqHistoricalDataEx(1, contract, '20190702 23:59:59','2 D','5 MINS','TRADES',0)
#app.reqHistoricalData(1, contract, '', '2 D', '1 hour', 'TRADES', 0, 2, True, [])  #app.reqHistoricalData( id,contract,end date, interval, time period, data type, rth, time format, streaming(update every 5 seconds))
#app.reqAccountUpdates(True, 'DU632069')
#app.reqAccountSummary(1, "All",  "$LEDGER:USD")

time.sleep(5) #Sleep interval to allow time for incoming price data


