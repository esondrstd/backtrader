
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime
from backtrader.feed import DataBase
from backtrader import date2num
from sqlalchemy import *

#Make sure SQL database table is indexed for increased speed (do this in mysql database directly)
class MySQLData(DataBase):
    params = (
        ('dbHost', None),
        ('dbUser', None),
        ('dbPWD', None),
        ('dbName', None),
        ('table', None),
        ('symbol', None),
        ('fromdate', None),
        ('todate', None),
        ('sessonstart',None),
        ('sessionend',None),
        )
								
    def __init__(self):
        self.engine = create_engine('mysql+pymysql://'+self.p.dbUser+':'+ self.p.dbPWD +'@'+ self.p.dbHost +'/'+ self.p.dbName +'?charset=utf8mb4', echo=False)
        
        
    def start(self):
        self.conn = self.engine.connect()
        self.result = self.conn.execute("SELECT date,open,high,low,close,volume FROM {} WHERE ticker = '{}' AND date >= '{}' and date <='{}' AND DATE_FORMAT(date,'{}') >= '{}' and DATE_FORMAT(date,'{}') <= '{}' ORDER BY date ASC".format(self.p.table,self.p.symbol,self.p.fromdate.strftime("%Y-%m-%d"),self.p.todate.strftime("%Y-%m-%d"),"%%H:%%i",self.p.sessionstart.strftime("%H:%M"),"%%H:%%i",self.p.sessionend.strftime("%H:%M")))                 
        #self.result = self.conn.execute(f'SELECT date,open,high,low,close,volume FROM {self.p.table} WHERE ticker = "{self.p.symbol}" AND date >= "{self.p.fromdate}" and date <="{self.p.todate}" and DATE_FORMAT(date, \'%%H:%%i\') >= "{self.p.sessionstart.strftime("%%H:%%i")}" and DATE_FORMAT(date, \'%%H:%%i\') <= "{self.p.sessionend.strftime("%%H:%%i")}" ORDER BY date ASC')                 
        print(f'Data AVAILABLE - Collecting data for {self.p.symbol} from mySQL database')
        """
        self.startdate = self.conn.execute(f"SELECT date FROM {self.p.table} WHERE ticker = '{self.p.symbol}' LIMIT 1")
        self.startdateid = self.startdate.fetchone()[0]
        if self.p.fromdate < self.startdateid:
            print(f"{self.p.symbol} - Data NOT AVAILABLE during this timeframe - RESTART PROGRAM.  Database date starts at '{self.startdateid}'") 
        else:
            print(f'Data AVAILABLE - Collecting data for {self.p.symbol} from mySQL database')
        """
        	
    def stop(self):
        self.conn.close()
        self.engine.dispose()

    def _load(self):
        self.one_row = self.result.fetchone()
   
        if self.one_row is None:
            self.stop()  
            return False
            
        else:
            self.lines.datetime[0] = date2num(self.one_row[0])
            self.lines.open[0] = self.one_row[1]
            self.lines.high[0] = self.one_row[2]
            self.lines.low[0] = self.one_row[3]
            self.lines.close[0] = self.one_row[4]
            self.lines.volume[0] = self.one_row[5]
            return True
 

        
