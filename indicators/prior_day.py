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

from . import Indicator
from datetime import datetime

class priorday(Indicator):
	
	params =(
			('period',79),
			)
	
	lines = ('prior_high','prior_low','prior_close','prior_open')
	
	def __init__(self):
		self.addminperiod(self.p.period)
		self.prior_high = 0
		self.prior_low = 0
		self.prior_close = 0
		self.prior_open = 0
		self.h = self.data.high(self.p.period)
		self.l = self.data.low(self.p.period)
	
	
	def next(self):
	
		hour = self.data.datetime.datetime().hour
		minute = self.data.datetime.datetime().minute
		
		if hour == 8 and minute == 30:
			self.prior_high = max(self.h)
			self.prior_low = min(self.l)
			self.prior_close = self.data.close[-1]
			self.prior_open = self.data.open[-79]

		self.lines.prior_high[0] = self.prior_high
		self.lines.prior_low[0] = self.prior_low
		self.lines.prior_close[0] = self.prior_close
		self.lines.prior_open[0] = self.prior_open
