
# coding: utf-8

# In[ ]:


# %matplotlib # add this line if you want figures to be opened in separate windows
import eme 
import matplotlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import sys
import subprocess
import os
import glob #for iterating over files
import locale #see next cell
from locale import *
import csv


# In[ ]:


locale.setlocale(locale.LC_ALL, '') #see espp line 45; used for parsing in case of double values in EXAA prices (e.g. summertime)


# In[ ]:


os.environ['http_proxy'] = "http://194.138.0.3:9400" 
os.environ['https_proxy'] = "https://194.138.0.3:9400"


# # Preparations

# ## Configuration of the Energy System

# In[ ]:


grid_access_prices = eme.s.GridAccessPrices()
bat = eme.s.Battery()


# In[ ]:


es_setup = eme.s.ESSetup()


# ## Create the object to load, store and process data from the real energy system

# In[ ]:


#Prices calculated based on EXAA prices and GridAccessPrices

use_reported_consumption_prices=False
use_reported_feeding_revenue=False

systemO = eme.s.EnergySystemReal(name="active", 
                                 es_setup=es_setup, battery=bat, grid_access_prices=grid_access_prices, 
                                 debug=True,
                                 use_reported_consumption_prices=use_reported_consumption_prices,
                                 use_reported_feeding_revenue=use_reported_feeding_revenue)


# ## Select the data corresponding to an active Research Mode

# In[ ]:


PATH = os.getcwd()+'\data.orig\\' #'\data.orig\\' is a subdirectory of .getcwd()
def retrieve_data(srcPath):
    for i, file_path in enumerate(os.listdir(PATH)):
        print("Reading file " +PATH+file_path)
        df = pd.read_csv(PATH+file_path, sep = ';') #read_csv, not DataFrame; still working with a filepath
        rm = df.ResearchModeStatus.ffill() #fill NaN values
        df.ResearchModeStatus= rm
        mask = (
                 (rm == 1) | 
                 ( (rm == 0) & 
                   (df.groupby((rm != rm.shift()).cumsum()).ResearchModeStatus.transform('size') <= 424) 
                 )
               )
        df = df[mask]
        p = PATH+'df_{}.csv'.format(i)
        print("Writing file ", p)
        df = df.to_csv(p, sep = ';')


# In[ ]:


retrieve_data('C:/Users/z003yh8t/Desktop/energy-management-evaluation/data.orig/2017-04-01_rawChannelData.csv')


# ## Check validity of data based on separator

# In[ ]:


def check_data_validity(file_a):
    with open(file_a, newline = "") as csvfile:
        try:
            dialect = csv.Sniffer().sniff(csvfile.read(1024), delimiters = ";")
            print("Delimiter is ;")
        except:
            print("Wrong Delimiter")


# In[ ]:


check_data_validity('C:/Users/z003yh8t/Desktop/energy-management-evaluation/data.active/data.active.1/active_2017-07-01_00-00-00_2017-08-01_00-00-00.csv')


# # Iterate over files to create weekly reports

# In[ ]:


def WeeklyReport(pathOfFiles):
    for file in list(glob.glob(pathOfFiles)):
        print("Start processing file {}.".format(file))
        enc = "utf_8"
        try:
            pd.read_csv(file, sep = ';', encoding = "utf_8")
        except UnicodeDecodeError:
            enc = "cp1252" #in case files have cp1252 encoding
        print("File encoding is " + enc)
        string_array = file.split('_') #extract the start/end date and time based on the name of the file (string)
        data_start_string = string_array[1].split('-')
        time_start_string = string_array[2].split('-')
        data_end_string = string_array[3].split('-')
        time_end_string = string_array[4][0:-4].split('-')
        start = datetime.datetime(year=int(data_start_string[0]), month=int(data_start_string[1]), day=int(data_start_string[2]), hour=int(time_start_string[0]), minute=int(time_start_string[1]), second=int(time_start_string[2]))
        end = datetime.datetime(year=int(data_end_string[0]), month=int(data_end_string[1]), day=int(data_end_string[2]), hour=int(time_end_string[0]), minute=int(time_end_string[1]), second=int(time_end_string[2]))
        systemX = eme.s.EnergySystemReal(name="active", battery=bat, grid_access_prices=grid_access_prices, debug=True)
        print("- Loading data from file.")
        systemX.load_field_data(file, start_date=start, end_date=end)
        period = pd.Timedelta(days=7) #weekly analysis
        end = systemX.data.index[-1] 
        period_start = systemX.data.index[0]
        period_end = period_start + period
        while period_start < end:
            print("- Calculating period {}-{}.".format(period_start, period_end))
            systemO = eme.s.EnergySystemReal(name="Research Mode", battery=bat, grid_access_prices=grid_access_prices, debug=True)
            systemO.load_field_data(file, start_date=period_start, end_date=period_end)

    
            systemS = eme.s.EnergySystemSimulation(name="Simulated Standard Mode".format(period_start, period_end), battery=bat, grid_access_prices=grid_access_prices, debug=True)
            systemS.load_field_data(file, start_date=period_start, end_date=period_end)

            
            print("- Creating report for period {}-{}.".format(period_start, period_end)) #create report
            path = "report_{}-{}".format(period_start, period_end).replace(" ","_").replace(":","_").replace("-","_")
            reporter = eme.r.EMSReportGenerator("D5B", [systemO, systemS], grid_access_prices, path)
            reporter.generate_doc()
            print("- Finished processing period {}-{}.".format(period_start, period_end))
    
            period_start = period_end
            period_end = period_start + period
        print("Finished processing file {}.".format(file))


# In[ ]:


WeeklyReport('C:/Users/z003yh8t/Desktop/energy-management-evaluation/data.active/*.csv')

