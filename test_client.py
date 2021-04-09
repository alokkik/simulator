import trd
import pprint
import numpy as np
from util import Util
import quickfix as fix
import time,os,sys
from numpy import random
from pytz import timezone
from datetime import datetime
from datetime import timedelta
from sessionfix import SessionFix
from message_factory import MessageFactory
pp = pprint.PrettyPrinter(indent=4)

class Client():
    
    def __init__(self,cfg_file,util):
        self.util = util
        self.logger = self.util.initialize_logger("client")
        self.MsgFct = MessageFactory(self.logger,util)
        self.startClient(cfg_file)
        
    def startClient(self, cfg_file):
        """
        Description : create a sessionfix object and start client.
        Keyword Arguments:
            cfg_file -- configuration file required for client
        Return : None
        """
        self.sess_fix = SessionFix(self.onMsg)
        self.util.checkLogStorePath()
        settings = fix.SessionSettings(cfg_file)
        storeFactory = fix.FileStoreFactory(settings)
        #logFactory = fix.ScreenLogFactory(settings)
        logFactory = fix.FileLogFactory(settings)
        client = fix.SocketInitiator(self.sess_fix,storeFactory,settings,logFactory)
        try:
            client.start()
            self.logger.debug("** Client Started **")
            time.sleep(5)
            self.run()
        except Exception as e:
            print(e)

    
    def run(self):
        """ Description : main function,runs the test_functions """
        self.logger.debug("** Begins Loop **")
        while True:
            self.test_function0()
            self.util.wait(self.util.getSleepTime()) #seconds
            
    def onMsg(self, message):
        """
        Description : this function gets called whenever a message
                    is received from server. 
        Keyword Arguments:
            message -- instance of fix.Message, received from server 
        Return : None
        """
        self.logger.debug("** Message Recieved from Server :**")
        text = fix.Text()
        message.getField(text)
        self.logger.debug("** Message :  %s **"%text.getValue())
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("\n")
        return
    
    def test_function0(self):
        sedol = self.util.dfMap['us'].id_sedol1
        bbid = self.util.dfMap['us'].bbid
        num = random.randint(0,len(sedol))
        rule = "s:new algo vwap 101"
        ClOrdID = self.util.gen_id()
        endTime = str(datetime.now(timezone(self.util.getTimeZone('us'))) + timedelta(minutes = 2)).replace('-','').replace(' ','-').split('.')[0]
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',OrderQty = 999,\
                                                  SecurityID = sedol[num],Symbol=bbid[num].split()[0],Currency='USD',EndTime = endTime)
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function1(self):
        #this function tests for NewOrder Placement and get its Acknowledgement and complete  fill
        #rule = "s:new wait 2 pfill 50 wait 10 fill"
        message = self.MsgFct.create_neworder_msg(ClOrdID  = self.util.gen_id(),OrdType = "1",OrderQty =199 ,Symbol='4206')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function1a(self):
        #this function test for NewOrder Placement followed by its Ack -> wait 2 sec-> part fill 50% -> wait for 20 sec replace -> complete fill
        rule = "s:new wait 2 pfill 50 wait 20 rpl fill"
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(ClOrdID  = ClOrdID,OrdType = '1',OrderQty = 199 ,Symbol='AAPL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(8)
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = self.util.gen_id(),OrigClOrdID=ClOrdID,OrdType = '1',OrderQty=500,Symbol='AAPL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        
#         self.util.wait(0.25)
#         message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=500,OrigClOrdID=ClOrdID,Symbol='AAPL') #cancel above order
#         self.sess_fix.send_msg(message)
#         self.logger.debug(self.util.pretty_print_msg(message))
#         self.logger.debug("** CancelOrder Request Sent **") 
        return
    
    def test_function2(self):
        #this function test for NewOrder Placement followed by its Ack -> wait 20 sec-> followed by Unsolicited Cancel
        rule = "s:new wait 20 cxl"
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID = self.util.gen_id(),OrdType = '2',Price = 65,OrderQty = 99 ,Symbol='GOOGL')
        self.sess_fix.send_msg(message)
        self.logger.debug(util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    
    def test_function3(self):
        rule = "s:new wait 600 cxl"
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID = ClOrdID,OrderQty = 500 ,Symbol='AAPL')
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        self.sess_fix.send_msg(message)
        
        self.util.wait(5)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=500,OrigClOrdID=ClOrdID,Symbol='AAPL') #cancel above order
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        return
    
    def test_function4(self):
        #this function test for NewOrder Placement, When rule is not provided
        message = self.MsgFct.create_neworder_msg(ClOrdID  = self.util.gen_id(),OrderQty = 99 ,Symbol='AAPL')
        self.logger.debug(self.util.pretty_print_msg(message))
        self.sess_fix.send_msg(message)
        return
    
    def test_function5(self):
        #this function test for NewOrder Placement followed by its Ack -> wait 2 sec-> part fill 50% -> wait for 20 sec replace -> Replace Reject 
        rule = "s:new wait 2 pfill 50 wait 20 rpl fill"
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrderQty = 199 ,Symbol='AAPL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(15)
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = self.util.gen_id(),OrigClOrdID=ClOrdID,OrderQty=50,Symbol='AAPL')#OrderQty<CumQty
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        return
    
    def test_function6(self):
        rule = "s:new wait 2 pfill 50 wait 20 rpl fill"
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrderQty = 199 ,Symbol='AAPL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(15)
        ClOrdID2 = self.util.gen_id()
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = ClOrdID2,OrigClOrdID=ClOrdID,OrderQty=500,Symbol='AAPL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        
        self.util.wait(60)
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = self.util.gen_id(),OrigClOrdID=ClOrdID2,OrderQty=1000,Symbol='AAPL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        return
    
    def test_function7(self):
        # test a long rule
        rule = 's:new wait 5 pfill 10 wait 5 pfill 10 wait 5 pfill 10 wait 5 pfill 10 wait 5 \
                                        pfill 10 wait 5 pfill 10 wait 5 pfill 10 wait 5 pfill 10 wait 5 pfill 10 wait 5 fill'
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrderQty = 1000 ,Symbol='SIRI')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(8)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=99,OrigClOrdID=ClOrdID,Symbol='SIRI') 
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **")
        
        util.wait(2)
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = self.util.gen_id(),OrigClOrdID=ClOrdID,OrderQty=1000,Symbol='SIRI')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        return
    
    def test_function8(self):
        #test another long rule 
        message = self.MsgFct.create_neworder_msg(ClOrdID  = self.util.gen_id(),OrderQty = 1000 ,Symbol='TSLA')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function9(self):
        #tests when rule = None and Symbol doesn't match to any format, execute " default : new wait 2 fill "
        message = self.MsgFct.create_neworder_msg(ClOrdID  = self.util.gen_id(),OrderQty = 1000 ,Symbol='BEAT')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function10(self):
        #tests rej-rpl
        rule ='s:new wait 30 rej-rpl'
        ClOrdID  = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrderQty = 50 ,Symbol='T')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(15)
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = self.util.gen_id(),OrigClOrdID=ClOrdID,OrderQty=500,Symbol='T')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        
        self.util.wait(1)
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = self.util.gen_id(),OrigClOrdID=ClOrdID,OrderQty=500,Symbol='T')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        return
    
    def test_function11(self):
        #tests rej-cxl
        rule ='s:new wait 30 rej-cxl'
        ClOrdID  = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrderQty = 50 ,Symbol='T')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(15)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=99,OrigClOrdID=ClOrdID,Symbol='T') #cancel above order
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        return
    
    def test_function12(self):
        #tests rej-cxl
        rule ='s:new wait 30 rej-cxl pfill 50 wait 2 fill'
        ClOrdID  = self.util.gen_id()
        #message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrderQty = 50 ,Symbol='T')
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrderQty = 50 ,OrdType= 1,Symbol='T',Price=100)
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(15)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=99,OrigClOrdID=ClOrdID,Symbol='T') #cancel above order
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        return
    
    def test_function13(self):
        rule = 's:wait 2 new wait 20 rpl wait 2 pfill 50'
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrderQty = 1000 ,Symbol='BDN')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(30)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=99,OrigClOrdID=ClOrdID,Symbol='BDN') #cancel above order
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        return
    
    def test_function14(self):
        rule = 's:new wait 15 rej'
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = self.util.gen_id(),OrderQty = 1000 ,Symbol='JBL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return #
    
    def test_function15(self):
        rule = 's:new wait 600 rpl wait 2 fill'
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrderQty = 10 ,Symbol='JBL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(15)
        ClOrdID2 = util.gen_id()
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = ClOrdID2,OrigClOrdID=ClOrdID,OrderQty=500,Symbol='JBL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        
        self.util.wait(30)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=99,OrigClOrdID=ClOrdID2,Symbol='JBL') 
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        return
    
    def test_function16(self):
        rule = 's:new wait 600 cxl wait 2 fill'
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrderQty = 10 ,Symbol='JPM')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(15)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=99,OrigClOrdID=ClOrdID,Symbol='JPM') 
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        return
    
    def test_function17(self):
        rule = 's:new wait 600 rpl wait 600 rpl wait 2 fill'
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',OrderQty =10 ,Symbol='JBT')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(5)
        ClOrdID2 = util.gen_id()
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = ClOrdID2,OrigClOrdID=ClOrdID,OrdType = '1',OrderQty=900,Symbol='JBT')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        
        self.util.wait(2)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=99,OrigClOrdID=ClOrdID2,Symbol='JBT') 
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        
        self.util.wait(2)
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = self.util.gen_id(),OrigClOrdID=ClOrdID2,OrdType = '1',Price=999,OrderQty=600,Symbol='JBT')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        return
    
    def test_function18(self):
        #this function tests for Invalid Ticker
        rule = "s:new wait 2 fill"
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = self.util.gen_id(),OrderQty = 99 ,Symbol='JOHN')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function19(self):
        #tests rej-rpl
        rule ='s:new wait 30 rej-rpl wait 2 fill'
        ClOrdID  = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType='1',OrderQty = 50 ,Symbol='T')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(5)
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = self.util.gen_id(),OrigClOrdID=ClOrdID,OrdType='1',OrderQty=500,Symbol='T')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        
        self.util.wait(1)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=50,OrigClOrdID=ClOrdID,OrdType='1',Symbol='T') 
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        return
    
    def test_function20(self):
        #tests rej-rpl
        rule ='s:new wait 30 rej-rpl wait 600 rpl wait 2 fill'
        ClOrdID  = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrderQty = 50,OrdType ='2',Price=100,Symbol='4206')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(1)
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = self.util.gen_id(),OrigClOrdID=ClOrdID,OrdType ='2',Price=200,OrderQty=500,Symbol='4206')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        
        self.util.wait(1)
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = self.util.gen_id(),OrigClOrdID=ClOrdID,OrdType ='2',Price=99,OrderQty=600,Symbol='4206')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        return
    
    def test_function21(self):
        #tests rej-rpl
        rule ='s:new wait 30 rej-cxl wait 10 fill'
        ClOrdID  = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrderQty = 50 ,Symbol='T')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(15)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=50,OrigClOrdID=ClOrdID,Symbol='T') 
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        
        self.util.wait(1)
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = self.util.gen_id(),OrigClOrdID=ClOrdID,OrderQty=500,Symbol='T')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        return
    
    def test_function22(self):
        #tests rej-rpl
        rule ='s:new wait 30 rej-cxl wait 600 cxl'
        ClOrdID  = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrderQty = 50 ,Symbol='T')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(15)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=50,OrigClOrdID=ClOrdID,Symbol='T') 
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        
        self.util.wait(30)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=50,OrigClOrdID=ClOrdID,Symbol='T') 
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        return
    
    
    def test_function24(self):
        rule = "s:new wait 2 pfill 50 wait 20 rpl fill"
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '2',OrderQty = 199 ,Symbol='AAPL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(15)
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = self.util.gen_id(),OrigClOrdID=ClOrdID,OrdType = '2',OrderQty=500,Symbol='AAPL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        return
    
    def test_function25(self):
        rule = "s:new wait 2 pfill 50 wait 20 rpl fill"
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',OrderQty = 199 ,Symbol='AAPL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(15)
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = self.util.gen_id(),OrigClOrdID=ClOrdID,OrdType = '1',OrderQty=500,Symbol='AAPL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        return
    
    def test_function26(self):
        #test NewOrder OrdType == 1 and Replace Order OrderType == 2
        rule = "s:new wait 2 pfill 50 wait 20 rpl fill"
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',OrderQty = 200 ,Symbol='AAPL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(15)
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = self.util.gen_id(),OrigClOrdID=ClOrdID,OrdType = '1',OrderQty=500,Symbol='AAPL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        return
    
    def test_function27(self):
        rule = "s:new wait 2 pfill 50 wait 20 rpl fill"
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',OrderQty = -5 ,Symbol='AAPL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(15)
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = self.util.gen_id(),OrigClOrdID=ClOrdID,OrdType = '1',OrderQty = 100,Symbol='AAPL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        return
    
    def test_function28(self):
        sedol = self.util.dfMap['us'].id_sedol1
        bbid = self.util.dfMap['us'].bbid
        num = random.randint(0,len(sedol))
        rule = "s:new wait 600 rej-rpl wait 600 rej-rpl  wait 600 rej-rpl cxl"
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',OrderQty = -5 ,SecurityID = sedol[num],Symbol=bbid[num].split()[0])
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(5)
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = self.util.gen_id(),OrigClOrdID=ClOrdID,OrdType = '1',\
                                                      OrderQty = 100,SecurityID = sedol[num],Symbol=bbid[num].split()[0])
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        
        self.util.wait(0.25)
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = self.util.gen_id(),OrigClOrdID=ClOrdID,OrdType = '1',\
                                                      OrderQty = 100,SecurityID = sedol[num],Symbol=bbid[num].split()[0])
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        
        self.util.wait(0.25)
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = self.util.gen_id(),OrigClOrdID=ClOrdID,OrdType = '1',\
                                                      OrderQty = 100,SecurityID = sedol[num],Symbol=bbid[num].split()[0])
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        return
    
    def test_function29(self):
        sedol = self.util.dfMap['us'].id_sedol1
        bbid = self.util.dfMap['us'].bbid
        num = random.randint(0,len(sedol))
        rule = "s:new wait 10 rej-rpl wait 10 rej-rpl wait 10 rej-rpl cxl"
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',OrderQty = 1000,SecurityID = sedol[num],Symbol=bbid[num].split()[0])
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function30(self):
        sedol = self.util.dfMap['us'].id_sedol1
        bbid = self.util.dfMap['us'].bbid
        num = random.randint(0,len(sedol))
        
        rule = "s:new wait 10 rej-rpl"
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',OrderQty = -5 ,SecurityID = sedol[num],Symbol=bbid[num].split()[0])
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function31(self):
        sedol = self.util.dfMap['us'].id_sedol1
        bbid = self.util.dfMap['us'].bbid
        num = random.randint(0,len(sedol))
        rule = "s:new wait 600 rej-cxl wait 600 rej-cxl  wait 600 rej-cxl cxl"
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',OrderQty = 10 ,SecurityID = sedol[num],Symbol=bbid[num].split()[0])
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(5)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=50,OrigClOrdID=ClOrdID,Symbol=bbid[num].split()[0]) 
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        
        self.util.wait(0.25)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=50,OrigClOrdID=ClOrdID,Symbol=bbid[num].split()[0]) 
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        
        self.util.wait(0.25)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=50,OrigClOrdID=ClOrdID,Symbol=bbid[num].split()[0]) 
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        return
    
    def test_function32(self):
        rule = "s:new wait 1 fillshares 10 100 wait 5 fill"
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',OrderQty = 1500 ,Symbol='AAPL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function33(self):
        sedol = self.util.dfMap['us'].id_sedol1
        bbid = self.util.dfMap['us'].bbid
        num = random.randint(0,len(sedol))
        rule = "s:new wait 1 fillshares 100 wait 2 fill"
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',OrderQty = 105 ,SecurityID = sedol[num],Symbol=bbid[num].split()[0])
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function34(self):
        sedol = self.util.dfMap['us'].id_sedol1
        bbid = self.util.dfMap['us'].bbid
        num = random.randint(0,len(sedol))
        rule = "s:new wait 1 fillshares 1 100 fill"
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',OrderQty = 105 ,SecurityID = sedol[num],Symbol=bbid[num].split()[0])
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function35(self):
        sedol = self.util.dfMap['us'].id_sedol1
        bbid = self.util.dfMap['us'].bbid
        num = random.randint(0,len(sedol))
        SecurityID = sedol[num],Symbol=bbid[num].split()[0]
        rule = "s:new wait 1 fillshares 1 100"
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',\
                                                  OrderQty = 90 ,SecurityID = sedol[num],Symbol=bbid[num].split()[0],Currency='USD')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function35a(self):
        sedol = self.util.dfMap['us'].id_sedol1
        bbid = self.util.dfMap['us'].bbid
        num = random.randint(0,len(sedol))
        rule = "s:new wait 1 fillshares 1 50 fill"
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',OrderQty = 90 ,Symbol='JOHN')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function36(self):
        sedol = self.util.dfMap['us'].id_sedol1
        bbid = self.util.dfMap['us'].bbid
        num = random.randint(0,len(sedol))
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(ClOrdID  = ClOrdID,OrdType = '1',OrderQty = 3000 ,SecurityID = sedol[num],Symbol=bbid[num].split()[0])
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function37(self):
        sedol = self.util.dfMap['us'].id_sedol1
        bbid = self.util.dfMap['us'].bbid
        num = random.randint(0,len(sedol))
        rule = "s:new wait 10 fillshares 100"
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',OrderQty = 90 ,SecurityID = sedol[num],Symbol=bbid[num].split()[0])
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(3)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=50,OrigClOrdID=ClOrdID,Symbol=bbid[num].split()[0]) 
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        return
    
    def test_function38(self):
        from random import randint
        g = trd.uni.secmap(datetime(2020,12,1), reg='us', use_all=True)
        tids = g.parsekyable_des_source
        for item in range(5000):
            rule = "s:new wait 2 pfill 50 wait 2 rpl fill"
            ClOrdID = self.util.gen_id()
            message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',\
                                                      OrderQty = randint(100,1000),Symbol=tids[randint(0,2992)].split()[0])
            self.sess_fix.send_msg(message)
            self.logger.debug(self.util.pretty_print_msg(message))
            self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function39(self):
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(ClOrdID  = ClOrdID,OrdType = '1',OrderQty = 100 ,Symbol='IVR')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function40(self):
        sedol = self.util.dfMap['ca'].id_sedol1
        bbid = self.util.dfMap['ca'].bbid
        num = random.randint(0,len(sedol))
        rule = "s:new algo twap"
        ClOrdID = self.util.gen_id()
        endTime = str(datetime.now() + timedelta(seconds=120)).replace('-','').replace(' ','-').split('.')[0]
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',\
                                                  OrderQty = 7777 ,SecurityID = sedol[num],Symbol=bbid[num].split()[0],EndTime = endTime)
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
    def test_function41(self):
        sedol = self.util.dfMap['us'].id_sedol1
        bbid = self.util.dfMap['us'].bbid
        num = random.randint(0,len(sedol))
        rule = "s:new algo vwap"
        ClOrdID = self.util.gen_id()
        endTime = str(datetime.now() + timedelta(seconds = 130)).replace('-','').replace(' ','-').split('.')[0]
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',\
                                                  OrderQty = 9999,SecurityID = sedol[num],Symbol=bbid[num].split()[0],EndTime = endTime)
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
    def test_function42(self):
        sedol = self.util.dfMap['us'].id_sedol1
        bbid = self.util.dfMap['us'].bbid
        num = random.randint(0,len(sedol))
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(ClOrdID  = ClOrdID,OrdType = '1',OrderQty = 10 ,Symbol=bbid[num].split()[0],SecurityID = sedol[num])
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(5)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=50,OrigClOrdID=ClOrdID,Symbol=bbid[num].split()[0]) 
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        
        self.util.wait(0.25)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=50,OrigClOrdID=ClOrdID,Symbol=bbid[num].split()[0]) 
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        
        self.util.wait(0.25)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=50,OrigClOrdID=ClOrdID,Symbol=bbid[num].split()[0]) 
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        return
    
    def test_function42b(self):
        rule = "s:new wait 20 fill"
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(ClOrdID  = ClOrdID,OrdType = '1',OrderQty = 10 ,Symbol='AAPL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(2)
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = self.util.gen_id(),OrigClOrdID=ClOrdID,OrderQty=1000,Symbol='AAPL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        return
    
    def test_function43(self):
        rule = "s:new wait 30 cxl"
        sedol = self.util.dfMap['us'].id_sedol1
        bbid = self.util.dfMap['us'].bbid
        num = random.randint(0,len(sedol))
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID = ClOrdID,OrderQty = 500 ,Symbol=bbid[num].split()[0],SecurityID = sedol[num])
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        self.sess_fix.send_msg(message)
        
        self.util.wait(1)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=500,OrigClOrdID=ClOrdID,Symbol=bbid[num].split()[0],SecurityID = sedol[num]) #cancel above order
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        return
    
    def test_function44(self):
        ids = []
        sedol = self.util.dfMap['jp'].id_sedol1
        bbid = self.util.dfMap['jp'].bbid
        for item in range(5):
            num = random.randint(0,len(sedol))
            #rule = "s:new algo twap"
            rule = "s:new algo vwap"
            ClOrdID = self.util.gen_id()
            ids.append(ClOrdID)
            endTime = str(datetime.now(timezone(self.util.getTimeZone('jp'))) + timedelta(seconds = 120)).replace('-','').replace(' ','-').split('.')[0]
            message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',\
                                                      OrderQty = random.randint(10000,100000),Symbol=bbid[num].split()[0],EndTime = endTime,
                                                     SecurityID = sedol[num],Currency='JPY')
            self.sess_fix.send_msg(message)
            self.logger.debug(self.util.pretty_print_msg(message))
            self.logger.debug("** NewOrder Request Sent : %s**"%(item+1))
        self.logger.debug("** Total Ids : %s**"%(len(np.unique(np.array(ids)))))
        return
    
    def test_function45(self):
        rule = "s:new wait 20 rpl wait 60 rpl fill"
        ClOrdID = self.util.gen_id()
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrderQty = 199 ,Symbol='AAPL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
        self.util.wait(5)
        ClOrdID2 = self.util.gen_id()
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = ClOrdID2,OrigClOrdID=ClOrdID,OrderQty=500,Symbol='AAPL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        
        self.util.wait(60)
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = self.util.gen_id(),OrigClOrdID=ClOrdID2,OrderQty=1000,Symbol='AAPL')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        return
    
    def test_function46(self):
        rule = "s:new algo twap 3600"
        ClOrdID = self.util.gen_id()
        endTime = str(datetime.now(timezone(self.util.getTimeZone('us'))) + timedelta(minutes = 40)).replace('-','').replace(' ','-').split('.')[0]
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',\
                                                  OrderQty = random.randint(10000,100000),Symbol='AAPL',EndTime = endTime)
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function47(self):
        rule = "s:new wait 60 fill"
        ClOrdID = self.util.gen_id()
        endTime = str(datetime.now(timezone(self.util.getTimeZone('jp'))) + timedelta(minutes=1)).replace('-','').replace(' ','-').split('.')[0]
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID = ClOrdID,OrdType = '1',OrderQty = 7777 ,Symbol='4206',EndTime = endTime)
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        
    def test_function48(self):
        sedol = self.util.dfMap['ca'].id_sedol1
        bbid = self.util.dfMap['ca'].bbid
        rule = "s:new algo twap"
        
        num = random.randint(0,len(sedol))
        ClOrdID = self.util.gen_id()
        endTime = str(datetime.now(timezone(self.util.getTimeZone('jp')))+ timedelta(minutes = 2)).replace('-','').replace(' ','-').split('.')[0]
        message = self.MsgFct.create_neworder_msg(Text= rule,ClOrdID  = ClOrdID,OrdType = '1',\
                                                  OrderQty = random.randint(10000,100000),Symbol=bbid[num].split()[0],EndTime = endTime,SecurityID = sedol[num])
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent**")
        
        self.util.wait(5)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=500,OrigClOrdID=ClOrdID,Symbol=bbid[num].split()[0]) 
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        return
    
    def test_function48a(self):
        sedol = self.util.dfMap['jp'].id_sedol1
        bbid = self.util.dfMap['jp'].bbid
        rule = "s:new algo twap"
        
        num = random.randint(0,len(sedol))
        ClOrdID = self.util.gen_id()
        endTime = str(datetime.now(timezone(self.util.getTimeZone('jp'))) + timedelta(minutes = 2)).replace('-','').replace(' ','-').split('.')[0]
        message = self.MsgFct.create_neworder_msg(Text= rule,ClOrdID  = ClOrdID,OrdType = '1',\
                                                  OrderQty = random.randint(10000,100000),Symbol=bbid[num].split()[0],EndTime = endTime,SecurityID = sedol[num])
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent**")
        
        self.util.wait(35)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=500,OrigClOrdID=ClOrdID,Symbol=bbid[num].split()[0]) 
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        return
    
    def test_function49(self):
        sedol = self.util.dfMap['us'].id_sedol1
        bbid = self.util.dfMap['us'].bbid
        rule = "s:new algo vwap"
        
        num = random.randint(0,len(sedol))
        ClOrdID = self.util.gen_id()
        endTime = str(datetime.now(timezone(self.util.getTimeZone('us'))) + timedelta(minutes = 2)).replace('-','').replace(' ','-').split('.')[0]
        message = self.MsgFct.create_neworder_msg(Text= rule,ClOrdID  = ClOrdID,OrdType = '1',\
                                                  OrderQty = 1000,Symbol=bbid[num].split()[0],SecurityID=sedol[num], EndTime=endTime)
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent**")
        
        self.util.wait(35)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=500,OrigClOrdID=ClOrdID,Symbol=bbid[num].split()[0]) 
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        return
    
    def test_function50(self):
        rule = "s:new algo twap 0"
        ClOrdID = self.util.gen_id()
        endTime = str(datetime.now(timezone(self.util.getTimeZone('jp'))) + timedelta(seconds = 90)).replace('-','').replace(' ','-').split('.')[0]
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',\
                                                  OrderQty = random.randint(10000,100000),Symbol='4206',EndTime = endTime)
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function51(self):
        rule = "s:new algo vwap -1"
        ClOrdID = self.util.gen_id()
        endTime = str(datetime.now(timezone(self.util.getTimeZone('jp')))+ timedelta(seconds = 90)).replace('-','').replace(' ','-').split('.')[0]
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',\
                                                  OrderQty = random.randint(10000,100000),Symbol='2175',EndTime = endTime)
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function52(self):
        rule = "s:new algo vwap 0"
        ClOrdID = self.util.gen_id()
        endTime = str(datetime.now(timezone(self.util.getTimeZone('jp'))) + timedelta(minutes = 15)).replace('-','').replace(' ','-').split('.')[0]
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',\
                                                  OrderQty = random.randint(10000,100000),Symbol='4206',EndTime = endTime)
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function53(self):
        sedol = self.util.dfMap['jp'].id_sedol1
        bbid = self.util.dfMap['jp'].bbid
        num = random.randint(0,len(sedol))
        rule = "s:new algo vwap"
        ClOrdID = self.util.gen_id()
        endTime = str(datetime.now(timezone(self.util.getTimeZone('jp'))) + timedelta(seconds = -131)).replace('-','').replace(' ','-').split('.')[0]
        message = self.MsgFct.create_neworder_msg(Text= rule,ClOrdID  = ClOrdID,OrdType = '1',\
                                                  OrderQty = random.randint(10000,100000),SecurityID = sedol[num],Symbol=bbid[num].split()[0],EndTime=endTime,Currency='JPY')
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent**")
        
        self.util.wait(35)
        message = self.MsgFct.create_cancelorder_msg(ClOrdID = self.util.gen_id(),OrderQty=500,OrigClOrdID=ClOrdID,Symbol=bbid[num].split()[0]) 
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** CancelOrder Request Sent **") 
        return
    
    def test_function54(self):
        sedol = self.util.dfMap['us'].id_sedol1
        bbid = self.util.dfMap['us'].bbid
        num = random.randint(0,len(sedol))
        
        rule = "s:new algo vwap 120"
        
        ClOrdID = self.util.gen_id()
        endTime = str(datetime.now(timezone(self.util.getTimeZone('us'))) + timedelta(minutes = 5)).replace('-','').replace(' ','-').split('.')[0]
        message = self.MsgFct.create_neworder_msg(Text= rule,ClOrdID  = ClOrdID,OrdType = '1',\
                                                  OrderQty = 9000,SecurityID = sedol[num],Symbol=bbid[num].split()[0])
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent**")
        
        self.util.wait(11)
        message = self.MsgFct.create_replaceorder_msg(ClOrdID = self.util.gen_id(),OrigClOrdID=ClOrdID,OrderQty=10000,SecurityID = sedol[num],Symbol=bbid[num].split()[0])
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** ReplaceOrder Request Sent **")
        return
    
    def test_function55(self):
        sedol = self.util.dfMap['us'].id_sedol1
        bbid = self.util.dfMap['us'].bbid
        num = random.randint(0,len(sedol))
        rule = "s:new algo close 0"
        ClOrdID = self.util.gen_id()
        endTime = str(datetime.now(timezone(self.util.getTimeZone('us'))) + timedelta(minutes = 2)).replace('-','').replace(' ','-').split('.')[0]
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',OrderQty = 999,\
                                                  SecurityID = sedol[num],Symbol=bbid[num].split()[0],Currency='USD',EndTime = endTime)
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function56(self):
        sedol = self.util.dfMap['us'].id_sedol1
        bbid = self.util.dfMap['us'].bbid
        num = random.randint(0,len(sedol))
        rule = "s:new algo close 1"
        ClOrdID = self.util.gen_id()
        endTime = str(datetime.now(timezone(self.util.getTimeZone('us'))) + timedelta(minutes = 2)).replace('-','').replace(' ','-').split('.')[0]
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',OrderQty = 999,\
                                                  SecurityID = sedol[num],Symbol=bbid[num].split()[0],Currency='USD',EndTime = endTime)
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function57(self):
        sedol = self.util.dfMap['us'].id_sedol1
        bbid = self.util.dfMap['us'].bbid
        num = random.randint(0,len(sedol))
        rule = "s:new algo open 0"
        ClOrdID = self.util.gen_id()
        endTime = str(datetime.now(timezone(self.util.getTimeZone('us'))) + timedelta(minutes = 2)).replace('-','').replace(' ','-').split('.')[0]
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',OrderQty = 999,\
                                                  SecurityID = sedol[num],Symbol=bbid[num].split()[0],Currency='USD',EndTime = endTime)
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    def test_function58(self):
        sedol = self.util.dfMap['us'].id_sedol1
        bbid = self.util.dfMap['us'].bbid
        num = random.randint(0,len(sedol))
        rule = "s:new algo open 1"
        ClOrdID = self.util.gen_id()
        endTime = str(datetime.now(timezone(self.util.getTimeZone('us'))) + timedelta(minutes = 2)).replace('-','').replace(' ','-').split('.')[0]
        message = self.MsgFct.create_neworder_msg(Text = rule,ClOrdID  = ClOrdID,OrdType = '1',OrderQty = 999,\
                                                  SecurityID = sedol[num],Symbol=bbid[num].split()[0],Currency='USD',EndTime = endTime)
        self.sess_fix.send_msg(message)
        self.logger.debug(self.util.pretty_print_msg(message))
        self.logger.debug("** NewOrder Request Sent **")
        return
    
    
def run(env):
    """ Description : runs the client program. """
    try:
        cfg_file = 'client.cfg'
        custom_file = 'custom.cfg'
        util = Util(env,custom_file,'client')
        os.chdir(util.getPath())
        app = Client(env+"_"+cfg_file,util)
    except Exception as e:
        print(e)