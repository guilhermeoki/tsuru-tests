from tsuru import TsuruRunner
import random
import string
import os
import yaml
import requests
import threading
from tsuruclient import client,base,apps

RANDOM_SIZE = 14
DEFAULT_APP_NAME = 'test-deploy-life-cycle-'

CMD_APP_CREATE = "app-create"
CMD_APP_REMOVE = "app-remove"
CMD_APP_DEPLOY = "app-deploy"

APP_OPTION = "-a"
YES_OPTION = "-y"
PLAN_OPTION = "-p"
POOL_OPTION = "-o"
TEAM_OPTION = "-t"

MSG_ERROR_CREATE_APP = "Error creating app in {}"
MSG_ERROR_DELETE_APP = "Error deleting app in {}"
MSG_ERROR_VERIFY_APP = "Error verifing app in {}"
MSG_ERROR_DEPLOY_APP = "Error deploying app in {}"

MSG_ERROR_POOL = "Pool {} is not working correctly."
MSG_POOL = "Pool {} is working correctly."

STATUS_APP_ERROR = 0
STATUS_APP_OK = 1

class TsuruApp(threading.Thread):

    def __init__(self,tsuru,pool,plan,tsuruClient):
        threading.Thread.__init__(self)
        self.lock = threading.Lock()
        self.__tsuru = tsuru
        self.__tsuruClient = tsuruClient
        self.__buffer = tsuru.buffer
        
        self.__appName = TsuruApp.generateRandomAppName()
        self.__pool = pool
        self.__plan = plan

        self.__code = tsuru.config["code"]
        self.__platform = tsuru.config["platform"]
        self.__team = tsuru.config["team"]
        self.__endpoint = tsuru.config["endpoint"]
        self.__healthcheckUrl = tsuru.config["healthcheck"]["path"]
        self.__healthcheckCode = tsuru.config["healthcheck"]["status"]

    def run(self):
        self.lock.acquire()

        if not self.__isAppInTsuru():
            self.__createApp()
        else:
            self.__deleteApp()
            self.__createApp()
        self.__deployApp()
        if not self.__verifyApp():
            self.__buffer.addPoolStatusMessageInBuffer(self.__pool,MSG_ERROR_POOL,STATUS_APP_ERROR)
        else:
            self.__buffer.addPoolStatusMessageInBuffer(self.__pool,MSG_POOL,STATUS_APP_OK)
        self.__deleteApp()
        
        self.lock.release()

    def __createApp(self):
        r = self.__tsuru.run(CMD_APP_CREATE,self.__appName,self.__platform,PLAN_OPTION,self.__plan,POOL_OPTION,self.__pool,TEAM_OPTION,self.__team)
        if r.returncode != 0:
            self.__buffer.addPoolStatusMessageInBuffer(self.__pool,MSG_ERROR_CREATE_APP,STATUS_APP_ERROR)
            exit(1)

    def __deleteApp(self):
        r = self.__tsuru.run(CMD_APP_REMOVE,YES_OPTION,APP_OPTION,self.__appName)
        if r.returncode != 0:
            self.__buffer.addPoolStatusMessageInBuffer(self.__pool,MSG_ERROR_DELETE_APP,STATUS_APP_ERROR)
            exit(1)
    
    def __deployApp(self):
        r = self.__tsuru.run(CMD_APP_DEPLOY,APP_OPTION,self.__appName,self.__code)
        if r.returncode != 0:
            self.__buffer.addPoolStatusMessageInBuffer(self.__pool,MSG_ERROR_DELETE_APP,STATUS_APP_ERROR)

    def __isAppInTsuru(self):
        if self.getAppInTsuru() == None:
            return False
        return True
    
    def __verifyApp(self):
        verifyUrl = "http://{}{}".format(self.appUrl,self.__healthcheckUrl)
        try:
            r = requests.get(verifyUrl)
        except requests.exceptions.RequestException as exc:
            verifyUrl = "https://{}{}".format(self.appUrl,self.__healthcheckUrl)
            try:
                r = requests.get(verifyUrl)
            except requests.exceptions.RequestException as exc:
                self.__buffer.addPoolStatusMessageInBuffer(self.__pool,ERROR_VERIFY_APP,status)
                exit(1)
        if r.status_code == self.__healthcheckCode:
            return True
        return False

    def getAppInTsuru(self):
        try:
            app = self.__tsuruClient.apps.get(self.__appName)
        except base.TsuruAPIError as tsu_ex:
            return None
        return app

    @property
    def appUrl(self):
        app = self.getAppInTsuru()
        return app["ip"]
        
    @staticmethod
    def generateRandomAppName():
        chars = string.ascii_lowercase
        return DEFAULT_APP_NAME+''.join(random.choice(chars) for _ in range(RANDOM_SIZE))
