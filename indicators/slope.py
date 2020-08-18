from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from . import Indicator
#import math
#from scipy.stats import linregress

class Slope(Indicator):
	
	lines = ('slope',)
	
	params = (
		('period', 5),  # distance to previous data point
	)
	
	plotinfo = dict(subplot=True)
	plotlines = dict(slope=dict(_name='slope', ls='solid',color='purple'),)

	def __init__(self):
		self.addminperiod(self.p.period)
		self.x1 = 1
		self.x2 = self.p.period
		self.y1 = self.data(-self.p.period)
		self.y2 = self.data(-1)
		self.lines.slope = (self.y2-self.y1)/(self.x2-self.x1)
		
	"""
	def next(self):
		data_list = self.data.get(size=self.p.period)

		y1 = data_list[-self.p.period]
		y2 = data_list[-1] 
		
		self.lines.slope[0] = (y2-y1)/(self.x2-self.x1)

		#myindx = list(range(self.p.period))
		#self.lines.slope[0] = linregress(myindx,data_list).slope
	"""
