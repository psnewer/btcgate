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

class Future_Handler(object):
    def __init__(self,contract = '',contract_params = {}):
	self.contract = contract
        self.settle = contract_params['settle']
        self.tap = contract_params['tap']
        self.level = contract_params['level']
        self.limit_position = contract_params['limit_position']
        self.limit_delta = contract_params['limit_delta']
        self.max_size = contract_params['max_size']
        self.limit_size = contract_params['limit_size']
        self.balance_overflow = 0
        self.forward_account_from = 0
        self.backward_account_from = 0
        self.forward_trigger_liq = -1
        self.backward_trigger_liq = -1
        self.quanto = contract_params['quanto']
        self.catch = contract_params['catch']
        self.T_limit = contract_params['T_limit']
        self.gra_T_std = contract_params['gra_T_std']
        self.forward_catch = False
        self.backward_catch = False
        self.forward_gap_balance = True
        self.backward_gap_balance = True
        self.retreat = contract_params['retreat']
        self.balance_rt = contract_params['balance_rt']
        self.goods = 0.0 
        self.forward_goods = 0.0
        self.backward_goods = 0.0
        self.goods_std = 0.0
        self.pre_overflow = 0.0
        self.pre_S = 0.0
        self.forward_push_clear = False
        self.backward_push_clear = False
        self.sleep_clear = False

    def get_flag(self):
        forward_orders = forward_api_instance.list_futures_orders(contract=self.contract,settle=self.settle,status='open',async_req=True)
        backward_orders = backward_api_instance.list_futures_orders(contract=self.contract,settle=self.settle,status='open',async_req=True)
        candles=backward_api_instance.list_futures_candlesticks(contract=self.contract,settle=self.settle,interval='1m',async_req=True)
        book = backward_api_instance.list_futures_order_book(contract=self.contract,settle=self.settle,async_req=True)
        forward_positions = forward_api_instance.get_position(contract=self.contract,settle=self.settle,async_req=True)
        backward_positions = backward_api_instance.get_position(contract=self.contract,settle=self.settle,async_req=True)
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

        if self.forward_entry_price == 0:
            self.forward_entry_price = self.bid_1
        if self.backward_entry_price == 0:
            self.backward_entry_price = self.ask_1
        self.entry_gap = self.forward_entry_price - self.backward_entry_price
    
        if self.forward_position_size >= self.limit_position:
            self.forward_position_alarm = True
        else:
            self.forward_position_alarm = False
        if abs(self.backward_position_size) >= self.limit_position:
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

        self.mom_f = 0.0
        self.mom_b = 0.0
        candlesticks.reverse()
