# -*- coding: utf-8 -*-

from __future__ import print_function
import requests
import time
import math
import numpy as np
import gate_api
from gate_api import FuturesOrder
from gate_api import FuturesPriceTriggeredOrder
from gate_api import FuturesInitialOrder
from gate_api import FuturesPriceTrigger
from gate_api.rest import ApiException
from conf import *
from handler import *

class Handler_T(FH):
    def __init__(self):
        self.tip = 't'

    def get_flag(self):
        self.get_std_flag()
        if FH.forward_account_from == 0:
            FH.forward_account_from = int(time.time())
        if FH.backward_account_from == 0:
            FH.backward_account_from = int(time.time())
        forward_account_book = forward_api_instance.list_futures_account_book(settle=FH.settle,_from=FH.forward_account_from)
        backward_account_book = backward_api_instance.list_futures_account_book(settle=FH.settle,_from=FH.backward_account_from)
        for item in forward_account_book:
            if FH.contract in item.text:
                FH.goods += float(item.change)
                if item.type == 'pnl':
                    FH.balance_overflow += float(item.change)
        for item in backward_account_book:
            if FH.contract in item.text:
                FH.goods += float(item.change)
                if item.type == 'pnl':
                    FH.balance_overflow += float(item.change)
        if len(forward_account_book) > 0:
            FH.forward_account_from = int(forward_account_book[0]._time) + 1
        if len(backward_account_book) > 0:
            FH.backward_account_from = int(backward_account_book[0]._time) + 1
        
        if FH.forward_gap < 0.0 and FH.backward_gap >= 0.0:
            FH._T = abs(float(FH.backward_position_size) / float(FH.forward_position_size))
        elif FH.backward_gap < 0.0 and FH.forward_gap >= 0.0:
            FH._T = abs(float(FH.forward_position_size) / float(FH.backward_position_size))
        elif FH.forward_gap < 0.0 and FH.backward_gap < 0.0:
            if FH.forward_gap > FH.backward_gap:
                FH._T = abs(float(FH.forward_position_size) / float(FH.backward_position_size))
            else:
                FH._T = abs(float(FH.backward_position_size) / float(FH.forward_position_size))
        elif FH.forward_gap >= 0.0 and FH.backward_gap >= 0.0:
            FH._T = 0.61

        if FH.forward_gap < 0.0 and FH.backward_gap >= 0.0:
            FH._S = -FH.balance_overflow/FH.forward_goods
            FH.S_ = -FH.backward_goods/FH.forward_goods
        elif FH.backward_gap < 0.0 and FH.forward_gap >= 0.0:
            FH._S = -FH.balance_overflow/FH.backward_goods
            FH.S_ = -FH.forward_goods/FH.backward_goods
        elif FH.forward_gap < 0.0 and FH.backward_gap < 0.0:
            FH._S = -FH.balance_overflow/(FH.forward_goods+FH.backward_goods)
            if FH.forward_gap > FH.backward_gap:
                FH.S_ = -FH.forward_goods/(FH.backward_goods+FH.forward_goods)
            else:
                FH.S_ = -FH.backward_goods/(FH.forward_goods+FH.backward_goods)
        elif FH.forward_gap >= 0.0 and FH.backward_gap >= 0.0:
            FH._S = 1.0
            FH.S_ = 1.0

        if FH.forward_gap < 0.0 and FH.backward_gap >= 0.0:
            FH.t = -FH.t_b/FH.t_f
            FH.T_std = 1.0 - 1.0*FH.t
            if FH._T  < FH.T_std:
                FH.t_tail = min(FH.t_tail,FH.forward_value*(FH.ask_1+FH.step_hard)/FH.ask_1*(FH.ask_1-FH.forward_entry_price+FH.step_hard)/FH.forward_entry_price + FH.backward_value*(FH.bid_1+FH.step_hard)/FH.bid_1*(FH.backward_entry_price-FH.bid_1-FH.step_hard)/FH.backward_entry_price + FH.balance_overflow) 
        elif FH.backward_gap < 0.0 and FH.forward_gap >= 0.0:
            FH.t = -FH.t_f/FH.t_b
            FH.T_std = 1.0 - 1.0*FH.t
            if FH._T < FH.T_std:
                FH.t_tail = min(FH.t_tail,FH.forward_value*(FH.ask_1-FH.step_hard)/FH.ask_1*(FH.ask_1-FH.forward_entry_price-FH.step_hard)/FH.forward_entry_price + FH.backward_value*(FH.bid_1-FH.step_hard)/FH.bid_1*(FH.backward_entry_price-FH.bid_1+FH.step_hard)/FH.backward_entry_price + FH.balance_overflow)
        elif FH.forward_gap < 0.0 and FH.backward_gap < 0.0:
            if FH.forward_gap > FH.backward_gap:
                FH.t = -FH.t_f/(FH.t_b+FH.t_f)
            else:
                FH.t = -FH.t_b/(FH.t_f+FH.t_b)
            FH.T_std = 1.0
