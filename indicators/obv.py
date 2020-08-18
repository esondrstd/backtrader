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

class obv(Indicator):

	params =(
			('period',10),
			)
	
	lines = ('obv',)
	
	plotlines = dict(
		obv=dict(
			color='purple',
			alpha=0.50,
			_plotvalue=False,
            _plotvaluetag=False,
			)
		)

	def __init__(self):
		self.addminperiod(self.p.period)
		# Aliases to avoid long lines
		self.c = self.data.close
		self.v = self.data.volume
		self.obv = self.lines.obv

	def nextstart(self):
		# We need to use next start to provide the initial value. This is because
		# we do not have a previous value for the first calcuation. These are
		# known as seed values.
		
		if self.c[0] > self.c[-1]:
			self.obv[0] = self.v[0]

		elif self.c[0] < self.c[-1]:
			self.obv[0] = -self.v[0]
		else:
			self.obv[0] = 0
		
	
	def next(self):
		#hourmin = self.data.datetime.datetime(ago=0).strftime('%H:%M')
		hour = self.data.datetime.datetime(ago=0).hour
		minute = self.data.datetime.datetime(ago=0).minute
		
		# Aliases to avoid long lines
		#c = self.data.close
		#v = self.data.volume
		#self.obv = self.lines.obv

		if hour == 8 and minute == 30:
			self.obv[0] = self.v[0]	
			
		elif self.c[0] > self.c[-1]:
			self.obv[0] = self.obv[-1] + self.v[0]
		elif self.c[0] < self.c[-1]:
			self.obv[0] = self.obv[-1] - self.v[0]
		else:
			self.obv[0] = self.obv[-1]
		