#        candlesticks = candlesticks[1:]
        if len(candlesticks) > 0:
            self.mom_f = self.bid_1 - float(candlesticks[0]._c)
            self.mom_b = self.ask_1 - float(candlesticks[0]._c)

        self.forward_stable_price = True
        self.backward_stable_price = True
        if len(candlesticks) > 0:
            o = float(candlesticks[0]._o)
            c = float(candlesticks[0]._c)
            if (c - o)/c < -0.001:
                self.backward_push_clear = True
                self.forward_push_clear = False
                forward_goods_std = float(self.forward_positions._value)*(c*(1.0+0.001)-self.forward_entry_price)/self.forward_entry_price
                backward_goods_std = float(self.backward_positions._value)*(self.backward_entry_price-c*(1.0+0.001))/self.backward_entry_price
                self.goods_std = forward_goods_std + backward_goods_std + self.goods
                if self.mom_b/c < 0.001:
                    self.backward_stable_price = False
            elif (c - o)/c > 0.001:
                self.forward_push_clear = True
                self.backward_push_clear = False
                forward_goods_std = float(self.forward_positions._value)*(c*(1.0-0.001)-self.forward_entry_price)/self.forward_entry_price
                backward_goods_std = float(self.backward_positions._value)*(self.backward_entry_price-c*(1.0-0.001))/self.backward_entry_price
                self.goods_std = forward_goods_std + backward_goods_std + self.goods
                if self.mom_f/c > -0.001:
                    self.forward_stable_price = False

        self.f_max = 0.0
        self.f_min = 0.0
        self.b_max = 0.0
        self.b_min = 0.0
        if self.mom_f > 0.0:
            for cand in candlesticks:
                o = float(cand._o)
                c = float(cand._c)
                if c - o < 0.0:
                    break
                if c - o > self.f_max or self.f_max == 0.0:
                    self.f_max = c - o
                elif c - o < self.f_min or self.f_min == 0.0:
                    self.f_min = c - o
        if self.mom_b < 0.0:
            for cand in candlesticks:
                o = float(cand._o)
                c = float(cand._c)
                if c - o > 0.0:
                    break
                if c - o < self.b_max or self.b_max == 0.0:
                    self.b_max = c - o
                elif c - o > self.b_min or self.b_min == 0.0:
                    self.b_min = c - o
        
        if self.forward_account_from == 0:
            self.forward_account_from = int(time.time())
        if self.backward_account_from == 0:
            self.backward_account_from = int(time.time())
        forward_account_book = forward_api_instance.list_futures_account_book(settle=self.settle,_from=self.forward_account_from,type='pnl')
        backward_account_book = backward_api_instance.list_futures_account_book(settle=self.settle,_from=self.backward_account_from,type='pnl')
        for item in forward_account_book:
            if self.contract in item.text:
                if float(item.change) > 0.0:
                    self.goods += float(item.change) * self.balance_rt
                else:
                    self.goods += float(item.change)
        for item in backward_account_book:
            if self.contract in item.text:
                if float(item.change) > 0.0:
                    self.goods += float(item.change) * self.balance_rt
                else:
                    self.goods += float(item.change)
        if len(forward_account_book) > 0:
            self.forward_account_from = int(forward_account_book[0]._time) + 1
        if len(backward_account_book) > 0:
            self.backward_account_from = int(backward_account_book[0]._time) + 1

        if self.forward_entry_price == 0:
            self.forward_goods = 0.0
        else:
            self.forward_goods = float(self.forward_positions._value)*(self.ask_1-self.forward_entry_price)/self.forward_entry_price
        if self.backward_entry_price == 0:
            self.backward_goods = 0.0
        else:
            self.backward_goods = float(self.backward_positions._value)*(self.backward_entry_price-self.bid_1)/self.backward_entry_price

        self.goods_total = self.forward_goods + self.backward_goods + self.goods

        if self.goods_total < self.goods_std:
            self.forward_push_clear = False
            self.backward_push_clear = False
            
