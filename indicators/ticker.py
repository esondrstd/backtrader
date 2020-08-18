from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from . import Indicator

class ticker(Indicator):
	lines = ('spy',)
	
	plotinfo = dict(subplot=True)
	plotlines = dict(spy=dict(_name='SPY', ls='solid',color='green'),)

	def __init__(self):
		self.lines.spy = self.data1
