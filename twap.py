import numpy as np

class Twap():
    
    def __init__(self,util):
        self.util = util
        
    def lowerNum(self,Num):
        """
        Description : lower bound of the Num.
        Parameters:
            Num -- Number to find the Lower bound.
        Return : integer.
        """
        if len(str(Num)) <= 2: return 0
        return int(Num[0]+len(Num[1:])*'0')

    def upperNum(self,Num):
        """
        Description : upper bound of the Num.
        Parameters:
            Num -- Number to find the Upper bound.
        Return : integer.
        """
        if len(str(Num)) <= 2: return 100
        return int(str(int(Num[0])+1)+len(Num[1:])*'0')

    def roundOff(self,Num):
        """
        Description : roundOff logic according to the Num.
        Parameters:
            Num -- Number to roundOff
        Return : integer.
        """
        Num = int(Num)
        _range = np.array([self.lowerNum(str(Num)),self.upperNum(str(Num))])
        _min_range = np.abs(_range - Num)
        _min = np.min(_min_range)
        idx, = np.where(_min_range == _min)
        return _range[idx][0]
    
    def fillPattern(self,Qty,Seconds,Interval=60):
        """
        Description : roundOff logic according to the Num.
        Parameters:
            Qty -- Qty to be broken into intervals.
            Seconds -- total number of seconds.
            Interval -- 30/60 seconds
        Return : list of fill quantity and list or interval.
        """
        share = float(Qty)/Seconds
        if Seconds < Interval or Qty <= 100: return self.util.seq(Qty), self.util.seq(min(Seconds,Interval)) #make it list
        TotalQty, listFill, listInterval, qtyFilled, itr = Qty, [], [], 0, 1 
        while(Seconds>0):
            fillByNow = self.roundOff(share*(Interval)*itr)#this much should be filled by now
            if Seconds<=Interval:
                fillQty = Qty 
                listFill.append(fillQty)
                listInterval.append(Seconds)
                break
            else:        
                fillQty = max(0,min(fillByNow - qtyFilled,Qty))
                listInterval.append(Interval)
            Seconds -= Interval
            Qty -= fillQty
            qtyFilled += fillQty
            listFill.append(fillQty)
            if TotalQty == fillByNow:break
            itr+=1
        return listFill, listInterval
    
    def getRuleString(self,LeavesQty,Sec):
        """
        Description : generate rule string to process order.
        Parameters:
            LeavesQty -- Left Quantity to be filled.
            Sec -- number of seconds remaining for order to fill.
        Return : string
        """
        listFill, listInterval = self.fillPattern(LeavesQty,Sec,self.util.getInterval())
        ruleString = ''
        for itr, item in enumerate(listFill):
            ruleString = ruleString+" "+"wait %s"%listInterval[itr]+" "+"fillshares %s"%item
        return ruleString