TYPE_STATISTIC = "Statistic"
TYPE_MESSAGE = "Message"

class Buffer(object):

    def __init__(self):
        self.message = []
    
    def __addPoolStatistic(self,poolName,value):
        self.message.append(Buffer.formatMessage(TYPE_STATISTIC,poolName,value))

    def __addPoolMessage(self,poolName,value):
        self.message.append(Buffer.formatMessage(TYPE_MESSAGE,poolName,value))

    def addPoolStatusMessageInBuffer(self,poolName,message,status):
        self.__addPoolMessage(poolName,message.format(poolName))
        self.__addPoolStatistic(poolName,status)    
    
    @staticmethod
    def formatMessage(messageType,name,value):
        return "{}.{}: {}\n".format(messageType,name,value)

    def printMessage(self):
        print(''.join(self.message),end='',flush=True)