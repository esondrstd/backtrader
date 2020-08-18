#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016, 2017 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from . import Indicator, CmpEx, Highest, Lowest
from datetime import datetime

class gap(Indicator):

	params =(
			('period',5),
			('b_time','08:55'),
			)
	
	lines = ('gap','rng_high','rng_low',)
	
	plotinfo = dict(subplot=False)
	plotlines = dict(vwap=dict(_name='GAP', ls='dotted'),)
	
	
	def _plotlabel(self):
		plabels = [self.p.period]  #Erik edited to just plot slow moving avg label
		return plabels

	def __init__(self):
		self.addminperiod(self.p.period)
		#self.rng_high = 10000
		#self.rng_low = 0
		self.today_open = 0
		self.prior_close = 1
		self.h = self.data.high(self.p.period)
		self.l = self.data.low(self.p.period)


	def next(self):

		hour = self.data.datetime.datetime().hour
		minute = self.data.datetime.datetime().minute
		
		if hour == 8 and minute == 30:	
			self.today_open = self.data.open[0]
			self.prior_close = self.data.close[-1]
		
		try: 
			self.gap = ((self.today_open-self.prior_close)/self.prior_close)*100
			self.lines.gap[0] = self.gap
		except ZeroDivisionError:
			self.gap = 0
		
		"""
		if hour == 8 and minute == 55:
			self.rng_high = max(self.h)
			self.rng_low = min(self.l)
		
		self.lines.rng_high[0] = self.rng_high
		self.lines.rng_low[0] = self.rng_low
		"""
		
		
		
	
