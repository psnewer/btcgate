# -*- coding: utf-8 -*-

from __future__ import print_function
from gate_api import FuturesOrder
from gate_api.rest import ApiException
from conf import *
from handler import *
from handler_t import *
from handler_0t import *
from handler_1t import *
from handler_w import *
from handler_f import *
import json
import codecs
import time
import traceback
import gate_api


class Future_Manager(object):
    def __init__(self):
        f_exp = codecs.open('./bucket/experiment_BTCUSDT.conf', 'r', encoding='utf-8')
        data_algs = json.load(f_exp)
        contracts = data_algs['contract']
        for contr in contracts:
            self.current_handler = FH(contr,contracts[contr])
            if contracts[contr]['first_handler'] == 't':
                self.current_handler = Handler_T()
            elif contracts[contr]['first_handler'] == '1t':
                self.current_handler = Handler_1T()
            elif contracts[contr]['first_handler'] == '0f':
                self.current_handler = Handler_0T('forward')
            elif contracts[contr]['first_handler'] == '0b':
                self.current_handler = Handler_0T('backward')
            elif contracts[contr]['first_handler'] == 'w':
                self.current_handler = Handler_W()
            elif contracts[contr]['first_handler'] == 'f':
                self.current_handler = Handler_F()
        f_exp.close()

    def get_handler(self):

        if FH.forward_position_size == 0 and FH.backward_position_size == 0:
            if self.current_handler.tip != 'f':
                FH.catch = False
                FH.balance = False
                self.current_handler = Handler_F()
                self.current_handler.get_flag()
        elif self.current_handler.tip == 't':
            if self.current_handler.current_side == 'biside':
                if ((FH.forward_position_size > 0.0 or FH.backward_position_size > 0.0) and FH.margin >= 0.0) or self.current_handler.T_rt != Handler_T.T_rt:
                    FH.catch = False
                    FH.balance = False
                    self.current_handler = Handler_W()
                    self.current_handler.get_flag()
            elif ((FH.backward_position_size > 0.0 and FH.forward_position_size > 0.0) and af(self.current_handler.D) >= af(FH.D_01 - Handler_0T.tap) and self.current_handler.D_std > af(FH.D_01 - Handler_0T.tap)) or \
                        (not (FH.backward_position_size > 0.0 and FH.forward_position_size > 0.0) and af(self.current_handler.D) >= af(FH.D_01) and af(self.current_handler.D_std) > FH.D_01) :
                FH.catch = False
                FH.balance = False
                if FH.forward_position_size > FH.backward_position_size:
                    self.current_handler = Handler_0T('backward')
                elif FH.forward_position_size < FH.backward_position_size:
                    self.current_handler = Handler_0T('forward')
                self.current_handler.get_flag()
                self.current_handler.adjust_guide(-FH.D_01 + Handler_0T.tap)
                self.current_handler.get_flag()
        elif self.current_handler.tip == '0t':
            if FH.margin >= 0.0:
                FH.catch = False
                FH.balance = False
                self.current_handler = Handler_W()
                self.current_handler.get_flag()
            elif self.current_handler.D_up >= af(-FH.D_01 + 3*Handler_0T.tap):
                self.current_handler.adjust_guide(-FH.D_01 + Handler_0T.tap)
                self.current_handler.get_flag()
            elif self.current_handler.D_dn < af(-FH.D_01 + Handler_0T.tap) and (FH.backward_position_size > 0.0 and FH.forward_position_size > 0.0):
                if af(self.current_handler.D) <= af(-FH.D_01 + Handler_0T.tap):
                    self.current_handler = Handler_T()
                    self.current_handler.get_flag()
                    if FH.goods_rt < 0.0:
                        self.current_handler.adjust_rt(FH.D_01 - Handler_0T.tap)
                        self.current_handler.get_flag()
            elif (self.current_handler.current_side == 'forward' and FH.forward_position_size == 0.0) or \
                    (self.current_handler.current_side == 'backward' and FH.backward_position_size == 0.0):
                if af(self.current_handler.D) <= af(-FH.D_01 + Handler_0T.tap):
                    self.current_handler = Handler_T()
                    self.current_handler.get_flag()
                    if FH.goods_rt < 0.0:
                        self.current_handler.adjust_rt(FH.D_01 - Handler_0T.tap)
                        self.current_handler.get_flag()
        elif self.current_handler.tip == 'w':
            if FH.margin < 0.0:
                FH.catch = False
                FH.balance = False
                self.current_handler = Handler_F()
                self.current_handler.get_flag()
        elif  self.current_handler.tip == 'f':
            if FH.forward_position_size == self.current_handler.forward_target_size and FH.backward_position_size == self.current_handler.backward_target_size:
                FH.catch = False
                FH.balance = False
                self.current_handler = Handler_T()
                self.current_handler.get_flag()

    def run(self):
        try:
            self.current_handler.get_flag()
            self.get_handler()
            print('aaaa', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), self.current_handler.tip)
            print(FH.goods, FH.balance_overflow, FH.margin, FH.endure_goods, FH.goods_rt)
            if FH.stable_spread:
                self.current_handler.put_position();
        except Exception as e:
            traceback.print_exc()
            dic_clear = True

            try:
                body_dic = json.loads(e.body)
            except Exception:
                send_email(e)
                dic_clear = False

            if dic_clear:
                e_sig = True
                if 'label' in body_dic:
                    if body_dic['label'] in ['ORDER_POC_IMMEDIATE','ORDER_NOT_FOUND','INCREASE_POSITION','ORDER_NOT_FOUND']:
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

