
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime
from backtrader.feed import DataBase
from backtrader import date2num
from sqlalchemy import *

#Make sure SQL database table is indexed for increased speed (do this in mysql database directly)
class MySQLFund(DataBase):
    linesoverride = True
    lines = ('datetime', 'eps_estimate', 'eps_actual', 'eps_diff') 
    
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
        ('datetime',0),
        ('eps_estimate',1),
        ('eps_actual',2),
        ('eps_diff',3),
        )
		
						
    def __init__(self):
        self.engine = create_engine('mysql+pymysql://'+self.p.dbUser+':'+ self.p.dbPWD +'@'+ self.p.dbHost +'/'+ self.p.dbName +'?charset=utf8mb4', echo=False)
		
    def start(self):
        super(MySQLFund, self).start() #Erik added
		
        self.conn = self.engine.connect()
        self.stockdata = self.conn.execute(f"SELECT ticker FROM {self.p.table} WHERE ticker = '{self.p.symbol}' LIMIT 1")
        self.stock_id = self.stockdata.fetchone()[0]
        self.symbol_string = str(self.stock_id)
          
        self.startdate = self.conn.execute(f"SELECT datetime FROM {self.p.table} WHERE ticker = '{self.symbol_string}' LIMIT 1")
        self.startdate_id = self.startdate.fetchone()[0]
        
        self.result = self.conn.execute("SELECT datetime,eps_estimate,eps_actual,eps_diff FROM {} WHERE ticker = '{}' AND datetime >= '{}' and datetime <='{}' AND DATE_FORMAT(datetime,'{}') >= '{}' and DATE_FORMAT(datetime,'{}') <= '{}' ORDER BY datetime ASC".format(self.p.table,self.symbol_string,self.p.fromdate.strftime("%Y-%m-%d"),self.p.todate.strftime("%Y-%m-%d"),"%%H:%%i",self.p.sessionstart.strftime("%H:%M"),"%%H:%%i",self.p.sessionend.strftime("%H:%M")))         
		
        if self.p.fromdate < self.startdate_id:
            print(f"{self.symbol_string} - FUNDAMENTAL Data NOT AVAILABLE during this timeframe - RESTART PROGRAM.  Database date starts at '{self.startdate_id}'")
        else:
            print(f'Data AVAILABLE - Collecting FUNDAMENTAL data for {self.symbol_string} from mySQL database')
			     
        #reset the iterator on each start
        self._rows = iter(self.result)
        init_dict = c.fetchall()
        print(init_dict)
        
    def stop(self):
        self.conn.close()
        self.engine.dispose()

    def _load(self):
        self.one_row = self.result.fetchone()
        print(self.one_row)
        if self.one_row is None:  
            return False
            
        else:
            self.lines.datetime[0] = date2num(self.one_row[0])
            self.lines.eps_estimate[0] = float(self.one_row[1])
            self.lines.eps_actual[0] = float(self.one_row[2])
            self.lines.eps_diff[0] = float(self.one_row[3])
            return True
       
			
        
