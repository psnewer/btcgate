# -*- coding: utf-8 -*-

from __future__ import print_function
import requests
import time
import math
import gate_api
from gate_api import FuturesOrder
from gate_api import FuturesPriceTriggeredOrder
from gate_api import FuturesInitialOrder
from gate_api import FuturesPriceTrigger
from gate_api.rest import ApiException
from conf import *
from handler import *

class Handler_1T(Future_Handler):
    def __init__(self):
        self.tip = '1t'

    def get_flag(self):
        forward_orders = forward_api_instance.list_futures_orders(contract=Future_Handler.contract,settle=Future_Handler.settle,status='open',async_req=True)
        backward_orders = backward_api_instance.list_futures_orders(contract=Future_Handler.contract,settle=Future_Handler.settle,status='open',async_req=True)
        candles=backward_api_instance.list_futures_candlesticks(contract=Future_Handler.contract,settle=Future_Handler.settle,interval='1m',async_req=True)
        book = backward_api_instance.list_futures_order_book(contract=Future_Handler.contract,settle=Future_Handler.settle,async_req=True)
        forward_positions = forward_api_instance.get_position(contract=Future_Handler.contract,settle=Future_Handler.settle,async_req=True)
        backward_positions = backward_api_instance.get_position(contract=Future_Handler.contract,settle=Future_Handler.settle,async_req=True)
        self.forward_orders = forward_orders.get()
        self.backward_orders = backward_orders.get()
        candlesticks = candles.get()
        self.book = book.get()
        self.forward_positions = forward_positions.get()
        self.backward_positions = backward_positions.get()
        self.forward_entry_price = float(self.forward_positions._entry_price)
        self.backward_entry_price = float(self.backward_positions._entry_price)
        self.forward_liq_price = float(self.forward_positions._liq_price)
        self.backward_liq_price = float(self.backward_positions._liq_price)
        self.forward_position_size = self.forward_positions._size
        self.backward_position_size = self.backward_positions._size
        self.forward_leverage = float(self.forward_positions._leverage)
        self.backward_leverage = float(self.backward_positions._leverage)
        self.mark_price = float(self.forward_positions._mark_price)
        self.ask_1 = float(self.book._asks[0]._p)
        self.bid_1 = float(self.book._bids[0]._p)
 
        self.forward_limit = Future_Handler.limit_size
        self.backward_limit = Future_Handler.limit_size

        if self.forward_entry_price == 0:
            self.forward_entry_price = self.bid_1
        if self.backward_entry_price == 0:
            self.backward_entry_price = self.ask_1
        self.entry_gap = self.forward_entry_price - self.backward_entry_price
    
        if self.forward_position_size >= Future_Handler.limit_position:
            self.forward_position_alarm = True
        else:
            self.forward_position_alarm = False
        if abs(self.backward_position_size) >= Future_Handler.limit_position:
            self.backward_position_alarm = True
        else:
            self.backward_position_alarm = False

        if self.forward_position_size > 0 and self.forward_entry_price > 0:
            self.t_f = self.ask_1 - self.forward_entry_price
            self.forward_gap = self.t_f/self.forward_entry_price
        else:
            self.t_f = 0.0
            self.forward_gap = 0.0
        if self.backward_position_size < 0 and self.backward_entry_price > 0:
            self.t_b = self.backward_entry_price - self.bid_1
            self.backward_gap = self.t_b/self.backward_entry_price
        else:
            self.t_b = 0.0
            self.backward_gap = 0.0

        self.forward_stable_price = True
        self.backward_stable_price = True
        if len(candlesticks) > 0:
            o = float(candlesticks[len(candlesticks)-1]._o)
            c = float(candlesticks[len(candlesticks)-1]._c)
            if (c - o)/self.bid_1 > 0.001:
                if (self.bid_1 - c)/self.bid_1 > -0.001:
                    self.forward_stable_price = False
            elif (c - o)/self.ask_1 < -0.001:
                if (self.ask_1 - c)/self.ask_1 < 0.001:
                    self.backward_stable_price = False
