#!/usr/bin/python3
"""Test a tsuru deploy"""
from subprocess import Popen, PIPE, run, SubprocessError
from tempfile import NamedTemporaryFile
from buffer import Buffer
import subprocess
import os
import yaml

CONFIGFILE = "test.yml"
TARGETFILE = os.environ["HOME"] + "/.tsuru/target"
BINARY_NAME = "tsuru"
TOKENFILE = os.environ["HOME"] + "/.tsuru/token"
DEFAULT_POOL = "tsuru-local"

STATUS_TSURU_ERROR = 0
STATUS_TSURU_OK = 1

MSG_ERROR_RUN_CMD = "Error running tsuru cmd."
MSG_ERROR_LOAD_CONFIG = "Unable to load config file."
MSG_ERROR_RESET_TARGET = "Unable to restore tsuru target file."
MSG_ERROR_BACKUP_TARGET = "Unable to backup tsuru target file."
MSG_ERROR_WRITE_TARGET = "Unable to write to tsuru target file."
MSG_ERROR_LOGIN_TIMEOUT = "Login timed out."
MSG_ERROR_GET_TOKEN = "Unable to get tsuru token file"
MSG_ERROR_LOGIN_FAILED = "Login failed. Message: "


class TsuruRunner(object):

    config = None
    targetBkp = None

    def __init__(self):
        self.config = TsuruRunner.loadConfig(CONFIGFILE)
        self.buffer = Buffer()
        self.__setTarget()
        self.__login()

    def run(self,*cmds):
        """Run a given tsuru command"""
        cmds = [BINARY_NAME]+list(cmds)
        try:
            return run(cmds, check=True, stdout=PIPE , stderr=PIPE)
        except SubprocessError as spe:
            self.buffer.addPoolStatusMessageInBuffer(DEFAULT_POOL,MSG_ERROR_RUN_CMD,STATUS_TSURU_ERROR)
            self.buffer.printMessage()
            exit(1)

    def loadConfig(configFile):
        """Loads the configuration file"""
        with open(configFile, 'r') as stream:
            try:
                config = yaml.safe_load(stream)
                return config
            except yaml.YAMLError as exc:
                self.buffer.addPoolStatusMessageInBuffer(DEFAULT_POOL,MSG_ERROR_LOAD_CONFIG,STATUS_TSURU_ERROR)
                self.buffer.printMessage()
                exit(1)
    
    def resetTarget(self):
        """Restore the original target"""
        try:
            with open(self.targetBkp, 'r') as stream:
                targetContent = stream.read()
            with open(TARGETFILE, 'w') as stream:
                stream.write(targetContent)
        except IOError as exc:
            self.buffer.addPoolStatusMessageInBuffer(DEFAULT_POOL,MSG_ERROR_RESET_TARGET,STATUS_TSURU_ERROR)
            self.buffer.printMessage()
            exit(1)

    def __setTarget(self):
        """Tells tsuru to use the endpoint provided"""
        if os.path.isfile(TARGETFILE):
            try:
                self.targetBkp = NamedTemporaryFile(mode="w+b").name
                with open(TARGETFILE, 'r') as stream:
                    targetBkpContent = stream.read()
                with open(self.targetBkp, 'w') as stream:
                    stream.write(targetBkpContent)
            except IOError as exc:
                self.buffer.addPoolStatusMessageInBuffer(DEFAULT_POOL,MSG_ERROR_BACKUPT_TARGET,STATUS_TSURU_ERROR)
                self.buffer.printMessage()
                exit(1)

        with open(TARGETFILE, 'w') as stream:
            try:
                stream.write(self.config["endpoint"])
            except IOError as exc:
                self.buffer.addPoolStatusMessageInBuffer(DEFAULT_POOL,MSG_ERROR_WRITE_TARGET,STATUS_TSURU_ERROR)
                self.buffer.printMessage()
                exit(1)

    def __login(self):
        """Log into the provided endpoint"""
        login = Popen([BINARY_NAME, "login", self.config["user"]], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        try:
            loginOut = login.communicate(input=str.encode(self.config["pass"] + '\n'), timeout=10)
            if login.returncode != 0:
                login.kill()
                message = MSG_ERROR_LOGIN_FAILED.format(bytes.decode(loginOut[1]))
                self.buffer.addPoolStatusMessageInBuffer(DEFAULT_POOL,message,STATUS_TSURU_ERROR)
                self.buffer.printMessage()
                exit(1)
        except TimeoutError as exc:
            self.buffer.addPoolStatusMessageInBuffer(DEFAULT_POOL,MSG_ERROR_LOGIN_TIMEOUT,STATUS_TSURU_ERROR)
            self.buffer.printMessage()
            exit(1)
    
    @property
    def token(self):
        try:
            with open(TOKENFILE, 'r') as stream:
                self.__token = stream.read()
                return self.__token
        except IOError as exc:
            self.buffer.addPoolStatusMessageInBuffer(DEFAULT_POOL,MSG_ERROR_GET_TOKEN,STATUS_TSURU_ERROR)
            self.buffer.printMessage()
            exit(1)
    
    @property
    def endpoint(self):
        return self.config["endpoint"]
