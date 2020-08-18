import backtrader as bt

class HammerCandles(bt.Indicator):
    '''
    Thor is a pin candle reversal indicator that tries to catch swings and
    ride the retracement down.
    '''
    lines = ('signal','bull_hammer', 'bear_hammer')
    params = (
        ('rev_wick_ratio', 0.667), #ratio of the long wick
    )
 
    plotinfo = dict(
        subplot=False,
        plotlinelabels=True
    )
    plotlines = dict(
        bull_hammer=dict(marker='^', markersize=8.0, color='blue', fillstyle='full', ls='',
        ),
        bear_hammer=dict(marker='v', markersize=8.0, color='orange', fillstyle='full', ls='',
        ),
        signal=dict(_plotskip=True)
    )
 
    def __init__(self):
        self.myrange =  self.data.high - self.data.low
        self.upper_wick_green =  self.data.high - self.data.close
        self.lower_wick_green = self.data.open - self.data.low
        self.upper_wick_red = self.data.high - self.data.open
        self.lower_wick_red = self.data.close - self.data.low
        
    
    def next(self):
 
        # Calcualte ratios for green candles or open/close are the same value
        if self.data.open[0] <= self.data.close[0]:
			
            try:
                upper_ratio = self.upper_wick_green[0]/self.myrange[0]
            except ZeroDivisionError:
                upper_ratio = 0
             
            try:
                lower_ratio = self.lower_wick_green[0]/self.myrange[0]
            except ZeroDivisionError:
                lower_ratio = 0
                        
        # Repeat for a red candle
        elif self.data.open[0] > self.data.close[0]:
 
            try:
                upper_ratio = self.upper_wick_red[0]/self.myrange[0]
            except ZeroDivisionError:
                upper_ratio = 0
 
            try:
                lower_ratio = self.lower_wick_red[0]/self.myrange[0]  
            except ZeroDivisionError:
                lower_ratio = 0

 
        if upper_ratio >= self.p.rev_wick_ratio and self.data.close[0]<self.data.open[0]:
            self.lines.bear_hammer[0] = self.data.high[0]*1.0005
            self.lines.signal[0] = -1
 
        elif lower_ratio >= self.p.rev_wick_ratio and self.data.close[0]>self.data.open[0]:
            self.lines.bull_hammer[0] = self.data.low[0]*.9995
            self.lines.signal[0] = 1
 
        else:
            self.lines.signal[0] = 0
    
