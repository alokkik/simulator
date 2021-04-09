import random,os
import numpy as np
import pandas as pd
from pandas.tseries.offsets import BDay
from emsabs import emsPrice
from datetime import datetime

class Price:
    
    def __init__(self,util):
        self.util = util
        self.close_df = self.util.dfClose
        self.tids = self.util.univ_df.parsekyable_des_source.tolist()
        self.pf = emsPrice.emsPrice()
    
    def getTick(self,low,high):
        """
        Description : returns random value between[low,high]
        Keyword Arguments:
            low -- lower bound
            high -- upper bound
        Return : random float number rounded to 3 digits.
        """
        return round(random.uniform(low,high),3)
    
    def isValidTicker(self,tid):
        """
        Description : check if Ticker is valid or not. 
        Keyword Arguments:
            tid -- Ticker ID
        Return : True/False
        """
        return True if tid in self.tids else False
            
    def getMarketPrice(self,dte,tid,reg):
        """
        Description : gets market price for today,if not then previous day
                      else generate random price.
        Keyword Arguments:
            dte -- datetime object
            tid -- Ticker ID
            reg -- region
        Return : float value as MarketPrice.
        """
        try:
            lastPrice = self.pf.getLastPrice(tid)
            if lastPrice == 0:
                if 'BB:'+tid in self.close_df[reg].tid.tolist():
                    lastPrice = float(self.close_df[reg][self.close_df[reg].tid == 'BB:'+tid].px)
                else: 
                    lastPrice = self.getTick(10,50)
        except IOError as e:
            return self.getTick(10,50)
        return lastPrice

    def getPrice(self,OrderObj):
        """
        Description : getPrice based on the OrdType "1" or "2" 
        Keyword Arguments:
            OrderObj -- NewOrder/ReplaceOrder Object.
        Return : float value of Price.
        """
        Price = OrderObj.Price
        if OrderObj.OrdType == '1': #Market Order
            Price = self.getMarketPrice(datetime.now(),OrderObj.SecurityID,self.util.CurrencyRegionDict[OrderObj.Currency]) 
            if pd.isnull(Price):
                Price = self.getTick(10,50)
            else: 
                Price = np.nan_to_num(Price)
        if pd.isnull(Price): return 0
        return round(Price,3) + self.getTick(-0.05,0.05) #Market Order
     
    def SetOrderPrice(self,OrderObj,LastPriceFlag=False):
        """
        Description : Set Order Price 
        Keyword Arguments:
            OrderObj -- NewOrder/ReplaceOrder Object.
        Return : None
        """
        if OrderObj.OrdStatus == '0':
            OrderObj.Price = self.getTick(10,50) if not self.isValidTicker(OrderObj.SecurityID) else self.getPrice(OrderObj)
            
        if LastPriceFlag:
            reg = self.util.CurrencyRegionDict[OrderObj.Currency]
            if 'BB:'+OrderObj.SecurityID in self.close_df[reg].tid.tolist():
                OrderObj.Price = float(self.close_df[reg][self.close_df[reg].tid == 'BB:'+OrderObj.SecurityID].px)
            else: 
                OrderObj.Price = None
        return