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

import backtrader as bt
from .. import Observer
from backtrader import Order, Trade


class OrderObserver(bt.observer.Observer):

    lines = ('createdP','executedP','executedV','open','high','low','close')
    
    plotinfo = dict(plot=False, subplot=False, plotlinelabels=False)

    plotlines = dict(
        #created=dict(marker='*', markersize=8.0, color='lime', fillstyle='full'),
        #expired=dict(marker='s', markersize=8.0, color='red', fillstyle='full'),
        #createdP=dict(marker='s', markersize=8.0, color='red', fillstyle='full'),
        #executedP=dict(marker='s', markersize=8.0, color='red', fillstyle='full'),
		)
    def __init__(self):
        self.pnl_dict = dict()
        for i,d in enumerate(self.datas):
            self.pnl_dict[d._name] = dict
            self.pnl_dict[d._name] = None
		
    def notify_trade(self, trade):
         #Erik added code
        if trade.isclosed:
            self.pnl_dict[trade.data._name] = trade.pnl

    def next(self):
        results = []
        myresults = []  #Erik added to create dictionary to store value referenced by create and executed lines
        
        pnl = self.pnl_dict.get(self.data._name)
        
        for order in self._owner._orderspending:
            date = self.data.datetime.datetime()
            
            o = self.data.open	#current open
            h = self.data.high  # current high
            l = self.data.low  # current low
            c = self.data.close  # current close
            
            if order.isbuy():
                direction = 'BUY'

            else:
                direction = 'SELL'
            
            if order.status in [bt.Order.Completed]:
                content = '''ORDER: %s %s %s CreateP: %.2f Size:%s ExecuteP: %.2f Cost: %.2f O: %.2f H: %.2f L: %.2f C: %.2f
                          ''' % (  date,
                                   direction,
                                   order.info['name'],
                                   order.created.price,
                                   order.created.size,
                                   order.executed.price,
                                   order.executed.value,
                                   o[0],
                                   h[0],
                                   l[0],
                                   c[0],
                                )
                                   
                content = content.replace('\n','')
                results.append(content)
                print(content)
                
                #Erik added code to create dictionary so line createdP and executedP line outputs can be seen on last columns of csv file
                #Cannot add strings or date to dictionary           
                myresults.append([
                                  order.created.price,
                                  order.executed.price,
                                  order.executed.value,
                                  o[0],
                                  h[0],
                                  l[0],
                                  c[0],
                                  pnl,
                                  ])
                                  
            #Erik added code to assign line to values in dictionary just created
            if len(myresults)>0:
                self.lines.createdP[0] = myresults[0][0]
                self.lines.executedP[0] = myresults[0][1]
                self.lines.executedV[0] = myresults[0][2]
                self.lines.open[0] = myresults[0][3]
                self.lines.high[0] = myresults[0][4]
                self.lines.low[0] = myresults[0][5]
                self.lines.close[0] = myresults[0][6]