#        if len(candlesticks) > 0:
#            o = float(candlesticks[len(candlesticks)-1]._o)
#            c = float(candlesticks[len(candlesticks)-1]._c)
#            if abs(o - c)/self.bid_1 < 0.001 or o > c:
#                self.forward_stable_price = True
#            else:
#                self.forward_stable_price = False
#            if abs(o - c)/self.ask_1 < 0.001 or o < c:
#                self.backward_stable_price = True
#            else:
#                self.backward_stable_price = False
#        else:
#            self.forward_stable_price = False
#            self.backward_stable_price = False

        if Future_Handler.forward_account_from == 0:
            Future_Handler.forward_account_from = int(time.time())
        if Future_Handler.backward_account_from == 0:
            Future_Handler.backward_account_from = int(time.time())
        forward_account_book = forward_api_instance.list_futures_account_book(settle=Future_Handler.settle,_from=Future_Handler.forward_account_from,type='pnl')
        backward_account_book = backward_api_instance.list_futures_account_book(settle=Future_Handler.settle,_from=Future_Handler.backward_account_from,type='pnl')
        for item in forward_account_book:
            if Future_Handler.contract in item.text:
                if float(item.change) > 0.0:
                    Future_Handler.goods += float(item.change) * Future_Handler.balance_rt
                else:
                    Future_Handler.goods += float(item.change)
        for item in backward_account_book:
            if Future_Handler.contract in item.text:
                if float(item.change) > 0.0:
                    Future_Handler.goods += float(item.change) * Future_Handler.balance_rt
                else:
                    Future_Handler.goods += float(item.change)
        if len(forward_account_book) > 0:
            Future_Handler.forward_account_from = int(forward_account_book[0]._time) + 1
        if len(backward_account_book) > 0:
            Future_Handler.backward_account_from = int(backward_account_book[0]._time) + 1

        Future_Handler.balance_overflow = 1.0 * Future_Handler.goods

        if self.forward_entry_price == 0:
            Future_Handler.forward_goods = 0.0
        else:
            Future_Handler.forward_goods = float(self.forward_positions._value)*(self.ask_1-self.forward_entry_price)/self.forward_entry_price
        if self.backward_entry_price == 0:
            Future_Handler.backward_goods = 0.0
        else:
            Future_Handler.backward_goods = float(self.backward_positions._value)*(self.backward_entry_price-self.bid_1)/self.backward_entry_price
            
        if self.forward_gap < 0.0 and self.backward_gap >= 0.0:
            Future_Handler._T = abs(float(self.backward_position_size) / float(self.forward_position_size))
        elif self.backward_gap < 0.0 and self.forward_gap >= 0.0:
            Future_Handler._T = abs(float(self.forward_position_size) / float(self.backward_position_size))
        elif self.forward_gap < 0.0 and self.backward_gap < 0.0:
            if self.forward_gap > self.backward_gap:
                Future_Handler._T = abs(float(self.forward_position_size) / float(self.backward_position_size))
            else:
                Future_Handler._T = abs(float(self.backward_position_size) / float(self.forward_position_size))
        elif self.forward_gap >= 0.0 and self.backward_gap >= 0.0:
            Future_Handler._T = 0.61

        if self.forward_gap < 0.0 and self.backward_gap >= 0.0:
            Future_Handler._S = -Future_Handler.balance_overflow/Future_Handler.forward_goods
            Future_Handler.S_ = -Future_Handler.backward_goods/Future_Handler.forward_goods
            Future_Handler.S_up = min(Future_Handler.S_up,Future_Handler.S_*1.1)
            Future_Handler.S_dn = max(Future_Handler.S_dn,Future_Handler.S_*0.9)
            Future_Handler.S_head = min(Future_Handler.S_head,Future_Handler.S_+0.1)
        elif self.backward_gap < 0.0 and self.forward_gap >= 0.0:
            Future_Handler._S = -Future_Handler.balance_overflow/Future_Handler.backward_goods
            Future_Handler.S_ = -Future_Handler.forward_goods/Future_Handler.backward_goods
            Future_Handler.S_up = min(Future_Handler.S_up,Future_Handler.S_*1.1)
            Future_Handler.S_dn = max(Future_Handler.S_dn,Future_Handler.S_*0.9)
            Future_Handler.S_head = min(Future_Handler.S_head,Future_Handler.S_+0.1)
        elif self.forward_gap < 0.0 and self.backward_gap < 0.0:
            Future_Handler._S = -Future_Handler.balance_overflow/(Future_Handler.forward_goods+Future_Handler.backward_goods)
            Future_Handler.S_ = 0.0
        elif self.forward_gap >= 0.0 and self.backward_gap >= 0.0:
            Future_Handler._S = 1.0
            Future_Handler.S_ = 1.0

        if Future_Handler.retreat:
            if Future_Handler._S + Future_Handler.S_ > 1.0 and Future_Handler._S > 0.0:
                Future_Handler.balance_overflow = max(0.0,(1.0-Future_Handler.S_)/Future_Handler._S*Future_Handler.balance_overflow)

        if self.forward_gap < 0.0 and self.backward_gap >= 0.0:
            Future_Handler.t = -self.t_b/self.t_f
            Future_Handler.T_std = math.exp(0.5*(1.0-Future_Handler.t))
            Future_Handler.t_head = min(Future_Handler.t_head,Future_Handler.t+0.1)
        elif self.backward_gap < 0.0 and self.forward_gap >= 0.0:
            Future_Handler.t = -self.t_f/self.t_b
            Future_Handler.T_std = math.exp(0.5*(1.0-Future_Handler.t))
            Future_Handler.t_head = min(Future_Handler.t_head,Future_Handler.t+0.1)
        elif self.forward_gap < 0.0 and self.backward_gap < 0.0:
            Future_Handler.t = 0.0
            Future_Handler.T_std = 0.0
