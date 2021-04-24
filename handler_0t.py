# -*- coding: utf-8 -*-

from __future__ import print_function
import requests
import time
import math
import numpy as np
from conf import *
from handler import *
from handler_t import *

class Handler_0T(FH):
    tap = 4

    def __init__(self,side):
        self.tip = '0t'
        self.tap = 4
        FH.current_side = side
        self.margin = 0.0
        #self.pre_N = min(FH.forward_position_size,FH.backward_position_size) / self.tap
        self.T_guide_up = 0.0
        self.T_guide_dn = 0.0

    def get_flag(self):

        self.get_std_flag()

        if FH.current_side == 'forward':
            self.margin = FH.forward_goods + FH.balance_overflow
            self.D = FH.forward_position_size - FH.backward_position_size
            #self.N = FH.forward_position_size / self.tap
        elif FH.current_side == 'backward':
            self.margin = FH.backward_goods + FH.balance_overflow
            self.D = FH.backward_position_size - FH.forward_position_size
            #self.N = FH.backward_position_size / self.tap

        self.get_side()

        #if self.N > 0.0:
        #    self.T_rt_up = self.T_para_up / self.N
        #else:
        #    self.T_rt_up = self.T_para_up
        #if self.N > 1.0:
        #    self.T_rt_dn = self.T_para_dn / (self.N - 1)
        #elif self.N > 0.0:
        #    self.T_rt_dn = self.T_para_dn / self.N
        #else:
        #    self.T_rt_dn = self.T_para_dn

        #if af(self.pre_N) != af(self.N):
        #    self.pre_N = self.N
        #    print('qqqq', self.N, self.T_rt_up, self.T_rt_dn)
        #    self.T_guide_up += self.T_std_up - (self.T_guide_up + self.goods_rt * self.T_rt_up)
        #    self.T_guide_dn += self.T_std_dn - (self.T_guide_dn + self.goods_rt * self.T_rt_dn)

        self.T_rt_up = FH.tick_price / (abs(FH.step_hard) * FH.T_level)
        self.T_rt_dn = FH.tick_price / (abs(FH.step_hard) * FH.T_level)

        self.goods_rt = self.margin / FH.limit_value * FH.T_level
        self.T_std_up = self.T_guide_up + self.T_rt_up * self.goods_rt
        self.T_std_dn = self.T_guide_dn + self.T_rt_dn * self.goods_rt
        self.D_up = FH.limit_size * self.T_std_up
        self.D_dn = FH.limit_size * self.T_std_dn

        self.bot = -FH.D_01 + self.tap
        if cutoff(self.tap,-FH.D_01 + self.tap,self.D,self.D_up,der='inc',bot=self.bot) >= self.tap:
            self.T_guide_dn += self.T_std_up - self.T_std_dn
            self.T_std_dn = self.T_std_up
        elif cutoff(self.tap,-FH.D_01 + self.tap,self.D,self.D_dn,der='red',bot=self.bot) >= (self.D - (FH.D_01 - self.tap)):
            self.T_guide_up += self.T_std_dn - self.T_std_up
            self.T_std_up = self.T_std_dn

        if self.D_up >= self.D:
            self.D_std = self.D_up
            self.put_tap = self.tap
        else:
            self.D_std = self.D_dn
            self.put_tap = (self.D - (FH.D_01 - self.tap)) if (self.D - (FH.D_01 - self.tap)) > 0.0 else self.tap

        #if self.D_up > FH.limit_size - min(FH.forward_position_size,FH.backward_position_size):
        #    self.adjust_guide(FH.limit_size - min(FH.forward_position_size,FH.backward_position_size))

        print (FH.current_side,self.T_guide_up,self.T_guide_dn,FH.balance_overflow,self.margin,self.goods_rt)
        print (self.T_std_up,self.T_std_dn,self.D,self.D_up,self.D_dn,FH.forward_stable_price,FH.backward_stable_price)

        self.forward_gap_balance = False
        self.forward_balance_size = 0
        self.backward_gap_balance = False
        self.backward_balance_size = 0
        if True:
            if len(FH.forward_orders) + len(FH.backward_orders) == 0:
                if FH.current_side == 'backward':
                        if FH.stable_spread and self.D > self.D_std:
                            self.backward_gap_balance = True
                        if FH.stable_spread and self.D < self.D_std:
                            self.forward_gap_balance = True
                elif FH.current_side == 'forward':
                        if FH.stable_spread and self.D > self.D_std:
                            self.forward_gap_balance = True
                        if FH.stable_spread and self.D < self.D_std:
                            self.backward_gap_balance = True

        if self.forward_gap_balance:
            if FH.forward_position_size > 0.0:
                if FH.current_side == 'forward':
                    self.forward_balance_size = int(min(cutoff(self.put_tap,-FH.D_01 + self.tap,self.D,self.D_std,der='red',bot=self.bot), FH.forward_position_size))
                    print('d1', self.D-self.D_std, FH.forward_position_size)
                else:
                    if FH.forward_goods < 0:
                        self.forward_balance_size = int(min(cutoff(self.put_tap,-FH.D_01 + self.tap,self.D,self.D_std,der='inc',bot=self.bot), -FH.forward_position_size*min(1.0,max(0.0,FH.balance_overflow)/FH.forward_goods)))
                        print ('d2',self.D_std-self.D,-FH.forward_position_size*FH.balance_overflow/FH.forward_goods)
                    else:
                        self.forward_balance_size = int(min(cutoff(self.put_tap,-FH.D_01 + self.tap,self.D,self.D_std,der='inc',bot=self.bot), FH.forward_position_size))
                        print('d2',self.D_std-self.D, FH.forward_position_size)
        if self.backward_gap_balance:
            if FH.backward_position_size > 0.0:
                if FH.current_side == 'backward':
                    self.backward_balance_size = int(min(cutoff(self.put_tap,-FH.D_01 + self.tap,self.D,self.D_std,der='red',bot=self.bot), FH.backward_position_size))
                    print ('d3', self.D-self.D_std, FH.backward_position_size)
                else:
                    if FH.backward_goods < 0:
                        self.backward_balance_size = int(min(cutoff(self.put_tap,-FH.D_01 + self.tap,self.D,self.D_std,der='inc',bot=self.bot), -FH.backward_position_size*min(1.0,max(0.0,FH.balance_overflow)/FH.backward_goods)))
                        print ('d4', self.D_std-self.D, -FH.backward_position_size*FH.balance_overflow/FH.backward_goods)
                    else:
                        self.backward_balance_size = int(min(cutoff(self.put_tap,-FH.D_01 + self.tap,self.D,self.D_std,der='inc',bot=self.bot), FH.backward_position_size))
                        print ('d4',self.D_std-self.D, FH.backward_position_size)

        self.forward_catch = False
        self.forward_catch_size = 0
        self.backward_catch = False
        self.backward_catch_size = 0
        if True:
            if len(FH.forward_orders) + len(FH.backward_orders) == 0:
                if FH.current_side == 'backward':
                        if FH.stable_spread and self.D < self.D_std:
                                self.backward_catch = True
                                self.backward_catch_size = int(min(cutoff(self.put_tap,-FH.D_01 + self.tap,self.D,self.D_std,der='inc',bot=self.bot), FH.backward_limit-FH.backward_position_size))
                                print ('b1',self.D_std-self.D, FH.backward_limit-FH.backward_position_size)
                        if FH.stable_spread and self.D > self.D_std:
                            self.forward_catch = True
                            self.forward_catch_size = int(min(cutoff(self.put_tap,-FH.D_01 + self.tap,self.D,self.D_std,der='red',bot=self.bot), FH.forward_limit-FH.forward_position_size))
                            print ('b2',self.D-self.D_std, FH.forward_limit-FH.forward_position_size)
                elif FH.current_side == 'forward':
                        if FH.stable_spread and self.D < self.D_std:
                                self.forward_catch = True
                                self.forward_catch_size = int(min(cutoff(self.put_tap,-FH.D_01 + self.tap,self.D,self.D_std,der='inc',bot=self.bot), FH.forward_limit-FH.forward_position_size))
                                print ('b3',self.D_std-self.D, FH.forward_limit-FH.forward_position_size)
                        if FH.stable_spread and self.D > self.D_std:
                            self.backward_catch = True
                            self.backward_catch_size = int(min(cutoff(self.put_tap,-FH.D_01 + self.tap,self.D,self.D_std,der='red',bot=self.bot), FH.backward_limit-FH.backward_position_size))
                            print ('b4',self.D-self.D_std, FH.backward_limit-FH.backward_position_size)

        if FH.current_side == 'forward' and self.backward_catch_size > 0.0:
            self.backward_catch = False
        elif FH.current_side == 'backward' and self.forward_catch_size > 0.0:
            self.forward_catch = False
        if FH.current_side == 'forward' and self.backward_balance_size > 0.0:
            self.backward_gap_balance = False
        elif FH.current_side == 'backward' and self.forward_balance_size > 0.0:
            self.forward_gap_balance = False

    def put_position(self):
        if FH.forward_leverage != FH.forward_gap_level:
            forward_api_instance.update_position_leverage(contract=FH.contract, settle=FH.settle,leverage=FH.forward_gap_level, _request_timeout=10)
            FH.forward_leverage = FH.forward_gap_level
        if FH.backward_leverage != FH.backward_gap_level:
            backward_api_instance.update_position_leverage(contract=FH.contract, settle=FH.settle,leverage=FH.backward_gap_level, _request_timeout=10)
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
                        forward_api_instance.cancel_futures_order(settle=FH.settle, order_id=order_id, _request_timeout=10)
                else:
                    forward_api_instance.cancel_futures_order(settle=FH.settle, order_id=order_id, _request_timeout=10)
            elif order_size < 0:
                if self.forward_gap_balance:
                    if order_price > FH.ask_1:
                        forward_api_instance.cancel_futures_order(settle=FH.settle, order_id=order_id,_request_timeout=10)
                else:
                    forward_api_instance.cancel_futures_order(settle=FH.settle, order_id=order_id, _request_timeout=10)
        if not self.forward_increase_clear:
            if FH.forward_position_size < FH.forward_limit:
                if self.forward_catch and self.forward_catch_size > 0:
                    forward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size=self.forward_catch_size,price=FH.bid_1, tif='poc'),_request_timeout=10)
        if not self.forward_reduce_clear and self.forward_gap_balance:
            if FH.forward_position_size > 0:
                if self.forward_balance_size > 0:
                    forward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size=-self.forward_balance_size,price=FH.ask_1, tif='poc'),_request_timeout=10)

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
                        backward_api_instance.cancel_futures_order(settle=FH.settle, order_id=order_id, _request_timeout=10)
                else:
                    backward_api_instance.cancel_futures_order(settle=FH.settle, order_id=order_id, _request_timeout=10)
            elif order_size > 0:
                if self.backward_gap_balance:
                    if order_price < FH.bid_1:
                        backward_api_instance.cancel_futures_order(settle=FH.settle, order_id=order_id,_request_timeout=10)
                else:
                    backward_api_instance.cancel_futures_order(settle=FH.settle, order_id=order_id, _request_timeout=10)
        if not self.backward_increase_clear:
            if FH.backward_position_size < FH.backward_limit:
                if self.backward_catch and self.backward_catch_size > 0:
                    backward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size=-self.backward_catch_size,price=FH.ask_1, tif='poc'),_request_timeout=10)
        if not self.backward_reduce_clear and self.backward_gap_balance:
            if FH.backward_position_size > 0:
                if self.backward_balance_size > 0:
                    backward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size=self.backward_balance_size,price=FH.bid_1, tif='poc'),_request_timeout=10)

        #if FH.forward_liq_flag:
        #    forward_api_instance.cancel_price_triggered_order_list(contract=FH.contract, settle=FH.settle,_request_timeout=10)
        #    if FH.forward_liq_price > 0:
        #        forward_api_instance.create_price_triggered_order(settle=FH.settle,
        #                                                          futures_price_triggered_order=FuturesPriceTriggeredOrder(
        #                                                              initial=FuturesInitialOrder(contract=FH.contract,
        #                                                                                          size=0, price=str(0),
        #                                                                                          close=True, tif='ioc',
        #                                                                                          text='api'),
        #                                                              trigger=FuturesPriceTrigger(strategy_type=0,
        #                                                                                          price_type=1, rule=2,
        #                                                                                          price=str(round(FH.forward_liq_price * (1.0 + 0.1 * 1.0 / FH.forward_leverage),FH.quanto)),
        #                                                                                          expiration=2592000)),_request_timeout=10)
        #        FH.forward_trigger_liq = FH.forward_liq_price * (1.0 + 0.1 * 1.0 / FH.forward_leverage)
        #if FH.backward_liq_flag:
        #    backward_api_instance.cancel_price_triggered_order_list(contract=FH.contract, settle=FH.settle,_request_timeout=10)
        #    if FH.backward_liq_price > 0:
        #        backward_api_instance.create_price_triggered_order(settle=FH.settle,
        #                                                           futures_price_triggered_order=FuturesPriceTriggeredOrder(
        #                                                               initial=FuturesInitialOrder(contract=FH.contract,
        #                                                                                           size=0, price=str(0),
        #                                                                                           close=True,
        #                                                                                           tif='ioc',
        #                                                                                           text='api'),
        #                                                               trigger=FuturesPriceTrigger(strategy_type=0,
        #                                                                                           price_type=1, rule=1,
        #                                                                                           price=str(round(FH.backward_liq_price * (1.0 - 0.1 * 1.0 / FH.backward_leverage),FH.quanto)),
        #                                                                                           expiration=2592000)),_request_timeout=10)
        #        FH.backward_trigger_liq = FH.backward_liq_price * (1.0 - 0.1 * 1.0 / FH.backward_leverage)

    def adjust_guide(self,D_std):
        self.T_guide_up += D_std / FH.limit_size - (self.T_guide_up + self.T_rt_up * self.goods_rt)
        self.T_guide_dn += D_std / FH.limit_size - (self.T_guide_dn + self.T_rt_dn * self.goods_rt)
        self.T_std_up = D_std / FH.limit_size
        self.T_std_dn = D_std / FH.limit_size
        self.D_std = D_std

