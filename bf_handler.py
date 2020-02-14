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
        self.limit_gap = contract_params['limit_gap']
        self.limit_size_std = contract_params['limit_size_std']
        self.max_size = contract_params['max_size']
        self.size_rt = contract_params['size_rt']
        self.follow_gap_rt = contract_params['follow_gap_rt']
        self.mark_total_flag = False
        self.balance_overflow = 0
        self.forward_account_from = 0
        self.backward_account_from = 0
        self.forward_trigger_liq = -1
        self.backward_trigger_liq = -1
        self.quanto = contract_params['quanto']
        self.chase = contract_params['chase']
        self.chase_level = contract_params['chase_level']
        self.catch = contract_params['catch']
        self.catch_neg_rt = contract_params['catch_neg_rt']
        self.catch_pos_rt = contract_params['catch_pos_rt']
        self.T_rt = contract_params['T_rt']
        self.forward_chase = False
        self.backward_chase = False
        self.forward_catch = False
        self.backward_catch = False
        self.forward_gap_balance = True
        self.backward_gap_balance = True
        self.retreat = contract_params['retreat']
        self.balance_rt = contract_params['balance_rt']
        self.goods = 0.0
        self.forward_goods = 0.0
        self.backward_goods = 0.0
        self.sleep_clear = False

    def get_flag(self):
        forward_accounts = forward_api_instance.list_futures_accounts(settle='usdt',async_req=True)
        forward_positions = forward_api_instance.get_position(contract=self.contract,settle='usdt',async_req=True)
        backward_accounts = backward_api_instance.list_futures_accounts(settle='usdt',async_req=True)
        backward_positions = backward_api_instance.get_position(contract=self.contract,settle='usdt',async_req=True)
        book = backward_api_instance.list_futures_order_book(contract=self.contract,settle='usdt',async_req=True)
        candles=backward_api_instance.list_futures_candlesticks(contract=self.contract,settle='usdt',limit=2,interval='1m',async_req=True)
        candlesticks = candles.get()
        self.forward_accounts = forward_accounts.get()
        self.forward_positions = forward_positions.get()
        self.backward_accounts = backward_accounts.get()
        self.backward_positions = backward_positions.get()
        self.book = book.get()
        self.forward_entry_price = float(self.forward_positions._entry_price)
        self.backward_entry_price = float(self.backward_positions._entry_price)
        self.forward_liq_price = float(self.forward_positions._liq_price)
        self.backward_liq_price = float(self.backward_positions._liq_price)
        self.forward_position_size = self.forward_positions._size
        self.backward_position_size = self.backward_positions._size
        self.forward_position_margin = float(self.forward_positions._margin)
        self.backward_position_margin = float(self.backward_positions._margin)
        self.forward_leverage = float(self.forward_positions._leverage)
        self.backward_leverage = float(self.backward_positions._leverage)
        self.mark_price = float(self.forward_positions._mark_price)
        self.ask_1 = float(self.book._asks[0]._p)
        self.bid_1 = float(self.book._bids[0]._p)

        entry_forward = self.forward_entry_price
        entry_backward = self.backward_entry_price
        if entry_forward == 0:
            entry_forward = self.bid_1
        if entry_backward == 0:
            entry_backward = self.ask_1
        entry_gap = (entry_forward - entry_backward)/((self.ask_1 + self.bid_1)/2)
        if entry_gap < 0.0:
            entry_gap = 0.0
    
        self.follow_gap = self.follow_gap_rt * entry_gap

        if self.forward_position_margin >= self.limit_position:
            self.forward_position_alarm = True
        else:
            self.forward_position_alarm = False
        if self.backward_position_margin >= self.limit_position:
            self.backward_position_alarm = True
        else:
            self.backward_position_alarm = False

        if self.forward_position_size > 0 and self.forward_entry_price > 0:
            self.forward_gap = (self.ask_1 - self.forward_entry_price)/self.forward_entry_price
        else:
            self.forward_gap = 0.0
        if -self.forward_gap > self.limit_gap:
            self.forward_gap_alarm = True
        else:
            self.forward_gap_alarm = False
        if -self.forward_gap > self.follow_gap:
            self.forward_follow_alarm = True
        else:
            self.forward_follow_alarm = False
        if self.backward_position_size < 0 and self.backward_entry_price > 0:
            self.backward_gap = (self.backward_entry_price - self.bid_1)/self.backward_entry_price
        else:
            self.backward_gap = 0.0
        if -self.backward_gap > self.limit_gap:
            self.backward_gap_alarm = True
        else:
            self.backward_gap_alarm = False
        if -self.backward_gap > self.follow_gap:
            self.backward_follow_alarm = True
        else:
            self.backward_follow_alarm = False

        self.limit_size = self.limit_size_std
        if self.forward_follow_alarm and not self.backward_follow_alarm and -self.backward_position_size >= self.limit_size_std:
            if -self.backward_position_size >= self.forward_position_size:
                self.limit_size = int(-self.backward_position_size * self.size_rt)
            else:
                self.limit_size = self.forward_position_size
        elif self.backward_follow_alarm and not self.forward_follow_alarm and self.forward_position_size >= self.limit_size_std:
            if self.forward_position_size >= -self.backward_position_size:
                self.limit_size = int(self.forward_position_size * self.size_rt)
            else:
                self.limit_size = -self.backward_position_size
        if self.limit_size > self.max_size:
            self.limit_size = self.max_size

        if len(candlesticks) > 0:
            o = float(candlesticks[len(candlesticks)-1]._o)
            c = float(candlesticks[len(candlesticks)-1]._c)
            if abs(o - c)/self.bid_1 < 0.001 or o > c:
                self.forward_stable_price = True
            else:
                self.forward_stable_price = False
            if abs(o - c)/self.ask_1 < 0.001 or o < c:
                self.backward_stable_price = True
            else:
                self.backward_stable_price = False
        else:
            self.forward_stable_price = False
            self.backward_stable_price = False

        if self.forward_account_from == 0:
            self.forward_account_from = int(time.time())
        if self.backward_account_from == 0:
            self.backward_account_from = int(time.time())
        forward_account_book = forward_api_instance.list_futures_account_book(settle='usdt',_from=self.forward_account_from,type='pnl')
        backward_account_book = backward_api_instance.list_futures_account_book(settle='usdt',_from=self.backward_account_from,type='pnl')
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
        if self.retreat:
            if self.forward_gap >= 0.0 and self.backward_gap >= 0.0:
                self.goods = 0.0

        self.balance_overflow = 1.0 * self.goods

        if self.forward_entry_price == 0:
            self.forward_goods = 0.0
        else:
            self.forward_goods = float(self.forward_positions._value)*(self.ask_1-self.forward_entry_price)/self.forward_entry_price
        if self.backward_entry_price == 0:
            self.backward_goods = 0.0
        else:
            self.backward_goods = float(self.backward_positions._value)*(self.backward_entry_price-self.bid_1)/self.backward_entry_price
            
        if self.forward_gap < 0.0 and self.backward_gap >= 0.0:
            self._T = abs(float(self.backward_position_size) / float(self.forward_position_size))
        elif self.backward_gap < 0.0 and self.forward_gap >= 0.0:
            self._T = abs(float(self.forward_position_size) / float(self.backward_position_size))
        elif self.forward_gap < 0.0 and self.backward_gap < 0.0:
            if self.forward_position_size < abs(self.backward_position_size):
                self._T = float(self.forward_position_size) / abs(float(self.backward_position_size))
            else:
                self._T = abs(float(self.backward_position_size)) / float(self.forward_position_size)
        elif self.forward_gap >= 0.0 and self.backward_gap >= 0.0:
            if self.forward_position_size < abs(self.backward_position_size):
                self._T = float(self.forward_position_size) / abs(float(self.backward_position_size))
            else:
                self._T = abs(float(self.backward_position_size)) / float(self.forward_position_size)

        if self.forward_gap < 0.0 and self.backward_gap >= 0.0:
            self._S = -self.backward_goods/(self.forward_goods + self.balance_overflow)
        elif self.backward_gap < 0.0 and self.forward_gap >= 0.0:
            self._S = -self.forward_goods/(self.backward_goods + self.balance_overflow)
        elif self.forward_gap < 0.0 and self.backward_gap < 0.0:
            self._S = 0.0
        elif self.forward_gap >= 0.0 and self.backward_gap >= 0.0:
            self._S = 1.0

        if self.forward_gap < 0.0 and self.backward_gap >= 0.0:
            if self._T == 0.0:
                self.goods_rt = 1.0
            else:
                self.goods_rt = math.exp(-1.0 - entry_gap/self.forward_gap)/self._T
            self.T_std = min(1.0,math.exp(0.5 * (-1.0 - entry_gap/self.forward_gap)))
            self.T_ = min(1.0,math.exp(self.T_rt * (-1.0 - entry_gap/self.forward_gap)))
        elif self.backward_gap < 0.0 and self.forward_gap >= 0.0:
            if self._T == 0.0:
                self.goods_rt = 1.0
            else:
                self.goods_rt = math.exp(-1.0 - entry_gap/self.backward_gap)/self._T
            self.T_std = min(1.0,math.exp(0.5* (-1.0 - entry_gap/self.backward_gap)))
            self.T_ = min(1.0,math.exp(self.T_rt * (-1.0 - entry_gap/self.backward_gap)))
        elif self.forward_gap < 0.0 and self.backward_gap < 0.0:
            self.goods_rt = 1.0
            self.T_std = 1.0
            self.T_ = 1.0
        elif self.forward_gap >= 0.0 and self.backward_gap >= 0.0:
            self.goods_rt = 0.0
            self.T_std = 0.61
            self.T_ = 0.61

        self.forward_limit = self.limit_size
        self.backward_limit = self.limit_size
        self.forward_gap_balance = False
        self.backward_gap_balance = False
        if self.forward_follow_alarm and self.backward_follow_alarm:
            if self.forward_position_size > abs(self.backward_position_size):
                if -self.balance_overflow/self.forward_goods > 1.0 - self.T_std and self.forward_stable_price:
                    self.forward_gap_balance = True
            elif self.forward_position_size < abs(self.backward_position_size):
                if -self.balance_overflow/self.backward_goods > 1.0 - self.T_std and self.backward_stable_price:
                    self.backward_gap_balance = True
        elif self.forward_follow_alarm and not self.backward_follow_alarm:
            if -self.balance_overflow/self.forward_goods > 1.0 - self.T_std and self.forward_stable_price:
                self.forward_gap_balance = True
            if self._S > self.goods_rt and self.backward_stable_price:
                self.backward_gap_balance = True
            elif -(self.backward_goods+self.balance_overflow)/self.forward_goods > self.goods_rt and self.backward_stable_price:
                self.backward_gap_balance = True
        elif self.backward_follow_alarm and not self.forward_follow_alarm:
            if -self.balance_overflow/self.backward_goods > 1.0 - self.T_std and self.backward_stable_price:
                self.backward_gap_balance = True
            if self._S > self.goods_rt and self.forward_stable_price:
                self.forward_gap_balance = True
            elif -(self.forward_goods+self.balance_overflow)/self.backward_goods > self.goods_rt and self.forward_stable_price:
                self.forward_gap_balance = True
        else:
            if self.forward_gap >= 0.0:
                self.forward_gap_balance = True
            if self.backward_gap >= 0.0:
                self.backward_gap_balance = True

        delta = abs(self.forward_position_size) - abs(self.backward_position_size)
        if delta >= self.limit_delta:
            self.forward_delta_alarm = True
        else:
            self.forward_delta_alarm = False

        if delta <= -self.limit_delta:
            self.backward_delta_alarm = True
        else:
            self.backward_delta_alarm = False

        gap_levels = self.level.keys()
        gap_levels.sort()
        for gap_level in gap_levels:
            if -self.forward_gap < float(gap_level):
                self.forward_gap_level = self.level[gap_level]['leverage']
                if self.forward_gap_level != self.forward_leverage:
                    self.forward_leverage_alarm = True
                else:
                    self.forward_leverage_alarm = False
                break

        for gap_level in gap_levels:
            if -self.backward_gap < float(gap_level):
                self.backward_gap_level = self.level[gap_level]['leverage']
                if self.backward_gap_level != self.backward_leverage:
                    self.backward_leverage_alarm = True
                else:
                    self.backward_leverage_alarm = False
                break

        self.forward_chase_margin = 0.0
        self.backward_chase_margin = 0.0
        chase_levels = self.chase_level.keys()
        chase_levels.sort(reverse = True)
        for chase_level in chase_levels:
            if self.forward_gap < 0 and -self.forward_gap > float(chase_level):
                self.forward_chase_margin = self.chase_level[chase_level]['margin']
                break

        for chase_level in chase_levels:
            if self.backward_gap < 0 and -self.backward_gap > float(chase_level):
                self.backward_chase_margin = self.chase_level[chase_level]['margin']
                break

        if self.chase:
            if self.forward_chase_margin > 0.0 and self.forward_position_margin < self.forward_chase_margin:
                if self.backward_stable_price and not self.forward_delta_alarm:
                    self.forward_chase = True
                else:
                    self.forward_chase = False
            else:
                self.forward_chase = False
            if self.backward_chase_margin > 0.0 and self.backward_position_margin < self.backward_chase_margin:
                if self.forward_stable_price and not self.backward_delta_alarm:
                    self.backward_chase = True
                else:
                    self.backward_chase = False
            else:
                self.backward_chase = False
        else:
            self.forward_chase = False
            self.backward_chase = False

        self.forward_catch = False
        self.backward_catch = False
        print ('aaaa')
        print (self.balance_overflow)
        print (self.goods_rt)
        print (self._S)
