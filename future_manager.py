# -*- coding: utf-8 -*-

from __future__ import print_function
from gate_api import FuturesOrder
from gate_api.rest import ApiException
from conf import *
from bf_handler import *
import json
import gflags
import codecs
import requests
import time
import gate_api

class Future_Manager(object):
    def __init__(self):
	self.follow_signal = True
	self.balance_signal = False
	f_exp = codecs.open('./experiment.conf', 'r', encoding='utf-8')
	data_algs = json.load(f_exp)
	contracts = data_algs['contract']
	self.handlers = []
	for contr in contracts:
	    handler = Future_Handler(contr,contracts[contr])
	    self.handlers.append(handler)
	f_exp.close()

    def run(self):
        for handler in self.handlers:
            try:
                handler.get_flag();
                handler.put_position();
            except Exception as e:
                print("Exception when calling FuturesApi: %s\n" % e)
                dic_clear = True

                try:
                    body_dic = json.loads(e.body)
                except Exception:
                    send_email(e)
                    dic_clear = False

                if dic_clear:
                    e_sig = True
                    if 'label' in body_dic:
                        if body_dic['label'] in ['ORDER_POC_IMMEDIATE','ORDER_NOT_FOUND','INCREASE_POSITION','INSUFFICIENT_AVAILABLE']:
                            e_sig = False
                        else:
                            e_sig = True
                    if e_sig and 'detail' in body_dic:
                        if body_dic['detail'] == 'invalid argument: #3':
                            e_sig = False
                        else:
                            e_sig = True
                    if e_sig:
                        print ('e_sig')
                        send_email(e)

