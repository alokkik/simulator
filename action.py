import datetime
import pprint
import random
import quickfix as fix
import copy,time
import pytz
from twap import Twap
from vwap import Vwap
from price import Price
from pytz import timezone
from message_factory import MessageFactory
from datetime import datetime as dt
from datetime import timedelta as td
pp = pprint.PrettyPrinter(indent=4)

class Action:
    
    def __init__(self,ordersMap,logger,util):
        self.util = util
        self.twap = Twap(self.util)
        self.vwap = Vwap(self.util)
        self.ordersMap = ordersMap
        self.logger = logger
        self.MsgFct = MessageFactory(logger,self.util)
        self.price = Price(self.util)
    
    def wait(self,t):
        time.sleep(t)
        return
    
    def new(self,OrderObj):
        """
        Description : send acknowledgement for new order 
        Parameters:
            OrderObj -- Order
        Return : message object
        """
        message = self.MsgFct.AckNewOrder(OrderObj)
        if OrderObj.SecurityID == None:
            return self.reject(OrderObj,"SecurityID Invalid")
        
        if "close" in OrderObj.Rule :
            MktCloseTime = self.util.getMktClsTime(self.util.CurrencyRegionDict[OrderObj.Currency])
            self.logger.debug("Market Open Time : %s"%MktCloseTime)
            self.logger.debug("Current Time : %s"%OrderObj.Epoch)
            if "1" in OrderObj.Rule and MktCloseTime > OrderObj.Epoch: 
                return self.reject(OrderObj,"Failed : trying to place order in market hours!")
            if "0" in OrderObj.Rule and MktCloseTime < OrderObj.Epoch:
                return self.reject(OrderObj,"Failed : Market has closed!")
            
        if "open" in OrderObj.Rule:
            MktOpenTime = self.util.getMktOpenTime(self.util.CurrencyRegionDict[OrderObj.Currency])
            self.logger.debug("Market Open Time : %s"%MktOpenTime)
            self.logger.debug("Current Time : %s"%OrderObj.Epoch)
            if "1" in OrderObj.Rule and MktOpenTime > OrderObj.Epoch: 
                return self.reject(OrderObj,"Failed : Market not open yet!")
            if "0" in OrderObj.Rule and MktOpenTime < OrderObj.Epoch:
                return self.reject(OrderObj,"Failed : Market open time has passed!")
        self.logger.debug("** NewOrder Ack Sent **")
        return message
    
    def invalidTicker(self,OrderObj):
        """
        Description : sends reject message, if order rejected due to invalid ticker.
        Parameters:
            OrderObj -- Order
        Return : message object
        """
        OrderObj.OrdStatus = '8' #Reject
        OrderObj.Text = "Reject: Invalid Ticker"
        message = self.MsgFct.InvalidTicker(OrderObj)
        self.logger.debug("** Reject Sent **")
        return message
    
    def invalidMsgType(self,message):
        """
        Description : sends reject message, if order rejected due to invalid ticker.
        Return : message object
        """
        message = self.MsgFct.InvalidMsgType(message)
        self.logger.debug("** Reject Sent **")
        return message
    
    def invalidDate(self,OrderObj):
        """
        Description : sends reject message, if order rejected due to invalid date.
        Parameters:
            OrderObj -- Order
        Return : message object
        """
        OrderObj.OrdStatus = '8' #Reject
        OrderObj.Text = "Reject: Invalid Order Date"
        message = self.MsgFct.InvalidDate(OrderObj)
        self.logger.debug("** Reject Sent **")
        return message
    
    def replace(self,OrderObj):
        """
        Description : send acknowledgement for Replace order 
        Parameters:
            OrderObj -- Order
        Return : message object
        """
        message = self.MsgFct.AckReplaceOrder(OrderObj)
        self.logger.debug("** Order Replaced **")
        return message
    
    def reject(self,OrderObj,text):
        """
        Description : sends reject message, if any order with type New is rejected.
        Parameters:
            OrderObj -- Order
            text -- Message to send
        Return : message object
        """
        OrderObj.OrdStatus = '8' #Reject
        OrderObj.Text = text
        message = self.MsgFct.RejectNewOrder(OrderObj)
        self.logger.debug("** Reject Sent **")
        return message
    
    def rejectCancel(self,OrderObj,text):
        """
        Description : sends reject message, if any order rejected.
        Parameters:
            OrderObj -- Order
            text -- Message to send
        Return : message object
        """
        OrderObj.OrdStatus = '8' #Reject
        OrderObj.Text = text
        message = self.MsgFct.Reject(OrderObj)
        self.logger.debug("** Cancel Reject Sent **")
        return message
    
    def rejectReplace(self,OrderObj,text):
        """
        Description : sends reject message, if any order rejected.
        Parameters:
            OrderObj -- Order
            text -- Message to send
        Return : message object
        """
        OrderObj.OrdStatus = '8' #Reject
        OrderObj.Text = text
        message = self.MsgFct.Reject(OrderObj)
        self.logger.debug("** Replace Reject Sent **")
        return message
    
    def unsolicitedcancel(self,OrderObj):
        """
        Description : Sends unsolicited cancel order after waiting for given amount of time 
        Parameters:
            OrderObj -- Order
        Return : message object
        """
        OrderObj.OrdStatus = '4'
        message = self.MsgFct.UnsolicitedCancelMsg(OrderObj)
        self.logger.debug("** UnsolicitedCancel Sent**")
        return message
    
    def processOrderPrice(self,OrderObj):
        """
        Description : Set order price and check if its valid. 
        Parameters:
            OrderObj -- Order
        Return : message object if Invalid Price
        """
        if OrderObj.SecurityID == None:
            return self.reject(OrderObj,"** No ticker found for SecurityID **")

        self.price.SetOrderPrice(OrderObj)
        message = self.CheckOrderPrice(OrderObj)
        return message
    
    def checkOrderTime(self,OrderObj):
        """
        Description : checks if endtime > starttime.  
        Parameters:
            OrderObj -- Order
        Return : message object if Invalid Price
        """
        message = None
        if OrderObj.EndTime < OrderObj.Epoch:
            message = self.reject(OrderObj,"**Could not process : Invalid EndTime**")
            return message
        return message
    
    def pfill(self,OrderObj,percent):
        """
        Description : Sends partial fill for an order. 
        Parameters:
            OrderObj -- Order
            percent -- percentage of the OrderQty to be filled.
        Return : message object
        """
        self.logger.debug("** Inside Partial Fill **")
        message = self.processOrderPrice(OrderObj)
        if message!= None:return message
        
        OrderObj.OrdStatus = '1'
        message = self.MsgFct.Fill(OrderObj, OrderObj.getQty(percent),float(OrderObj.Price))
        self.logger.debug("** Partial Fill Ack Sent **")
        return message
    
    def fill(self,OrderObj):
        """
        Description : Sends fill for rest of the quantity. 
        Parameters:
            OrderObj -- Order
        Return : message object
        """
        message = self.processOrderPrice(OrderObj)
        if message!= None:return message
        
        OrderObj.OrdStatus = '2'
        message = self.MsgFct.Fill(OrderObj,int(OrderObj.LeavesQty),float(OrderObj.Price))
        self.logger.debug("**Complete Fill Ack Sent **")
        return message
    
    def fillshares(self,OrderObj,Unit,N=None):
        """
        Description : Sends fill, N number of shares at a time. 
        Parameters:
            OrderObj -- Order
            Unit -- number of shares
            N -- Counts
        Return : message object
        """
        message = self.processOrderPrice(OrderObj)
        if message!= None:return message
    
        OrderObj.OrdStatus = '1'
        message = None
        if N == None:
            if OrderObj.LeavesQty < Unit: 
                Unit = OrderObj.LeavesQty
                OrderObj.OrdStatus = '2'
            message = self.MsgFct.Fill(OrderObj,int(Unit),float(OrderObj.Price)) if Unit != 0 else None 
        else:
            message,i = [],1
            while(i<=N):
                if OrderObj.LeavesQty < Unit: break
                message.append(self.MsgFct.Fill(OrderObj,int(Unit),float(OrderObj.Price)))
                i+=1
        if not message: self.logger.debug("**Fillshares Ack Sent **")
        return message
        
    def calculateAlgoTime(self,OrderObj,Seconds):
        """
        Description : calculate time for order to process.
        Parameters:
            OrderObj -- NewOrder order object.
            Seconds -- given number of seconds for order to process.
        Return : Seconds
        """
        OrderObj.EndTime = OrderObj.EndTime.replace(microsecond=OrderObj.Epoch.microsecond)
        if Seconds == None or Seconds <=0:
            if OrderObj.EndTime < OrderObj.Epoch:
                Seconds = 30*60
            else : Seconds = (OrderObj.EndTime - OrderObj.Epoch).seconds
        secondsToMktClose = self.util.secondsToMktClose(self.util.CurrencyRegionDict[OrderObj.Currency],OrderObj.Epoch)
        self.logger.debug("Market Closes in : %s seconds"%secondsToMktClose) #-1 means already closed
        if secondsToMktClose>0: Seconds = min(Seconds,secondsToMktClose)
        OrderObj.EndTime = OrderObj.Epoch + td(seconds=Seconds)
        self.logger.debug("StartTime : %s"%str(OrderObj.Epoch))
        self.logger.debug("EndTime : %s"%str(OrderObj.EndTime))
        self.logger.debug("Seconds to ProcessOrder : %s"%Seconds)
        return Seconds
    
    def close(self,OrderObj,Seconds):
        """
        Description : fill order at market closing time or after market closed
                      "algo close 0/1"
        Parameters:
            OrderObj -- NewOrder Object
        Return : None
        """
        self.logger.debug("Inside Close")
        MktCloseTime = self.util.getMktClsTime(self.util.CurrencyRegionDict[OrderObj.Currency])
        self.logger.debug("Market Close Time : %s"%MktCloseTime)
        self.logger.debug("Current Time : %s"%OrderObj.Epoch)
        if Seconds !=1: OrderObj.Epoch = MktCloseTime
        else : OrderObj.Epoch = OrderObj.EndTime
        self.logger.debug("End Time : %s"%OrderObj.EndTime)
        OrderObj.Rule+=['fill']
        return
    
    def _open(self,OrderObj,Seconds):
        """
        Description : fill order at market opening time or after market opened.
                      "algo open 0/1"
        Parameters:
            OrderObj -- NewOrder Object
        Return : None
        """
        self.logger.debug("Inside Open")
        MktOpenTime = self.util.getMktOpenTime(self.util.CurrencyRegionDict[OrderObj.Currency])
        self.logger.debug("Market Open Time : %s"%MktOpenTime)
        self.price.SetOrderPrice(OrderObj,True)
        self.logger.debug("Current Time : %s"%OrderObj.Epoch)
        if Seconds!=1: OrderObj.Epoch = MktOpenTime
        else : OrderObj.Epoch = OrderObj.EndTime
        self.logger.debug("End Time : %s"%OrderObj.EndTime)
        OrderObj.Rule+=['fill']
        return
            
    def algo(self,OrderObj,Type,Seconds=None):
        """
        Description : breaks total number of seconds into Intervals and
                      total quantity into relatively smaller quantity. 
        Parameters:
            OrderObj -- NewOrder Object
            Type -- vwap/twap/close
            Seconds -- number of seconds for order to fill.
        Return : None
        """
        self.logger.debug("Inside algo")
        if Type == 'close': self.close(OrderObj,Seconds)
        elif Type == 'open':self._open(OrderObj,Seconds)
        else : #wap algos
            Seconds = self.calculateAlgoTime(OrderObj,Seconds)
            if Type == 'twap':ruleString = self.twap.getRuleString(OrderObj.LeavesQty,Seconds)
            else: ruleString = self.vwap.getRuleString(OrderObj.LeavesQty,Seconds)
            OrderObj.Rule.extend(ruleString.split())
        return 
        
    def OrderNotFound(self,OrderObj):
        """
        Description : sends Error message on order Not Found 
        Parameters:
            OrderObj -- NewOrder Object
        Return : message object
        """
        #ack about the replace order not found
        OrderObj.OrdStatus = '8' #marking request order obj as rejected.
        message = self.MsgFct.ErrorMsg(OrderObj)
        self.logger.debug("** OrderNotFound **")
        return message
    
    def CheckOrderPrice(self,OrderObj):
        """
        Description : sends Error message if price is Invalid. 
        Parameters:
            OrderObj -- NewOrder Object 
        Return : message object
        """
        message = None
        if not OrderObj.isPriceValid(): 
            message = self.reject(OrderObj,"InvalidPrice : Either -ve, 0 or Not provided, Value: %s"%OrderObj.Price)
        return message
    
    def cancelOrd(self,OrderObj): #updating status for CancelOrder and Cancelled Order.
        """
        Description : Cancels order and sends cancel acknowledgement.
        Parameters:
            OrderObj -- Order
        Return : message object
        """
        #look for target order in ordersMap with "OrigClOrdID"
        OrderObj.OrdStatus = '3'  #3 = 'Done for day'
        origclordid = OrderObj.OrigClOrdID
        ord_to_cancel = self.ordersMap.get(origclordid,None)
        message = None
        
        #if order to cancel not found.
        if ord_to_cancel == None:
            OrderObj.OrdStatus = '8' #Rejected
            OrderObj.Text = "OrderNotFoundError"
            message = self.OrderNotFound(OrderObj)
            return message
        
        if ord_to_cancel.inActive():
            return self.rejectCancel(OrderObj,"Cancel Rejected : Order already Rejected/Filled/Cancelled/Done for Day")
        
        if ord_to_cancel.CancelAfter > dt.now(timezone(self.util.getTimeZone(ord_to_cancel.Currency))):
            timeNow = dt.now(timezone(self.util.getTimeZone(ord_to_cancel.Currency)))
            ord_to_cancel.CancelAfter,ord_to_cancel.Epoch  = timeNow,timeNow #update cancel time now.
            return self.rejectCancel(OrderObj,"Cancel Rejected : Not allowed till sometime")
            
        if ord_to_cancel.Rule[0] != 'cxl':
            if ord_to_cancel.Text != None and 'algo' in ord_to_cancel.Text: pass
            else:return self.rejectReplace(OrderObj,"Cancel Rejected : Not in Instruction")
            
        #Check if not already cancelled or already filled
        if not ord_to_cancel.inActive(): 
            ord_to_cancel.OrdStatus = '4' #4 = 'Cancelled'
            ord_to_cancel.ExecType = '4'
            ord_to_cancel.LeavesQty = 0
            
        message = self.MsgFct.AckCancelOrder(OrderObj,ord_to_cancel)
        self.logger.debug("** Order Cancelled **")
        return message
    
    def replaceOrd(self,OrderObj):
        """
        Description : Replaces order target order.
        Parameters:
            OrderObj -- Order
        Return : message object
        """
        self.logger.debug("** Inside replaceOrd **") 
        #look for target order in ordersMap with "OrigClOrdID"
        origclordid = OrderObj.OrigClOrdID
        ord_to_cancel = self.ordersMap.get(origclordid,None)
        message = None
        
        #if order to cancel not found. 
        if ord_to_cancel == None:
            OrderObj.OrdStatus = '8' #Rejected
            OrderObj.Text = "OrderNotFoundError"
            message = self.OrderNotFound(OrderObj)
            return message
        
        if ord_to_cancel.SecurityID != OrderObj.SecurityID:
            return self.rejectCancel(OrderObj,"Replace Rejected : SecurityID Invalid")
        
        if ord_to_cancel.inActive():
            return self.rejectReplace(OrderObj,"Replace Rejected : Order already Rejected/Filled/Cancelled/Done for Day")
        
        if ord_to_cancel.ReplaceAfter > dt.now(timezone(self.util.getTimeZone(ord_to_cancel.Currency))):
            timeNow = dt.now(timezone(self.util.getTimeZone(ord_to_cancel.Currency)))
            ord_to_cancel.ReplaceAfter, ord_to_cancel.Epoch = timeNow,timeNow #update replace time now.
            return self.rejectReplace(OrderObj,"Replace Rejected : Not allowed till sometime")
        
        if ord_to_cancel.Rule[0] != 'rpl':
            if ord_to_cancel.Text != None and 'algo' in ord_to_cancel.Text:pass
            else:return self.rejectReplace(OrderObj,"Replace Rejected : Not in Instruction")
        
        if OrderObj.OrdType == '2':
            message = self.CheckOrderPrice(OrderObj) #checking for Invalid price
            if message != None:return message
        
        #if order not already cancelled or already filled
        if not ord_to_cancel.inActive(): 
            if OrderObj.OrderQty < ord_to_cancel.CumQty: # if OrderQty of replaced order is less than CumQty
                return self.rejectReplace(OrderObj,"Invalid Order Quantity")
            
            RplOrderObj = copy.deepcopy(ord_to_cancel)
            RplOrderObj.OrderQty = OrderObj.OrderQty
            RplOrderObj.ClOrdID = OrderObj.ClOrdID
            RplOrderObj.OrigClOrdID = ord_to_cancel.ClOrdID
            RplOrderObj.LeavesQty = RplOrderObj.OrderQty - ord_to_cancel.CumQty
            RplOrderObj.Epoch = dt.now(timezone(self.util.getTimeZone(ord_to_cancel.Currency)))
            RplOrderObj.OrdType = OrderObj.OrdType
            RplOrderObj.Price = OrderObj.Price
            if RplOrderObj.OrdType == '1': 
                RplOrderObj.Price = self.price.getPrice(RplOrderObj)
            RplOrderObj.ExecType = '5' #5 == Replaced
            RplOrderObj.MsgType = 'D'  #D == NewSingleOrder
            ord_to_cancel.OrdStatus ='4' #Cancel
            OrderObj.OrdStatus = '3' #Done for Day
            if RplOrderObj.Text != None and 'algo' in RplOrderObj.Text:
                Sec = (RplOrderObj.EndTime - RplOrderObj.Epoch).seconds
                if 'twap' in RplOrderObj.Text:
                    ruleString = self.twap.getRuleString(RplOrderObj.LeavesQty,Sec)
                else:
                    ruleString = self.vwap.getRuleString(RplOrderObj.LeavesQty,Sec)
                RplOrderObj.Rule=ruleString.split()
            #updating the ordersMap
            self.ordersMap[RplOrderObj.ClOrdID] = RplOrderObj
        message = self.replace(RplOrderObj)
        return message