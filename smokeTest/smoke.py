from tsuru import TsuruRunner
from apps import TsuruApp
from tsuruclient import client,base,apps

MAX_DEPLOY_TIME = 300

class SmokeTest(object):
    @staticmethod
    def runTest():
        runner = TsuruRunner()
        tsuruClient = client.Client(runner.endpoint,runner.token)
        threads = []
        for conf in runner.config["envs"]:
           app = TsuruApp(runner,conf["pool"],conf["plan"],tsuruClient) 
           threads.append(app)
           app.start()
        
        for thread in threads:
            thread.join(MAX_DEPLOY_TIME)
        
        runner.buffer.printMessage()
        runner.resetTarget()
        exit(0)

SmokeTest.runTest()
