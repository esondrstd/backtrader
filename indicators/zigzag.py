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
"""
if you're attempting to use this live it obviously looks ahead one bar into the future which isn't allowed. 
If you're using it for preloaded historical data in a batch it works for identifying the exact turning point
rather than one bar late. But for live data you'll need to move it one bar back by subtracting one from every
bar reference as below. I added a couple of del lines just to prompt a bit of memory cleanup but they are
entirely optional.
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import copy
import backtrader as bt


class zigzag(bt.Indicator):

	plotinfo = dict(subplot=False, zigzag=dict(_name='zigzag', color='darkblue', ls='--', _skipnan=True), )

	plotlines = dict(
		zigzag_peak=dict(marker='v', markersize=7.0, color='red', fillstyle='full', ls=''),
		zigzag_valley=dict(marker='^', markersize=7.0, color='red', fillstyle='full', ls=''),
		#zigzag=dict(_name='zigzag', color='red', ls='--', _skipnan=True),
	)

	params = (
	('up_retrace', 0.02),  # 0.02
	('dn_retrace', 0.02),  # 0.02
	('plotdistance', 0.03),  # distance to plot arrows (alters high/low indicator lines but not zigzag line)
	)
	
	lines = ('zigzag',
			 'zigzag_peak',
			 'zigzag_valley',)

	
	def __init__(self):
		
		cpy = copy.copy(self.data) #Make a copy
		tmp = bt.If(self.data(0) == self.data(-1), cpy(-1) + 0.000001, self.data(0))  #Peak shift
		self.lines.zigzag_peak = bt.If(bt.And(tmp(-1)>tmp(-2), tmp(-1)>tmp(0)), self.data(-1), float('nan'))
		cpy = copy.copy(self.data)
		tmp = bt.If(self.data(0) == self.data(-1), cpy(-1) - 0.000001, self.data(0))  #Valley shift
		self.lines.zigzag_valley = bt.If(bt.And(tmp(-1) < tmp(-2), tmp(-1) < tmp(0)), self.data(-1), float('nan'))
		self.lines.zigzag = bt.If(self.zigzag_peak, self.zigzag_peak, bt.If(self.zigzag_valley, self.zigzag_valley, float('nan')))
