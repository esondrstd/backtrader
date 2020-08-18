from glob import glob
import pandas as pd
import os

"""
This program returns ticker names from file path in output folder.
Can use this after loading csv files from Interactive Brokers to generate list of tickers to feed into 
the csv to mysql file for loading stocks into the mysql database
"""

# csvs will contain all CSV files names ends with .csv in a list
csvs = glob('C:\\ProgramData\\MySQL\\MySQL Server 8.0\\Uploads\\*.csv')

# remove the trailing .csv from CSV files names
table_list = [os.path.basename(csv)[:-4] for csv in csvs]

print(table_list)


