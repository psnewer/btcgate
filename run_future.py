# -*- coding: utf-8 -*-

from __future__ import print_function
import requests
import time
import gate_api
import json
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
    while True:
#        try:
        future_manager.run()
#	except Exception as e:
#	    print("Exception when calling FuturesApi: %s\n" % e)
#            body_dic = json.loads(e.body)
#            e_sig = True
#            if 'label' in body_dic:
#                print (body_dic['label'])
#                if body_dic['label'] in ['ORDER_POC_IMMEDIATE','ORDER_NOT_FOUND','AUTO_ORDER_NOT_FOUND','INCREASE_POSITION'] :
#                    e_sig = False
#                else:
#                    e_sig = True
#            if e_sig and 'detail' in body_dic:
#                print (body_dic['detail'])
#                if body_dic['detail'] == 'invalid argument: #3':
#                    e_sig = False
#                else:
#                    e_sig = True
#            if e_sig:
#                 raise ImportError('OpenAPI Python client requires urllib3.')
#	    send_weixin(e)