#            if self.forward_gap > self.backward_gap:
#                Future_Handler.t = self.t_f/self.t_b
#            else:
#                Future_Handler.t = self.t_b/self.t_f
#            Future_Handler.T_std = math.exp(0.5-0.5*Future_Handler.t)
#        elif self.forward_gap >= 0.0 and self.backward_gap >= 0.0:
#            Future_Handler.T_std = 0.61

        self.forward_gap_balance = False
        self.forward_balance_size = 0
        self.backward_gap_balance = False
        self.backward_balance_size = 0
        if self.forward_gap < 0.0 and self.backward_gap >= 0.0:
            if self.forward_stable_price and Future_Handler._T < Future_Handler.T_std:
                if Future_Handler.S_ <= Future_Handler.S_dn:
                    Future_Handler_S_dn = Future_Handler.S_
                    self.forward_gap_balance = True
            elif self.backward_stable_price and Future_Handler._T > Future_Handler.T_std:
                if Future_Handler.S_ >= Future_Handler.S_up:
                    Future_Handler.S_up = Future_Handler.S_
                    self.backward_gap_balance = True
        elif self.backward_gap < 0.0 and self.forward_gap >= 0.0:
            if self.backward_stable_price and Future_Handler._T < Future_Handler.T_std:
                if Future_Handler.S_ <= Future_Handler.S_dn:
                    Future_Handler.S_dn = Future_Handler.S_
                    self.backward_gap_balance = True
            elif self.forward_stable_price and Future_Handler._T > Future_Handler.T_std:
                if Future_Handler.S_ >= Future_Handler.S_up:
                    Future_Handler.S_up = Future_Handler.S_
                    self.forward_gap_balance = True
