import backtrader as bt
from . import Indicator, Slope

class EngulfingCandles(bt.Indicator):
	'''
	Calculates bullish and bearish engulfing candles
	'''
	lines = ('signal','bull_engulfing','bear_engulfing',)
	params = (
			('slope_period',5),
			)

	plotinfo = dict(
		subplot=False,
		plotlinelabels=True
	)
	plotlines = dict(
		signal=dict(_plotskip=True)
	)

	  
	plotlines = dict(
		bull_engulfing=dict(marker='^', markersize=8.0, color='black', fillstyle='full', ls='',
		),
		bear_engulfing=dict(marker='v', markersize=8.0, color='yellow', fillstyle='full', ls='',
		),
		signal=dict(_plotskip=True)
	)

	def __init__(self):
		pass


	def next(self):

		bull_body_signal = self.data.close[0] > self.data.high[-1] and self.data.open[0]<self.data.low[-1] 
		bear_body_signal = self.data.open[0] > self.data.high[-1] and self.data.close[0]<self.data.low[-1]
		
		if bull_body_signal and self.data.close[-1] < self.data.open[-1]:
			self.lines.bull_engulfing[0] = self.data.high[0]*(1.0005)
			self.lines.signal[0] = 1
			
		elif bear_body_signal and self.data.close[-1] > self.data.open[-1]:
			self.lines.bear_engulfing[0] = self.data.low[0]*.9995
			self.lines.signal[0] = -1
			
		else:
			self.lines.signal[0] = 0
		
