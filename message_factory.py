import quickfix as fix
import numpy as np
from datetime import datetime
from datetime import timedelta as td

class MessageFactory:
    
    def __init__(self,logger,util):
        self.util = util
        self.logger = logger
        self.BeginString = 'FIX.4.2'
        self.BodyLength = 228
        self.MsgType = 'D'
        self.SenderCompID = 'client'
        self.TargetCompID = 'server'
        self.DeliverToCompID = 'ACSIM'
        self.SendingTime = '20200914-13:45:33.000' #update it to the current time
        self.SenderSubID = '10536646'
        self.TargetSubID = '10536646'
        self.SendingTime = self.util.cur_timestamp()
        
    def set_header(self,message,sender=None,target=None):
        """ Description : Initialize header for every message
            Params:
                message -- message object,header to be initialized.
            Return:  message object.
        """
        header = message.getHeader()
        header.setField(fix.BeginString(self.BeginString)) #8
        header.setField(fix.BodyLength(self.BodyLength)) #9
        header.setField(fix.MsgType(self.MsgType)) #35 #depends on the msg
        header.setField(fix.SenderCompID(self.SenderCompID if target == None else target)) #49
        header.setField(fix.TargetCompID(self.TargetCompID if sender == None else sender)) #56
        header.setField(fix.MsgSeqNum(1)) #34
        header.setField(fix.DeliverToCompID(self.DeliverToCompID)) #128
        header.setField(fix.SenderSubID(self.SenderSubID)) #50
        send_time = fix.SendingTime()
        send_time.setString(self.SendingTime) #replace it with current time
        header.setField(send_time) #52
        return message
    
    def set_trailer(self,message,val):
        """ Description : Initialize header for every message
            Params:
                message -- message object,header to be initialized.
                val     -- checksum value
            Return:  message object. 
        """
        trailer = message.getTrailer()
        trailer.setField(fix.CheckSum(val)) 
        return message
    
    #** client side **
    def create_neworder_msg(self,**kwargs):
        """ Description : NewOrder request message
            Params:
                **kwargs -- dynamic param dict
            Return:  message object.    
        """
        self.logger.debug("Inside create new order!")
        self.MsgType = 'D' #NewOrder
        message = fix.Message()
        message = self.set_header(message)
        message.setField(fix.Account('ACSIM')) #1
        message.setField(fix.ClOrdID(kwargs.get('ClOrdID',None))) #11 #unique identifier client side
        message.setField(fix.Currency(kwargs.get("Currency"))) #15
        message.setField(fix.HandlInst('1')) #21
        message.setField(fix.IDSource('2')) #22
        message.setField(fix.OrderQty(kwargs.get('OrderQty',None))) #38
        message.setField(fix.OrdType(str(kwargs.get("OrdType",'1')))) #40
        message.setField(fix.Price(kwargs.get('Price',0))) #44
        message.setField(fix.SecurityID(str(kwargs.get('SecurityID')))) 
        #message.setField(fix.SecurityID('2046251')) #48 #IBM : 2769796 , AAPL : 2046251 , T : 2831811, TSLA = "B616C79", CN ABST = 2570761,JP 4206: 6010047
        message.setField(fix.Symbol(kwargs.get('Symbol',None))) #55
        message.setField(fix.Side('1')) #54
        message.setField(fix.TimeInForce('0')) #59
        transact_time = fix.TransactTime()
        transact_time.setString(self.util.cur_timestamp())
        message.setField(transact_time) #60
        endTime = str(datetime.now() + td(minutes = 30)).replace('-','').replace(' ','-').split('.')[0]
        message.setField(6063,kwargs.get('EndTime',endTime))
        #message.setField(fix.ExDestination('CN')) #100
        message.setField(fix.SecurityType('CS')) #167
        if kwargs.get('Text',None) != None:
            message.setField(fix.Text(kwargs.get('Text'))) #58
        message = self.set_trailer(message,219)
        return message
    
    #** client side **
    def create_cancelorder_msg(self,**kwargs):
        """ Description : CancelOrder request message
            Params:
                **kwargs -- dynamic param dict
            Return:  message object.   
        """
        self.logger.debug("Inside CancelOrder")
        self.MsgType = 'F'
        self.BodyLength = 229
        message = fix.Message()
        message = self.set_header(message)
        message.setField(fix.ClOrdID(kwargs['ClOrdID'])) #11
        message.setField(fix.HandlInst('1'))
        message.setField(fix.IDSource('2')) #22
        message.setField(fix.OrderQty(kwargs['OrderQty'])) #38
        message.setField(fix.OrigClOrdID(kwargs['OrigClOrdID'])) #41
        #message.setField(fix.SecurityID(str(kwargs.get('SecurityID')))) 
        message.setField(fix.SecurityID("B02RK08")) #48
        message.setField(fix.Symbol(kwargs['Symbol'])) #55
        message.setField(fix.Side('1')) #54
        transact_time = fix.TransactTime()
        transact_time.setString(self.util.cur_timestamp())
        message.setField(transact_time) #60
        message.setField(fix.SecurityType('CS')) #167
        message.setField(fix.Text("CancelOrder Request"))
        message = self.set_trailer(message,197)
        return message
    
    #** client side **
    def create_replaceorder_msg(self,**kwargs):
        """ Description : ReplaceOrder request message
            Params:
                **kwargs -- dynamic param dict
            Return:  message object.  
        """
        self.logger.debug("Inside ReplaceOrder")
        self.BodyLength = 265
        self.MsgType = 'G'
        message = fix.Message()
        message = self.set_header(message)
        message.setField(fix.Account('JPM')) #1
        message.setField(fix.ClOrdID(kwargs.get('ClOrdID',None))) #11
        message.setField(fix.Currency(kwargs.get("Currency"))) #15
        message.setField(fix.HandlInst('1')) #21
        message.setField(fix.IDSource('2')) #22
        message.setField(fix.OrderQty(kwargs.get('OrderQty',0))) #38
        message.setField(fix.OrdType(kwargs.get('OrdType','1'))) #40
        message.setField(fix.Price(kwargs.get('Price',0)))
        message.setField(fix.OrigClOrdID(kwargs.get('OrigClOrdID',None))) #41
        message.setField(fix.SecurityID(str(kwargs.get('SecurityID')))) 
        #message.setField(fix.SecurityID('2046251')) #AAPL Cusip : 037833100 , Sedol : 2046251
        message.setField(fix.Side('1')) #54
        message.setField(fix.Symbol(kwargs.get('Symbol',None))) #55
        message.setField(fix.TimeInForce('0')) #59
        transact_time = fix.TransactTime()
        transact_time.setString(self.util.cur_timestamp())
        message.setField(transact_time) #60
        message.setField(fix.Text('ReplaceOrder Request')) #58
        message.setField(fix.SecurityType('CS')) #167
        message = self.set_trailer(message,36)
        return message
    
    # ** Server Side **
    def AckNewOrder(self,NewOrd_Obj):
        """ Description : NewOrder acknowledgement message
            Params:
                NewOrd_Obj -- NewOrder object to be acknowledged by server.
            Return:  message object.   
        """
        self.logger.debug("Inside AckNewOrder")
        self.MsgType = '8'
        self.BodyLength = 228
        NewOrd_Obj.OrdStatus = '0'
        message = fix.Message()
        Price = NewOrd_Obj.Price if NewOrd_Obj.Price != None else 0.0
        sender,target = NewOrd_Obj.SenderCompID, NewOrd_Obj.TargetCompID
        self.logger.debug("Sender : %s"%target)
        self.logger.debug("Target : %s"%sender)
        message = self.set_header(message,sender,target)
        message.setField(fix.CumQty(NewOrd_Obj.CumQty))
        message.setField(fix.Currency(NewOrd_Obj.Currency))
        message.setField(fix.ExecTransType('0'))
        message.setField(fix.ExecID(NewOrd_Obj.ClOrdID))
        message.setField(fix.IDSource(NewOrd_Obj.IDSource))
        message.setField(fix.LastQty(NewOrd_Obj.LastQty))
        message.setField(fix.OrderID(NewOrd_Obj.ClOrdID)) #Unique Identifier assigned by sell-side
        message.setField(fix.ClOrdID(NewOrd_Obj.ClOrdID))
        message.setField(fix.OrderQty(NewOrd_Obj.OrderQty))
        message.setField(fix.OrdStatus(NewOrd_Obj.OrdStatus))
        message.setField(fix.OrdType(NewOrd_Obj.OrdType))
        message.setField(fix.SecurityID(NewOrd_Obj.SecurityID))
        message.setField(fix.Price(Price))
        message.setField(fix.Symbol(NewOrd_Obj.Symbol))
        message.setField(fix.Side(NewOrd_Obj.Side))
        message.setField(fix.TimeInForce(NewOrd_Obj.TimeInForce))
        transact_time = fix.TransactTime()
        transact_time.setString(self.util.cur_timestamp()) #current time
        message.setField(transact_time)
        NewOrd_Obj.ExecType = '0'
        message.setField(fix.ExecType(NewOrd_Obj.ExecType)) 
        message.setField(fix.LeavesQty(NewOrd_Obj.LeavesQty))
        message.setField(fix.AvgPx(NewOrd_Obj.AvgPx))
        message.setField(fix.SecurityType(NewOrd_Obj.SecurityType))
        message.setField(fix.Text("NewOrder Acknowledgement"))
        message = self.set_trailer(message,219)
        return message
    
    def AckCancelOrder(self,Cancel_Obj, Ord_Cancelled):
        """ Description : CancelOrder acknowledgement message
            Params:
                Cancel_Obj -- CancelOrder object carried request 
                              to cancel target order.
                Ord_Cancelled -- order to be cancelled.
            Return:  message object.   
        """
        self.logger.debug("Inside AckCancelOrder")
        self.MsgType = '8'
        self.BodyLength = 361
        self.SenderSubID = 'ALGO'
        ID = self.util.gen_id()
        Cancel_Obj.OrderID, Cancel_Obj.ExecID = ID, ID
        message = fix.Message()
        sender,target = Cancel_Obj.SenderCompID, Cancel_Obj.TargetCompID
        self.logger.debug("Sender : %s"%target)
        self.logger.debug("Target : %s"%sender)
        message = self.set_header(message,sender,target)
        message.setField(fix.Account(Ord_Cancelled.Account)) #1
        message.setField(fix.AvgPx(Ord_Cancelled.AvgPx)) #6
        message.setField(fix.ClOrdID(Cancel_Obj.ClOrdID)) #11
        message.setField(fix.CumQty(Ord_Cancelled.CumQty)) #14
        message.setField(fix.Currency(Ord_Cancelled.Currency)) #15
        message.setField(fix.ExecID(Cancel_Obj.ExecID)) #17 
        message.setField(fix.ExecTransType('1')) #20
        message.setField(fix.IDSource(Ord_Cancelled.IDSource)) #22
        message.setField(fix.LastPx(Ord_Cancelled.LastPx)) #31
        message.setField(fix.LastQty(Ord_Cancelled.LastQty)) #32
        message.setField(fix.OrderID(Cancel_Obj.OrderID)) #37
        message.setField(fix.OrderQty(Ord_Cancelled.OrderQty)) #38
        message.setField(fix.OrdStatus(Ord_Cancelled.OrdStatus)) #39
        message.setField(fix.OrigClOrdID(Cancel_Obj.OrigClOrdID)) #41
        message.setField(fix.SecurityID(Ord_Cancelled.SecurityID)) #48
        message.setField(fix.Side(Cancel_Obj.Side)) #54
        message.setField(fix.Symbol(Ord_Cancelled.Symbol)) #55
        message.setField(fix.Text("Order Cancelled")) #58
        message.setField(fix.TimeInForce(Ord_Cancelled.TimeInForce)) #59
        transact_time = fix.TransactTime()
        transact_time.setString(self.util.cur_timestamp())
        message.setField(transact_time) #60 #add current time
        message.setField(fix.TradeDate(str(datetime.utcnow()).split()[0].replace('-',''))) #today's date
        message.setField(fix.ExecType(Ord_Cancelled.ExecType)) #150 
        message.setField(fix.LeavesQty(Ord_Cancelled.LeavesQty)) #151 
        message.setField(fix.SecurityType('CS')) #167
        message = self.set_trailer(message,184)
        return message
    
    def UnsolicitedCancelMsg(self, Ord_Cancelled):
        """ Description : UnsolicitedCancel order acknowledgement message,
                          Cancelling order if no cancel request received
                          during waiting for cancel.
            Params:
                Ord_Cancelled -- order to be Unsolicitly cancelled.
            Return:  message object.   
        """
        self.logger.debug("Inside UnsolicitedCancel")
        self.MsgType = '8'
        self.BodyLength = 338
        self.SenderSubID = 'ALGO'
        Ord_Cancelled.LeavesQty = 0
        Ord_Cancelled.Text = "** Unsolicited Cancel by Server **"
        message = fix.Message()
        sender,target = Ord_Cancelled.SenderCompID, Ord_Cancelled.TargetCompID
        self.logger.debug("Sender : %s"%target)
        self.logger.debug("Target : %s"%sender)
        message = self.set_header(message,sender,target)
        message.setField(fix.Account(Ord_Cancelled.Account)) #1
        message.setField(fix.AvgPx(Ord_Cancelled.AvgPx)) #6
        message.setField(fix.ClOrdID(Ord_Cancelled.ClOrdID)) #11
        message.setField(fix.CumQty(Ord_Cancelled.CumQty)) #14
        message.setField(fix.Currency(Ord_Cancelled.Currency)) #15
        message.setField(fix.ExecID(Ord_Cancelled.ClOrdID)) #17
        message.setField(fix.ExecTransType('1')) #20
        message.setField(fix.IDSource(Ord_Cancelled.IDSource)) #22
        message.setField(fix.LastPx(Ord_Cancelled.LastPx)) #31
        message.setField(fix.LastQty(Ord_Cancelled.LastQty)) #32
        message.setField(fix.OrderID(Ord_Cancelled.ClOrdID)) #37
        message.setField(fix.OrderQty(Ord_Cancelled.OrderQty)) #38
        message.setField(fix.OrdStatus(Ord_Cancelled.OrdStatus)) #39
        message.setField(fix.OrdType(Ord_Cancelled.OrdType)) #40
        message.setField(fix.SecurityID(Ord_Cancelled.SecurityID)) #48
        message.setField(fix.Side(Ord_Cancelled.Side)) #54
        message.setField(fix.Symbol(Ord_Cancelled.Symbol)) #55
        message.setField(fix.Text(Ord_Cancelled.Text)) #58
        message.setField(fix.TimeInForce(Ord_Cancelled.TimeInForce)) #59
        transact_time = fix.TransactTime()
        transact_time.setString(self.util.cur_timestamp())
        message.setField(transact_time) #60 #add current time
        message.setField(fix.TradeDate(str(datetime.utcnow()).split()[0].replace('-',''))) #today's date
        message.setField(fix.ExecType(Ord_Cancelled.OrdStatus)) #150 
        message.setField(fix.LeavesQty(Ord_Cancelled.LeavesQty)) #151 
        message.setField(fix.SecurityType('CS')) #167
        message = self.set_trailer(message,168)
        return message
    
    def AckReplaceOrder(self, Replace_Ord):
        """ Description : Replace order acknowledgement message,
                          Acknowledging that order has been replaced.
            Params:
                Replace_Ord -- Object of Replaced order.
            Return:  message object.   
        """
        self.logger.debug("Inside AckReplaceOrder")
        self.MsgType = '8'
        self.BodyLength = 365
        ID = self.util.gen_id()
        Replace_Ord.OrderID, Replace_Ord.ExecID = ID, ID
        message = fix.Message()
        sender,target = Replace_Ord.SenderCompID, Replace_Ord.TargetCompID
        self.logger.debug("Sender : %s"%target)
        self.logger.debug("Target : %s"%sender)
        message = self.set_header(message,sender,target)
        message.setField(fix.Account(Replace_Ord.Account)) #1
        message.setField(fix.AvgPx(Replace_Ord.AvgPx)) #6
        message.setField(fix.ClOrdID(Replace_Ord.ClOrdID)) #11
        message.setField(fix.CumQty(Replace_Ord.CumQty)) #14
        message.setField(fix.Currency(Replace_Ord.Currency)) #15
        message.setField(fix.ExecID(Replace_Ord.ExecID)) #17
        message.setField(fix.ExecTransType('0'))#20
        message.setField(fix.IDSource('2')) #22
        message.setField(fix.LastPx(Replace_Ord.LastPx)) #31
        message.setField(fix.LastQty(Replace_Ord.LastQty)) #32
        message.setField(fix.OrderID(Replace_Ord.OrderID)) #37
        message.setField(fix.OrderQty(Replace_Ord.OrderQty)) #38
        message.setField(fix.OrdStatus(Replace_Ord.OrdStatus)) #39
        message.setField(fix.OrdType(Replace_Ord.OrdType))
        message.setField(fix.OrigClOrdID(Replace_Ord.OrigClOrdID)) #41
        message.setField(fix.SecurityID(Replace_Ord.SecurityID)) #48
        message.setField(fix.Price(Replace_Ord.Price))#44
        message.setField(fix.Side(Replace_Ord.Side)) #54
        message.setField(fix.Symbol(Replace_Ord.Symbol)) #55
        message.setField(fix.Text("Order Replaced")) #58
        message.setField(fix.TimeInForce(Replace_Ord.TimeInForce)) #59
        transact_time = fix.TransactTime()
        transact_time.setString(self.util.cur_timestamp())
        message.setField(transact_time) #60 #add current time
        message.setField(fix.TradeDate(str(datetime.utcnow()).split()[0].replace('-','')))
        Replace_Ord.ExecType = '5'
        message.setField(fix.ExecType(Replace_Ord.ExecType)) #150 #add
        message.setField(fix.LeavesQty(Replace_Ord.LeavesQty)) #151 #add
        message.setField(fix.SecurityType('CS')) #167
        message = self.set_trailer(message, 17)
        return message
    
    def Fill(self,OrderObj,Qty,Price):
        """ Description : Fill acknowledgement message,
                          Acknowledging that order has filled partially/completely.
            Params:
                OrderObj -- Order object that has filled.
                Qty      -- Quantity that has filled.
                Price    -- Price per unit.
            Return:  message object.   
        """
        self.logger.debug("Inside Fill")
        OrderObj.update_qty(Qty)
        OrderObj.update_fill_qty_and_price(Qty,Price)
        OrderObj.LastMkt = 'ARCX'
        ID = self.util.gen_id()
        OrderObj.OrderID, OrderObj.ExecID = ID, ID
        if OrderObj.LeavesQty == 0: OrderObj.OrdStatus = '2'
        text = "Partial Fill" if OrderObj.OrdStatus == '1' else "Complete Fill"
        OrderObj.ExecType = OrderObj.OrdStatus
        self.MsgType = '8'
        message = fix.Message()
        sender,target = OrderObj.SenderCompID, OrderObj.TargetCompID
        self.logger.debug("Sender : %s"%target)
        self.logger.debug("Target : %s"%sender)
        message = self.set_header(message,sender,target)
        message.setField(fix.CumQty(OrderObj.CumQty)) #14 #add
        message.setField(fix.Currency(OrderObj.Currency)) #15 
        message.setField(fix.ExecID(OrderObj.ExecID)) #17 #add
        message.setField(fix.ExecTransType('0')) #20
        message.setField(fix.IDSource(OrderObj.IDSource)) #22
        message.setField(fix.LastMkt(OrderObj.LastMkt)) #30 #add
        message.setField(fix.LastPx(OrderObj.LastPx)) #31 add    Price of last Fill
        message.setField(fix.LastQty(OrderObj.LastQty)) #32 #add
        message.setField(fix.ClOrdID(OrderObj.ClOrdID))
        message.setField(fix.OrderID(OrderObj.OrderID)) #37 #add
        message.setField(fix.OrderQty(int(OrderObj.OrderQty))) #38 #add
        message.setField(fix.OrdStatus(OrderObj.OrdStatus)) #39 #add 
        message.setField(fix.OrdType(OrderObj.OrdType)) #40   
        message.setField(fix.Price(np.nan_to_num(OrderObj.Price))) #44 
        message.setField(fix.SecurityID(OrderObj.SecurityID)) #48 
        message.setField(fix.Symbol(OrderObj.Symbol)) #55 
        message.setField(fix.Side(OrderObj.Side)) #54 #add
        message.setField(fix.TimeInForce('0')) #59
        transact_time = fix.TransactTime()
        transact_time.setString(self.util.cur_timestamp()) #replace this with current time
        message.setField(transact_time) #60 
        message.setField(fix.ExecType(OrderObj.ExecType)) #150 #add
        message.setField(fix.LeavesQty(OrderObj.LeavesQty)) #151 #add
        message.setField(fix.AvgPx(OrderObj.AvgPx)) #6 #add
        message.setField(fix.SecurityType('CS')) #167
        message.setField(fix.Text(text)) #58
        message = self.set_trailer(message,230)
        return message

    
    def ErrorMsg(self,OrderObj):
        """ Description : Acknowledging that request/order raised an error.
                          
            Params:
                OrderObj -- Order object that raised error.
            Return:  message object.   
        """
        self.logger.debug("Inside ErrorMsg")
        self.MsgType = '8'
        ID = self.util.gen_id()
        OrderObj.OrdStatus, OrderObj.ExecType = '8', '8'
        OrderObj.OrderID, OrderObj.ExecID = ID, ID
        message = fix.Message()
        sender,target = OrderObj.SenderCompID, OrderObj.TargetCompID
        self.logger.debug("Sender : %s"%target)
        self.logger.debug("Target : %s"%sender)
        message = self.set_header(message,sender,target)
        message.setField(fix.OrderID(OrderObj.OrderID))
        message.setField(fix.ClOrdID(OrderObj.ClOrdID))
        message.setField(fix.ExecID(OrderObj.ExecID))
        message.setField(fix.Symbol(OrderObj.Symbol))
        message.setField(fix.ExecTransType('3'))
        message.setField(fix.ExecType(OrderObj.ExecType))
        message.setField(fix.OrdStatus(OrderObj.OrdStatus))
        message.setField(fix.Side(OrderObj.Side))
        message.setField(fix.LeavesQty(0))
        message.setField(fix.CumQty(0))
        message.setField(fix.AvgPx(0))
        message.setField(fix.Text(OrderObj.Text))
        message = self.set_trailer(message,219)
        return message
    
    def RejectNewOrder(self,OrderObj): #Rejects New Order
        """ Description : Acknowledging that NewOrder is reject for some reason.
                          
            Params:
                OrderObj -- NewOrder object that is rejected.
            Return:  message object.   
        """
        self.logger.debug("Inside RejectNewOrder")
        self.MsgType = '8'
        ID = self.util.gen_id()
        OrderObj.OrderID, OrderObj.ExecID = ID, ID
        OrderObj.OrdStatus, OrderObj.ExecType = '8', '8'
        message = fix.Message()
        sender,target = OrderObj.SenderCompID, OrderObj.TargetCompID
        self.logger.debug("Sender : %s"%target)
        self.logger.debug("Target : %s"%sender)
        message = self.set_header(message,sender,target)
        message.setField(fix.OrderID(OrderObj.OrderID))
        message.setField(fix.ClOrdID(OrderObj.ClOrdID))
        message.setField(fix.ExecID(OrderObj.ExecID))
        message.setField(fix.ExecTransType('3'))
        message.setField(fix.ExecType(OrderObj.ExecType))
        message.setField(fix.OrdStatus(OrderObj.OrdStatus))
        message.setField(fix.Side(OrderObj.Side))
        message.setField(fix.Symbol(OrderObj.Symbol))
        message.setField(fix.LeavesQty(0))
        message.setField(fix.CumQty(0))
        message.setField(fix.AvgPx(0))
        message.setField(fix.Text(OrderObj.Text))
        message = self.set_trailer(message,219)
        return message
    
    def Reject(self,OrderObj): #Reject Cancel or Replace
        """ Description : Acknowledging that request for Cancelling or
                          Replacing an order has been rejected.        
            Params:
                OrderObj -- Cancel/Replace request order object that has been rejected.
            Return:  message object.   
        """
        self.logger.debug("Reject: Cancel/Replace")
        self.MsgType = '9'
        ID = self.util.gen_id()
        OrderObj.OrdStatus, OrderObj.ExecType = '8', '8'
        OrderObj.OrderID, OrderObj.ExecID = ID, ID
        CxlRejRes = '1' if OrderObj.MsgType == 'F' else '2'
        message = fix.Message()
        sender,target = OrderObj.SenderCompID, OrderObj.TargetCompID
        self.logger.debug("Sender : %s"%target)
        self.logger.debug("Target : %s"%sender)
        message = self.set_header(message,sender,target)
        message.setField(fix.OrderID(OrderObj.OrderID))
        message.setField(fix.ClOrdID(OrderObj.ClOrdID))
        message.setField(fix.OrigClOrdID(OrderObj.OrigClOrdID))
        message.setField(fix.OrdStatus(OrderObj.OrdStatus))
        message.setField(fix.CxlRejResponseTo(CxlRejRes))
        message.setField(fix.Text(OrderObj.Text))
        message = self.set_trailer(message,219)
        return message
    
    def InvalidMsgType(self,msg): #Reject Invalid MsgTpye
        """ Description : Acknowledging that request message type is Invalid.        
            Return:  message object.   
        """
        self.logger.debug("Rejected : MsgType Invalid")
        self.MsgType = '9'
        item = fix.ClOrdID()
        SenderCompID = fix.SenderCompID()
        TargetCompID = fix.TargetCompID()
        msg.getField(item)
        msg.getHeader().getField(SenderCompID)
        msg.getHeader().getField(TargetCompID)
        sender,target,ClOrdID = SenderCompID.getValue(),TargetCompID.getValue(),item.getString()
        message = fix.Message()
        message = self.set_header(message,sender,target)
        message.setField(fix.OrderID("None"))
        message.setField(fix.ClOrdID(ClOrdID))
        message.setField(fix.OrigClOrdID("None"))
        message.setField(fix.OrdStatus('8'))
        message.setField(fix.CxlRejResponseTo('1'))
        message.setField(fix.Text("Rejected : MsgType Invalid"))
        message = self.set_trailer(message,219)
        return message
    
    def InvalidTicker(self,OrderObj): #Reject
        """ Description : Acknowledging that order has InvalidTicker.
            Params:
                OrderObj -- Order object that raised above error.
            Return:  message object.   
        """
        self.logger.debug("Reject: Invalid Ticker")
        self.MsgType = '8'
        ID = self.util.gen_id()
        OrderObj.OrdStatus, OrderObj.ExecType = '8', '8'
        OrderObj.OrderID, OrderObj.ExecID = ID, ID
        message = fix.Message()
        sender,target = OrderObj.SenderCompID, OrderObj.TargetCompID
        self.logger.debug("Sender : %s"%target)
        self.logger.debug("Target : %s"%sender)
        message = self.set_header(message,sender,target)
        message.setField(fix.OrderID(OrderObj.OrderID))
        message.setField(fix.ClOrdID(OrderObj.ClOrdID))
        message.setField(fix.ExecID(OrderObj.ExecID))
        message.setField(fix.ExecTransType('3'))
        message.setField(fix.ExecType(OrderObj.ExecType))
        message.setField(fix.OrdStatus(OrderObj.OrdStatus))
        message.setField(fix.Side(OrderObj.Side))
        message.setField(fix.Symbol(OrderObj.Symbol))
        message.setField(fix.LeavesQty(0))
        message.setField(fix.CumQty(0))
        message.setField(fix.AvgPx(0))
        message.setField(fix.Text(OrderObj.Text))
        message = self.set_trailer(message,219)
        return message
    
    def InvalidDate(self,OrderObj): #Reject
        """ Description : Acknowledging that order has InvalidDate
                          i.e. date specified has passed already.
            Params:
                OrderObj -- Order object that raised error.
            Return:  message object.   
        """
        self.logger.debug("Reject: Invalid Dates")
        self.MsgType = '8'
        ID = self.util.gen_id()
        OrderObj.OrdStatus, OrderObj.ExecType = '8', '8'
        OrderObj.OrderID, OrderObj.ExecID = ID, ID
        message = fix.Message()
        sender,target = OrderObj.SenderCompID, OrderObj.TargetCompID
        self.logger.debug("Sender : %s"%target)
        self.logger.debug("Target : %s"%sender)
        message = self.set_header(message,sender,target)
        message.setField(fix.OrderID(OrderObj.OrderID))
        message.setField(fix.ClOrdID(OrderObj.ClOrdID))
        message.setField(fix.ExecID(OrderObj.ExecID))
        message.setField(fix.ExecTransType('3'))
        message.setField(fix.ExecType(OrderObj.ExecType))
        message.setField(fix.OrdStatus(OrderObj.OrdStatus))
        message.setField(fix.Side(OrderObj.Side))
        message.setField(fix.Symbol(OrderObj.Symbol))
        message.setField(fix.LeavesQty(0))
        message.setField(fix.CumQty(0))
        message.setField(fix.AvgPx(0))
        message.setField(fix.Text(OrderObj.Text))
        message = self.set_trailer(message,219)
        return message