#        self.forward_limit = min(abs(self.backward_position_size) * 1.42,self.limit_size)
#        self.backward_limit = min(self.forward_position_size * 1.42,self.limit_size)

        self.forward_limit = self.forward_position_size
        self.backward_limit = abs(self.backward_position_size)

        if self.forward_gap >= 0.0 and self.backward_gap < 0.0:
            self.forward_limit = abs(self.backward_position_size)
        elif self.forward_gap < 0.0 and self.backward_gap >= 0.0:
            self.backward_limit = self.forward_position_size

        self.forward_gap_balance = False
        self.backward_gap_balance = False
        if self.goods_total >= self.goods_std:
            if self.forward_push_clear and self.forward_stable_price and self.mom_f > 0.0 and self.f_max > 0.0:
                if self.forward_goods >= 0.0:
                    self.forward_gap_balance = True
                    self.forward_balance_size = int((-self.forward_position_size-self.backward_position_size*0.7)*min(self.mom_f/self.f_max,1.0))
                elif self.forward_goods < 0.0:
                    self.forward_gap_balance = True
                    self.forward_balance_size = int(max((-self.forward_position_size-self.backward_position_size*0.7)*min(self.mom_f/self.f_max,1.0),self.forward_position_size*self.goods/self.forward_goods))
                print ('aaaa',self.forward_balance_size)
            elif self.backward_push_clear and self.backward_stable_price and self.mom_b < 0.0 and self.b_max < 0.0:
                if self.backward_goods >= 0.0:
                    self.backward_gap_balance = True
                    self.backward_balance_size = int((-self.backward_position_size-self.forward_position_size*0.7)*min(self.mom_b/self.b_max,1.0))
                elif self.backward_goods < 0.0:
                    self.backward_gap_balance = True
                    self.backward_balance_size = int(min((-self.backward_position_size-self.forward_position_size*0.7)*min(self.mom_b/self.b_max,1.0),self.backward_position_size*self.goods/self.backward_goods))
                print ('bbbb',self.backward_balance_size)

        self.forward_catch = False
        self.backward_catch = False
        if self.mom_b < 0.0 and self.b_max < 0.0 and self.backward_stable_price and not self.forward_push_clear:
            self.forward_catch = True
            self.forward_catch_size = int(min((self.forward_limit - self.forward_position_size) * self.mom_b / self.b_max,self.forward_limit - self.forward_position_size))
            print ('1111',self.forward_catch_size)
        elif self.mom_f > 0.0 and self.f_max > 0.0 and self.forward_stable_price and not self.backward_push_clear:
            self.backward_catch = True
            self.backward_catch_size = int(max((-self.backward_limit - self.backward_position_size) * self.mom_f /self.f_max,-self.backward_limit - self.backward_position_size))
            print ('2222',self.backward_catch_size)

        delta = abs(self.forward_position_size) - abs(self.backward_position_size)
        if delta >= self.limit_delta:
            self.forward_delta_alarm = True
        else:
            self.forward_delta_alarm = False

        if delta <= -self.limit_delta:
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

        gap_levels = self.level.keys()
        gap_levels.sort()
        for gap_level in gap_levels:
            if max(-self.forward_liq_gap,-self.forward_gap) < float(gap_level):
                self.forward_gap_level = self.level[gap_level]['leverage']
                break

        for gap_level in gap_levels:
            if max(-self.backward_liq_gap,-self.backward_gap) < float(gap_level):
                self.backward_gap_level = self.level[gap_level]['leverage']
                break

        if self.forward_position_size == 0:
            self.forward_trigger_liq = 0
        if self.backward_position_size == 0:
            self.backward_trigger_liq = 0
        if self.forward_position_size > 0 and self.forward_liq_price < self.mark_price and (self.forward_trigger_liq < 0 or (self.forward_trigger_liq <= (1.0+1.0/self.forward_leverage*0.05)*self.forward_liq_price or self.forward_trigger_liq >= (1.0+1.0/self.forward_leverage*0.2)*self.forward_liq_price)):
            self.forward_liq_flag = True
        else:
            self.forward_liq_flag = False
        if self.backward_position_size < 0 and self.backward_liq_price > self.mark_price and (self.backward_trigger_liq < 0 or (self.backward_trigger_liq <= (1.0-1.0/self.backward_leverage*0.2)*self.backward_liq_price or self.backward_trigger_liq >= (1.0-1.0/self.backward_leverage*0.05)*self.backward_liq_price)):
            self.backward_liq_flag = True
        else:
            self.backward_liq_flag = False

        print (self.forward_push_clear,self.backward_push_clear)
        print (self.goods_total,self.goods_std,self.goods)
        print (self.mom_f,self.f_max,self.f_min)
        print (self.mom_b,self.b_max,self.b_min)
            
    def put_position(self):
        if self.forward_leverage != self.forward_gap_level:
            forward_api_instance.update_position_leverage(contract=self.contract,settle=self.settle,leverage = self.forward_gap_level)
            self.forward_leverage = self.forward_gap_level
        if self.backward_leverage != self.backward_gap_level:
            backward_api_instance.update_position_leverage(contract=self.contract,settle=self.settle,leverage = self.backward_gap_level)
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
                if ((self.forward_position_alarm or self.forward_delta_alarm) and not self.forward_catch) or self.forward_position_size >= self.limit_size:
                    forward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
                elif self.forward_catch and self.forward_catch_size <= 0:
                    forward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
                elif self.bid_1 > order_price:
                    forward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
            elif order_size < 0:
                if self.forward_gap_balance:
                    if order_price > self.ask_1 or self.forward_balance_size >= 0:
                        forward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
                else:
                    forward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
        if not self.forward_increase_clear:
            if self.forward_position_size < self.limit_size:
                if self.forward_catch and self.forward_catch_size > 0:
                    forward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size = self.forward_catch_size, price = self.bid_1,tif='poc'))
                elif (not self.forward_position_alarm and not self.forward_delta_alarm and self.backward_stable_price):
                    forward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size = self.tap * self.forward_leverage, price = self.bid_1,tif='poc'))
        if not self.forward_reduce_clear and self.forward_gap_balance:
            if self.forward_gap >= 0.0 and self.forward_position_size > 0:
                if self.forward_balance_size < 0:
                    forward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size=self.forward_balance_size,price = self.ask_1,tif='poc'))
            elif self.forward_gap < 0.0 and self.forward_position_size > 0:
                if self.forward_balance_size < 0:
