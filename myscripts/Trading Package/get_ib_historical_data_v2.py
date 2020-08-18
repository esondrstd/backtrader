# Gist example of IB wrapper ...
#
# Download API from http://interactivebrokers.github.io/#
#
# Install python API code /IBJts/source/pythonclient $ python3 setup.py install
#
# Note: The test cases, and the documentation refer to a python package called IBApi,
#    but the actual package is called ibapi. Go figure.
#
# Get the latest version of the gateway:
# https://www.interactivebrokers.com/en/?f=%2Fen%2Fcontrol%2Fsystemstandalone-ibGateway.php%3Fos%3Dunix
#    (for unix: windows and mac users please find your own version)
#
import pandas
from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import Contract as IBcontract
from threading import Thread
import queue
import datetime
from datetime import datetime
from datetime import date
import numpy as np


DEFAULT_HISTORIC_DATA_ID=50
DEFAULT_GET_CONTRACT_ID=43

## marker for when queue is finished
FINISHED = object()
STARTED = object()
TIME_OUT = object()

class finishableQueue(object):

    def __init__(self, queue_to_finish):

        self._queue = queue_to_finish
        self.status = STARTED

    def get(self, timeout):
        """
        Returns a list of queue elements once timeout is finished, or a FINISHED flag is received in the queue
        :param timeout: how long to wait before giving up
        :return: list of queue elements
        """
        contents_of_queue=[]
        finished=False

        while not finished:
            try:
                current_element = self._queue.get(timeout=timeout)
                if current_element is FINISHED:
                    finished = True
                    self.status = FINISHED
                else:
                    contents_of_queue.append(current_element)
                    ## keep going and try and get more data

            except queue.Empty:
                ## If we hit a time out it's most probable we're not getting a finished element any time soon
                ## give up and return what we have
                finished = True
                self.status = TIME_OUT

        return contents_of_queue

    def timed_out(self):
        return self.status is TIME_OUT


class TestWrapper(EWrapper):
    """
    The wrapper deals with the action coming back from the IB gateway or TWS instance
    We override methods in EWrapper that will get called when this action happens, like currentTime
    Extra methods are added as we need to store the results in this object
    """

    def __init__(self):
        self._my_contract_details = {}
        self._my_historic_data_dict = {}

    ## error handling code
    def init_error(self):
        error_queue=queue.Queue()
        self._my_errors = error_queue

    def get_error(self, timeout=5):
        if self.is_error():
            try:
                return self._my_errors.get(timeout=timeout)
            except queue.Empty:
                return None

        return None

    def is_error(self):
        an_error_if=not self._my_errors.empty()
        return an_error_if

    def error(self, id, errorCode, errorString):
        ## Overriden method
        errormsg = "IB error id %d errorcode %d string %s" % (id, errorCode, errorString)
        self._my_errors.put(errormsg)


    ## get contract details code
    def init_contractdetails(self, reqId):
        contract_details_queue = self._my_contract_details[reqId] = queue.Queue()

        return contract_details_queue

    def contractDetails(self, reqId, contractDetails):
        ## overridden method

        if reqId not in self._my_contract_details.keys():
            self.init_contractdetails(reqId)

        self._my_contract_details[reqId].put(contractDetails)

    def contractDetailsEnd(self, reqId):
        ## overriden method
        if reqId not in self._my_contract_details.keys():
            self.init_contractdetails(reqId)

        self._my_contract_details[reqId].put(FINISHED)

    ## Historic data code
    def init_historicprices(self, tickerid):
        historic_data_queue = self._my_historic_data_dict[tickerid] = queue.Queue()

        return historic_data_queue


    def historicalData(self, tickerid , bar):

        ## Overriden method
        ## Note I'm choosing to ignore barCount, WAP and hasGaps but you could use them if you like
        bardata=(bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)

        historic_data_dict=self._my_historic_data_dict

        ## Add on to the current data
        if tickerid not in historic_data_dict.keys():
            self.init_historicprices(tickerid)

        historic_data_dict[tickerid].put(bardata)

    def historicalDataEnd(self, tickerid, start:str, end:str):
        ## overriden method

        if tickerid not in self._my_historic_data_dict.keys():
            self.init_historicprices(tickerid)

        self._my_historic_data_dict[tickerid].put(FINISHED)



