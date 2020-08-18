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


class Resistance(Indicator):

	lines = ('resistance',)
	
	params =(
			('period',10),
			('min_touches',2),
			('tol_perc',3),
			('bounce_perc',5),
			)
	plotinfo = dict(subplot=False)
	plotlines = dict(resistance=dict(_name='Resistance', ls='--',_plotvalue=False))
	

	def __init__(self):
		self.addminperiod(self.p.period)
		#Alias to shorten code lines for readibility
		self.h = self.data.high
	
	
	def next(self):
		#Test resistance by iterating through data to check for touches delimited by bounces
		self.touchdown = 0
		awaiting_bounce = False
		
		if len(self.h)>self.p.period *2:  #Ensure minimal amount of data is loaded
			for x in range(1,self.p.period+1):
				self.maxima = max(self.h.get(ago=-x,size=self.p.period))
				self.minima = min(self.h.get(ago=-x,size=self.p.period))
				#print(-x,h.get(size=20),h.get(ago=-x,size=self.p.period),self.maxima)
				
				#Calculate distance between max and min (total price movement)
				move_range = self.maxima - self.minima
				
				#Calculate bounce distance and allowable margin of error for proximity to support/resistance 
				move_allowance = move_range * (self.p.tol_perc/100)
				bounce_distance = move_range * (self.p.bounce_perc/100)
				
				if abs(self.maxima - self.h.get(size=self.p.period)[-x]) < move_allowance and not awaiting_bounce:
					self.touchdown = self.touchdown + 1
					awaiting_bounce = True
				
				elif abs(self.maxima - self.h.get(size=self.p.period)[-x]) > bounce_distance:
					awaiting_bounce = False
				
			if self.touchdown >= self.p.min_touches:
				self.lines.resistance[0] = self.maxima
			
			elif self.lines.resistance[-1] != 0:
				self.lines.resistance[0] = self.lines.resistance[-1]
			
			else: self.lines.resistance[0]=0	

	 
	def once(self, start, end):
		resistance_array = self.lines.resistance.array
		
		for i in range(start, end):
			if self.touchdown >= self.p.min_touches:
				resistance_array[i] = self.maxima
