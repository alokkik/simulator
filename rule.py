import quickfix as fix
from action import Action
from pytz import timezone
from datetime import datetime as dt
from datetime import timedelta as td

class Rule(Action):
    
    def __init__(self,ordersMap,logger,util):
        self.logger = logger
        self.util = util
        Action.__init__(self,ordersMap,logger,util)
    
    def processRule(self,OrderObj):
        """
        Description : takes action according to rule in "Rule" queue.
        Parameters:  
            OrderObj -- Order (New/Replace/Cancel)
        Return : message object
        """
        message = None
        if not OrderObj.Rule:
            OrderObj.OrdStatus = '3'
            return
        if OrderObj.Rule[0] == 'new':
            message = self.new(OrderObj)
            OrderObj.Rule.pop(0)
            
        elif OrderObj.Rule[0] == 'rej':
            message = self.reject(OrderObj,"Order Rejected")
            OrderObj.Rule.pop(0)

        elif OrderObj.Rule[0] == 'rpl':
            OrderObj.Rule.pop(0)
            
        elif OrderObj.Rule[0] == 'cxl':
            message = self.unsolicitedcancel(OrderObj)
            OrderObj.Rule.pop(0)
        
        elif OrderObj.Rule[0] == 'rej-rpl':
            OrderObj.Rule.pop(0)
        
        elif OrderObj.Rule[0] == 'rej-cxl':
            OrderObj.Rule.pop(0)
            
        elif OrderObj.Rule[0] == 'wait':
            self.logger.debug("** waiting.. **")
            OrderObj.Epoch = dt.now(timezone(self.util.getTimeZone(OrderObj.Currency))) + td(seconds=int(OrderObj.Rule[1]))
            if self.util.isIndex(OrderObj.Rule,2) and OrderObj.Rule[2] == 'rej-rpl':
                OrderObj.ReplaceAfter = dt.now(timezone(self.util.getTimeZone(OrderObj.Currency))) + td(seconds=int(OrderObj.Rule[1]))
                del OrderObj.Rule[:2]
                
            elif self.util.isIndex(OrderObj.Rule,2) and OrderObj.Rule[2] == 'rej-cxl':
                OrderObj.CancelAfter = dt.now(timezone(self.util.getTimeZone(OrderObj.Currency))) + td(seconds=int(OrderObj.Rule[1]))
                del OrderObj.Rule[:2]   
            else:
                del OrderObj.Rule[:2]
                
        elif OrderObj.Rule[0] == 'pfill':
            message = self.pfill(OrderObj,int(OrderObj.Rule[1]))
            del OrderObj.Rule[:2]
            
        elif OrderObj.Rule[0] == 'fill':
            message = self.fill(OrderObj)
            OrderObj.Rule.pop(0)
            
        elif OrderObj.Rule[0] == 'fillshares':
            if self.util.isIndex(OrderObj.Rule,2):
                if self.util.isNum(OrderObj.Rule[2]):
                    message = self.fillshares(OrderObj,int(OrderObj.Rule[1]),int(OrderObj.Rule[2]))
                    del OrderObj.Rule[:3]
                else:
                    message = self.fillshares(OrderObj,int(OrderObj.Rule[1]))
                    del OrderObj.Rule[:2]
            else:
                message = self.fillshares(OrderObj,int(OrderObj.Rule[1]))
                OrderObj.OrdStatus = '3'#Done for day
                del OrderObj.Rule[:2]
            
        elif OrderObj.Rule[0] == 'algo':
            if self.util.isIndex(OrderObj.Rule,2):
                message = self.algo(OrderObj,OrderObj.Rule[1],int(OrderObj.Rule[2]))
                del OrderObj.Rule[:3]
            else:
                message = self.algo(OrderObj,OrderObj.Rule[1])
                del OrderObj.Rule[:2]
        else:
            message = self.reject(OrderObj,"OrderRejected : Invalid Instruction")
        return message