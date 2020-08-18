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

import sys
import backtrader
from backtrader import Analyzer
from backtrader.utils import AutoOrderedDict, AutoDict
from backtrader.utils.py3 import MAXINT

class AcctStats(Analyzer):
    def create_analysis(self):
		#self.rets is backtrader analyzer dictionary - need to use to print results.  self.rets.total.closed means "total" will print, followed by sub heading "closed"
        self.rets = AutoOrderedDict()

        self.rets.expectancy_dollars = 0
        self.rets.winratio = 0
        self.rets.lossratio = 0 
        self.rets.pnl.gross.total = 0
        self.rets.pnl.net.total = 0
        self.rets.total.total = 0
        self.rets.total.open = 0
        self.rets.total.closed = 0
        self.rets.won.pnl.average = 0
        self.rets.lost.pnl.average = 0
        self.rets.won.total = 0
        self.rets.lost.total = 0
		
    def stop(self):
		#used to add final calculations (to values in rets dictionary) after all counts have iterated
        super(AcctStats, self).stop()
                
        if self.rets.total.closed >0:
            self.rets.winratio = round(self.rets.won.total/self.rets.total.closed,3)
            self.rets.lossratio = round(self.rets.lost.total/self.rets.total.closed,3)
            self.rets.expectancy_dollars = round((self.rets.winratio * self.rets.won.pnl.average) + (self.rets.lossratio * self.rets.lost.pnl.average),3)
		
		
    def notify_trade(self, trade):
  
        if trade.justopened:
            # Trade just opened
            self.rets.total.total += 1
            self.rets.total.open += 1
            #self.rets.expectancy +=5
            
        elif trade.status == trade.Closed:
            self.rets = self.rets
            
            self.rets.total.open -= 1
            self.rets.total.closed += 1

            self.res = AutoDict()

            # Trade just closed
            self.won = self.res.mywon = int(trade.pnlcomm > 0.0)
            
            won = self.res.won = int(trade.pnlcomm > 0.0)
            lost = self.res.lost = int(not won)
            tlong = self.res.tlong = trade.long
            tshort = self.res.tshort = not trade.long
            
            trpnl = self.rets.pnl
            trpnl.gross.total += trade.pnl
            trpnl.gross.average = self.rets.pnl.gross.total / self.rets.total.closed
            trpnl.net.total += trade.pnlcomm
            trpnl.net.average = self.rets.pnl.net.total / self.rets.total.closed
            
  
            # Won/Lost statistics
            for wlname in ['won', 'lost']:
                wl = self.res[wlname]
                trwl = self.rets[wlname]
                
                trwl.total += wl  # won.total / lost.total

                trwlpnl = trwl.pnl
                pnlcomm = trade.pnlcomm * wl

                trwlpnl.total += pnlcomm
                trwlpnl.average = trwlpnl.total / (trwl.total or 1.0)

                wm = trwlpnl.max or 0.0
                func = max if wlname == 'won' else min
                trwlpnl.max = func(wm, pnlcomm)
			
			 # Long/Short statistics
            for tname in ['long', 'short']:
                trls = self.rets[tname]
                ls = self.res['t' + tname]

                trls.total += ls  # long.total / short.total
                trls.pnl.total += trade.pnlcomm * ls
                trls.pnl.average = trls.pnl.total / (trls.total or 1.0)

                for wlname in ['won', 'lost']:
                    wl = self.res[wlname]
                    pnlcomm = trade.pnlcomm * wl * ls

                    trls[wlname] += wl * ls  # long.won / short.won

                    trls.pnl[wlname].total += pnlcomm
                    trls.pnl[wlname].average = \
                        trls.pnl[wlname].total / (trls[wlname] or 1.0)

                    wm = trls.pnl[wlname].max or 0.0
                    func = max if wlname == 'won' else min
                    trls.pnl[wlname].max = func(wm, pnlcomm)
