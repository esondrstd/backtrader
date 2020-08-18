
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
        self.conn = self.engine.connect()
        self.result = self.conn.execute(f'SELECT date,open,high,low,close,volume FROM {self.p.table} WHERE ticker = "{self.p.symbol}" AND date >= "{self.p.fromdate.strftime("%Y-%m-%d")}" and date <="{self.p.todate.strftime("%Y-%m-%d")}" ORDER BY date ASC')                 
        
        #self.result = self.conn.execute(f'SELECT date,open,high,low,close,volume FROM {self.p.table} WHERE ticker = "{self.p.symbol}" AND date >= "{self.p.fromdate.strftime("%Y-%m-%d")}" and date <="{self.p.todate.strftime("%Y-%m-%d")}" ORDER BY date ASC')                 
        print(f'Data AVAILABLE - Collecting data for {self.p.symbol} from mySQL database')
        
        myresult = self.result.fetchall()
        print(myresult)
		#Get dictionary from SQL results
        self.mytuple = ()
        mylist = [[] for _ in range(len(myresult))]
		
        rowcount=0
        for rowproxy in myresult:
            count=0
	
            for i in rowproxy:
                if count != 0:
                    mylist[rowcount].append(i)

                if count == 0:
                    dateset = date2num(i)
                    mylist[rowcount].append(dateset)
		
                count += 1
            rowcount +=1
		
        self.mytuple = tuple(mylist)
        self.counter=0

    def stop(self):
        self.conn.close()
        self.engine.dispose()

  
    def _load(self):
        print("PRINT IT",self.mytuple[0])
        if self.mytuple[self.counter] is None:
            self.stop()  
            return False
            
        else:
            self.one_row = self.mytuple[self.counter]
			
            self.lines.datetime[0] = self.one_row[0]
            self.lines.open[0] = self.one_row[1]
            self.lines.high[0] = self.one_row[2]
            self.lines.low[0] = self.one_row[3]
            self.lines.close[0] = self.one_row[4]
            self.lines.volume[0] = self.one_row[5]
            self.counter += 1
            return True
            
    
           
           

            
 

        
