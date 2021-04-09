import quickfix as fix

class SessionFix(fix.Application):
    
    def __init__(self,func):
        self.SessionDict = {}
        fix.Application.__init__(self)
        self.func=func
        
    def onCreate(self, sessionID):
        self.sessionID = sessionID
        self.SessionDict[sessionID.toString()] = sessionID
        print ('On Session Create: %s' % sessionID.toString())
        return
    
    def onLogon(self, sessionID):
        #print ("Successful Logon to session '%s'" % sessionID.toString())
        return
    
    def onLogout(self, sessionID):
        #print ('On Logout')
        return
    
    def toAdmin(self, message, sessionID):
        #print ("Send the Admin following message: %s" % message.toString())
        return
    
    def toApp(self, message, sessionID):
        return
    
    def fromAdmin(self, message, sessionID):
        #print ("Received the Admin following message: %s" % message.toString())
        return
    
    def fromApp(self, message, sessionID):
        self.func(message)
        return
        
    def send_msg(self,message):
        fix.Session.sendToTarget(message,self.sessionID)
        return