# -*- coding: utf-8 -*-

from __future__ import print_function
from gate_api import FuturesOrder
from gate_api.rest import ApiException
from conf import *
from handler import *
from handler_t import *
from handler_1t import *
from handler_w import *
from handler_f import *
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
	    self.handler = FH(contr,contracts[contr])
            self.handler_t = Handler_T()
            self.handler_1t = Handler_1T()
            self.handler_w = Handler_W()
            self.handler_f = Handler_F()
            if contracts[contr]['first_handler'] == 't':
                self.current_handler = self.handler_t
            elif contracts[contr]['first_handler'] == '1t':
                self.current_handler = self.handler_1t
            elif contracts[contr]['first_handler'] == 'w':
                self.current_handler = self.handler_w
            elif contracts[contr]['first_handler'] == 'f':
                self.current_handler = self.handler_f
            self.current_handler.get_flag()
	f_exp.close()

    def get_handler(self):
        rt_abandon = FH.surplus_abandon/((FH.ask_1+FH.bid_1)/2.0)
        print ('aaaa',time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),self.current_handler.tip)
        print (FH.goods,FH.balance_overflow,FH.forward_goods+FH.backward_goods+FH.balance_overflow,rt_abandon * FH.limit_goods)
        if FH.forward_goods + FH.backward_goods + FH.balance_overflow < rt_abandon * FH.limit_goods:
            if self.current_handler.tip == 't':
                if FH.t <= FH.t_tail:
                    self.current_handler = self.handler_1t
                    FH.t_head = 1.0
                print (self.current_handler.tip,FH.t,FH.t_tail)
            elif self.current_handler.tip == '1t':
                if FH.t >= FH.t_head:
                    self.current_handler = self.handler_t
                    FH.t_tail = -1.0
                print (self.current_handler.tip,FH.t,FH.t_head)
            elif self.current_handler.tip == 'w' or self.current_handler.tip == 'f':
                if (FH.forward_sprint and FH.backward_gap >= 0.0) or (FH.backward_sprint and FH.forward_gap >= 0.0):
                    self.current_handler = self.handler_t
                else:
                    if self.current_handler.tip == 'w':
                        if (FH.forward_sprint and FH.forward_mom) or (FH.backward_sprint and FH.backward_mom):
                            self.current_handler = self.handler_f
                    elif self.current_handler.tip == 'f':
                        if (FH.forward_sprint and FH.backward_mom) or (FH.backward_sprint and FH.forward_mom):
                            self.current_handler = self.handler_w
                    else:
                        self.current_handler = self.handler_f
        else:
            if self.current_handler.tip == 'w':
                if (FH.forward_sprint and FH.forward_mom) or (FH.backward_sprint and FH.backward_mom):
                    self.current_handler = self.handler_f
            elif self.current_handler.tip == 'f':
                if (FH.forward_sprint and FH.backward_mom) or (FH.backward_sprint and FH.forward_mom):
                    self.current_handler = self.handler_w
            else:
                self.current_handler = self.handler_f

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

