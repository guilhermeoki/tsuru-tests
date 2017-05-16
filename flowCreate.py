"""Test a tsuru deploy"""
from subprocess import Popen, PIPE, run
from tempfile import NamedTemporaryFile
import os
import yaml

CONFIGFILE = "config.yml"
TARGETFILE = os.environ["HOME"] + "/.tsuru/target"

class Tsuru(object):
    """Provides a connection to a tsuru endpoint"""

    config = yaml
    targetBkp = str

    def __init__(self):
        self.loadConfig()
        self.setTarget()
        self.login()

    def __del__(self):
        self.resetTarget()

    def loadConfig(self):
        """Loads the configuration file"""
        with open(CONFIGFILE, 'r') as stream:
            try:
                self.config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print("Unable to open file " + CONFIGFILE)
                print(exc)
                exit(1)

    def setTarget(self):
        """Tells tsuru to use the endpoint provided"""
        if os.path.isfile(TARGETFILE):
            try:
                self.targetBkp = NamedTemporaryFile(mode="w+b").name
                with open(TARGETFILE, 'r') as stream:
                    targetBkpContent = stream.read()
                with open(self.targetBkp, 'w') as stream:
                    stream.write(targetBkpContent)
            except IOError as exc:
                print("Unable to backup tsuru target file " + TARGETFILE)
                print(exc)
                exit(1)

        with open(TARGETFILE, 'w') as stream:
            try:
                stream.write(self.config["endpoint"])
            except IOError as exc:
                print("Unable to write to tsuru target file " + TARGETFILE)
                exit(1)

    def resetTarget(self):
        """Restore the original target"""
        try:
            with open(self.targetBkp, 'r') as stream:
                targetContent = stream.read()
            with open(TARGETFILE, 'w') as stream:
                stream.write(targetContent)
        except IOError as exc:
            print("Unable to restore tsuru target file " + TARGETFILE)
            print(exc)
            exit(1)


    def login(self):
        """Log into the provided endpoint"""
        login = Popen(["tsuru", "login", self.config["user"]], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        try:
            loginOut = login.communicate(input=str.encode(self.config["pass"] + '\n'), timeout=10)
            if login.returncode != 0:
                login.kill()
                print("Login failed. Message: " + bytes.decode(loginOut[1]))
                exit(1)
        except TimeoutError as exc:
            print("Login timed out.")
            print(exc)
            exit(1)

    def run(self, cmd):
        """Run a given tsuru command"""
        run(["tsuru", cmd], check=True)

tsuru = Tsuru()
tsuru.run("pool-list")