class TestClient(EClient):
    """
    The client method
    We don't override native methods, but instead call them from our own wrappers
    """
    def __init__(self, wrapper):
        ## Set up with a wrapper inside
        EClient.__init__(self, wrapper)


    def resolve_ib_contract(self, ibcontract, reqId=DEFAULT_GET_CONTRACT_ID):

        """
        From a partially formed contract, returns a fully fledged version
        :returns fully resolved IB contract
        """

        ## Make a place to store the data we're going to return
        contract_details_queue = finishableQueue(self.init_contractdetails(reqId))

        print("Getting full contract details from the server... ")

        self.reqContractDetails(reqId, ibcontract)

        ## Run until we get a valid contract(s) or get bored waiting
        MAX_WAIT_SECONDS = 10000
        new_contract_details = contract_details_queue.get(timeout = MAX_WAIT_SECONDS)

        while self.wrapper.is_error():
            print(self.get_error())

        if contract_details_queue.timed_out():
            print("Exceeded maximum wait for wrapper to confirm finished - seems to be normal behaviour")

        if len(new_contract_details)==0:
            print("Failed to get additional contract details: returning unresolved contract")
            return ibcontract

        if len(new_contract_details)>1:
            print("got multiple contracts using first one")

        new_contract_details=new_contract_details[0]

        resolved_ibcontract=new_contract_details.contract

        return resolved_ibcontract


    def get_IB_historical_data(self, ibcontract, durationStr, barSizeSetting,endDateTime,
                               tickerid=DEFAULT_HISTORIC_DATA_ID):

        """
        Returns historical prices for a contract, up to end date
        ibcontract is a Contract
        :returns list of prices in 4 tuples: Open high low close volume
        """


        ## Make a place to store the data we're going to return
        historic_data_queue = finishableQueue(self.init_historicprices(tickerid))

        # Request some historical data. Native method in EClient
        self.reqHistoricalData(
            tickerid,  # tickerId,
            ibcontract,  # contract,
            endDateTime,  # endDateTime,
            durationStr,  # durationStr,
            barSizeSetting,  # barSizeSetting,
            "TRADES",  # whatToShow,
            1,  # useRTH,
            1,  # formatDate
            False,  # KeepUpToDate <<==== added for api 9.73.2
            [] ## chartoptions not used
        )

        ## Wait until we get a completed data, an error, or get bored waiting
        MAX_WAIT_SECONDS = 10000
        print("Getting historical data from the server... could take %d seconds to complete " % MAX_WAIT_SECONDS)

        historic_data = historic_data_queue.get(timeout = MAX_WAIT_SECONDS)

        while self.wrapper.is_error():
            print(self.get_error())

        if historic_data_queue.timed_out():
            print("Exceeded maximum wait for wrapper to confirm finished - seems to be normal behaviour")

        self.cancelHistoricalData(tickerid)

        return historic_data


class TestApp(TestWrapper, TestClient):
    def __init__(self, ipaddress, portid, clientid):
        TestWrapper.__init__(self)
        TestClient.__init__(self, wrapper=self)

        self.connect(ipaddress, portid, clientid)

        thread = Thread(target = self.run)
        thread.start()

        setattr(self, "_thread", thread)

        self.init_error()
        

app = TestApp("127.0.0.1", 7497, 100)


	 
	    
#IF 1 symbol only, make sure to put ',' next to it or weird things happen.  Type in symbols you want historical data for
contractlist = ('AAPL',) 

#INPUT START DATE AND END DATE
start_date = "2019-07-03"
end_date = "2020-04-13"
#timedif = days_between(start_date,end_date)
tdif = np.busday_count(start_date, end_date)
print(tdif)