#                    if self.sleep_clear:
                    forward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size = self.forward_balance_size, price = self.ask_1,tif='poc'))
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
                if ((self.backward_position_alarm or self.backward_delta_alarm) and not self.backward_catch) or abs(self.backward_position_size) >= self.limit_size:
                    backward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
                elif self.backward_catch and self.backward_catch_size >= 0:
                    backward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
                elif self.ask_1 < order_price:
                    backward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
            elif order_size > 0:
                if self.backward_gap_balance:
                    if order_price < self.bid_1 or self.backward_balance_size <= 0:
                        backward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
                else:
                    backward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
        if not self.backward_increase_clear:
            if abs(self.backward_position_size) < self.limit_size:
                if self.backward_catch and self.backward_catch_size < 0:
                    backward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size = self.backward_catch_size, price = self.ask_1,tif='poc'))
                elif (not self.backward_position_alarm and not self.backward_delta_alarm and self.forward_stable_price):
                    backward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size = -self.tap * self.backward_leverage, price = self.ask_1,tif='poc'))
        if not self.backward_reduce_clear and self.backward_gap_balance:
            if self.backward_gap >= 0.0 and self.backward_position_size < 0:
                if self.backward_balance_size > 0:
                    backward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size=self.backward_balance_size,price = self.bid_1,tif='poc'))
            elif self.backward_gap < 0.0 and self.backward_position_size < 0:
                if self.backward_balance_size > 0:
#                    if self.sleep_clear:
                    backward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size = self.backward_balance_size, price = self.bid_1,tif='poc'))
#                        self.sleep_clear = False
#                    else:
#                        time.sleep(30)
#                        self.sleep_clear = True

        if self.forward_liq_flag:
            forward_api_instance.cancel_price_triggered_order_list(contract=self.contract,settle=self.settle)
            if self.forward_liq_price > 0:
                forward_api_instance.create_price_triggered_order(settle=self.settle,futures_price_triggered_order=FuturesPriceTriggeredOrder(initial=FuturesInitialOrder(contract=self.contract,size=0,price=str(0),close=True,tif='ioc',text='api'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=2,price=str(round(self.forward_liq_price*(1.0+0.1*1.0/self.forward_leverage),self.quanto)),expiration=2015360)))
                self.forward_trigger_liq = self.forward_liq_price*(1.0+0.1*1.0/self.forward_leverage)
        if self.backward_liq_flag:
            backward_api_instance.cancel_price_triggered_order_list(contract=self.contract,settle=self.settle)
            if self.backward_liq_price > 0:
                backward_api_instance.create_price_triggered_order(settle=self.settle,futures_price_triggered_order=FuturesPriceTriggeredOrder(initial=FuturesInitialOrder(contract=self.contract,size=0,price=str(0),close=True,tif='ioc',text='api'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=1,price=str(round(self.backward_liq_price*(1.0-0.1*1.0/self.backward_leverage),self.quanto)),expiration=2015360)))
                self.backward_trigger_liq = self.backward_liq_price*(1.0-0.1*1.0/self.backward_leverage)

