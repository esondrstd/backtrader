from ib.ext.Contract import Contract
from ib.ext.Order import Order
from ib.opt import ibConnection, message
from ib.ext.ScannerSubscription import ScannerSubscription
import time

gapup = []
gapdown = []

def scan_results(msg):
	global gappingup_id
	global gappingdown_id
	#print (f'Server Response: {msg.typeName}, {msg}')
	
	if msg.reqId == gappingup_id:
		gapup.append(msg.contractDetails.m_summary.m_symbol)
	else:
		gapdown.append(msg.contractDetails.m_summary.m_symbol)


def error_handler(msg):
    """Handles the capturing of error messages"""
    print (f'Server Error: {msg}')
  

def create_contract(symbol, sec_type, exch, prim_exch, curr):
    """Create a Contract object defining what will
    be purchased, at which exchange and in which currency.

    symbol - The ticker symbol for the contract
    sec_type - The security type for the contract ('STK' is 'stock')
    exch - The exchange to carry out the contract on
    prim_exch - The primary exchange to carry out the contract on
    curr - The currency in which to purchase the contract"""
    contract = Contract()
    contract.m_symbol = symbol
    contract.m_secType = sec_type
    contract.m_exchange = exch
    contract.m_primaryExch = prim_exch
    contract.m_currency = curr
    return contract
    
def create_order(order_type, quantity, action):
    """Create an Order object (Market/Limit) to go long/short.

    order_type - 'MKT', 'LMT' for Market or Limit orders
    quantity - Integral number of assets to order
    action - 'BUY' or 'SELL'"""
    order = Order()
    order.m_orderType = order_type
    order.m_totalQuantity = quantity
    order.m_action = action
    return order


def scanDataEnd():
	global gappingup_id
	global gappingdown_id
	con.cancelScannerSubscription(gappingup_id)
	con.cancelScannerSubscription(gappingdown_id)
	con.disconnect()
	print ("DISCONNECTED")
    

con = ibConnection(host='127.0.0.1', port=7497, clientId=100)
con.connect()
	
# Assign the error handling function defined above
# to the TWS connection
con.register(error_handler, 'Error')

# Assign all of the server reply messages to the
# reply_handler function defined above
#con.registerAll(reply_handler)
con.register(scan_results, message.scannerData)

# Create a contract in GOOG stock via SMART order routing
goog_contract = create_contract('GOOG', 'STK', 'SMART', 'SMART', 'USD')

#Get market data stream
#con.reqMktData(1, goog_contract, '', False)

# Go long 100 shares of Google
goog_order = create_order('MKT', 100, 'BUY')

# Use the connection to the send the order to IB
#con.placeOrder(100,goog_contract, goog_order)

gappingup_id = 13851
gappingup = ScannerSubscription()
gappingup.numberOfRows(5)
gappingup.m_scanCode = 'HIGH_OPEN_GAP'
gappingup.m_instrument = 'STK'
gappingup.m_averageOptionVolumeAbove ='0'
gappingup.m_abovePrice = '5'
gappingup.m_aboveVolume = '100000'

gappingdown_id = gappingup_id + 1
gappingdown = ScannerSubscription()
gappingdown.numberOfRows(5)
gappingdown.m_scanCode = 'LOW_OPEN_GAP'
gappingdown.m_instrument = 'STK'
gappingdown.m_averageOptionVolumeAbove ='0'
gappingdown.m_abovePrice = '5'
gappingdown.m_aboveVolume = '100000'

con.reqScannerSubscription(gappingup_id,gappingup)
time.sleep(5)
con.reqScannerSubscription(gappingdown_id,gappingdown)
time.sleep(5)

print(gapup)
print(gapdown)

	
	