#        elif self.forward_gap >= 0.0 and self.backward_gap >= 0.0:
#            if self.forward_position_size > 0:
#                self.forward_gap_balance = True
#            if self.backward_position_size > 0:
#                self.backward_gap_balance = True

        if self.forward_gap_balance:
            if self.forward_gap >= 0.0:
                if self.backward_gap < 0.0:
                    self.forward_balance_size = int(max(-self.forward_position_size-self.backward_position_size*Future_Handler.T_std,-self.forward_position_size))
                    print ('d1',-self.forward_position_size-self.backward_position_size*Future_Handler.T_std,-self.forward_position_size)
                else:
                    self.forward_balance_size = int(-self.forward_position_size - self.backward_position_size*Future_Handler.T_std)
            else:
                if self.backward_gap >= 0.0:
                    self.forward_balance_size = int(max(-self.backward_position_size/Future_Handler.T_std-self.forward_position_size,self.forward_position_size*Future_Handler.balance_overflow/Future_Handler.forward_goods))
                    print ('d2',-self.backward_position_size/Future_Handler.T_std-self.forward_position_size,self.forward_position_size*Future_Handler.balance_overflow/Future_Handler.forward_goods)
        if self.backward_gap_balance:
            if self.backward_gap >= 0.0:
                if self.forward_gap < 0.0:
                    self.backward_balance_size = int(min(-self.backward_position_size-self.forward_position_size*Future_Handler.T_std,-self.backward_position_size))
                    print ('d3',-self.backward_position_size-self.forward_position_size*Future_Handler.T_std,-self.backward_position_size)
                else:
                    self.backward_balance_size = int(-self.backward_position_size - self.forward_position_size*Future_Handler.T_std)
            else:
                if self.forward_gap >= 0.0:
                    self.backward_balance_size = int(min(-self.forward_position_size/Future_Handler.T_std-self.backward_position_size,self.backward_position_size*Future_Handler.balance_overflow/Future_Handler.backward_goods))
                    print ('d4',-self.forward_position_size/Future_Handler.T_std-self.backward_position_size,self.backward_position_size*Future_Handler.balance_overflow/Future_Handler.backward_goods)
        
        delta = abs(self.forward_position_size) - abs(self.backward_position_size)
        if delta >= Future_Handler.limit_delta:
            self.forward_delta_alarm = True
        else:
            self.forward_delta_alarm = False

        if delta <= -Future_Handler.limit_delta:
            self.backward_delta_alarm = True
        else:
            self.backward_delta_alarm = False

        if self.forward_position_size > 0 and self.forward_entry_price > 0:
            self.forward_liq_gap = (self.mark_price - self.forward_entry_price)/self.forward_entry_price
        else:
            self.forward_liq_gap = 0.0
        if self.backward_position_size < 0 and self.backward_entry_price > 0:
            self.backward_liq_gap = (self.backward_entry_price - self.mark_price)/self.backward_entry_price
        else:
            self.backward_liq_gap = 0.0
        gap_levels = Future_Handler.level.keys()
        gap_levels.sort()
        for gap_level in gap_levels:
            if max(-self.forward_liq_gap,-self.forward_gap) < float(gap_level):
                self.forward_gap_level = Future_Handler.level[gap_level]['leverage']
                break

        for gap_level in gap_levels:
            if max(-self.backward_liq_gap,-self.backward_gap) < float(gap_level):
                self.backward_gap_level = Future_Handler.level[gap_level]['leverage']
                break

        self.forward_catch = False
        self.forward_catch_size = 0
        self.backward_catch = False
        self.backward_catch_size = 0
        print ('aaaa')
        print (Future_Handler.balance_overflow)
        print (Future_Handler._T,Future_Handler.T_std)
        if Future_Handler.catch:
            if self.forward_gap < 0.0 and self.backward_gap >= 0.0:
                if Future_Handler._T > Future_Handler.T_std:
                    if self.backward_stable_price and not (self.backward_gap_balance and self.backward_balance_size > 0):
                        self.forward_catch = True
#                        regression_size = regression_2(self.backward_entry_price,self.forward_entry_price,-self.backward_position_size,self.forward_position_size,self.bid_1,0.5)
                        self.forward_catch_size = int(min(-self.backward_position_size/Future_Handler.T_std-self.forward_position_size,self.forward_limit-self.forward_position_size))
                        print ('1111',-self.backward_position_size/Future_Handler.T_std-self.forward_position_size,self.forward_limit-self.forward_position_size)
                elif Future_Handler._T < Future_Handler.T_std:
                    if self.forward_stable_price and not (self.forward_gap_balance and self.forward_balance_size < 0):
                        self.backward_catch = True
#                        regression_size = regression_1(self.backward_entry_price,self.forward_entry_price,-self.backward_position_size,self.forward_position_size,self.ask_1,0.5)
                        self.backward_catch_size = int(max(-self.forward_position_size*Future_Handler.T_std-self.backward_position_size,-self.backward_limit-self.backward_position_size))
                        print ('bbbb',-self.forward_position_size*Future_Handler.T_std-self.backward_position_size,-self.backward_limit-self.backward_position_size)
            elif self.backward_gap < 0.0 and self.forward_gap >= 0.0:
                if Future_Handler._T > Future_Handler.T_std:
                    if self.forward_stable_price and not (self.forward_gap_balance and self.forward_balance_size < 0):
                        self.backward_catch = True
