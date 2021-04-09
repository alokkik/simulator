import quickfix as fix
from order import Order
import numpy as np
import pytz
from pytz import timezone
from rulebook import rulebook
from datetime import datetime as dt
from datetime import timedelta as td

class NewOrder(Order):
    def __init__(self,message,util):
        Order.__init__(self,message)
        self.Account = self.get_value(message,fix.Account())
        self.Currency = self.get_value(message,fix.Currency())
        self.Epoch = dt.now(timezone(util.getTimeZone(self.Currency)))
        self.HandlInst = self.get_value(message,fix.HandlInst())
        self.IDSource = self.get_value(message,fix.IDSource())
        self.OrdType = self.get_value(message,fix.OrdType())
        self.TimeInForce = self.get_value(message,fix.TimeInForce())
        self.ExDestination = self.get_value(message,fix.ExDestination())
        Price = self.get_value(message,fix.Price())
        self.Price = np.nan_to_num(float(Price)) if Price != None and float(Price) != 0.0 else None
        self.maptoTicker(util)
        self.Rule = self.checkRule().split() if self.Text == None else self.Text.split(':')[1].split()
        self.Symbol = self.SecurityID if self.SecurityID != None else self.Symbol+" "+self.ExDestination+" "+"Equity" 
        self.OrigClOrdID = None
        self.CancelAfter = self.Epoch
        self.ReplaceAfter = self.Epoch
        self.EndTime = self.getEndTime(message,util)
        self.MsgType = 'D'
        self.ExecType = '0'
        self.CumQty = 0
        self.AvgPx = 0
        self.LastPx = 0
        self.LastMkt = None
        self.LastQty = 0 
        self.LeavesQty = int(self.OrderQty) #Qty yet to fill
        self.FillQty = [] #not a tag
        self.FillPrice = [] #not a tag
        self.TransactTime = self.stringToTimeWithTimeZone(util,self.TransactTime)
    
    def stringToTimeWithTimeZone(self,util,dateString):
        dte = dt.strptime(dateString,'%Y%m%d-%H:%M:%S')
        timeZone = pytz.timezone(util.getTimeZone(self.Currency))
        dte = timeZone.localize(dte)
        return dte
    
    def getEndTime(self,message,util):
        """
        Description : getting EndTime as per the region timezone. 
        Keyword Arguments:
            message -- message object received
            util -- instance of util class.
        Return : datetime object
        """
        if message.isSetField(6063):
            dte = self.stringToTimeWithTimeZone(util,message.getField(6063))
        else:
            dte = self.Epoch+td(minutes=30)
        return dte
    
    #updates CumQty and LeavesQty 
    def update_qty(self,Qty):
        """
        Description : updates order quantity. 
        Keyword Arguments:
            Qty -- Order Quantity 
        Return : None
        """
        self.CumQty += Qty
        self.LeavesQty -= Qty
        
    def update_fill_qty_and_price(self,Qty,Price):
        """
        Description : updates filled quantity and price. 
        Keyword Arguments:
            Qty -- Order Quantity 
            Price -- Price 
        Return : None
        """
        self.FillQty.append(Qty)
        self.FillPrice.append(round(np.nan_to_num(Price),3))
        self.LastPx = round(np.nan_to_num(Price),3)
        self.LastQty = Qty
        self.AvgPx = self.updateAvgPx(self.FillQty, self.FillPrice)
        
    def updateAvgPx(self,FillQty, FillPrice):
        """
        Description : updates Average Price on each fill. 
        Keyword Arguments:
            FillQty -- Order Quantity 
            FillPrice -- Price 
        Return : Average Price
        """
        try:
            FillQty = np.array(FillQty)
            FillPrice =  np.array(FillPrice)
            AvgPx = np.sum(FillPrice*FillQty)/np.sum(FillQty)
        except ZeroDivisionError :
            AvgPx = 0
        return round(AvgPx,3)
    
    def getQty(self, Per=None):
        """
        Description : calculates quantity based on percentage.
        Keyword Arguments:
            per -- Percentage 
        Return : Leaves Quantity
        """
        if Per != None:
            return int(np.ceil((float(Per)/100)*self.LeavesQty)) \
                        if self.LeavesQty > 0 else int(np.floor((float(Per)/100)*self.LeavesQty))
        else:
            return self.LeavesQty
        

    def checkRule(self):
        """
        Description : matches symbol to the predefined format 
                      and return corresponding rule.
        Parameters:
            symbol -- symbol or ticker of a stock   
        Return : rule from rulebook
        """
        rule = None
        for key in rulebook.keys():
            if '*' in key:
                if self.Symbol.startswith(key[:key.index('*')]):
                    rule = rulebook[key]
            elif key == self.Symbol:
                rule = rulebook[key]
        print(rule)
        return rulebook['default'] if rule == None else rule

class ReplaceOrder(Order):
    def __init__(self,message,util):
        Order.__init__(self,message)
        self.SecurityIDSource = self.get_value(message,fix.OrigClOrdID())
        self.OrigClOrdID = self.get_value(message,fix.OrigClOrdID())
        self.Account = self.get_value(message,fix.Account())
        self.Currency = self.get_value(message,fix.Currency())
        self.Epoch = dt.now(timezone(util.getTimeZone(self.Currency)))
        self.HandlInst = self.get_value(message,fix.HandlInst())
        self.IDSource = self.get_value(message,fix.IDSource())
        self.OrdType = self.get_value(message,fix.OrdType())
        self.TimeInForce = self.get_value(message,fix.TimeInForce())
        self.maptoTicker(util)
        Price = self.get_value(message,fix.Price())
        self.Price = np.nan_to_num(float(Price)) if Price != None and float(Price) != 0.0 else None
        self.CancelAfter = self.Epoch
        self.ReplaceAfter = self.Epoch
        self.MsgType = 'G'
        self.ExecType = '0'
        self.CumQty = 0
        self.AvgPx = 0
        self.LastPx = 0
        self.LastQty = 0 
        self.LeavesQty = int(self.OrderQty)
    
        
class CancelOrder(Order):
    def __init__(self,message,util):
        Order.__init__(self,message)
        self.MsgType = 'F'
        self.IDSource = self.get_value(message,fix.IDSource())
        self.ExecTransType = self.get_value(message,fix.ExecTransType())
        self.OrigClOrdID = self.get_value(message,fix.OrigClOrdID())