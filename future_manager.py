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
            self.handler_t = Handler_T()
            self.handler_1t = Handler_1T()
            self.handler_w = Handler_W()
            if contracts[contr]['first_handler'] == 't':
                self.current_handler = self.handler_t
            elif contracts[contr]['first_handler'] == '1t':
                self.current_handler = self.handler_1t
            self.current_handler.get_flag()
<<<<<<< HEAD
=======
<<<<<<< HEAD
            Future_Handler.t_head = min(((1.0-Future_Handler.rt_hard)*Future_Handler.t+Future_Handler.rt_hard)/(1.0+Future_Handler.rt_hard*(1.0-Future_Handler.t)),1.0)
            if -min(Future_Handler.t_f,Future_Handler.t_b) <= Future_Handler.step_hard:
                Future_Handler.t_tail = -0.5
            else:
                Future_Handler.t_tail = max(((1.0+Future_Handler.rt_hard)*Future_Handler.t-Future_Handler.rt_hard)/(1.0+Future_Handler.rt_hard*(Future_Handler.t-1.0)),-0.5)
=======
            Future_Handler.t_head = min(Future_Handler.t+Future_Handler.rt_hard,3.0)
            Future_Handler.t_tail = max(Future_Handler.t-2*Future_Handler.rt_hard,-0.5)
>>>>>>> 7125560b86f91b4b770b11526d7264b85b401658
>>>>>>> 30b82598ed68e8fe453d9adf424c77c5d009cde1
	f_exp.close()

    def get_handler(self):
        print ('aaaa')
        print (Future_Handler.goods,Future_Handler.balance_overflow,Future_Handler.forward_goods+Future_Handler.backward_goods+Future_Handler.balance_overflow,Future_Handler.surplus_abandon * Future_Handler.limit_goods)
        if self.current_handler.tip == 't':
<<<<<<< HEAD
            if Future_Handler.forward_goods+Future_Handler.backward_goods+Future_Handler.balance_overflow > Future_Handler.surplus_abandon * Future_Handler.limit_goods or Future_Handler.limit_goods == 0.0:
                self.current_handler = self.handler_w
            elif Future_Handler.t < Future_Handler.t_tail:
                self.current_handler = self.handler_1t
            print (self.current_handler.tip,Future_Handler.t,Future_Handler.t_tail)
        elif self.current_handler.tip == '1t':
            if Future_Handler.forward_goods+Future_Handler.backward_goods+Future_Handler.balance_overflow > Future_Handler.surplus_abandon * Future_Handler.limit_goods or Future_Handler.limit_goods == 0.0:
                self.current_handler = self.handler_w
            elif Future_Handler.t > Future_Handler.t_head:
<<<<<<< HEAD
                self.current_handler = self.handler_t
=======
                self.current_handler = Handler_T()
                if -min(Future_Handler.t_f,Future_Handler.t_b) <= Future_Handler.step_hard:
                    Future_Handler.t_tail = -0.5
                else:
                    Future_Handler.t_tail = max(((1.0+Future_Handler.rt_hard)*Future_Handler.t-Future_Handler.rt_hard)/(1.0+Future_Handler.rt_hard*(Future_Handler.t-1.0)),-0.5)
=======
            if Future_Handler.t < Future_Handler.t_tail:
                self.current_handler = self.handler_1t
                Future_Handler.t_head = min(Future_Handler.t+Future_Handler.rt_hard,3.0)
            print (self.current_handler.tip,Future_Handler.t,Future_Handler.t_tail)
        elif self.current_handler.tip == '1t':
            if Future_Handler.t > Future_Handler.t_head:
                self.current_handler = self.handler_t
                Future_Handler.t_tail = max(Future_Handler.t-2*Future_Handler.rt_hard,-0.5)
>>>>>>> 7125560b86f91b4b770b11526d7264b85b401658
>>>>>>> 30b82598ed68e8fe453d9adf424c77c5d009cde1
            print (self.current_handler.tip,Future_Handler.t,Future_Handler.t_head)
        elif self.current_handler.tip == 'w':
            if Future_Handler.forward_goods+Future_Handler.backward_goods+Future_Handler.balance_overflow < Future_Handler.surplus_endure * Future_Handler.limit_goods and Future_Handler.limit_goods > 0.0:
                self.current_handler = self.handler_t

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