#                        regression_size = regression_2(self.forward_entry_price,self.backward_entry_price,self.forward_position_size,-self.backward_position_size,self.ask_1,0.5)
                        self.backward_catch_size = int(max(-self.forward_position_size/Future_Handler.T_std-self.backward_position_size,-self.backward_limit-self.backward_position_size))
                        print ('2222',-self.forward_position_size/Future_Handler.T_std-self.backward_position_size,-self.backward_limit-self.backward_position_size)
                elif Future_Handler._T < Future_Handler.T_std:
                    if self.backward_stable_price and not (self.backward_gap_balance and self.backward_balance_size > 0):
                        self.forward_catch = True
#                        regression_size = regression_1(self.forward_entry_price,self.backward_entry_price,self.forward_position_size,-self.backward_position_size,self.bid_1,0.5)
                        self.forward_catch_size = int(min(-self.backward_position_size*Future_Handler.T_std-self.forward_position_size,self.forward_limit-self.forward_position_size))
                        print ('cccc',-self.backward_position_size*Future_Handler.T_std-self.forward_position_size,self.forward_limit-self.forward_position_size)

        if self.forward_position_size == 0:
            Future_Handler.forward_trigger_liq = 0
        if self.backward_position_size == 0:
            Future_Handler.backward_trigger_liq = 0
        if self.forward_position_size > 0 and self.forward_liq_price < self.mark_price and (Future_Handler.forward_trigger_liq < 0 or (Future_Handler.forward_trigger_liq <= (1.0+1.0/self.forward_leverage*0.05)*self.forward_liq_price or Future_Handler.forward_trigger_liq >= (1.0+1.0/self.forward_leverage*0.2)*self.forward_liq_price)):
            self.forward_liq_flag = True
        else:
            self.forward_liq_flag = False
        if self.backward_position_size < 0 and self.backward_liq_price > self.mark_price and (Future_Handler.backward_trigger_liq < 0 or (Future_Handler.backward_trigger_liq <= (1.0-1.0/self.backward_leverage*0.2)*self.backward_liq_price or Future_Handler.backward_trigger_liq >= (1.0-1.0/self.backward_leverage*0.05)*self.backward_liq_price)):
            self.backward_liq_flag = True
        else:
            self.backward_liq_flag = False
            
    def put_position(self):
        if self.forward_leverage != self.forward_gap_level:
            forward_api_instance.update_position_leverage(contract=Future_Handler.contract,settle=Future_Handler.settle,leverage = self.forward_gap_level)
            self.forward_leverage = self.forward_gap_level
        if self.backward_leverage != self.backward_gap_level:
            backward_api_instance.update_position_leverage(contract=Future_Handler.contract,settle=Future_Handler.settle,leverage = self.backward_gap_level)
            self.backward_leverage = self.backward_gap_level

        self.forward_increase_clear = False
        self.forward_reduce_clear = False
        for order in self.forward_orders:
            order_price = float(order._price)
            order_size = order._size
            order_id = order._id
            if order_size > 0:
                self.forward_increase_clear = True
            elif order_size < 0:
                self.forward_reduce_clear = True
            if order_size > 0:
                if ((self.forward_position_alarm or self.forward_delta_alarm) and not self.forward_catch) or self.forward_position_size >= self.forward_limit:
                    forward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
                elif self.forward_catch and self.forward_catch_size <= 0:
                    forward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
                elif self.bid_1 > order_price:
                    forward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
            elif order_size < 0:
                if self.forward_gap_balance:
                    if order_price > self.ask_1 or self.forward_balance_size >= 0:
                        forward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
                else:
                    forward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
        if not self.forward_increase_clear:
            if self.forward_position_size < self.forward_limit:
                if self.forward_catch and self.forward_catch_size > 0:
                    forward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size = self.forward_catch_size, price = self.bid_1,tif='poc'))
                elif (not self.forward_position_alarm and not self.forward_delta_alarm and self.backward_stable_price):
                    forward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size = Future_Handler.tap * self.forward_leverage, price = self.bid_1,tif='poc'))
        if not self.forward_reduce_clear and self.forward_gap_balance:
            if self.forward_gap >= 0.0 and self.forward_position_size > 0:
                if self.forward_balance_size < 0:
                    forward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size=self.forward_balance_size,price = self.ask_1,tif='poc'))
            elif self.forward_gap < 0.0 and self.forward_position_size > 0:
                if self.forward_balance_size < 0:
