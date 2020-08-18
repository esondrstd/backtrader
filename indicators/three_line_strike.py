import backtrader as bt
from . import Indicator, Slope

class three_line_strike(bt.Indicator):
	'''
	Calculates bullish and bearish three line strike candles
	'''
	lines = ('signal','bull_strike','bear_strike',)
	params = (
			('period',5),
			('body_ratio', .5),
			)

	plotinfo = dict(
		subplot=False,
		plotlinelabels=True
	)
	plotlines = dict(
		signal=dict(_plotskip=True)
	)

	  
	plotlines = dict(
		bull_strike=dict(marker='^', markersize=8.0, color='purple', fillstyle='full', ls='',
		),
		bear_strike=dict(marker='v', markersize=8.0, color='gray', fillstyle='full', ls='',
		),
		signal=dict(_plotskip=True)
	)

	def __init__(self):
		self.addminperiod(self.p.period)


	def next(self):

		o = self.data.open.get(size=self.p.period)
		h = self.data.high.get(size=self.p.period)
		l = self.data.low.get(size=self.p.period)
		c = self.data.close.get(size=self.p.period)
		
		#Ensure body width represents 2/3 of candle max/min range (body_ratio at .667)
		
		try:
			bar_body_candle1 = abs(c[-3] - o[-3]) / (h[-3]-l[-3])
			bar_body_candle2 = abs(c[-2] - o[-2]) / (h[-2]-l[-2])
			bar_body_candle3 = abs(c[-1] - o[-1]) / (h[-1]-l[-1])	
		except ZeroDivisionError:
			bar_body_candle1 = 0
			bar_body_candle2 = 0
			bar_body_candle3 = 0
		
		bar_body_signal = bar_body_candle1 >= self.p.body_ratio and bar_body_candle2 >= self.p.body_ratio and bar_body_candle3 >= self.p.body_ratio
		
		bear_candle1 = c[-3] >= o[-3]
		bear_candle2 = c[-2] >= h[-3] and c[-2] >= o[-2]
		bear_candle3 = c[-1] >= h[-2] and c[-1] >= o[-1]
		bear_candle4 = o[0] >= c[-1] and c[0] <= o[-3]
		bear_candles = bear_candle1 and bear_candle2 and bear_candle3 and bear_candle4
		
		bull_candle1 = o[-3] <= c[-3]
		bull_candle2 = o[-2] <= l[-3] and o[-2] <= c [-2]
		bull_candle3 = o[-1] <= l[-2] and o[-1] <= c [-1]
		bull_candle4 = o[0] <= c[-1] and c[0] >= o[-3]
		bull_candles = bull_candle1 and bull_candle2 and bull_candle3 and bull_candle4  
		
		
		if bull_candles and bar_body_signal:
			self.lines.bull_strike[0] = h[0]*(1.0005)
			self.lines.signal[0] = 1
		
		if bear_candles and bar_body_signal:
			self.lines.bear_strike[0] = l[0]*(.9995)
			self.lines.signal[0] = -1
		
		else:
			self.lines.signal[0] = 0
		
