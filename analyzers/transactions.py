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


import collections

import backtrader as bt
from backtrader import Order, Position


class Transactions(bt.Analyzer):
    '''This analyzer reports the transactions occurred with each an every data in
    the system

    It looks at the order execution bits to create a ``Position`` starting from
    0 during each ``next`` cycle.

    The result is used during next to record the transactions

    Params:

      - headers (default: ``True``)

        Add an initial key to the dictionary holding the results with the names
        of the datas

        This analyzer was modeled to facilitate the integration with
        ``pyfolio`` and the header names are taken from the samples used for
        it::

          'date', 'amount', 'price', 'sid', 'symbol', 'value'

    Methods:

      - get_analysis

        Returns a dictionary with returns as values and the datetime points for
        each return as keys
    '''
    params = (
        ('headers', False),
        ('_pfheaders', ('date', 'amount', 'price', 'sid', 'symbol', 'value')),
    )

    def start(self):
        super(Transactions, self).start()
        if self.p.headers:
            self.rets[self.p._pfheaders[0]] = [list(self.p._pfheaders[1:])]
        self.direction_dict = dict()  #Erik added code to create dictionary that holds 'Buy' or 'Sell' order status 
        self.pnl_dict = dict()
        self._positions = collections.defaultdict(Position)
        self._idnames = list(enumerate(self.strategy.getdatanames()))

    def notify_order(self, order):
        # An order could have several partial executions per cycle (unlikely
        # but possible) and therefore: collect each new execution notification
        # and let the work for next

        # We use a fresh Position object for each round to get summary of what
        # the execution bits have done in that round
        if order.status not in [Order.Partial, Order.Completed]:
            return  # It's not an execution
        
        #Erik added code
        if order.isbuy():
            direction = 'BUY'
            self.direction_dict[order.data._name] = direction
        else:
            direction = 'SELL'
            self.direction_dict[order.data._name] = direction
		
        pos = self._positions[order.data._name]

        for exbit in order.executed.iterpending():
			
            if exbit is None:
                break  # end of pending reached

            pos.update(exbit.size, exbit.price)

    def notify_trade(self, trade):
         #Erik added code
        if trade.isclosed:
            self.pnl_dict[trade.data._name] = trade.pnl
        else:
            self.pnl_dict[trade.data._name] = 'None'
			
    def next(self):
        # super(Transactions, self).next()  # let dtkey update
        o = self.data.open	#current open
        h = self.data.high  # current high
        l = self.data.low  # current low
        c = self.data.close  # current close
        
        entries = []
        for i, dname in self._idnames:
			
            direction = self.direction_dict.get(dname)  #Erik added code to fetch buy/sell status from dictionary
            pnl = self.pnl_dict.get(dname, None)
            pos = self._positions.get(dname, None)
            if pos is not None:
                size, price = pos.size, pos.price
                if size:
                    entries.append([dname, direction, size, price, i,(-size * price), pnl, None])
                    #entries.append([dname, size, price, i, -size * price,o[0],h[0],l[0],c[0]])  #Erik note - if you want to include additional transactional data

        if entries:
            self.rets[self.strategy.datetime.datetime()] = entries

        self._positions.clear()
