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
from handler_0t import *

class Handler_T(FH):
    T_rt = 1.0
    tap = 1

    def __init__(self):
        self.tip = 't'
        self.tap = Handler_T.tap
        self.T_rt = Handler_T.T_rt
        self.T_guide = 0.0

    def get_flag(self):
        self.get_std_flag()

        if FH.backward_position_size > FH.forward_position_size:
            FH.current_side = 'forward'
            self.D = FH.backward_position_size - FH.forward_position_size
        elif FH.forward_position_size > FH.backward_position_size:
            FH.current_side = 'backward'
            self.D = FH.forward_position_size - FH.backward_position_size
        else:
            FH.current_side = 'biside'
            self.D = 0.0

        self.get_side()

        self.T_std = self.T_guide - FH.goods_rt / self.T_rt
        self.D_std = FH.limit_size * self.T_std

        if FH.backward_position_size > 0.0 and FH.forward_position_size > 0.0:
            self.top = FH.D_01 - Handler_0T.tap
        else:
            self.top = FH.D_01

        print(FH.current_side, self.T_guide, self.T_rt)
        print(self.T_std, self.D, self.D_std, FH.forward_stable_price, FH.backward_stable_price)

        self.forward_gap_balance = False
        self.forward_balance_size = 0
        self.backward_gap_balance = False
        self.backward_balance_size = 0
        if FH.balance:
            if len(FH.forward_orders) + len(FH.backward_orders) == 0:
                if FH.current_side == 'backward':
                    if FH.tick_price > FH.t_dn:
                        if FH.stable_spread and self.D > self.D_std:
                            self.forward_gap_balance = True
                    elif FH.tick_price <= FH.t_up:
                        if FH.stable_spread and self.D < self.D_std:
                            if FH.backward_goods >= 0.0:
                                self.backward_gap_balance = True
                elif FH.current_side == 'forward':
                    if FH.tick_price < FH.t_dn:
                        if FH.stable_spread and self.D > self.D_std:
                            self.backward_gap_balance = True
                    elif FH.tick_price >= FH.t_up:
                        if FH.stable_spread and self.D < self.D_std:
                            if FH.forward_goods >= 0.0:
                                self.forward_gap_balance = True
                elif FH.current_side == 'biside':
                    self.adjust_guide(self.tap)
                    if FH.tick_price >= FH.t_up:
                        if FH.stable_spread and self.D < self.D_std:
                            if FH.forward_goods >= 0.0:
                                self.forward_gap_balance = True
                    elif FH.tick_price <= FH.t_dn:
                        if FH.stable_spread and self.D < self.D_std:
                            if FH.backward_goods >= 0.0:
                                self.backward_gap_balance = True

        if self.forward_gap_balance:
            if FH.forward_position_size > 0.0:
                if FH.current_side == 'forward' or FH.current_side == 'biside':
                    self.forward_balance_size = int(min(cutoff(self.tap, 0, self.D, self.D_std, der='inc', top=self.top),FH.forward_position_size))
                    print ('d1',self.D_std-self.D,FH.forward_position_size)
                else:
                    if FH.forward_goods < 0:
                        self.forward_balance_size = int(min(cutoff(self.tap, 0, self.D, self.D_std, der='red', top=self.top), -FH.forward_position_size * min(1.0, max(0.0, FH.balance_overflow) / FH.forward_goods)))
                        print ('d2',self.D-self.D_std,-FH.forward_position_size*FH.balance_overflow/FH.forward_goods)
                    else:
                        self.forward_balance_size = int(min(cutoff(self.tap, 0, self.D, self.D_std, der='red', top=self.top),FH.forward_position_size))
        if self.backward_gap_balance:
            if FH.backward_position_size > 0.0:
                if FH.current_side == 'backward' or FH.current_side == 'biside':
                    self.backward_balance_size = int(min(cutoff(self.tap, 0, self.D, self.D_std, der='inc', top=self.top),FH.backward_position_size))
                    print ('d3',self.D_std-self.D,FH.backward_position_size)
                else:
                    if FH.backward_goods < 0:
                        self.backward_balance_size = int(min(cutoff(self.tap, 0, self.D, self.D_std, der='red', top=self.top), -FH.backward_position_size * min(1.0, max(0.0, FH.balance_overflow) / FH.backward_goods)))
                        print ('d4',self.D-self.D_std,-FH.backward_position_size*FH.balance_overflow/FH.backward_goods)
                    else:
                        self.backward_balance_size = int(min(cutoff(self.tap, 0, self.D, self.D_std, der='red', top=self.top),FH.backward_position_size))

        self.forward_catch = False
        self.forward_catch_size = 0
        self.backward_catch = False
        self.backward_catch_size = 0
        if FH.catch:
            if len(FH.forward_orders) + len(FH.backward_orders) == 0:
                if FH.current_side == 'backward':
                    if FH.tick_price <= FH.S_up:
                        if FH.stable_spread and self.D < self.D_std:
                            if FH.backward_goods >= 0.0:
                                self.forward_catch = True
                                self.forward_catch_size = int(min(cutoff(self.tap,0,self.D,self.D_std,der='inc',top=self.top), FH.forward_limit-FH.forward_position_size))
                                print ('b1',self.D_std-self.D, FH.forward_limit-FH.forward_position_size)
                    elif FH.tick_price >= FH.S_dn:
                        if FH.stable_spread and self.D > self.D_std:
                            self.backward_catch = True
                            self.backward_catch_size = int(min(cutoff(self.tap,0,self.D,self.D_std,der='red',top=self.top), FH.forward_position_size-FH.backward_position_size))
                            print ('b2',self.D-self.D_std,FH.backward_limit-FH.backward_position_size)
                elif FH.current_side == 'forward':
                    if FH.tick_price >= FH.S_up:
                        if FH.stable_spread and self.D < self.D_std:
                            if FH.t_f >= 0.0:
                                self.backward_catch = True
                                self.backward_catch_size = int(min(cutoff(self.tap,0,self.D,self.D_std,der='inc',top=self.top), FH.backward_limit-FH.backward_position_size))
                                print ('b3',self.D_std-self.D,FH.backward_limit-FH.backward_position_size)
                    elif FH.tick_price <= FH.S_dn:
                        if FH.stable_spread and self.D > self.D_std:
                            self.forward_catch = True
                            self.forward_catch_size = int(min(cutoff(self.tap, 0, self.D, self.D_std, der='red', top=self.top),FH.backward_position_size - FH.forward_position_size))
                            print ('b4',self.D-self.D_std,FH.forward_limit-FH.forward_position_size)
                elif FH.current_side == 'biside':
                    self.adjust_guide(self.tap)
                    if  FH.tick_price <= FH.S_dn:
                        if FH.stable_spread and self.D < self.D_std:
                            if FH.backward_goods >= 0.0:
                                self.forward_catch = True
                                self.forward_catch_size = int(min(cutoff(self.tap,0,self.D,self.D_std,der='inc',top=self.top), FH.forward_limit-FH.forward_position_size))
                    elif FH.tick_price >= FH.S_up:
                        if FH.stable_spread and self.D < self.D_std:
                            if FH.forward_goods >= 0.0:
                                self.backward_catch = True
                                self.backward_catch_size = int(min(cutoff(self.tap,0,self.D,self.D_std,der='inc',top=self.top), FH.backward_limit-FH.backward_position_size))

    def put_position(self):
        if FH.forward_leverage != FH.forward_gap_level:
            forward_api_instance.update_position_leverage(contract=FH.contract,settle=FH.settle,leverage = FH.forward_gap_level,_request_timeout=10)
            FH.forward_leverage = FH.forward_gap_level
        if FH.backward_leverage != FH.backward_gap_level:
            backward_api_instance.update_position_leverage(contract=FH.contract,settle=FH.settle,leverage = FH.backward_gap_level,_request_timeout=10)
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
                if self.forward_catch:
                    if FH.bid_1 > order_price:
                        forward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id,_request_timeout=10)
                else:
                    forward_api_instance.cancel_futures_order(settle=FH.settle, order_id=order_id, _request_timeout=10)
            elif order_size < 0:
                if self.forward_gap_balance:
                    if order_price > FH.ask_1:
                        forward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id,_request_timeout=10)
                else:
                    forward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id,_request_timeout=10)
        if not self.forward_increase_clear:
            if FH.forward_position_size < FH.forward_limit:
                if self.forward_catch and self.forward_catch_size > 0:
                    forward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size = self.forward_catch_size, price = FH.bid_1,tif='poc'),_request_timeout=10)
        if not self.forward_reduce_clear and self.forward_gap_balance:
            if FH.forward_position_size > 0:
                if self.forward_balance_size > 0:
                    forward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size=-self.forward_balance_size,price = FH.ask_1,tif='poc'),_request_timeout=10)

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
                if self.backward_catch:
                    if FH.ask_1 < order_price:
                        backward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id,_request_timeout=10)
                else:
                    backward_api_instance.cancel_futures_order(settle=FH.settle, order_id=order_id, _request_timeout=10)
            elif order_size > 0:
                if self.backward_gap_balance:
                    if order_price < FH.bid_1:
                        backward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id,_request_timeout=10)
                else:
                    backward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id,_request_timeout=10)
        if not self.backward_increase_clear:
            if FH.backward_position_size < FH.backward_limit:
                if self.backward_catch and self.backward_catch_size > 0:
                    backward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size = -self.backward_catch_size, price = FH.ask_1,tif='poc'),_request_timeout=10)
        if not self.backward_reduce_clear and self.backward_gap_balance:
            if FH.backward_position_size > 0:
                if self.backward_balance_size > 0:
                    backward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size=self.backward_balance_size,price = FH.bid_1,tif='poc'),_request_timeout=10)

        #if FH.forward_liq_flag:
        #    forward_api_instance.cancel_price_triggered_order_list(contract=FH.contract,settle=FH.settle,_request_timeout=10)
        #    if FH.forward_liq_price > 0:
        #        forward_api_instance.create_price_triggered_order(settle=FH.settle,futures_price_triggered_order=FuturesPriceTriggeredOrder(initial=FuturesInitialOrder(contract=FH.contract,size=0,price=str(0),close=True,tif='ioc',text='api'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=2,price=str(round(FH.forward_liq_price*(1.0+0.1*1.0/FH.forward_leverage),FH.quanto)),expiration=2592000)),_request_timeout=10)
        #        FH.forward_trigger_liq = FH.forward_liq_price*(1.0+0.1*1.0/FH.forward_leverage)
        #if FH.backward_liq_flag:
        #    backward_api_instance.cancel_price_triggered_order_list(contract=FH.contract,settle=FH.settle,_request_timeout=10)
        #    if FH.backward_liq_price > 0:
        #        backward_api_instance.create_price_triggered_order(settle=FH.settle,futures_price_triggered_order=FuturesPriceTriggeredOrder(initial=FuturesInitialOrder(contract=FH.contract,size=0,price=str(0),close=True,tif='ioc',text='api'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=1,price=str(round(FH.backward_liq_price*(1.0-0.1*1.0/FH.backward_leverage),FH.quanto)),expiration=2592000)),_request_timeout=10)
        #        FH.backward_trigger_liq = FH.backward_liq_price*(1.0-0.1*1.0/FH.backward_leverage)

    def adjust_guide(self,D_std):
        self.T_guide += D_std / FH.limit_size - (self.T_guide - FH.goods_rt / self.T_rt)
        self.T_std = D_std / FH.limit_size
        self.D_std = D_std

    def adjust_rt(self,D_std):
        self.T_rt = FH.goods_rt / (self.T_guide - D_std / FH.limit_size)
        self.T_std = D_std / FH.limit_size
        self.D_std = D_std

