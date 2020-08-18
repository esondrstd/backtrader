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

from . import Indicator, ATR, math
from datetime import datetime

class atr_stop(Indicator):

	params =(
			('atrdist',2),
			('dollars_risked',20000),
			('dollars_per_trade',300),
			('live',False),
			)
	
	lines = ('long_stop','short_stop','size','pos_cost')
	plotinfo = dict(subplot=False)
	
	def __init__(self):

		self.c = self.data0.close
		self.atr = self.data1.atr
		self.stop_dist = self.atr * self.p.atrdist
		self.long_stop = self.c - self.stop_dist
		self.short_stop = self.c + self.stop_dist
		self.maxsize = self.p.dollars_risked/self.c
		self.atrsize = self.p.dollars_per_trade/self.stop_dist
		tolerance = 2
		self.rounding = float(10**tolerance)

		if not self.p.live==True:
			self.lines.long_stop = self.long_stop
			self.lines.short_stop = self.short_stop
		
		self.size = self.maxsize
		#self.size = self.atrsize
		self.lines.size = self.size
		self.lines.pos_cost = self.size * self.c

	
	def next(self):

		if self.p.live==True:
			self.lines.long_stop[0] = self.my_round(self.long_stop[0])
			self.lines.short_stop[0] = self.my_round(self.short_stop[0])
	
	
	#*****CRITICAL FUNCTION FOR LIVE TRADING - NEED TO ENSURE PRICE IS ROUNDED TO MULTIPLE OF $.005 FOR INTERACTIVE BROKERS
	def my_round(self,x):
		return int(x * self.rounding + 0.05)/self.rounding
