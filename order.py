import quickfix as fix
from datetime import datetime as dt
from datetime import timedelta as td
from pytz import timezone
import pandas as pd
import numpy as np

class Order:
    def __init__(self, message):
        self.SenderCompID = self.get_value(message,fix.SenderCompID(),True)
        self.TargetCompID = self.get_value(message,fix.TargetCompID(),True)
        self.ClOrdID = self.get_value(message,fix.ClOrdID())
        self.OrderQty = int(self.get_value(message,fix.OrderQty()))
        self.SecurityID = str(self.get_value(message,fix.SecurityID()))
        self.Symbol = self.get_value(message,fix.Symbol())
        self.Side = self.get_value(message,fix.Side())
        self.TransactTime = self.get_value(message,fix.TransactTime())
        self.Text = self.get_value(message,fix.Text())
        self.SecurityType = self.get_value(message,fix.SecurityType())
        self.OrderID = None
        self.ExecID = None
        self.OrdStatus = '0'
    
    def maptoTicker(self,util):
        """
        Description : maps sedol/cusip to ticker using dfMap
        Parameters:
            dfMap -- dataframe for mapping.   
        Return : None
        """
        dfMap = util.dfMap[util.CurrencyRegionDict[self.Currency]]
        if self.IDSource == '8':return
        elif self.IDSource == '1':
            dfMap = dfMap.set_index('id_cusip')
        elif self.IDSource == '2':
            dfMap = dfMap.set_index('id_sedol1')
        try:
            if hasattr(self,'ExDestination') and self.ExDestination == None:
                self.ExDestination = dfMap.loc[self.SecurityID].eqy_prim_security_comp_exch
                if pd.isnull(self.ExDestination): self.ExDestination = util.CurrencyExdesDict[self.Currency]
            self.SecurityID = dfMap.loc[self.SecurityID].bbid
            dfMap = dfMap.reset_index()
        except KeyError as e:
            self.SecurityID = None
            self.ExDestination = util.CurrencyRegionDict[self.Currency].upper()
            
    def get_value(self, message, tag, header=False):
        """ Description : get Field value from Message"""
        item = tag
        if not header:
            if message.isSetField(item):
                message.getField(item)
                return item.getString()
            else:return None
        else:
            message.getHeader().getField(item)
            return item.getString()
        
    def isPriceValid(self):
        """
        Description : check if price of order is valid or not.
        Return : True/False
        """
        return False if self.Price <= 0 or self.Price == None else True
    
    def isActive(self):
        "Description : checks if order is active or not"
        return True if self.OrdStatus in ['0','1','A'] else False
    
    def inActive(self):
        "Description : checks if order is InActive or not"
        return True if self.OrdStatus in ['4','2','3','8'] else False
    
    def isNew(self):
        "Description : check if order is New"
        return True if self.MsgType == 'D' else False
    
    def isReplace(self):
        "Description : check if order is Replace"
        return True if self.MsgType == 'G' else False
    
    def isCancel(self):
        "Description : check if order is Cancel"
        return True if self.MsgType == 'F' else False
    
    def isOrdReplaced(self):
        "Description : check if order is Replaced"
        return True if self.ExecType == '5' else False 