#        elif FH.forward_gap >= 0.0 and FH.backward_gap >= 0.0:
#            FH.T_std = 0.61

        if (FH.forward_position_size == 0 and FH.backward_position_size < 0) or (FH.forward_position_size != 0 and FH.backward_position_size > 0):
            self.tif = 'ioc'
        else:
            self.tif = 'poc'

        if FH.forward_position_size == 0 or FH.backward_position_size == 0:
            FH.catch = True
            FH.balance = False
            FH.S_dn = FH.S_
            FH.S_dn_t = -FH.rt_soft
            FH.S_up = FH.rt_soft
            FH.S_up_t = 2*FH.rt_soft
        else:
            if FH.balance and not FH.catch:
                FH.t_up = min(FH.t_up,(1.0-FH.rt_soft)*FH.t+FH.rt_soft)
                FH.t_up_S = min(FH.t_up_S,(1.0-2*FH.rt_soft)*FH.t+2*FH.rt_soft)
                FH.t_dn = max(FH.t_dn,(1.0+FH.rt_soft)*FH.t-FH.rt_soft)
                FH.t_dn_S = max(FH.t_dn_S,(1.0+2*FH.rt_soft)*FH.t-2*FH.rt_soft)
                if FH.t >= FH.t_up_S:
                    FH.balance = False
                    FH.catch = True
                    FH.S_up = FH.S_
                    FH.S_up_t = (1.0-FH.rt_soft)*FH.S_+FH.rt_soft*FH._T
                    FH.S_dn = (1.0+FH.rt_soft)*FH.S_-FH.rt_soft*FH._T
                    FH.S_dn_t = (1.0+2*FH.rt_soft)*FH.S_-2*FH.rt_soft*FH._T
                elif FH.t <= FH.t_dn_S:
                    FH.balance = False
                    FH.catch = True
                    FH.S_dn = FH.S_
                    FH.S_dn_t = (1.0+FH.rt_soft)*FH.S_-FH.rt_soft*FH._T
                    FH.S_up = (1.0-FH.rt_soft)*FH.S_+FH.rt_soft*FH._T
                    FH.S_up_t = (1.0-2*FH.rt_soft)*FH.S_+2*FH.rt_soft*FH._T
                print ('balance',FH.t,FH.t_up_S,FH.t_up,FH.t_dn,FH.t_dn_S)
            elif not FH.balance and FH.catch:
                FH.S_up = min(FH.S_up,(1.0-FH.rt_soft)*FH.S_+FH.rt_soft*FH._T)
                FH.S_up_t = min(FH.S_up_t,(1.0-2*FH.rt_soft)*FH.S_+2*FH.rt_soft*FH._T)
                FH.S_dn = max(FH.S_dn,(1.0+FH.rt_soft)*FH.S_-FH.rt_soft*FH._T)
                FH.S_dn_t = max(FH.S_dn_t,(1.0+2*FH.rt_soft)*FH.S_-2*FH.rt_soft*FH._T)
                if FH.S_ >= FH.S_up_t:
                    FH.catch = False
                    FH.balance = True
                    FH.t_up = FH.t
                    FH.t_dn = (1.0+FH.rt_soft)*FH.t-FH.rt_soft
                    FH.t_up_S = (1.0-FH.rt_soft)*FH.t+FH.rt_soft
                    FH.t_dn_S = (1.0+2*FH.rt_soft)*FH.t-2*FH.rt_soft
                elif FH.S_ <= FH.S_dn_t:
                    FH.catch = False
                    FH.balance = True
                    FH.t_dn = FH.t
                    FH.t_up = (1.0-FH.rt_soft)*FH.t+FH.rt_soft
                    FH.t_dn_S = (1.0+FH.rt_soft)*FH.t-FH.rt_soft
                    FH.t_up_S = (1.0-2*FH.rt_soft)*FH.t+2*FH.rt_soft
                print ('catch',FH.S_,FH.S_up_t,FH.S_up,FH.S_dn,FH.S_dn_t)
            elif not FH.balance and not FH.catch:
                FH.balance = True
                FH.t_up = (1.0-FH.rt_soft)*FH.t+FH.rt_soft
                FH.t_dn = (1.0+FH.rt_soft)*FH.t-FH.rt_soft
                FH.t_up_S = (1.0-2*FH.rt_soft)*FH.t+2*FH.rt_soft
                FH.t_dn_S = (1.0+2*FH.rt_soft)*FH.t-2*FH.rt_soft
        
        self.forward_gap_balance = False
        self.forward_balance_size = 0
        self.backward_gap_balance = False
        self.backward_balance_size = 0
        if FH.balance:
            if FH.forward_gap < 0.0 and FH.backward_gap >= 0.0:
                if FH.forward_stable_price and FH._T < FH.T_std:
                    if FH.t <= FH.t_dn:
                        self.forward_gap_balance = True
                elif FH.backward_stable_price and FH._T > FH.T_std:
                    if FH.t >= FH.t_up:
                        self.backward_gap_balance = True
            elif FH.backward_gap < 0.0 and FH.forward_gap >= 0.0:
                if FH.backward_stable_price and FH._T < FH.T_std:
                    if FH.t <= FH.t_dn:
                        self.backward_gap_balance = True
                elif FH.forward_stable_price and FH._T > FH.T_std:
                    if FH.t >= FH.t_up:
                        self.forward_gap_balance = True
            elif FH.forward_gap < 0.0 and FH.backward_gap < 0.0:
                if FH.forward_gap > FH.backward_gap:
                    if FH.backward_stable_price and FH._T < FH.T_std:
                        if FH.t <= FH.t_dn and FH.backward_sprint:
                            self.backward_gap_balance = True
                else:
                    if FH.forward_stable_price and FH._T < FH.T_std:
                        if FH.t <= FH.t_dn and FH.forward_sprint:
                            self.forward_gap_balance = True
    #        elif FH.forward_gap >= 0.0 and FH.backward_gap >= 0.0:
    #            if FH.forward_position_size > 0:
    #                self.forward_gap_balance = True
    #            if FH.backward_position_size > 0:
    #                self.backward_gap_balance = True

        if self.forward_gap_balance:
            if FH.forward_gap >= 0.0:
                if FH.backward_gap < 0.0:
                    self.forward_balance_size = int(max(-FH.forward_position_size-FH.backward_position_size*FH.T_std,-FH.forward_position_size))
                    print ('d1',-FH.forward_position_size-FH.backward_position_size*FH.T_std,-FH.forward_position_size)
                else:
                    self.forward_balance_size = int(-FH.forward_position_size - FH.backward_position_size*FH.T_std)
            else:
                if FH.backward_gap >= 0.0:
                    self.forward_balance_size = int(max(-FH.backward_position_size/FH.T_std-FH.forward_position_size,FH.forward_position_size*FH.balance_overflow/FH.forward_goods))
                    print ('d2',-FH.backward_position_size/FH.T_std-FH.forward_position_size,FH.forward_position_size*FH.balance_overflow/FH.forward_goods)
                else:
                    self.forward_balance_size = int(max(-FH.backward_position_size/FH.T_std-FH.forward_position_size,FH.forward_position_size*FH.balance_overflow/FH.forward_goods))
                    print ('d2',-FH.backward_position_size/FH.T_std-FH.forward_position_size,FH.forward_position_size*FH.balance_overflow/FH.forward_goods)
        if self.backward_gap_balance:
            if FH.backward_gap >= 0.0:
                if FH.forward_gap < 0.0:
                    self.backward_balance_size = int(min(-FH.backward_position_size-FH.forward_position_size*FH.T_std,-FH.backward_position_size))
                    print ('d3',-FH.backward_position_size-FH.forward_position_size*FH.T_std,-FH.backward_position_size)
                else:
                    self.backward_balance_size = int(-FH.backward_position_size - FH.forward_position_size*FH.T_std)
            else:
                if FH.forward_gap >= 0.0:
                    self.backward_balance_size = int(min(-FH.forward_position_size/FH.T_std-FH.backward_position_size,FH.backward_position_size*FH.balance_overflow/FH.backward_goods))
                    print ('d4',-FH.forward_position_size/FH.T_std-FH.backward_position_size,FH.backward_position_size*FH.balance_overflow/FH.backward_goods)
                else:
                    self.backward_balance_size = int(min(-FH.forward_position_size/FH.T_std-FH.backward_position_size,FH.backward_position_size*FH.balance_overflow/FH.backward_goods))
                    print ('d4',-FH.forward_position_size/FH.T_std-FH.backward_position_size,FH.backward_position_size*FH.balance_overflow/FH.backward_goods)
        
        self.forward_catch = False
        self.forward_catch_size = 0
        self.backward_catch = False
        self.backward_catch_size = 0
        print (FH._T,FH.T_std)
        if FH.catch:
            if FH.forward_gap < 0.0 and FH.backward_gap >= 0.0:
                if FH._T > FH.T_std:
                    if FH.backward_stable_price and FH.S_ >= FH.S_up:
                        self.forward_catch = True
                        self.forward_catch_size = int(min(-FH.backward_position_size/FH.T_std-FH.forward_position_size,FH.forward_limit-FH.forward_position_size))
                        print ('1111',-FH.backward_position_size/FH.T_std-FH.forward_position_size,FH.forward_limit-FH.forward_position_size)
                elif FH._T < FH.T_std:
                    if FH.forward_stable_price and FH.S_ <= FH.S_dn:
                        self.backward_catch = True
                        self.backward_catch_size = int(max(-FH.forward_position_size*FH.T_std-FH.backward_position_size,-FH.backward_limit-FH.backward_position_size))
                        print ('bbbb',-FH.forward_position_size*FH.T_std-FH.backward_position_size,-FH.backward_limit-FH.backward_position_size)
            elif FH.backward_gap < 0.0 and FH.forward_gap >= 0.0:
                if FH._T > FH.T_std:
                    if FH.forward_stable_price and FH.S_ >= FH.S_up:
                        self.backward_catch = True
                        self.backward_catch_size = int(max(-FH.forward_position_size/FH.T_std-FH.backward_position_size,-FH.backward_limit-FH.backward_position_size))
                        print ('2222',-FH.forward_position_size/FH.T_std-FH.backward_position_size,-FH.backward_limit-FH.backward_position_size)
                elif FH._T < FH.T_std:
                    if FH.backward_stable_price and FH.S_ <= FH.S_dn:
                        self.forward_catch = True
                        self.forward_catch_size = int(min(-FH.backward_position_size*FH.T_std-FH.forward_position_size,FH.forward_limit-FH.forward_position_size))
                        print ('cccc',-FH.backward_position_size*FH.T_std-FH.forward_position_size,FH.forward_limit-FH.forward_position_size)
            elif FH.forward_gap < 0.0 and FH.backward_gap < 0.0:
                if FH._T < FH.T_std:
                    if FH.forward_gap > FH.backward_gap:
                        if FH.backward_stable_price and FH.S_ <= FH.S_dn and FH.backward_sprint:
                            self.forward_catch = True
                            self.forward_catch_size = int(min(-FH.backward_position_size*FH.T_std-FH.forward_position_size,FH.forward_limit-FH.forward_position_size))
                            print ('cccc',-FH.backward_position_size*FH.T_std-FH.forward_position_size,FH.forward_limit-FH.forward_position_size)
                    else:
                        if FH.forward_stable_price and FH.S_ <= FH.S_dn and FH.forward_sprint:
                            self.backward_catch = True
                            self.backward_catch_size = int(max(-FH.forward_position_size*FH.T_std-FH.backward_position_size,-FH.backward_limit-FH.backward_position_size))
                            print ('bbbb',-FH.forward_position_size*FH.T_std-FH.backward_position_size,-FH.backward_limit-FH.backward_position_size)

    def put_position(self):
        if FH.forward_leverage != FH.forward_gap_level:
            forward_api_instance.update_position_leverage(contract=FH.contract,settle=FH.settle,leverage = FH.forward_gap_level)
            FH.forward_leverage = FH.forward_gap_level
        if FH.backward_leverage != FH.backward_gap_level:
            backward_api_instance.update_position_leverage(contract=FH.contract,settle=FH.settle,leverage = FH.backward_gap_level)
            FH.backward_leverage = FH.backward_gap_level

        self.forward_increase_clear = False
        self.forward_reduce_clear = False
        for order in FH.forward_orders:
            order_price = float(order._price)
            order_size = order._size
            order_id = order._id
            if order_size > 0:
                self.forward_increase_clear = True
            elif order_size < 0:
                self.forward_reduce_clear = True
            if order_size > 0:
                if (not self.forward_catch) or FH.forward_position_size >= FH.forward_limit:
                    forward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
                elif self.forward_catch and self.forward_catch_size <= 0:
                    forward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
                elif FH.bid_1 > order_price:
                    forward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
            elif order_size < 0:
                if self.forward_gap_balance:
                    if order_price > FH.ask_1 or self.forward_balance_size >= 0:
                        forward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
                else:
                    forward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
        if not self.forward_increase_clear:
            if FH.forward_position_size < FH.forward_limit:
                if self.forward_catch and self.forward_catch_size > 0:
                    if self.tif == 'ioc':
                        forward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size = self.forward_catch_size, price = FH.ask_1*1.0001,tif='ioc'))
                    else:
                        forward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size = self.forward_catch_size, price = FH.bid_1,tif='poc'))
        if not self.forward_reduce_clear and self.forward_gap_balance:
            if FH.forward_position_size > 0:
                if self.forward_balance_size < 0:
                    forward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size=self.forward_balance_size,price = FH.ask_1,tif='poc'))

        self.backward_increase_clear = False
        self.backward_reduce_clear = False
        for order in FH.backward_orders:
            order_price = float(order._price)
            order_size = order._size
            order_id = order._id
            if order_size < 0:
                self.backward_increase_clear = True
            elif order_size > 0:
                self.backward_reduce_clear = True
            if order_size < 0:
                if (not self.backward_catch) or abs(FH.backward_position_size) >= FH.backward_limit:
                    backward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
                elif self.backward_catch and self.backward_catch_size >= 0:
                    backward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
                elif FH.ask_1 < order_price:
                    backward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
            elif order_size > 0:
                if self.backward_gap_balance:
                    if order_price < FH.bid_1 or self.backward_balance_size <= 0:
                        backward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
                else:
                    backward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
        if not self.backward_increase_clear:
            if abs(FH.backward_position_size) < FH.backward_limit:
                if self.backward_catch and self.backward_catch_size < 0:
                    if self.tif == 'ioc':
                        backward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size = self.backward_catch_size, price = FH.bid_1*0.9999,tif='ioc'))
                    else:
                        backward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size = self.backward_catch_size, price = FH.ask_1,tif='poc'))
        if not self.backward_reduce_clear and self.backward_gap_balance:
            if FH.backward_position_size < 0:
                if self.backward_balance_size > 0:
                    backward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size=self.backward_balance_size,price = FH.bid_1,tif='poc'))

        if FH.forward_liq_flag:
            forward_api_instance.cancel_price_triggered_order_list(contract=FH.contract,settle=FH.settle)
            if FH.forward_liq_price > 0:
                forward_api_instance.create_price_triggered_order(settle=FH.settle,futures_price_triggered_order=FuturesPriceTriggeredOrder(initial=FuturesInitialOrder(contract=FH.contract,size=0,price=str(0),close=True,tif='ioc',text='api'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=2,price=str(round(FH.forward_liq_price*(1.0+0.1*1.0/FH.forward_leverage),FH.quanto)),expiration=2592000)))
                FH.forward_trigger_liq = FH.forward_liq_price*(1.0+0.1*1.0/FH.forward_leverage)
        if FH.backward_liq_flag:
            backward_api_instance.cancel_price_triggered_order_list(contract=FH.contract,settle=FH.settle)
            if FH.backward_liq_price > 0:
                backward_api_instance.create_price_triggered_order(settle=FH.settle,futures_price_triggered_order=FuturesPriceTriggeredOrder(initial=FuturesInitialOrder(contract=FH.contract,size=0,price=str(0),close=True,tif='ioc',text='api'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=1,price=str(round(FH.backward_liq_price*(1.0-0.1*1.0/FH.backward_leverage),FH.quanto)),expiration=2592000)))
                FH.backward_trigger_liq = FH.backward_liq_price*(1.0-0.1*1.0/FH.backward_leverage)

