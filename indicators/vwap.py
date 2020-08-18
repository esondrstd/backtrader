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

class vwap(Indicator):

	params =(
			)
	
	lines = ('vwap','cumtypprice','cumvol')
	
	plotinfo = dict(subplot=False)
	plotlines = dict(vwap=dict(_name='VWAP', ls='dotted',color='black'),)
	
	def __init__(self):
		# Aliases to avoid long lines
		self.c = self.data.close
		self.h = self.data.high
		self.l = self.data.low
		self.v = self.data.volume
		self.vwap = self.lines.vwap

	"""
	def nextstart(self):
		# We need to use next start to provide the initial value. This is because
		# we do not have a previous value for the first calcuation. These are
		# known as seed values.
		hour = self.data.datetime.datetime().hour
		minute = self.data.datetime.datetime().minute
		
		if hour == 8 and minute == 30:	
			self.cumtypprice[0] = self.cumtypprice[-1]+((self.c[0]+self.h[0]+self.l[0])/3)*self.v[0]
			self.cumvol[0] = self.v[0]

			if self.cumvol[0] !=0:
				self.vwap[0] = self.cumtypprice[0]/self.cumvol[0]
			else:
				self.vwap[0] = 0
		
		self.cumtypprice[0] = self.cumtypprice[-1]+((self.c[0]+self.h[0]+self.l[0])/3)*self.v[0]
		self.cumvol[0]= self.v[0]

		if self.cumvol[0] !=0:
			self.vwap[0] = self.cumtypprice[0]/self.cumvol[0]
		else:
			self.vwap[0] = 0
	"""	
	def next(self):
		
		hour = self.data.datetime.datetime().hour
		minute = self.data.datetime.datetime().minute
		
		self.cumtypprice[0]=self.cumtypprice[-1]+((self.c[0]+self.h[0]+self.l[0])/3)*self.v[0]
		self.cumvol[0]=self.cumvol[-1]+self.v[0]
		
		if self.cumvol[0] !=0:
			self.vwap[0] = self.cumtypprice[0]/self.cumvol[0]
		else:
			self.vwap[0] = 0
		
		if hour == 8 and minute == 30:	
			self.cumtypprice[0]= ((self.c[0]+self.h[0]+self.l[0])/3)*self.v[0]
			self.cumvol[0] = self.v[0]
			if self.cumvol[0] !=0:
				self.vwap[0] = self.cumtypprice[0]/self.cumvol[0]
			else:
				self.vwap[0] = 0