#duration = "{} D".format(tdif)  #i.e. "5 Y" - Use when duration is greater than 1 year (IB does not let you specify days greater than 365 days for some symbols
duration =  "2 D"
barsize = "5 MINS"
end_date = "20200413 23:59:59" #Has to be in this format "20160127 23:59:59"

ibcontract = IBcontract()
ibcontract.LastTradeDateOrContractMonth=end_date
ibcontract.secType = "STK" #for stocks, "STK", for Indices, "IND"
ibcontract.exchange= "NYSE" #usually "SMART", but can be "NYSE","AMEX","CBOE",NASDAQ - Make sure you are subscribed to exchanges
ibcontract.currency= "USD"


for s in contractlist:
	
	print("Getting Data for {}".format(s))
	
	ibcontract.symbol= s
	resolved_ibcontract=app.resolve_ib_contract(ibcontract)
	historic_data = app.get_IB_historical_data(resolved_ibcontract,duration,barsize,end_date)
	
	data = pandas.DataFrame(historic_data, columns=['date','open','high','low','close','volume'])
	#Add ticker name column and date updated column to data table
	data.insert(0, 'ticker', s)
	data.insert(7,'created', datetime.now())
	data.insert(8,'source', 'Interactive Brokers')
	
	#Add new column called 'key' and populate with concatenated values from 2 other columns
	newdata = data['ticker'] + ' ' + data['date']
	data.insert(9,'key',newdata)
	
	#Change date format
	data['date'] = pandas.to_datetime(data['date'], infer_datetime_format=True, errors='coerce')
	
	#drop first field and rename date field
	#data.rename(columns={'date':'price_date'}, inplace=True)
	
	#Output to csv file
	data.to_csv('C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/{}.csv'.format(s))
	
app.disconnect()

