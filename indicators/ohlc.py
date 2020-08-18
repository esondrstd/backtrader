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

from . import Indicator, CmpEx
from datetime import datetime

class ohlc(Indicator):

	params =(
			('period',3),
			)
	
	lines = ('o','h','l','c','v',)
	
	plotinfo = dict(subplot=False)
	plotlines = dict(vwap=dict(_name='avgvolume', ls='dashdot'),)
	
	def __init__(self):
		self.addminperiod(self.p.period)

	def next(self):			
		self.o = self.data.open.get(size=self.p.period)
		self.h = self.data.high.get(size=self.p.period)
		self.l = self.data.low.get(size=self.p.period)
		self.c = self.data.close.get(size=self.p.period)
		self.v = self.data.volume.get(size=self.p.period)
		
		self.lines.o[0] = round(self.o[0],3)
		self.lines.h[0] = round(self.h[0],3)
		self.lines.l[0] = round(self.l[0],3)
		self.lines.c[0] = round(self.c[0],3)
		self.lines.v[0] = round(self.v[0],3)
		
	def once(self, start, end):
		o_array = self.lines.o.array
		h_array = self.lines.h.array
		l_array = self.lines.l.array
		c_array = self.lines.c.array
		v_array = self.lines.v.array

		for i in xrange(start, end):
			o_array[i] = self.o[0]
			h_array[i] = self.h[0]
			l_array[i] = self.l[0]
			c_array[i] = self.c[0]
			v_array[i] = self.v[0]
		
	
