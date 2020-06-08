# -*- coding: utf-8 -*-

from __future__ import print_function
from gate_api import FuturesOrder
from gate_api.rest import ApiException
from conf import *
from handler import *
from handler_t import *
from handler_1t import *
import json
import gflags
import codecs
import requests
import time
import gate_api

class Future_Manager(object):
    def __init__(self):
	f_exp = codecs.open('./experiment.conf', 'r', encoding='utf-8')
	data_algs = json.load(f_exp)
	contracts = data_algs['contract']
	for contr in contracts:
	    self.handler = Future_Handler(contr,contracts[contr])
            self.handler_t = Handler_T()
            self.handler_1t = Handler_1T()
            if contracts[contr]['first_handler'] == 't':
                self.current_handler = self.handler_t
            elif contracts[contr]['first_handler'] == '1t':
                self.current_handler = self.handler_1t
            self.current_handler.get_flag()
            Future_Handler.t_head = min(Future_Handler.t + 0.2,0.9)
            Future_Handler.t_tail = max(Future_Handler.t - 0.4,-0.9)
            Future_Handler.S_up = Future_Handler.S_
            Future_Handler.S_dn = Future_Handler.S_
	f_exp.close()

    def get_handler(self):
        if self.current_handler.tip == 't':
            if Future_Handler.t < Future_Handler.t_tail:
                #if Future_Handler._T <= Future_Handler.T_std or (self.current_handler.forward_gap>0.0 and self.current_handler.forward_balance_size==0) or (self.current_handler.backward_gap>0.0 and self.current_handler.backward_balance_size==0):
                self.current_handler = self.handler_1t
                Future_Handler.S_up = Future_Handler.S_
                Future_Handler.S_dn = Future_Handler.S_
                Future_Handler.t_head = min(Future_Handler.t + 0.2,0.9)
            print (self.current_handler.tip,Future_Handler.t,Future_Handler.t_tail)
        elif self.current_handler.tip == '1t':
            if Future_Handler.t > Future_Handler.t_head:
                self.current_handler = self.handler_t
                Future_Handler.S_up = Future_Handler.S_
                Future_Handler.S_dn = Future_Handler.S_
                Future_Handler.t_tail = max(Future_Handler.t - 0.4,-0.9)
            print (self.current_handler.tip,Future_Handler.t,Future_Handler.t_head)
        print (self.current_handler.tip,Future_Handler.S_,Future_Handler.S_up,Future_Handler.S_dn)

    def run(self):
        self.get_handler()
        try:
            self.current_handler.get_flag();
            self.current_handler.put_position();
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