"""
IB CONTRACT REFERENCE GUIDE
Basic Contracts
FX Pairs

                Contract contract = new Contract();
                contract.Symbol = "EUR";
                contract.SecType = "CASH";
                contract.Currency = "GBP";
                contract.Exchange = "IDEALPRO";

Stocks

                Contract contract = new Contract();
                contract.Symbol = "IBKR";
                contract.SecType = "STK";
                contract.Currency = "USD";
                //In the API side, NASDAQ is always defined as ISLAND in the exchange field
                contract.Exchange = "ISLAND";

For certain smart-routed stock contracts that have the same symbol, currency and exchange, you would also need to specify the primary exchange attribute to uniquely define the contract. This should be defined as the native exchange of a contract, and is good practice to include for all stocks:

                Contract contract = new Contract();
                contract.Symbol = "MSFT";
                contract.SecType = "STK";
                contract.Currency = "USD";
                contract.Exchange = "SMART";
                //Specify the Primary Exchange attribute to avoid contract ambiguity
                // (there is an ambiguity because there is also a MSFT contract with primary exchange = "AEB")
                contract.PrimaryExch = "ISLAND";

For the purpose of requesting market data, the routing exchange and primary exchange can be specified in a single 'exchange' field if they are separated by a valid component exchange separator, for instance exchange = "SMART:ARCA". The default separators available are colon ":" and slash "/". Other component exchange separators can be defined using the field defined in TWS Global Configuration under API -> Settings. The component exchange separator syntax in TWS versions prior to 971 can only be used to request market data and not to place orders.
Indexes

ISINs for indices which are available in IB's database are available in the API as of TWS 965+.

                Contract contract = new Contract();
                contract.Symbol = "DAX";
                contract.SecType = "IND";
                contract.Currency = "EUR";
                contract.Exchange = "DTB";

CFDs

                Contract contract = new Contract();
                contract.Symbol = "IBDE30";
                contract.SecType = "CFD";
                contract.Currency = "EUR";
                contract.Exchange = "SMART";

Futures

A regular futures contract is commonly defined using an expiry and the symbol field defined as the symbol of the underlying. Historical data for futures is available up to 2 years after they expire by setting the includeExpired flag within the Contract class to True.

                Contract contract = new Contract();
                contract.Symbol = "ES";
                contract.SecType = "FUT";
                contract.Exchange = "GLOBEX";
                contract.Currency = "USD";
                contract.LastTradeDateOrContractMonth = "201803";

By contract the 'local symbol' field is IB's symbol for the future itself (the Symbol within the TWS' Contract Description dialog). Since a local symbol uniquely defines a future, an expiry is not necessary.

                Contract contract = new Contract();
                contract.SecType = "FUT";
                contract.Exchange = "GLOBEX";
                contract.Currency = "USD";
                contract.LocalSymbol = "ESU6";

Occasionally, you can expect to have more than a single future contract for the same underlying with the same expiry. To rule out the ambiguity, the contract's multiplier can be given as shown below:

                Contract contract = new Contract();
                contract.Symbol = "DAX";
                contract.SecType = "FUT";
                contract.Exchange = "DTB";
                contract.Currency = "EUR";
                contract.LastTradeDateOrContractMonth = "201609";
                contract.Multiplier = "5";

Continuous futures are available from the API with TWS v971 and higher. Continuous futures cannot be used with real time data or to place orders, but only for historical data.

                Contract contract = new Contract();
                contract.Symbol = "ES";
                contract.SecType = "CONTFUT";
                contract.Exchange = "GLOBEX";

The security type "FUT+CONTFUT" can be used to request contract details about the futures and continuous futures on an underlying. This security type cannot be used with other functionality.

                Contract contract = new Contract();
                contract.Symbol = "ES";
                contract.SecType = "FUT+CONTFUT";
                contract.Exchange = "GLOBEX";

Options

Options, like futures, also require an expiration date plus a strike and a multiplier:

                Contract contract = new Contract();
                contract.Symbol = "GOOG";
                contract.SecType = "OPT";
                contract.Exchange = "BOX";
                contract.Currency = "USD";
                contract.LastTradeDateOrContractMonth = "20170120";
                contract.Strike = 615;
                contract.Right = "C";
                contract.Multiplier = "100";

It is not unusual to find many option contracts with an almost identical description (i.e. underlying symbol, strike, last trading date, multiplier, etc.). Adding more details such as the trading class will help:

                Contract contract = new Contract();
                contract.Symbol = "SANT";
                contract.SecType = "OPT";
                contract.Exchange = "MEFFRV";
                contract.Currency = "EUR";
                contract.LastTradeDateOrContractMonth = "20190621";
                contract.Strike = 7.5;
                contract.Right = "C";
                contract.Multiplier = "100";
                contract.TradingClass = "SANEU";

The OCC options symbol can be used to define an option contract in the API through the option's 'local symbol' field.

                Contract contract = new Contract();
                //Watch out for the spaces within the local symbol!
                contract.LocalSymbol = "C DBK  DEC 20  1600";
                contract.SecType = "OPT";
                contract.Exchange = "DTB";
                contract.Currency = "EUR";

Futures Options

Important: In TWS versions prior to 972, if defining a futures option that has a price magnifier using the strike price, the strike will be the strike price displayed in TWS divided by the price magnifier. (e.g. displayed in dollars not cents for ZW)
In TWS versions 972 and greater, the strike prices will be shown in TWS and the API the same way (without a price magnifier applied)
For some futures options (e.g GE) it will be necessary to define a trading class, or use the local symbol, or conId.

                Contract contract = new Contract();
                contract.Symbol = "ES";
                contract.SecType = "FOP";
                contract.Exchange = "GLOBEX";
                contract.Currency = "USD";
                contract.LastTradeDateOrContractMonth = "20180316";
                contract.Strike = 2800;
                contract.Right = "C";
                contract.Multiplier = "50";

Bonds

Bonds can be specified by defining the symbol as the CUSIP or ISIN.

                Contract contract = new Contract();
                // enter CUSIP as symbol
                contract.Symbol = "912828C57";
                contract.SecType = "BOND";
                contract.Exchange = "SMART";
                contract.Currency = "USD";

Bonds can also be defined with the conId and exchange as with any security type.

                Contract contract = new Contract();
                contract.ConId = 285191782;
                contract.Exchange = "SMART";

Mutual Funds

Trading Mutual Funds is not currently fully-supported from the API. Note: Mutual Funds orders cannot be placed in paper accounts from any trading system.

                Contract contract = new Contract();
                contract.Symbol = "VINIX";
                contract.SecType = "FUND";
                contract.Exchange = "FUNDSERV";
                contract.Currency = "USD";

Commodities

                Contract contract = new Contract();
                contract.Symbol = "XAUUSD";
                contract.SecType = "CMDTY";
                contract.Exchange = "SMART";
                contract.Currency = "USD";

Dutch Warrants and Structured Products

To unambiguously define a Dutch Warrant or Structured Product (IOPTs) the conId or localSymbol field must be used.

    It is important to note that if reqContractDetails is used with an incompletely-defined IOPT contract definition, that thousands of results can be returned and the API connection broken.
    IOPT contract definitions will often change and it will be necessary to restart TWS or IB Gateway to download the new contract definition.

                Contract contract = new Contract();
                contract.LocalSymbol = "B881G";
                contract.SecType = "IOPT";
                contract.Exchange = "SBF";
                contract.Currency = "EUR";


OTHER PARAMETERS:
Valid Duration String units
Unit	Description
S	Seconds
D	Day
W	Week
M	Month
Y	Year
Valid Bar Sizes
Size
1 secs 	5 secs 	10 secs 	15 secs 	30 secs
1 min 	2 mins 	3 mins 	5 mins 	10 mins 	15 mins 	20 mins 	30 mins
1 hour 	2 hours 	3 hours 	4 hours 	8 hours
1 day
1 week
1 month
Historical Data Types

(whatToShow)

All different kinds of historical data are returned in the form of candlesticks and as such the values return represent the state of the market during the period covered by the candlestick.
Type	Open	High	Low	Close	Volume
TRADES	First traded price	Highest traded price	Lowest traded price	Last traded price	Total traded volume
MIDPOINT	Starting midpoint price	Highest midpoint price	Lowest midpoint price	Last midpoint price	N/A
BID	Starting bid price	Highest bid price	Lowest bid price	Last bid price	N/A
ASK	Starting ask price	Highest ask price	Lowest ask price	Last ask price	N/A
BID_ASK	Time average bid	Max Ask	Min Bid	Time average ask	N/A
ADJUSTED_LAST	Dividend-adjusted first traded price	Dividend-adjusted high trade	Dividend-adjusted low trade	Dividend-adjusted last trade	Total traded volume
HISTORICAL_VOLATILITY	Starting volatility	Highest volatility	Lowest volatility	Last volatility	N/A
OPTION_IMPLIED_VOLATILITY	Starting implied volatility	Highest implied volatility	Lowest implied volatility	Last implied volatility	N/A
REBATE_RATE	Starting rebate rate	Highest rebate rate	Lowest rebate rate	Last rebate rate	N/A
FEE_RATE	Starting fee rate	Highest fee rate	Lowest fee rate	Last fee rate	N/A
YIELD_BID	Starting bid yield	Highest bid yield	Lowest bid yield	Last bid yield 	N/A
YIELD_ASK	Starting ask yield	Highest ask yield	Lowest ask yield	Last ask yield	N/A
YIELD_BID_ASK	Time average bid yield	Highest ask yield	Lowest bid yield	Time average ask yield	N/A
YIELD_LAST	Starting last yield	Highest last yield	Lowest last yield	Last last yield	

N/A

    TRADES data is adjusted for splits, but not dividends
    ADJUSTED_LAST data is adjusted for splits and dividends. Requires TWS 967+.

"""
