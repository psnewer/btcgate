# -*- coding: utf-8 -*-

from __future__ import print_function
import requests
import time
import gate_api
from future_manager import *
from future_handler import *
from gate_api import FuturesOrder
from gate_api.rest import ApiException

		
N_message = 100

def send_weixin(msg):
    global N_message
    if N_message < 500:
	N_message = N_message + 1
	requests.get("https://sc.ftqq.com/SCU60300T026729377fffbccacceb5c62ab430d7f5d78a7743d03a.send?text={}&desp={}".format('告警', str(N_message)+' '+str(msg)))
	time.sleep(3)

if __name__ == "__main__":
    future_manager = Future_Manager()
#    while True:
#	try:
    future_manager.run()
#            future_manager.handle_position()
#	except Exception as e:
#	    print("Exception when calling FuturesApi: %s\n" % e)
#	    send_weixin(e)
