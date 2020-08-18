from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from . import Indicator

class close(Indicator):
	
	lines = ('close',)
	
	params = (
		('period', 30),  # distance to previous data point
	)
	
	def __init__(self):
		self.addminperiod(self.p.period)
		#c = self.data(self.params.period)		
		#self.lines.close = c
		
	
	def next(self):
		c = self.data.get(ago=0,size=self.params.period)		
		self.lines.close[0] = c[0]
	
