# -*- coding: utf-8 -*-

from __future__ import print_function
from gate_api import FuturesOrder
from gate_api.rest import ApiException
from conf import *
from handler import *
from handler_t import *
from handler_1t import *
from handler_w import *
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
            if contracts[contr]['first_handler'] == 't':
                self.current_handler = Handler_T()
            elif contracts[contr]['first_handler'] == '1t':
                self.current_handler = Handler_1T()
            self.current_handler.get_flag()
            Future_Handler.t_head = min(((1.0-Future_Handler.rt_hard)*Future_Handler.t+Future_Handler.rt_hard)/(1.0+Future_Handler.rt_hard*(1.0-Future_Handler.t)),1.0)
            if -min(Future_Handler.t_f,Future_Handler.t_b) <= Future_Handler.step_hard:
                Future_Handler.t_tail = -0.5
            else:
                Future_Handler.t_tail = max(((1.0+Future_Handler.rt_hard)*Future_Handler.t-Future_Handler.rt_hard)/(1.0+Future_Handler.rt_hard*(Future_Handler.t-1.0)),-0.5)
	f_exp.close()

    def get_handler(self):
        if self.current_handler.tip == 't':
            if Future_Handler.forward_goods + Future_Handler.backward_goods + Future_Handler.goods > Future_Handler.surplus_abandon * Future_Handler.limit_goods or Future_Handler.limit_goods == 0.0:
                self.current_handler = Handler_W()
            elif Future_Handler.t < Future_Handler.t_tail:
                self.current_handler = Handler_1T()
                Future_Handler.t_head = min(((1.0-Future_Handler.rt_hard)*Future_Handler.t+Future_Handler.rt_hard)/(1.0+Future_Handler.rt_hard*(1.0-Future_Handler.t)),1.0)
            print (self.current_handler.tip,Future_Handler.t,Future_Handler.t_tail)
        elif self.current_handler.tip == '1t':
            if Future_Handler.forward_goods + Future_Handler.backward_goods + Future_Handler.goods > Future_Handler.surplus_abandon * Future_Handler.limit_goods or Future_Handler.limit_goods == 0.0:
                self.current_handler = Handler_W()
            elif Future_Handler.t > Future_Handler.t_head:
                self.current_handler = Handler_T()
                if -min(Future_Handler.t_f,Future_Handler.t_b) <= Future_Handler.step_hard:
                    Future_Handler.t_tail = -0.5
                else:
                    Future_Handler.t_tail = max(((1.0+Future_Handler.rt_hard)*Future_Handler.t-Future_Handler.rt_hard)/(1.0+Future_Handler.rt_hard*(Future_Handler.t-1.0)),-0.5)
            print (self.current_handler.tip,Future_Handler.t,Future_Handler.t_head)
        elif self.current_handler.tip == 'w':
            if Future_Handler.forward_goods + Future_Handler.backward_goods + Future_Handler.goods < Future_Handler.surplus_endure * Future_Handler.limit_goods and Future_Handler.limit_goods > 0.0:
                self.current_handler = Handler_T()
                Future_Handler.catch = False
                Future_Handler.balance = False
            print(self.current_handler.tip, Future_Handler.forward_goods,Future_Handler.backward_goods)

    def run(self):
        self.get_handler()
#        try:
        self.current_handler.get_flag();
        self.current_handler.put_position();
#        except Exception as e:
#            print("Exception when calling FuturesApi: %s\n" % e)
#            dic_clear = True
#
#            try:
#                body_dic = json.loads(e.body)
#            except Exception:
#                send_email(e)
#                dic_clear = False
#
#            if dic_clear:
#                e_sig = True
#                if 'label' in body_dic:
#                    if body_dic['label'] in ['ORDER_POC_IMMEDIATE','ORDER_NOT_FOUND','INCREASE_POSITION','INSUFFICIENT_AVAILABLE']:
#                        e_sig = False
#                    else:
#                        e_sig = True
#                if e_sig and 'detail' in body_dic:
#                    if body_dic['detail'] == 'invalid argument: #3':
#                        e_sig = False
#                    else:
#                        e_sig = True
#                if e_sig:
#                    print ('e_sig')
#                    send_email(e)

