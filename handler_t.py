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

        if FH.limit_value > 0.0:
            FH.T_rt = FH.T_rt_std  + ((FH.forward_goods + FH.backward_goods + FH.balance_overflow) / FH.limit_value * FH.T_level) * FH.T_rt_std
            FH.max_T = 1.0 - (FH.forward_goods + FH.backward_goods + FH.balance_overflow) / FH.limit_value * FH.T_level
            FH.T_std = FH.T_guide + (FH.forward_goods + FH.backward_goods + FH.balance_overflow) / (FH.limit_value*FH.T_rt) * FH.T_level
        #if len(FH.forward_orders) + len(FH.backward_orders) == 0:
        #    if FH.T_std < 0.0:
        #        FH.T_guide += 0.0 - FH.T_std
        #        FH.T_std = 0.0
        #    elif FH.T_std > max_T:
        #        FH.T_guide += max_T - FH.T_std
        #        FH.T_std = max_T
        FH.D_std = FH.limit_size * (1.0 - FH.T_std)

        print('rt', FH.T_rt, FH.max_T)
        print(FH._T, FH.T_std, FH.D, FH.D_std, FH.forward_stable_price, FH.backward_stable_price)

        #if FH.forward_position_size == 0 or FH.backward_position_size == 0:
        #    FH.catch = True
        #    FH.balance = False
        #    FH.S_dn = FH.tick_price
        #    FH.S_dn_t = FH.tick_price - FH.step_soft
        #    FH.S_up = FH.tick_price + FH.step_soft
        #    FH.S_up_t = FH.tick_price + 2 * FH.step_soft
        #else:
        if FH.balance and not FH.catch:
            if (FH.tick_price >= FH.t_up_S and FH.step_soft > 0) or (
                    FH.tick_price <= FH.t_up_S and FH.step_soft < 0):
                FH.balance = False
                FH.catch = True
                FH.S_up = FH.tick_price
                FH.S_up_t = FH.tick_price + FH.step_soft
                FH.S_dn = FH.tick_price - FH.step_soft
                FH.S_dn_t = FH.tick_price - 2 * FH.step_soft
            elif (FH.tick_price <= FH.t_dn_S and FH.step_soft > 0) or (
                    FH.tick_price >= FH.t_dn_S and FH.step_soft < 0):
                FH.balance = False
                FH.catch = True
                FH.S_dn = FH.tick_price
                FH.S_dn_t = FH.tick_price - FH.step_soft
                FH.S_up = FH.tick_price + FH.step_soft
                FH.S_up_t = FH.tick_price + 2 * FH.step_soft
            print('balance', FH.tick_price, FH.t_up_S, FH.t_up, FH.t_dn, FH.t_dn_S)
        elif not FH.balance and FH.catch:
            if (FH.tick_price >= FH.S_up_t and FH.step_soft > 0) or (
                    FH.tick_price <= FH.S_up_t and FH.step_soft < 0):
                FH.catch = False
                FH.balance = True
                FH.t_up = FH.tick_price
                FH.t_dn = FH.tick_price - FH.step_soft
                FH.t_up_S = FH.tick_price + FH.step_soft
                FH.t_dn_S = FH.tick_price - 2 * FH.step_soft
            elif (FH.tick_price <= FH.S_dn_t and FH.step_soft > 0) or (
                    FH.tick_price >= FH.S_dn_t and FH.step_soft < 0):
                FH.catch = False
                FH.balance = True
                FH.t_dn = FH.tick_price
                FH.t_up = FH.tick_price + FH.step_soft
                FH.t_dn_S = FH.tick_price - FH.step_soft
                FH.t_up_S = FH.tick_price + 2 * FH.step_soft
            print('catch', FH.tick_price, FH.S_up_t, FH.S_up, FH.S_dn, FH.S_dn_t)
        elif not FH.balance and not FH.catch:
            FH.balance = True
            FH.t_up = FH.tick_price + FH.step_soft
            FH.t_dn = FH.tick_price - FH.step_soft
            FH.t_up_S = FH.tick_price + 2 * FH.step_soft
            FH.t_dn_S = FH.tick_price - 2 * FH.step_soft

        self.forward_gap_balance = False
        self.forward_balance_size = 0
        self.backward_gap_balance = False
        self.backward_balance_size = 0
        if FH.balance:
            if len(FH.forward_orders) + len(FH.backward_orders) == 0:
                if FH.forward_goods < FH.backward_goods:
                    if FH.tick_price > FH.t_dn:
                        if FH.stable_spread and FH.D > FH.D_std:
                            self.forward_gap_balance = True
                    elif FH.tick_price <= FH.t_up:
                        if FH._T >= 1.0 and FH.backward_goods > 0.0:
                            FH.T_guide += (1.0 - FH.tap / FH.limit_size) - FH.T_std
                            FH.T_std = 1.0 - FH.tap / FH.limit_size
                            FH.D_std = FH.tap
                        if FH.stable_spread and FH.D <= FH.D_std:
                            self.backward_gap_balance = True
                elif FH.forward_goods > FH.backward_goods:
                    if FH.tick_price < FH.t_dn:
                        if FH.stable_spread and FH.D > FH.D_std:
                            self.backward_gap_balance = True
                    elif FH.tick_price >= FH.t_up:
                        if FH._T >= 1.0 and FH.forward_goods > 0.0:
                            FH.T_guide += (1.0 - FH.tap / FH.limit_size) - FH.T_std
                            FH.T_std = 1.0 - FH.tap / FH.limit_size
                            FH.D_std = FH.tap
                        if FH.stable_spread and FH.D <= FH.D_std:
                            self.forward_gap_balance = True

        if self.forward_gap_balance:
            if FH.forward_goods > FH.backward_goods:
                self.forward_balance_size = int(max(FH.D-FH.D_std,-FH.forward_position_size))
                print ('d1',FH.D-FH.D_std,-FH.forward_position_size)
            else:
                if FH.forward_goods < 0:
                    self.forward_balance_size = int(max(FH.D_std-FH.D,FH.forward_position_size*FH.balance_overflow/FH.forward_goods))
                    print ('d2',FH.D_std-FH.D,FH.forward_position_size*FH.balance_overflow/FH.forward_goods,-FH.forward_position_size)
                else:
                    self.forward_balance_size = int(max(FH.D_std-FH.D,-FH.forward_position_size))
        if self.backward_gap_balance:
            if FH.backward_goods > FH.forward_goods:
                self.backward_balance_size = int(min(FH.D_std-FH.D,-FH.backward_position_size))
                print ('d3',FH.D_std-FH.D,-FH.backward_position_size)
            else:
                if FH.backward_goods < 0:
                    self.backward_balance_size = int(min(FH.D-FH.D_std,FH.backward_position_size*FH.balance_overflow/FH.backward_goods,-FH.backward_position_size))
                    print ('d4',FH.D-FH.D_std,FH.backward_position_size*FH.balance_overflow/FH.backward_goods)
                else:
                    self.backward_balance_size = int(min(FH.D-FH.D_std,-FH.backward_position_size))

        self.forward_catch = False
        self.forward_catch_size = 0
        self.backward_catch = False
        self.backward_catch_size = 0
        if FH.catch:
            if len(FH.forward_orders) + len(FH.backward_orders) == 0:
                if FH.forward_goods < FH.backward_goods:
                    if FH.tick_price <= FH.S_up:
                        if FH._T >= 1.0 and FH.backward_goods >= 0.0:
                            FH.T_guide += (1.0 - FH.tap / FH.limit_size) - FH.T_std
                            FH.T_std = 1.0 - FH.tap / FH.limit_size
                            FH.D_std = FH.tap
                        if FH.stable_spread and FH.D <= FH.D_std:
                            self.forward_catch = True
                            self.forward_catch_size = int(min(FH.D_std-FH.D,FH.forward_limit-FH.forward_position_size))
                            print ('b1',FH.D_std-FH.D,FH.forward_limit-FH.forward_position_size)
                    elif FH.tick_price >= FH.S_dn:
                        if FH.stable_spread and FH.D > FH.D_std:
                            self.backward_catch = True
                            self.backward_catch_size = int(max(FH.D_std-FH.D,-FH.backward_limit-FH.backward_position_size))
                            print ('b2',FH.D_std-FH.D,-FH.backward_limit-FH.backward_position_size)
                elif FH.backward_goods < FH.forward_goods:
                    if FH.tick_price >= FH.S_up:
                        if FH._T >= 1.0 and FH.forward_goods >= 0.0:
                            FH.T_guide += (1.0 - FH.tap / FH.limit_size) - FH.T_std
                            FH.T_std = 1.0 - FH.tap / FH.limit_size
                            FH.D_std = FH.tap
                        if FH.stable_spread and FH.D <= FH.D_std:
                            self.backward_catch = True
                            self.backward_catch_size = int(max(FH.D-FH.D_std,-FH.backward_limit-FH.backward_position_size))
                            print ('b3',FH.D-FH.D_std,-FH.backward_limit-FH.backward_position_size)
                    elif FH.tick_price <= FH.S_dn:
                        if FH.stable_spread and FH.D > FH.D_std:
                            self.forward_catch = True
                            self.forward_catch_size = int(min(FH.D-FH.D_std,FH.forward_limit-FH.forward_position_size))
                            print ('b4',FH.D-FH.D_std,FH.forward_limit-FH.forward_position_size)

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
                if (not self.forward_catch) or FH.forward_position_size >= FH.forward_limit:
                    forward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id,_request_timeout=10)
                elif self.forward_catch and self.forward_catch_size <= 0:
                    forward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id,_request_timeout=10)
                elif FH.bid_1 > order_price:
                    forward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id,_request_timeout=10)
            elif order_size < 0:
                if self.forward_gap_balance:
                    if order_price > FH.ask_1 or self.forward_balance_size >= 0:
                        forward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id,_request_timeout=10)
                else:
                    forward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id,_request_timeout=10)
        if not self.forward_increase_clear:
            if FH.forward_position_size < FH.forward_limit:
                if self.forward_catch and self.forward_catch_size > 0:
                    forward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size = self.forward_catch_size, price = FH.bid_1,tif='poc'),_request_timeout=10)
        if not self.forward_reduce_clear and self.forward_gap_balance:
            if FH.forward_position_size > 0:
                if self.forward_balance_size < 0:
                    forward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size=self.forward_balance_size,price = FH.ask_1,tif='poc'),_request_timeout=10)

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
                    backward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id,_request_timeout=10)
                elif self.backward_catch and self.backward_catch_size >= 0:
                    backward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id,_request_timeout=10)
                elif FH.ask_1 < order_price:
                    backward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id,_request_timeout=10)
            elif order_size > 0:
                if self.backward_gap_balance:
                    if order_price < FH.bid_1 or self.backward_balance_size <= 0:
                        backward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id,_request_timeout=10)
                else:
                    backward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id,_request_timeout=10)
        if not self.backward_increase_clear:
            if abs(FH.backward_position_size) < FH.backward_limit:
                if self.backward_catch and self.backward_catch_size < 0:
                    backward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size = self.backward_catch_size, price = FH.ask_1,tif='poc'),_request_timeout=10)
        if not self.backward_reduce_clear and self.backward_gap_balance:
            if FH.backward_position_size < 0:
                if self.backward_balance_size > 0:
                    backward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size=self.backward_balance_size,price = FH.bid_1,tif='poc'),_request_timeout=10)

        if FH.forward_liq_flag:
            forward_api_instance.cancel_price_triggered_order_list(contract=FH.contract,settle=FH.settle,_request_timeout=10)
            if FH.forward_liq_price > 0:
                forward_api_instance.create_price_triggered_order(settle=FH.settle,futures_price_triggered_order=FuturesPriceTriggeredOrder(initial=FuturesInitialOrder(contract=FH.contract,size=0,price=str(0),close=True,tif='ioc',text='api'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=2,price=str(round(FH.forward_liq_price*(1.0+0.1*1.0/FH.forward_leverage),FH.quanto)),expiration=2592000)),_request_timeout=10)
                FH.forward_trigger_liq = FH.forward_liq_price*(1.0+0.1*1.0/FH.forward_leverage)
        if FH.backward_liq_flag:
            backward_api_instance.cancel_price_triggered_order_list(contract=FH.contract,settle=FH.settle)
            if FH.backward_liq_price > 0:
                backward_api_instance.create_price_triggered_order(settle=FH.settle,futures_price_triggered_order=FuturesPriceTriggeredOrder(initial=FuturesInitialOrder(contract=FH.contract,size=0,price=str(0),close=True,tif='ioc',text='api'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=1,price=str(round(FH.backward_liq_price*(1.0-0.1*1.0/FH.backward_leverage),FH.quanto)),expiration=2592000)),_request_timeout=10)
                FH.backward_trigger_liq = FH.backward_liq_price*(1.0-0.1*1.0/FH.backward_leverage)

