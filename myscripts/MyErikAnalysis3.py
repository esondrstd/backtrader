import mysql.connector
import pandas as pd
from pandas import Series, DataFrame
from collections import defaultdict
from datetime import date, time, datetime
import matplotlib.pyplot as plt
#import mplfinance as mpf
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
import numpy as np

"""
Allows you to query stock database and perform research/analysis.
"Lines" are provided in the dictionary format (most recent value as 0, next recent as 1, etc.)
"""
#*****************GET CONNECTION AND DEFINE PARAMETERS**********************************
mydb = mysql.connector.connect(
	host="127.0.0.1",           
	user="root",           
	password="EptL@Rl!1",       
	database = "Stock_Prices", 
)
table='5_min_prices'
ticker_list = []
ticker_list =['A', 'AAL', 'AAPL', 'ABBV', 'ABT', 'ACN', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP', 'AFL', 'AGG', 'AGN', 'ALGN', 'ALL', 'ALXN', 'AMAT', 'AMGN', 'AMT', 'AMZN', 'ANTM', 'AON', 'APD', 'APH', 'ASML', 'ATVI', 'AVGO', 'AWK', 'AXP', 'AZO', 'BA', 'BABA', 'BAC', 'BAX', 'BDX', 'BIDU', 'BIIB', 'BK', 'BKNG', 'BLK', 'BMRN', 'BMY', 'BSX', 'C', 'CAT', 'CB', 'CCI', 'CDNS', 'CERN', 'CHKP', 'CHTR', 'CI', 'CL', 'CLX', 'CMCSA', 'CME', 'CNC', 'COF', 'COP', 'COST', 'CRM', 'CSCO', 'CSX', 'CTAS', 'CTSH', 'CTXS', 'CVS', 'CVX', 'D', 'DBA', 'DE', 'DG', 'DHR', 'DIS', 'DLR', 'DLTR', 'DUK', 'EA', 'EBAY', 'ECL', 'ED', 'EL', 'EMR', 'EQIX', 'EQR', 'ES', 'ETN', 'EW', 'EWH', 'EWW', 'EXC', 'EXPE', 'FAST', 'FB', 'FDX', 'FE', 'FIS', 'FISV', 'GD', 'GE', 'GILD', 'GIS', 'GM', 'GOOG', 'GPN', 'GS', 'HAS', 'HCA', 'HD', 'HON', 'HPQ', 'HSIC', 'HUM', 'HYG', 'IAU', 'IBM', 'ICE', 'IDXX', 'ILMN', 'INCY', 'INFO', 'INTC', 'INTU', 'ISRG', 'ITW', 'JBHT', 'JD', 'JNJ', 'JPM', 'KHC', 'KLAC', 'KMB', 'KMI', 'KO', 'KR', 'LBTYA', 'LBTYK', 'LHX', 'LLY', 'LMT', 'LOW', 'LQD', 'LRCX', 'LULU', 'MA', 'MAR', 'MCD', 'MCHP', 'MCO', 'MDLZ', 'MDT', 'MELI', 'MET', 'MMC', 'MMM', 'MNST', 'MO', 'MRK', 'MS', 'MSCI', 'MSFT', 'MSI', 'MU', 'MXIM', 'MYL', 'NEE', 'NEM', 'NFLX', 'NKE', 'NLOK', 'NOC', 'NOW', 'NSC', 'NTAP', 'NTES', 'NVDA', 'NXPI', 'ORCL', 'ORLY', 'PAYX', 'PCAR', 'PEG', 'PFE', 'PG', 'PGR', 'PLD', 'PM', 'PNC', 'PSA', 'PSX', 'PYPL', 'QCOM', 'REGN', 'RMD', 'ROP', 'ROST', 'RTX', 'SBAC', 'SBUX', 'SCHW', 'SHOP', 'SHW', 'SIRI', 'SNPS', 'SO', 'SPGI', 'SPY', 'SRE', 'STZ', 'SWKS', 'SYK', 'SYY', 'T', 'TCOM', 'TFC', 'TGT', 'TIP', 'TJX', 'TMO', 'TMUS', 'TROW', 'TRV', 'TSLA', 'TTWO', 'TWLO', 'TXN', 'ULTA', 'UNH', 'UNP', 'UPS', 'USB', 'V', 'VNQ', 'VRSK', 'VRSN', 'VRTX', 'VZ', 'WBA', 'WDC', 'WEC', 'WFC', 'WLTW', 'WM', 'WMT', 'WYNN', 'XHB', 'XLK', 'XLNX', 'XLU', 'XLV', 'XOM', 'XRT', 'YUM', 'ZTS']
#ticker_list = ['SPY','VIX']
start_date = date(2015,1,2)
end_date = date(2020,3,30)
sessionstart = time(8,30)
sessionend = time(14,55)
lookback = 30
ago = 0
myresult = defaultdict(list)
mynewresult = defaultdict(list)
closelist = defaultdict(list)
highlist = defaultdict(list)
lowlist = defaultdict(list)
datelist = defaultdict(list)
k = 0
i = 0
j = 0
x = 0


#***************************************************************************************************************************************
#CREATE COMBINED DATAFRAME OF RETURNS AND GET CORRELATIONS, COVARIANCES, and PORTFOLIO VARIANCE

#Code to combine multiple tickers into 1 dataframe of just close prices
main_df = pd.DataFrame()
for t in ticker_list:
	print("Loading {} ".format(t))
	result = "SELECT date,open,high,low,close,volume FROM {} WHERE ticker = '{}' and date >= '{}' and date <='{}' ORDER BY date DESC".format(table,t,start_date.strftime("%Y-%m-%d"),end_date.strftime("%Y-%m-%d"))   
	myohlc=pd.read_sql(result,con=mydb)
	ohlc = myohlc.loc[:, ['date', 'open', 'high', 'low', 'close','volume']]
	ohlc.rename(columns={'date':'Date','open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'}, inplace=True)
	
	df = pd.read_sql(result,con=mydb)
	df.set_index('date', inplace=True)
	df.rename(columns={'close':t}, inplace=True)
	df.drop(['open','high','low','volume'],1,inplace=True)
	#print(df)
	#print(df[t])

	if main_df.empty:
		main_df = df
	else:
		main_df = main_df.join(df, how='outer')

#print(main_df)
	#print(main_df.head())

print("*****************************************************")
#daily_df = main_df.resample('D',axis=0).ohlc()
daily_df = main_df.resample('D',axis=0).mean()
for t in ticker_list:
	daily_df[t].fillna(method = 'ffill')
	#print(daily_df[t])

#print(daily_df)

returns = main_df.pct_change()  ##**NEED TO CONVERT 5 MIN BARS TO DAILY CHARTS TO DO THIS**
#Print out useful stats on returns
#print(returns.describe())

#Generate Correlation Table of all stocks
corr = returns.corr()
corr.to_csv("C:\\Users\\Erik\\Desktop\\correlations.csv")  #OUTPUT TO CSV ON DESKTOP
print("Correlations =  ",corr)

#Generate covariances
cov_matrix = returns.cov()
cov_matrix_a = cov_matrix * 252 #to annualise the daily covariance matrix with the standard 250 trading days
print("Covariance Matrix ",cov_matrix_a)

# Assign equal weights to all stocks. Weights must = 1 
stock_count = len(ticker_list)
weights = 1/stock_count
weight_array = np.empty((0, stock_count))
weight_list = []
for i in ticker_list:
	weight_list.append(weights)
	#np.append(weight_array,[weights], axis=0)

weight_array = np.array(weight_list)
	
# Calculate the variance with the formula
port_variance = np.dot(weight_array.T, np.dot(cov_matrix_a, weight_array))

# Just converting the variance float into a percentage
print("Standard Deviation = {} %".format(port_variance * 100)) # The standard deviation of a portfolio is just a square root of its variance

port_volatility = np.sqrt(np.dot(weight_array.T, np.dot(cov_matrix_a, weight_array)))
print("Portfolio Volatility = {} %".format(port_volatility * 100))

#************************************************************************************************************************************


#Build Regressions
"""
Interpreting the Regression Results:

Adjusted. R-squared reflects the fit of the model. R-squared values range from 0 to 1, where a higher value generally indicates a better fit, assuming certain conditions are met.
const coefficient is your Y-intercept. It means that if both the Interest_Rate and Unemployment_Rate coefficients are zero, then the expected output (i.e., the Y) would be equal to the const coefficient.
Interest_Rate coefficient represents the change in the output Y due to a change of one unit in the interest rate (everything else held constant)
Unemployment_Rate coefficient represents the change in the output Y due to a change of one unit in the unemployment rate (everything else held constant)
std err reflects the level of accuracy of the coefficients. The lower it is, the higher is the level of accuracy
P >|t| is your p-value. A p-value of less than 0.05 is considered to be statistically significant
Confidence Interval represents the range in which our coefficients are likely to fall (with a likelihood of 95%)
"""
combined_df = pd.DataFrame()
for t in ticker_list:
	#Calculate OHLC, then drop columns to prepare for combined dataframe
	query = "SELECT date,open,high,low,close,volume FROM {} WHERE ticker = '{}' and date >= '{}' and date <='{}' ORDER BY date DESC".format(table,t,start_date.strftime("%Y-%m-%d"),end_date.strftime("%Y-%m-%d"))   
	mydf=pd.read_sql(query,con=mydb)  #Save sql query to dataframe
	mydf.set_index('date', inplace=True)
	#mydf_log = np.log(mydf['close']).diff()   #Calculate log returns for all regressions performed
	#mydf_log[0]=0  #assign starting value to 0, replacing NaN
	mydf_log = np.log(mydf['close']/mydf['close'].shift(1)).dropna()  #Safer way to do log calculation, accounts for negatives
	mydf['Logs']=mydf_log  #Add new column to dataframe
	
	mydf.rename(columns={'Logs':t}, inplace=True)  #rename Logs column to name of ticker
	mydf.drop(['open','high','low','close','volume'],1,inplace=True)  #remove all other columns

	combined_df = combined_df.join(mydf, how='outer')  #Create combined dataframe with all tickers, each with colmn for log returns

	#Replace starting values with number other than NaN
	combined_df[t].fillna(value=0, inplace=True)  #replace NaN value at start of column
	

#print(combined_df)


#Set regression variables
Y = combined_df['SPY']
X = combined_df[['VIX']] # here we have 2 variables for the multiple linear regression. If you just want to use one variable for simple linear regression, then use X = df['Interest_Rate'] for example

X = sm.add_constant(X.values) # adding a constant

#Execute regression
model = sm.OLS(Y, X).fit()
resid = model.resid  #Calculate Residuals
#print(resid)
#predictions = model.fittedvalues
#print(predictions)

#Print model
print_model = model.summary()
print(print_model)

result = adfuller(resid, autolag='AIC')  #Perform ADF unit root test on residuals to determine data stationarity.
print(result)
print('ADF Statistic {}'.format(result[0]))
print('p-value: {}'.format(result[1]))
for key, value in result[4].items():
     print('Critical Values {} {}'.format(key,value))
     
"""
ADF Output:
First data point: -1.8481210964862593: Critical value of the data in your case
Second data point: 0.35684591783869046: Probability that null hypothesis will not be rejected(p-value)
Third data point: 0: Number of lags used in regression to determine t-statistic. So there are no auto correlations going back to '0' periods here.
Forth data point: 1954: Number of observations used in the analysis.
Fifth data point: {'10%': -2.5675580437891359, '1%': -3.4337010293693235, '5%': -2.863020285222162}: T values corresponding to adfuller test.
Since critical value -1.8>-2.5,-3.4,-2.8 (t-values at 1%,5%and 10% confidence intervals), null hypothesis cannot be rejected. So there is non stationarity in your data
Also p-value of 0.35>0.05(if we take 5% significance level or 95% confidence interval), null hypothesis cannot be rejected.
Hence data is non stationary (that means it has relation with time)
"""
#****************************************************************************************************************************

#USING DICTIONARIES TO GET SPECIFIC PRICES

"""
#Get all tickers from Database and store in dictionary
ticker_query = "SELECT DISTINCT ticker FROM 5_min_prices"
sqltickers = pd.read_sql(ticker_query,con=mydb)
sqlticker_list = sqltickers.values.tolist()

newlist=[]
for t in sqlticker_list:
	y = "{}".format(t[0])
	newlist.append(y)
#print(newlist)


for t in ticker_list:
	result = "SELECT date,open,high,low,close,volume FROM {} WHERE ticker = '{}' and date >= '{}' and date <='{}' ORDER BY date DESC".format(table,t,start_date,end_date)   
	erikresult = pd.read_sql(result,con=mydb)

	myresult[t] = erikresult.to_dict() 
	erikresult.set_index('date', inplace=True)

	mynewresult[t] = erikresult.to_dict()  #For resample, can't reference myresult[t] because index is being changed to date by next line which causes other code to break in the program
	test=pd.DataFrame.from_dict(mynewresult[t])  #convert dictionary back to dataframe for analysis
	rolling_mean = test['close'].rolling(10).mean()
	rets = test['close']/ test['close'].shift(1) - 1
	
	#print(test)
	#print(rolling_mean, rets) #calculate rolling mean
	
	
#Resample Dates
#print(erikresult.info())
#print(erikresult.index.time,erikresult.index.day[0],erikresult.index.hour,erikresult.index.minute)

#print(myresult.get('SPY').get('date'))

#GET just time, or just date:
#print(spy_date.date(),spy_date.time(),spy_date.day,spy_date.month,spy_date.year,spy_date.hour,spy_date.minute)

for k in myresult.get('SPY').get('high').keys():   # The order of the k's is not defined
	#print(k)
	
	#if k >= ago and k < lookback: 
		#print("Got key", k, "which maps to value", myresult.get('SPY').get('date')[k])


#Get average of close prices over last 10 days for 1 stock	
for i in myresult.get('SPY').get('date').keys():   # The order of the k's is not defined
	if i < 10:  #Think of this as lookback period where you can sum, max, min values over certain time periods
		closelist['SPY'].append(myresult.get('SPY').get('close')[i])
		
	avg = sum(closelist['SPY'])/len(closelist['SPY'])			
	#print(closelist,avg)



#Get high over last 10 days for multiple stocks
for t in ticker_list:
	for j in myresult.get(t).get('high').keys():   # The order of the k's is not defined
		if j < lookback:  #Think of this as lookback period where you can sum, max, min values over certain time periods
			highlist[t].append(myresult.get(t).get('high')[j])
		per_high = max(highlist[t])	
		
	for j in myresult.get(t).get('low').keys():   # The order of the k's is not defined
		if j < lookback:  #Think of this as lookback period where you can sum, max, min values over certain time periods
			lowlist[t].append(myresult.get(t).get('high')[j])
		per_low = min(lowlist[t])				
	
	for j in myresult.get(t).get('date').keys():   	
		if j < lookback:  
			datelist[t].append(myresult.get(t).get('date')[j])


#SPY_closelog = np.log(myresult.get('SPY').get('close')).diff()
#print(SPY_closelog)
		
	#print(t,datelist[t][0].date(),datelist[t][0].time(),lowlist[t],per_high,per_low)
"""

#*****************************************************************************************************************
"""
#Plot to see logarithmic return (eye test for stationarity)

pd.plotting.register_matplotlib_converters()
plt.plot(resid)
plt.ylabel('Log Returns')
plt.show()

mpf.plot(ohlc,type='candle',
			style='charles',
			#mav=(20),
			volume=True,
			figratio=(15,10),
			figscale=0.9,
			title='{} Prices from {} to {}'.format(t,start_date,end_date),
			ylabel='Price',
			ylabel_lower='Volume')
"""


