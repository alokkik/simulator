import quickfix as fix
import time,os,sys,uuid,traceback,datetime
from orderFactory import *
from util import Util
from os.path import expanduser
from sessionfix import SessionFix
from rule import Rule
from datetime import datetime as dt
from datetime import timedelta as td
from Queue import Queue
import pprint
import argparse

pp = pprint.PrettyPrinter(indent=4)

class Server():
    
    def __init__(self,cfg_file,util):
        self.ordersMap = {}
        self.util = util
        self.logger = self.util.initialize_logger('server')
        self.msgInQueue = Queue() #Queue holds all incoming msgs
        self.rule = Rule(self.ordersMap,self.logger,self.util)
        self.dd = fix.DataDictionary('FIX42.xml')
        self.startServer(cfg_file)
        
    def startServer(self,cfg_file):
        """
        Description : create a sessionfix object and start server.
        Parameters:
            cfg_file -- configuration file required for server
        Return : None
        """
        try:
            self.sess_fix = SessionFix(self.onMsg)
            self.util.checkLogStorePath()
            settings = fix.SessionSettings(cfg_file)
            storeFactory = fix.FileStoreFactory(settings)
            #logFactory = fix.ScreenLogFactory(settings)
            logFactory = fix.FileLogFactory(settings)
            server = fix.SocketAcceptor(self.sess_fix, storeFactory, settings, logFactory)
            server.start()
            self.logger.debug("** Server Started **")
            self.run()
            print("** Server Stopped **")
        except:
            print(str(traceback.format_exc()))
    

    def run(self):
        """
        Description : main function, reads message in foreground
                      and processes order in background.
        """
        self.logger.debug("Begin processMsgs")
        self.logger.debug("Begin processOrders")
        self.logger.debug("Time Now : %s"%dt.now())
        while True:
            try :
                self.processMsgs()
                self.processOrders()
                time.sleep(self.util.getSleepTime())
            except :
                self.logger.debug(str(traceback.format_exc()))
        
    def onMsg(self, message):
        """
        Description : this function gets called whenever a message
                    is received from client. 
        Parameters:
            message -- instance of fix.Message, received from client 
        Return : None
        """
        self.logger.debug("** Message Recieved : **")
        self.msgInQueue.put(message.toString())
        return
    
    def createOrder(self, message):
        """
        Description : this function creates OrderObj based on
                      OrdType in message. 
        Parameters:
            message -- instance of fix.Message, received from client 
        Return : None
        """
        msg_type = fix.MsgType()
        message.getHeader().getField(msg_type)
        OrderObj = None
        if msg_type.getValue() == 'D':#NewOrder
            OrderObj = NewOrder(message,self.util)
        elif msg_type.getValue() == 'F':#CancelOrder
            OrderObj = CancelOrder(message,self.util)
        elif msg_type.getValue() == 'G':#ReplaceOrder
            OrderObj = ReplaceOrder(message,self.util)
        else:
            message = self.rule.invalidMsgType(message)
            fix.Session.sendToTarget(message,self.getMessageSession(message))
        return OrderObj
      
    def processMsgs(self):
        """
        Description : runs in foreground and process messages from msgInQueue. 
        Return : None
        """
        #take the order msgs out of the queue and put it in your dict
        while self.msgInQueue.qsize() != 0:
            msg = self.msgInQueue.get()
            fixMsg = fix.Message(msg, self.dd, False)
            order = self.createOrder(fixMsg)
            if order == None:return
            if order.ClOrdID not in self.ordersMap:
                self.ordersMap[order.ClOrdID] = order
            else:
                message = self.rule.reject(order,"OrderDuplicateError")
                fix.Session.sendToTarget(message,self.getMessageSession(message))
        return

    def processOrders(self):
        """
        Description : runs in background and process orders from ordersMap.     
        Return : message object.
        """
        for order in self.ordersMap.values():
        #figure out what action is required for each order, and then take the appropriate action, and send the msg back
            if order.isActive():
                #Orders which are new to the system and not already in queue "waiting"
                if hasattr(order,"Epoch") and order.Epoch >= dt.now(timezone(self.util.getTimeZone(order.Currency))): 
                    continue
                self.logger.debug("Order to Process ")
                self.logger.debug(order.__dict__)
                self.logger.debug("\n")
                message = None
                if order.isCancel(): #check if order is CancelOrder
                    message = self.rule.cancelOrd(order)
                elif order.isReplace(): #check if order is ReplaceOrder
                    message = self.rule.replaceOrd(order)
                else: 
                    #if Order is NewOrder
                    if order.TransactTime.date() < dt.today().date(): 
                        message = self.rule.reject(order,"Invalid Date : %s"%order.TransactTime)    
                    else : message = self.rule.processRule(order)
               
                message = self.util.seq(message)
                for item in message:
                    if item != None:
                        fix.Session.sendToTarget(item,self.getMessageSession(item))                
        return
    
    def getMessageSession(self,message):
        """ Description : get the SessionID string from message and look for session in dict """
        BeginString  = fix.BeginString()
        SenderCompID = fix.SenderCompID()
        TargetCompID = fix.TargetCompID()
        message.getHeader().getField(BeginString)
        message.getHeader().getField(SenderCompID)
        message.getHeader().getField(TargetCompID)
        sess = BeginString.getValue()+':'+SenderCompID.getValue()+"->"+TargetCompID.getValue()
        return self.sess_fix.SessionDict[sess]
    
def run(env):
    """ Description : runs the server program. """
    try:
        cfg_file = 'server.cfg'
        custom_file = 'custom.cfg'
        util = Util(env,custom_file,'server')
        os.chdir(util.getPath())
        app = Server(env+"_"+cfg_file,util)
    except Exception as e:
        print(e)


if __name__ == '__main__':
   env = 'test'
   parser = argparse.ArgumentParser(description='FIX Server')
   parser.add_argument('--env', type=str, default=env, dest='env', help='env paper/test')
   args = parser.parse_args()
   if args.env:
     env = args.env
   assert env in ['test', 'test2', 'paper', 'paper2']
   run(env)