#        print (self.catch_neg_rt * self.goods_rt)
#        print (self.catch_pos_rt * self.goods_rt)
        print (self._T)
        print (self.T_)
        print (self.T_std)
        if self.catch:
            if self.forward_gap < 0.0 and  self.backward_gap >= 0.0:
                if self._T > self.T_:
#                    if not self.backward_gap_balance and (self._S > self.catch_neg_rt * self.goods_rt or 1.0/self._T < self.T_std) and self.backward_stable_price:
                    if not self.backward_gap_balance and self.backward_stable_price:
                        self.forward_catch = True
                        self.forward_catch_size = int(min(max(self.tap*self.forward_leverage,(-self.backward_position_size/self.T_-self.forward_position_size)),self.forward_limit-self.forward_position_size))
                elif self._T < self.T_std:
#                    if not self.forward_gap_balance and (self._S < self.catch_pos_rt * self.goods_rt or self._T < self.T_std) and self.forward_stable_price:
                    if not self.forward_gap_balance and self.forward_stable_price:
                        self.backward_catch = True
                        self.backward_catch_size = int(max(min(-self.tap*self.backward_leverage,(-self.forward_position_size*self.T_-self.backward_position_size)),-self.backward_limit-self.backward_position_size))
            elif self.backward_gap < 0.0 and self.forward_gap >= 0.0:
                if self._T > self.T_:
#                    if not self.forward_gap_balance and (self._S > self.catch_neg_rt * self.goods_rt or 1.0/self._T < self.T_std) and self.forward_stable_price:
                    if not self.forward_gap_balance and self.forward_stable_price:
                        self.backward_catch = True
                        self.backward_catch_size = int(max(min(-self.tap*self.backward_leverage,(-self.forward_position_size/self.T_-self.backward_position_size)),-self.backward_limit-self.backward_position_size))
                elif self._T < self.T_std:
#                    if not self.backward_gap_balance and (self._S < self.catch_pos_rt * self.goods_rt or self._T < self.T_std) and self.backward_stable_price:
                    if not self.backward_gap_balance and self.backward_stable_price:
                        self.forward_catch = True
                        self.forward_catch_size = int(min(max(self.tap*self.forward_leverage,(-self.backward_position_size*self.T_-self.forward_position_size)),self.forward_limit-self.forward_position_size))
            elif self.forward_gap < 0.0 and self.backward_gap < 0.0:
                if self.forward_position_size > abs(self.backward_position_size) and not self.forward_gap_balance:
                    self.backward_catch = True
                    self.backward_catch_size = max((self.forward_position_size + self.backward_position_size)*self.backward_gap/entry_gap,-self.backward_limit-self.backward_position_size) 
                elif self.forward_position_size < abs(self.backward_position_size) and not self.backward_gap_balance:
                    self.forward_catch = True
                    self.forward_catch_size = min((self.forward_position_size + self.backward_position_size)*self.forward_gap/entry_gap,self.forward_limit-self.forward_position_size)

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

    def put_position(self):
        if self.forward_leverage_alarm:
            if self.forward_leverage != self.forward_gap_level:
                forward_api_instance.update_position_leverage(contract=self.contract,settle='usdt',leverage = self.forward_gap_level)
                self.forward_leverage = self.forward_gap_level
        if self.backward_leverage_alarm:
            if self.backward_leverage != self.backward_gap_level:
                backward_api_instance.update_position_leverage(contract=self.contract,settle='usdt',leverage = self.backward_gap_level)
                self.backward_leverage = self.backward_gap_level

        self.forward_orders = forward_api_instance.list_futures_orders(contract=self.contract,settle='usdt',status='open')
        forward_increase_clear = False
        forward_reduce_clear = False
        for order in self.forward_orders:
            order_price = float(order._price)
            order_size = order._size
            order_id = order._id
            if order_size > 0:
                forward_increase_clear = True
            elif order_size < 0:
                forward_reduce_clear = True
            if order_size > 0:
                if ((self.forward_position_alarm or self.forward_delta_alarm) and not self.forward_chase  and not self.forward_catch) or self.forward_position_size >= self.forward_limit:
                    forward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
                else:
                    if self.bid_1 > order_price:
                        forward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
                        if self.forward_catch and self.forward_catch_size > 0:
                            forward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = self.forward_catch_size, price = self.bid_1,tif='poc'))
                        else:
                            forward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = order_size, price = self.bid_1,tif='poc'))
            elif order_size < 0:
                if self.forward_gap_balance:
                    if self.ask_1 < self.forward_entry_price and self.forward_position_size > 0:
                        if order_price > self.ask_1:
                            forward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
                            if self.balance_overflow > 0.0:
                                _size = int(min(self.forward_position_size * (self.balance_overflow/abs(self.forward_goods)),self.forward_position_size+self.backward_position_size*self.T_std))
                                if _size >= 1:
                                    forward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size =-_size, price = self.ask_1,tif='poc'))
                    elif self.ask_1 >= self.forward_entry_price and order_price > self.ask_1 and self.forward_position_size > 0:
                        forward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
                        _size = max(int(-self.forward_position_size-self.backward_position_size*self.T_std),-self.forward_position_size)
                        if _size < 0:
                            forward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size=_size,price = self.ask_1,tif='poc'))
                    elif self.forward_position_size == 0 or order_price > self.ask_1:
                        forward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
                else:
                    forward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
        if not forward_increase_clear:
            if self.forward_position_size < self.forward_limit and ((not self.forward_position_alarm and not self.forward_delta_alarm) or self.forward_chase or self.forward_catch):
                if self.forward_catch and self.forward_catch_size > 0:
                    forward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = self.forward_catch_size, price = self.bid_1,tif='poc'))
                else:
                    forward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = self.tap * self.forward_leverage, price = self.bid_1,tif='poc'))
        if not forward_reduce_clear and self.forward_gap_balance:
            if self.ask_1 >= self.forward_entry_price and self.forward_position_size > 0:
                _size = max(int(-self.forward_position_size-self.backward_position_size*self.T_std),-self.forward_position_size)
                if _size < 0:
                    forward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size=_size,price = self.ask_1,tif='poc'))
            elif self.ask_1 < self.forward_entry_price and self.balance_overflow > 0.0 and self.forward_position_size > 0:
                _size = int(min(self.forward_position_size * (self.balance_overflow/abs(self.forward_goods)),self.forward_position_size+self.backward_position_size*self.T_std))
                if _size >= 1:
                    if self.sleep_clear:
                        forward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = -_size, price = self.ask_1,tif='poc'))
                        self.sleep_clear = False
                    else:
                        time.sleep(30)
                        self.sleep_clear = True

        self.backward_orders = backward_api_instance.list_futures_orders(contract=self.contract,settle='usdt',status='open')
        backward_increase_clear = False
        backward_reduce_clear = False
        for order in self.backward_orders:
            order_price = float(order._price)
            order_size = order._size
            order_id = order._id
            if order_size < 0:
                backward_increase_clear = True
            elif order_size > 0:
                backward_reduce_clear = True
            if order_size < 0:
                if ((self.backward_position_alarm or self.backward_delta_alarm) and not self.backward_chase and not self.backward_catch) or abs(self.backward_position_size) >= self.backward_limit:
                    backward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
                else:
                    if self.ask_1 < order_price:
                        backward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
                        if self.backward_catch and self.backward_catch_size < 0:
                            backward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = self.backward_catch_size, price = self.ask_1,tif='poc'))
                        else:
                            backward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = order_size, price = self.ask_1,tif='poc'))
            elif order_size > 0:
                if self.backward_gap_balance:
                    if self.bid_1 > self.backward_entry_price and self.backward_position_size < 0:
                        if order_price < self.bid_1:
                            backward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
                            if self.balance_overflow > 0.0:
                                _size = max(self.backward_position_size * (self.balance_overflow/abs(self.backward_goods)),self.backward_position_size+self.forward_position_size*self.T_std)
                                if _size <= -1:
                                    backward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = -_size, price = self.bid_1,tif='poc'))
                    elif self.bid_1 <= self.backward_entry_price and order_price < self.bid_1 and self.backward_position_size < 0:
                        backward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
                        _size = min(int(-self.backward_position_size-self.forward_position_size*self.T_std),-self.backward_position_size)
                        if _size > 0:
                            backward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size=_size,price = self.bid_1,tif='poc'))
                    elif self.backward_position_size == 0 or order_price < self.bid_1:
                        backward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
                else:
                    backward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
        if not backward_increase_clear:
            if abs(self.backward_position_size) < self.backward_limit and ((not self.backward_position_alarm and not self.backward_delta_alarm) or self.backward_chase or self.backward_catch):
                if self.backward_catch and self.backward_catch_size < 0:
                    backward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = self.backward_catch_size, price = self.ask_1,tif='poc'))
                else:
                    backward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = -self.tap * self.backward_leverage, price = self.ask_1,tif='poc'))
        if not backward_reduce_clear and self.backward_gap_balance:
            if self.bid_1 <= self.backward_entry_price and self.backward_position_size < 0:
                _size = min(int(-self.backward_position_size-self.forward_position_size* self.T_std),-self.backward_position_size)
                if _size > 0:
                    backward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size=_size,price = self.bid_1,tif='poc'))
            elif self.bid_1 > self.backward_entry_price and self.balance_overflow > 0.0 and self.backward_position_size < 0:
                _size = int(max(self.backward_position_size * (self.balance_overflow/abs(self.backward_goods)),self.backward_position_size+self.forward_position_size*self.T_std))
                if _size <= -1:
                    if self.sleep_clear:
                        backward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = -_size, price = self.bid_1,tif='poc'))
                        self.sleep_clear = False
                    else:
                        time.sleep(30)
                        self.sleep_clear = True

        if self.forward_liq_flag:
            forward_api_instance.cancel_price_triggered_order_list(contract=self.contract,settle='usdt')
            if self.forward_liq_price > 0:
                forward_api_instance.create_price_triggered_order(settle='usdt',futures_price_triggered_order=FuturesPriceTriggeredOrder(initial=FuturesInitialOrder(contract=self.contract,size=0,price=str(0),close=True,tif='ioc',text='api'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=2,price=str(round(self.forward_liq_price*(1.0+0.1*1.0/self.forward_leverage),self.quanto)),expiration=2015360)))
                self.forward_trigger_liq = self.forward_liq_price*(1.0+0.1*1.0/self.forward_leverage)
        if self.backward_liq_flag:
            backward_api_instance.cancel_price_triggered_order_list(contract=self.contract,settle='usdt')
            if self.backward_liq_price > 0:
                backward_api_instance.create_price_triggered_order(settle='usdt',futures_price_triggered_order=FuturesPriceTriggeredOrder(initial=FuturesInitialOrder(contract=self.contract,size=0,price=str(0),close=True,tif='ioc',text='api'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=1,price=str(round(self.backward_liq_price*(1.0-0.1*1.0/self.backward_leverage),self.quanto)),expiration=2015360)))
                self.backward_trigger_liq = self.backward_liq_price*(1.0-0.1*1.0/self.backward_leverage)

