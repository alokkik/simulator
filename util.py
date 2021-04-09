import pprint
import numpy as np
import pandas as pd
import quickfix as fix
import time,sys,os,logging,ast
from bson import ObjectId
from pytz import timezone
from os.path import expanduser
from datetime import datetime as dt
from datetime import timedelta as td
from pandas.tseries.offsets import BDay
from ConfigParser import SafeConfigParser
pp = pprint.PrettyPrinter(indent=4)

class Util:
    
    def __init__(self,env,configfile,side):
        self.env = env
        self.side = side.upper()
        self.config = SafeConfigParser()
        self.FixsimPath = os.path.join(expanduser("~"),'code','fixsim')
        self.configfile = os.path.join(self.FixsimPath,env+"_"+configfile)
        self.initialize()
        dte = self.getDate()
        self.univ_df = pd.read_csv(os.path.join(self.MapFilePath,"uni","secmap",str(dte).replace('-','')+".csv.gz"))
        self.dfMap,self.dfClose = self.loadFiles()
        self.tags = ["fix.SendingTime()", "fix.Account()", "fix.ClOrdID()", "fix.Currency()", \
                         "fix.HandlInst()", "fix.IDSource()","fix.OrderQty()", "fix.OrdType()", \
                         "fix.CumQty()", "fix.SecurityID()", "fix.Symbol()", "fix.Side()", "fix.TimeInForce()",\
                         "fix.TransactTime()","fix.SecurityType()", "fix.Text()", "fix.OrigClOrdID()",\
                         "fix.LeavesQty()","fix.AvgPx()",'fix.LastPx()','fix.LastQty','fix.LastMkt()','fix.OrdStatus()',\
                         "fix.CxlRejResponseTo()","fix.Price()"]
    
    def initialize(self):
        self.config.optionxform = str
        self.config.read(self.configfile)
        self.reg =  ast.literal_eval(self.config.get(self.side,'Region'))
        self.CurrencyExdesDict = ast.literal_eval(self.config.get(self.side,'MapDict'))
        self.CurrencyRegionDict = self.CurrencyExdesDict.copy()
        self.CurrencyRegionDict['CAD'] = 'CA'
        self.CurrencyRegionDict = dict((k,v.lower())for k,v in self.CurrencyRegionDict.iteritems())
        self.StoreLogPath = self.config.get(self.side,'StoreLogPath')
        self.MapFilePath = self.config.get(self.side,'MapFilePath')
    
    def getDate(self):
        dow=dt.today().weekday()
        if dow == 6:
            dte = (dt.today() + td(days=-2)).date()
        else:
            dte = dt.today().date()
        return dte

    def loadMappingFile(self,dte,prevDte,reg):
        """ 
        Description : loading Mapping files, mapping cusip/sedol to Exchange ID.
        """
        CurFilePath = os.path.join(self.MapFilePath,'data','idmap',str(reg),str(dte.year),str(dte).replace('-','')+".csv.gz")
        PrevFilePath = os.path.join(self.MapFilePath,'data','idmap',str(reg),str(prevDte.year),str(prevDte.date()).replace('-','')+".csv.gz")
        if os.path.exists(CurFilePath):
            return pd.read_csv(CurFilePath,compression='gzip')
        else:
            return pd.read_csv(PrevFilePath,compression='gzip')
    
    def loadPriceFile(self,dte,pdate,reg):
        """ 
        Description : loading price file.
        """
        return pd.read_csv(os.path.join(self.MapFilePath,"data","mark",str(reg),str(pdate.year),str(pdate.date()).replace('-','')+".csv.gz"))
        
    def loadFiles(self):
        """ 
        Description : loading Mapping files and Pricing files for all regions at once.
        """
        _dictMap, _dictPrice = {}, {}
        dte = self.getDate()
        prevDte = dte - BDay(1)
        for reg in self.reg: 
            _dictMap[reg] = self.loadMappingFile(dte,prevDte,str(reg))
            _dictPrice[reg] = self.loadPriceFile(dte,prevDte,str(reg))
        return _dictMap, _dictPrice
    
    def gen_id(self):
        """ 
        Description : generate unique object id.
        """
        return str(ObjectId())
    
    def wait(self,t):
        time.sleep(t)
        return
    
    def seq(self,val):
        return [val] if not isinstance(val,list) else val

    def isIndex(self,array,idx):
        """ 
        Description : checking if index exists or not.
        """
        try:
            array[idx]
            return True
        except IndexError as e:
            return False
            
    def cur_timestamp(self):
        """ 
        Description : current UTC timestamp 
        """
        t = str(dt.now())
        t = t.split()
        t[0]= t[0].replace('-','')
        return t[0]+"-"+t[1].split('.')[0]
    
    def timestampToDatetime(self,dte):
        """
        Description : converting string timestamp to datetime object.
        """
        return dt.strptime(dte,'%Y%m%d-%H:%M:%S')

    
    def getTimeZone(self,value):
        """
        Description : returns timezone according to the region or currency 
        """
        if value == 'ca' or value=='CAD':return 'America/Toronto'
        elif value == 'jp' or value=='JPY':return 'Asia/Tokyo'
        else : return 'America/New_York'
        
    def getMktClsTime(self,reg):
        """ 
        Description : return datetime object of market closing time.
        """
        dte = dt.now(timezone(self.getTimeZone(reg)))
        if reg == 'us' or reg == 'ca':
            dte = dte.replace(hour=16, minute=0, second=0, microsecond=0)
        elif reg == 'jp':
            dte = dte.replace(hour=15, minute=0, second=0, microsecond=0)
        return dte
    
    def getMktOpenTime(self,reg):
        """ 
        Description : return datetime object of market opening time.
        """
        dte = dt.now(timezone(self.getTimeZone(reg)))
        print dte
        if reg == 'us' or reg == 'ca':
            dte = dte.replace(hour=9, minute=30, second=0, microsecond=0)
        elif reg == 'jp':
            dte = dte.replace(hour=9, minute=0, second=0, microsecond=0)
        if dt.now(timezone(self.getTimeZone(reg))) > self.getMktClsTime(reg): dte = dte+td(days=1)
        return dte
    
    def secondsToMktClose(self,reg,epoch):
        """ 
        Description : return number of seconds left for market to close.
        """
        dte = self.getMktClsTime(reg)
        if (dte - epoch).days < 0:return -1
        else : return (dte - epoch).seconds
    
    def pretty_print_msg(self,message):
        """ 
        Description : pretty print messages 
        Parameters:
            message -- message object to be pretty print.
        Return : dictionary of tag and value.
        """
        _dict = {}
        for item in self.tags:
            val = eval(item)
            try :
                if message.isSetField(val):
                    message.getField(val)
                    _dict[item.split('.')[1][:-2]] = val.getString()
                else: pass
            except NotImplementedError as e: pass
        return _dict
    
    def clearStore(self):
        """ 
        Description : clears previous store files before new program. 
        """
        for file in os.listdir(os.path.join(self.FixsimPath,self.env,'store')):
            if file.startswith('FIX'):
                os.remove(os.path.join(os.path.join(self.FixsimPath,self.env,'store'),file))
        return
    
    def initialize_logger(self,side):
        """
        Description : create a logging object,Set format of output log.
        Parameters:
            log_name -- data/alpha log
        Return : logger object.
        """
        logger = logging.getLogger('fixserver')
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        logFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        if not os.path.exists(os.path.join(self.StoreLogPath,'fixsim',self.env,'log')):
            os.makedirs(os.path.join(self.StoreLogPath,'fixsim',self.env,'log'))
        fileHandler = logging.FileHandler(os.path.join(os.path.join(self.StoreLogPath,'fixsim',self.env,'log'),\
                                                       side+"_%s.log"%(str(dt.now())[:10]).replace('-','')),mode='w+')
        fileHandler.setFormatter(logFormatter)
        logger.addHandler(fileHandler)
        return logger
    
    def getPath(self):
        """
        Description : get project's directory path
        """
        return self.FixsimPath
    
    def checkLogStorePath(self):
        """
        Description : check if Log and Store paths are available,
                      create path if doesn't exit.
        Return : None
        """
        if not os.path.exists(os.path.join(self.StoreLogPath,'fixsim',self.env,'log')):
            os.makedirs(os.path.join(self.StoreLogPath,'fixsim',self.env,'log'))
        if not os.path.exists(os.path.join(self.StoreLogPath,'fixsim',self.env,'store')):
            os.makedirs(os.path.join(self.StoreLogPath,'fixsim',self.env,'store'))
        return
    
    def getInterval(self):
        """
        Description : getting Interval value from config.
        """
        self.config.read(self.configfile)
        value = self.config.get(self.side,'Interval')
        if value == None: return 60
        return int(value)
    
    def getSleepTime(self):
        """
        Description : getting SleepTime value from config.
        """
        self.config.read(self.configfile)
        value = self.config.get(self.side,'SleepTime')
        if value == None: return 0.05
        return float(value)
    
    def isNum(self,string):
        """
        Description : checking if text is number or word.
        Parameters:
            string -- string from rule.
        Return : True/False
        """
        try:
            float(string)
            return True
        except ValueError as e:
            return False