#                    if self.sleep_clear:
                    forward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size = self.forward_balance_size, price = self.ask_1,tif='poc'))
#                        self.sleep_clear = False
#                    else:
#                        time.sleep(30)
#                        self.sleep_clear = True

        self.backward_increase_clear = False
        self.backward_reduce_clear = False
        for order in self.backward_orders:
            order_price = float(order._price)
            order_size = order._size
            order_id = order._id
            if order_size < 0:
                self.backward_increase_clear = True
            elif order_size > 0:
                self.backward_reduce_clear = True
            if order_size < 0:
                if ((self.backward_position_alarm or self.backward_delta_alarm) and not self.backward_catch) or abs(self.backward_position_size) >= self.backward_limit:
                    backward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
                elif self.backward_catch and self.backward_catch_size >= 0:
                    backward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
                elif self.ask_1 < order_price:
                    backward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
            elif order_size > 0:
                if self.backward_gap_balance:
                    if order_price < self.bid_1 or self.backward_balance_size <= 0:
                        backward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
                else:
                    backward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
        if not self.backward_increase_clear:
            if abs(self.backward_position_size) < self.backward_limit:
                if self.backward_catch and self.backward_catch_size < 0:
                    backward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size = self.backward_catch_size, price = self.ask_1,tif='poc'))
                elif (not self.backward_position_alarm and not self.backward_delta_alarm and self.forward_stable_price):
                    backward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size = -Future_Handler.tap * self.backward_leverage, price = self.ask_1,tif='poc'))
        if not self.backward_reduce_clear and self.backward_gap_balance:
            if self.backward_gap >= 0.0 and self.backward_position_size < 0:
                if self.backward_balance_size > 0:
                    backward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size=self.backward_balance_size,price = self.bid_1,tif='poc'))
            elif self.backward_gap < 0.0 and self.backward_position_size < 0:
                if self.backward_balance_size > 0:
#                    if self.sleep_clear:
                    backward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size = self.backward_balance_size, price = self.bid_1,tif='poc'))
#                        self.sleep_clear = False
#                    else:
#                        time.sleep(30)
#                        self.sleep_clear = True

        if self.forward_liq_flag:
            forward_api_instance.cancel_price_triggered_order_list(contract=Future_Handler.contract,settle=Future_Handler.settle)
            if self.forward_liq_price > 0:
                forward_api_instance.create_price_triggered_order(settle=Future_Handler.settle,futures_price_triggered_order=FuturesPriceTriggeredOrder(initial=FuturesInitialOrder(contract=Future_Handler.contract,size=0,price=str(0),close=True,tif='ioc',text='api'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=2,price=str(round(self.forward_liq_price*(1.0+0.1*1.0/self.forward_leverage),Future_Handler.quanto)),expiration=2015360)))
                Future_Handler.forward_trigger_liq = self.forward_liq_price*(1.0+0.1*1.0/self.forward_leverage)
        if self.backward_liq_flag:
            backward_api_instance.cancel_price_triggered_order_list(contract=Future_Handler.contract,settle=Future_Handler.settle)
            if self.backward_liq_price > 0:
                backward_api_instance.create_price_triggered_order(settle=Future_Handler.settle,futures_price_triggered_order=FuturesPriceTriggeredOrder(initial=FuturesInitialOrder(contract=Future_Handler.contract,size=0,price=str(0),close=True,tif='ioc',text='api'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=1,price=str(round(self.backward_liq_price*(1.0-0.1*1.0/self.backward_leverage),Future_Handler.quanto)),expiration=2015360)))
                Future_Handler.backward_trigger_liq = self.backward_liq_price*(1.0-0.1*1.0/self.backward_leverage)
