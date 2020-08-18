from ibapi.client import EClient
from ibapi.wrapper import EWrapper
import threading
import time
from ibapi.ticktype import TickTypeEnum
import pandas
from datetime import date, datetime
from collections import defaultdict
from ibapi.contract import Contract
import queue

class IBapi(EWrapper, EClient):
	def __init__(self):
		EClient.__init__(self, self)
		self.qs = defaultdict(list)
		self._my_contract_details = {}
		self._my_historic_data_dict = {}

	#Method returns a queue object, and a dictionary, that is ready to be filled 
	def init_contractdetails(self, reqId):
		contract_details_queue = self._my_contract_details[reqId] = queue.Queue()

		return contract_details_queue
		
	
	def contractDetails(self, reqId, contractDetails):
		#Wrapper for contract details
		print("ContractDetails", reqId,
              contractDetails.contract.symbol,
              contractDetails.contract.secType,
              "ConId:", contractDetails.contract.conId,
              "@", contractDetails.contract.exchange)
	
	
		#if reqID not in dictionary, call the queue function to make it available, and then put contractdetails in
		if reqId not in self._my_contract_details.keys():
			self.init_contractdetails(reqId)  #call function that instantiates queue object (makes it available to add to)

		self._my_contract_details[reqId].put(contractDetails)  #put contractdetails message into queue
		print(self._my_contract_details[reqId].get())
		
		
	def tickPrice(self, reqId, tickType, price, attrib):
		#Wrapper that handles reqMrketData call - this is where you can filter the streamed results

		print("PRINT ALL TICKTYPES",tickType,price)
		if tickType==4:
			#Store responses in dictionary for later use
			self.qs['tickType'].append(tickType)
			self.qs['price'].append(price)
			print(self.qs['price'])
	
				
	def historicalData(self, reqId, bar):
		#Wrapper that handles reqHistoricalData call - this is where you can filter the streamed results
		bardata=(bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)

		historic_data_dict=self._my_historic_data_dict

		"""
		## Add on to the current data
		if tickerid not in historic_data_dict.keys():
			self.init_historicprices(tickerid)

		historic_data_dict[tickerid].put(bardata)
		"""

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
api_thread = threading.Thread(target=app.run(), daemon=True)
qlive = api_thread.start()

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

contract.symbol = 'GBP'
contract.secType = 'CASH'
contract.exchange = 'IDEALPRO'
contract.currency = 'USD'

"""
contract.symbol = 'INTC'
contract.secType = 'STK'
contract.exchange = 'SMART'
contract.currency = 'USD'
"""
#app.reqContractDetails(1,contract)

#The following are how you request data from Interactive Brokers Directly
#Request Market Data
#app.reqMktData(1, contract, '233' , False, False, [])  #id, contract, generic ticks - numbers correspond to a tick ID - 233 generic tick corresponds to 48 tick ID which corresponds to RTVolume, or 293 corresponds to tick ID 54 which is Trade Count.
app.reqContractDetails(1,contract)

#Historical Candlestick data request
app.reqHistoricalData(1, contract, '', '2 D', '1 hour', 'BID', 0, 2, True, [])  #app.reqHistoricalData( id,contract,end date, interval, time period, data type, rth, time format, streaming(update every 5 seconds))

#Request Portfolio Updates
#app.reqAccountUpdates(True, 'DU632069')
#app.reqAccountSummary(1, "All",  "$LEDGER:USD")

time.sleep(3) #Sleep interval to allow time for incoming price data

def startfunc(self):
	qlive = app.reqMktData(1, contract, '233' , False, False, [])
	return qlive
	
