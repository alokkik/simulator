import numpy as np
import math

class Vwap():

    def __init__(self,util):
        self.util = util
    
    def roundOff(self,Num):
        """
        Description : roundOff Num to closest multiple of 10/100..
        Parameters:
            Num -- Number to round off.
        Return : integer.
        """
        Num = str(Num)
        if len(Num)<=3: return int(round(int(Num),-1))
        else: return int(round(int(Num),-(len(Num)-2)))

    def roundoffdecimal(self,Num):
        """
        Description : roundOff Num to ceil(>0.5) or floor(<0.5). 
        Parameters:
            Num -- Number to round off.
        Return : float
        """
        return round(Num*2)/2

    def getIntervals(self,Num):
        """
        Description : get range of intervals to process.
        Parameters:
            Num -- Number to intervals
        Return : range of interval.
        """
        return range(-Num/2,Num/2+1) if Num%2==0 else range(-Num/2+1,Num/2+1)

    def listInterval(self,Num,Seconds,Interval):
        """
        Description : get list of interval in seconds.
        Parameters:
            Num -- Number to intervals
            Seconds -- Total duration for order to process.
            Interval -- size in seconds 60/30
        Return : list of interval in seconds.
        """
        intervalList = []
        for i in range(Num):
            intervalList.append(min(Interval,Seconds))
            Seconds-=min(Interval,Seconds)
        return intervalList

    def intervalQuantity(self,Num,Qty):
        """
        Description : get list of Qty to be filled in interval.
        Parameters:
            Num -- Number to intervals
            Qty -- OrderQty
        Return : list of Qty to be filled per interval.
        """
        intervals = np.array(self.getIntervals(Num))
        interval_y = intervals**3
        norm_y = [0]+[interval_y[i]+(-min(interval_y)) for i in range(1,len(interval_y))]
        norm_intvl = [round((1.0*item/max(norm_y))*100,2) for item in norm_y]
        cum_qty = [int(self.roundoffdecimal((item*Qty)/100)) for item in norm_intvl] #Cumulative Quantity.
        interval_qty = [0]+[cum_qty[i]+(-cum_qty[i-1]) for i in range(1,len(cum_qty))] #Interval Quantity.
        return interval_qty

    def roundOffIntervalQty(self,IntervalQty,Qty):
        """
        Description : get list of Qty to be filled in interval.
        Parameters:
            IntervalQty -- list of Qty to be filled per interval.
            Qty -- OrderQty
        Return : list of Rounded off Qty to be filled per interval.
        """
        _roundedOff = []
        for item in IntervalQty:
            if Qty>0:
                _roundedOff.append(min(Qty,self.roundOff(item)))
                Qty-=self.roundOff(item)
        if Qty>0:_roundedOff[-1]+=Qty # if any qunatity left
        return _roundedOff

    def fillPattern(self,Qty,Seconds,Interval=60):
        """
        Description : roundOff logic according to the Num.
        Parameters:
            Qty -- Qty to be broken into intervals.
            Seconds -- total number of seconds.
            Interval -- 30/60 seconds
        Return : list of fill quantity and list or interval.
        """
        Num = int(math.ceil(1.0*Seconds/Interval))
        if Seconds<Interval or Qty<=100 or Num<=1: 
            return self.util.seq(Qty), self.util.seq(min(Seconds,Interval))
        IntervalList = self.listInterval(Num,Seconds,Interval) #list of Intervals in seconds.
        IntervalQty = self.intervalQuantity(Num,Qty) #list of Interval quantities.
        roundOffQty = self.roundOffIntervalQty(IntervalQty,Qty) #list of RoundOff Interval quantities.
        if Num%2==1:IntervalList = IntervalList[1:]
        return roundOffQty[1:], IntervalList
    
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