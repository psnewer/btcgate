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
        self.limit_size = contract_params['limit_size']
        self.max_size = contract_params['max_size']
        self.balance_overflow = 0
        self.forward_account_from = 0
        self.backward_account_from = 0
        self.forward_trigger_liq = -1
        self.backward_trigger_liq = -1
        self.quanto = contract_params['quanto']
        self.catch = contract_params['catch']
        self.T_limit = contract_params['T_limit']
        self.gra_T_std = contract_params['gra_T_std']
        self.gra_T_ = contract_params['gra_T_']
        self.gra_T_cmp = contract_params['gra_T_cmp']
        self.forward_catch = False
        self.backward_catch = False
        self.forward_gap_balance = True
        self.backward_gap_balance = True
        self.retreat = contract_params['retreat']
        self.balance_rt = contract_params['balance_rt']
        self.goods = 10.1428738734
        self.forward_goods = 0.0
        self.backward_goods = 0.0
        self.pre_overflow = 0.0
        self.pre_S = 0.0
        self.s_rt = contract_params['s_rt']
        self.size_rt = 1
        self.sleep_clear = False

    def get_flag(self):
        forward_positions = forward_api_instance.get_position(contract=self.contract,settle='usdt',async_req=True)
        forward_orders = forward_api_instance.list_futures_orders(contract=self.contract,settle='usdt',status='open',async_req=True)
        backward_positions = backward_api_instance.get_position(contract=self.contract,settle='usdt',async_req=True)
        backward_orders = backward_api_instance.list_futures_orders(contract=self.contract,settle='usdt',status='open',async_req=True)
        book = backward_api_instance.list_futures_order_book(contract=self.contract,settle='usdt',async_req=True)
        candles=backward_api_instance.list_futures_candlesticks(contract=self.contract,settle='usdt',interval='1m',async_req=True)
        candlesticks = candles.get()
        self.forward_positions = forward_positions.get()
        self.forward_orders = forward_orders.get()
        self.backward_positions = backward_positions.get()
        self.backward_orders = backward_orders.get()
        self.book = book.get()
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
            self.forward_gap = (self.ask_1 - self.forward_entry_price)/self.forward_entry_price
        else:
            self.forward_gap = 0.0
        if self.backward_position_size < 0 and self.backward_entry_price > 0:
            self.backward_gap = (self.backward_entry_price - self.bid_1)/self.backward_entry_price
        else:
            self.backward_gap = 0.0

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
            self._T = 1.0
        elif self.forward_gap >= 0.0 and self.backward_gap >= 0.0:
            self._T = 0.61

        if self.forward_gap < 0.0 and self.backward_gap >= 0.0:
            if self.pre_overflow != self.balance_overflow:
                self.pre_overflow = self.balance_overflow
                self.pre_S = -self.pre_overflow/self.forward_goods
            self._S = -self.balance_overflow/self.forward_goods
            self.S_ = -self.backward_goods/self.forward_goods
        elif self.backward_gap < 0.0 and self.forward_gap >= 0.0:
            if self.pre_overflow != self.balance_overflow:
                self.pre_overflow = self.balance_overflow
                self.pre_S = -self.pre_overflow/self.backward_goods
            self._S = -self.balance_overflow/self.backward_goods
            self.S_ = -self.forward_goods/self.backward_goods
        elif self.forward_gap < 0.0 and self.backward_gap < 0.0:
            self._S = 0.0
            self.S_ = 0.0
        elif self.forward_gap >= 0.0 and self.backward_gap >= 0.0:
            self._S = 1.0
            self.S_ = 1.0

        if self.retreat:
            if self._S + self.S_ > 1.0:
                self.balance_overflow = max(0.0,(1.0-self.S_)/self._S*self.balance_overflow)

        if self.forward_gap < 0.0 and self.backward_gap >= 0.0:
            if self._T == 0.0:
                self.t_f = 0.0
#                t_pre = 0.0
            else:
                self.t_f = self.backward_entry_price - self.bid_1
#                t_pre = 1.0 - 2.0/self.gra_T_std * math.log(self._T)
            self.t_b = self.forward_entry_price - self.bid_1
            self.t = self.t_f/self.t_b
#            if t_pre == 1.0:
#                self.t_foc = 1.0
#            else:
#                #self.t_foc = (t_pre*(self.t_b-self.t_f))/self.t_f*(1.0 - t_pre)
#                self.t_foc = (self.t_b-self.t_f)/((1.0-t_pre)*self.t_b)
#            print ('qqqq',t_pre,self.t_foc)
            if self._T == 0.0:
                self.goods_rt = math.exp(self.gra_T_std*(1.0-(self.pre_S)))
            else:
                self.goods_rt = math.exp(self.gra_T_std*(1.0-(self.pre_S)-self.t))/self._T
            self.T_std = math.exp(0.5*self.gra_T_std*(1.0-(self.pre_S)-self.t))
#            self.T_cmp = math.exp(0.5*self.gra_T_cmp*(1.0-self.t_foc*self.t_f/self.t_b))
#            self.T_ = math.exp(0.5*self.gra_T_*(1.0-self.t_foc*self.t_f/self.t_b))
#            self.T_normal = math.exp(0.5*self.gra_T_std*(1.0-self.t_f/self.t_b))
        elif self.backward_gap < 0.0 and self.forward_gap >= 0.0:
            if self._T == 0.0:
                self.t_f = 0.0
#                t_pre = 0.0
            else:
                self.t_f = self.ask_1 - self.forward_entry_price
#                t_pre = 1.0 - 2.0/self.gra_T_std * math.log(self._T)
            self.t_b = self.ask_1 - self.backward_entry_price
            self.t = self.t_f/self.t_b
#            if t_pre == 1.0:
#                self.t_foc = 1.0
#            else:
#                #self.t_foc = (t_pre*(self.t_b-self.t_f))/self.t_f*(1.0 - t_pre)
#                self.t_foc = (self.t_b-self.t_f)/((1.0-t_pre)*self.t_b)
#            print ('qqqq',t_pre,self.t_foc)
            if self._T == 0.0:
                self.goods_rt = math.exp(self.gra_T_std*(1.0-(self.pre_S)))
            else:
                self.goods_rt = math.exp(self.gra_T_std*(1.0-(self.pre_S)-self.t))/self._T
            self.T_std = math.exp(0.5*self.gra_T_std*(1.0-(self.pre_S)-self.t))
#            self.T_cmp = math.exp(0.5*self.gra_T_cmp*(1.0-self.t_foc*self.t_f/self.t_b))
#            self.T_ = math.exp(0.5*self.gra_T_*(1.0-self.t_foc*self.t_f/self.t_b))
#            self.T_normal = math.exp(0.5*self.gra_T_std*(1.0-self.t_f/self.t_b))
        elif self.forward_gap < 0.0 and self.backward_gap < 0.0:
            self.goods_rt = 1.0
            self.T_std = 1.0
            self.t = 0.0
#            self.T_ = 1.0
#            self.T_cmp = 1.0
#            self.T_normal = 1.0
#            self.t_foc = 1.0
        elif self.forward_gap >= 0.0 and self.backward_gap >= 0.0:
            self.goods_rt = 0.61
            self.T_std = 0.61
            self.t = 1.0
#            self.T_ = math.exp(-0.5*self.gra_T_)
#            self.T_cmp = math.exp(-0.5*self.gra_T_cmp)
#            self.T_normal = 1.0
#            self.t_foc = 1.0

        self.s_pos_rt = self.t * self.S_
        self.s_neg_rt = self.S_
        self.forward_gap_balance = False
        self.backward_gap_balance = False
        if self.forward_gap < 0.0 and self.backward_gap >= 0.0:
            if self._S > self.s_neg_rt and self.forward_stable_price and self._T < self.T_std:
                self.forward_gap_balance = True
#                self.T_limit_std = 1.0
            elif self._S < self.s_pos_rt and self.backward_stable_price and self._T > self.T_std:
                self.backward_gap_balance = True
#                self.backward_balance_size = int(min(-self.backward_position_size-self.forward_position_size*self.T_std,-self.backward_position_size))
#            elif self.backward_stable_price and self._T > self.T_std and self.S_ > self.goods_rt:
#                self.backward_gap_balance = True
#                self.backward_balance_size = int(min(-self.backward_position_size-self.forward_position_size*self.T_std,-self.backward_position_size))
#                self.T_limit_std = 1.0
        elif self.backward_gap < 0.0 and self.forward_gap >= 0.0:
            if self._S > self.s_neg_rt and self.backward_stable_price and self._T < self.T_std:
                self.backward_gap_balance = True
#                self.T_limit_std = 1.0
            elif self._S < self.s_pos_rt and self.forward_stable_price and self._T > self.T_std:
                    self.forward_gap_balance = True
#                    self.forward_balance_size = int(max(-self.forward_position_size-self.backward_position_size*self.T_std,-self.forward_position_size))
#            elif self.forward_stable_price and self._T > self.T_std and self.S_ > self.goods_rt:
#                self.forward_gap_balance = True
#                self.forward_balance_size = int(max(-self.forward_position_size-self.backward_position_size*self.T_std,-self.forward_position_size))
#                self.T_limit_std = 1.0
        elif self.forward_gap >= 0.0 and self.backward_gap >= 0.0:
            if self.forward_position_size > 0:
                self.forward_gap_balance = True
            if self.backward_position_size > 0:
                self.backward_gap_balance = True
        elif self.forward_gap < 0.0 and self.backward_gap < 0.0:
            self.forward_gap_balance = False
            self.backward_gap_balance = False

        if self.forward_gap_balance:
            if self.forward_gap >= 0.0:
                if self.backward_gap < 0.0:
                    self.forward_balance_size = int(max(self.forward_position_size*(self.s_pos_rt-self._S)*self.backward_goods/self.forward_goods,-self.forward_position_size))
                    print ('d1',self.forward_position_size*(self.s_pos_rt-self._S)*self.backward_goods/self.forward_goods,-self.forward_position_size)
                else:
                    self.forward_balance_size = int(-self.foward_positionsize - self.backward_position_size*self.T_std)
            else:
                #self.forward_balance_size = int(max(-self.forward_position_size * ((self._S-self.s_rt)/(1.0-self.s_rt)),self.forward_position_size * (self.balance_overflow/self.forward_goods)))
                #if self.forward_position_size > self.forward_limit:
                self.forward_balance_size = int(max(self.forward_position_size * (self.balance_overflow/self.forward_goods),-self.forward_position_size))
                print ('d2',self.forward_position_size * (self.balance_overflow/self.forward_goods),-self.forward_position_size)
                #else:
                #    self.forward_balance_size = int(max(-self.forward_position_size-self.backward_position_size/self.T_std,self.forward_position_size * (self.balance_overflow/self.forward_goods)))
                #    print ('d2',-self.forward_position_size-self.backward_position_size/self.T_std,self.forward_position_size * (self.balance_overflow/self.forward_goods))
        if self.backward_gap_balance:
            if self.backward_gap >= 0.0:
                if self.forward_gap < 0.0:
                    self.backward_balance_size = int(min(self.backward_position_size*(self.s_pos_rt-self._S)*self.forward_goods/self.backward_goods,-self.backward_position_size))
                    print ('d3',self.backward_position_size*(self.s_pos_rt-self._S)*self.forward_goods/self.backward_goods,-self.backward_position_size)
                else:
                    self.backward_balance_size = int(-self.backward_position_size - self.forward_position_size*self.T_std)
            else:
                #self.backward_balance_size = int(min(-self.backward_position_size * ((self._S-self.s_rt)/(1.0-self.s_rt)),self.backward_position_size * (self.balance_overflow/self.backward_goods)))
                #if abs(self.backward_position_size) > self.backward_limit:
                    self.backward_balance_size = int(min(self.backward_position_size * (self.balance_overflow/self.backward_goods),-self.backward_position_size))
                    print ('d4',self.backward_position_size * (self.balance_overflow/self.backward_goods),-self.backward_position_size)
                #else:
                #    self.backward_balance_size = int(min(-self.backward_position_size-self.forward_position_size/self.T_std,self.backward_position_size * (self.balance_overflow/self.backward_goods)))
                #    print ('d4',-self.backward_position_size-self.forward_position_size/self.T_std,self.backward_position_size * (self.balance_overflow/self.backward_goods))

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
                break

        for gap_level in gap_levels:
            if -self.backward_gap < float(gap_level):
                self.backward_gap_level = self.level[gap_level]['leverage']
                break

        if self.forward_gap < 0.0 and self.backward_gap >= 0.0:
            if self._T < self.T_std and not self.forward_gap_balance and self.forward_position_size >= self.limit_size*self.size_rt:
#                backward_accounts = backward_api_instance.list_futures_accounts(settle='usdt')
#                if float(backward_accounts._available)/(float(self.backward_positions._value)/abs(self.backward_position_size))*self.backward_leverage > self.limit_size*self.size_rt*2+self.backward_position_size: 
                self.size_rt = self.size_rt * 2
#                else:
#                    raise Exception('insufficient backward available')
            elif not (self._T < self.T_std and not self.forward_gap_balance) and self.forward_position_size < self.limit_size*self.size_rt:
                self.size_rt = self.size_rt / 2
            self.size_rt = min(2,max(1,self.size_rt))
        elif self.forward_gap >= 0.0 and self.backward_gap < 0.0:
            if self._T < self.T_std and not self.backward_gap_balance and abs(self.backward_position_size) >= self.limit_size*self.size_rt:
#                forward_accounts = forward_api_instance.list_futures_accounts(settle='usdt')
#                if float(forward_accounts._available)/(float(self.forward_positions._value)/self.forward_position_size)*self.forward_leverage > self.limit_size*self.size_rt*2-self.forward_position_size:
                self.size_rt = self.size_rt * 2
#                else:
#                    raise Exception('insufficient forward available')
            elif not (self._T < self.T_std and not self.backward_gap_balance) and abs(self.backward_position_size) < self.limit_size*self.size_rt:
                self.size_rt = self.size_rt / 2
            self.size_rt = min(2,max(1,self.size_rt))

        self.forward_limit = self.limit_size * self.size_rt
        self.backward_limit = self.limit_size * self.size_rt
        if self.forward_gap >= 0.0 and self.backward_gap < 0.0:
            if abs(self.backward_position_size) < self.backward_limit:
                self.forward_limit = max(self.forward_limit,abs(self.backward_position_size)*min(self.T_std,self.T_limit))
                self.backward_limit = max(self.backward_limit,self.forward_position_size/max(self.T_std,1.0/self.T_limit))
            else:
                self.forward_limit = max(self.forward_limit,abs(self.backward_position_size))
                self.backward_limit = max(self.backward_limit,self.forward_position_size/max(self.T_std,1.0/self.T_limit))
        elif self.forward_gap < 0.0 and self.backward_gap >= 0.0:
            if self.forward_position_size < self.forward_limit:
                self.backward_limit = max(self.backward_limit,self.forward_position_size*min(self.T_std,self.T_limit))
                self.forward_limit = max(self.forward_limit,abs(self.backward_position_size)/max(self.T_std,1.0/self.T_limit))
            else:
                self.backward_limit = max(self.backward_limit,self.forward_position_size)
                self.forward_limit = max(self.forward_limit,abs(self.backward_position_size)/max(self.T_std,1.0/self.T_limit))

        self.forward_limit = min(self.forward_limit,self.max_size)
        self.backward_limit = min(self.backward_limit,self.max_size)

        self.forward_catch = False
        self.backward_catch = False
        print ('aaaa',self.forward_limit,self.backward_limit)
        print (self.balance_overflow)
        print (self.S_,self._S,self.pre_S,self.s_pos_rt,self.s_neg_rt)
#        print (self._S, 1.0-self._T/self.T_std)
        print (self._T,self.T_std)
#        print (self.T_)
#        print (self.T_std,self.T_normal)
        if self.catch:
            if self.forward_gap < 0.0 and self.backward_gap >= 0.0:
                if self._T > self.T_std:
#                    if -self.backward_position_size >= self.limit_size:
#                        if self.S_ > self.goods_rt and self.backward_stable_price:
#                            self.forward_catch = True
#                            self.backward_gap_balance = False
#                            self.forward_catch_size = int(min((-self.backward_position_size/self.T_std-self.forward_position_size),self.forward_limit-self.forward_position_size))
#                    else:
                    if self.backward_stable_price and not self.backward_gap_balance:
                        self.forward_catch = True
                        if self.forward_position_size < self.limit_size:
                            self.forward_catch_size = int(min(self.forward_limit-self.forward_position_size,self.forward_limit-self.forward_position_size))
                            print ('1111',self.forward_limit-self.forward_position_size)
                        else:
                            self.forward_catch_size = int(min(-self.backward_position_size/self.T_std-self.forward_position_size,self.forward_limit-self.forward_position_size))
                            print ('1111',-self.backward_position_size/self.T_std-self.forward_position_size,self.forward_limit-self.forward_position_size)
                elif self._T < self.T_std:
                    if self.forward_stable_price and not self.forward_gap_balance:
                        self.backward_catch = True
#                        regression_size = regression_1(self.backward_entry_price,self.forward_entry_price,-self.backward_position_size,self.forward_position_size,self.ask_1,-0.5*self.gra_T_*self.t_foc,0.5*self.gra_T_)
#                        self.backward_catch_size = int(max(-regression_size,-self.backward_limit-self.backward_position_size))
                        self.backward_catch_size = int(max(-self.forward_position_size*self.T_std-self.backward_position_size,-self.backward_limit-self.backward_position_size))
                        print ('bbbb',-self.forward_position_size*self.T_std-self.backward_position_size,-self.backward_limit-self.backward_position_size)
            elif self.backward_gap < 0.0 and self.forward_gap >= 0.0:
                if self._T > self.T_std:
#                    if self.forward_position_size >= self.limit_size:
#                        if self.S_ > self.goods_rt and self.forward_stable_price:
#                            self.backward_catch = True
#                            self.forward_gap_balance = False
#                            self.backward_catch_size = int(max((-self.forward_position_size/self.T_std-self.backward_position_size),-self.backward_limit-self.backward_position_size))
#                    else:
                    if self.forward_stable_price and not self.forward_gap_balance:
                        self.backward_catch = True
                        if abs(self.backward_position_size) < self.limit_size:
                            self.backward_catch_size = int(max(-self.backward_limit-self.backward_position_size,-self.backward_limit-self.backward_position_size))
                            print ('2222',-self.backward_limit-self.backward_position_size)
                        else:
                            self.backward_catch_size = int(max(-self.forward_position_size/self.T_std-self.backward_position_size,-self.backward_limit-self.backward_position_size))
                            print ('2222',-self.forward_position_size/self.T_std-self.backward_position_size,-self.backward_limit-self.backward_position_size)
                elif self._T < self.T_std:
                    if self.backward_stable_price and not self.backward_gap_balance:
                        self.forward_catch = True
#                        regression_size = regression_1(self.forward_entry_price,self.backward_entry_price,self.forward_position_size,-self.backward_position_size,self.bid_1,-0.5*self.gra_T_*self.t_foc,0.5*self.gra_T_)
#                        self.forward_catch_size = int(min(regression_size,self.forward_limit-self.forward_position_size))
                        self.forward_catch_size = int(min(-self.backward_position_size*self.T_std-self.forward_position_size,self.forward_limit-self.forward_position_size))
                        print ('cccc',-self.backward_position_size*self.T_std-self.forward_position_size,self.forward_limit-self.forward_position_size)
#            elif self.forward_gap < 0.0 and self.backward_gap < 0.0:
#                if self.forward_position_size > abs(self.backward_position_size):
#                    self.backward_catch = True
#                    self.backward_catch_size = int(max((-self.forward_position_size-self.backward_position_size),-self.backward_limit-self.backward_position_size))
#                elif self.forward_position_size < abs(self.backward_position_size):
#                    self.forward_catch = True
#                    self.forward_catch_size = int(min((-self.forward_position_size-self.backward_position_size),self.forward_limit-self.forward_position_size))
        
#        print (self.forward_gap_level,self.backward_gap_level)
#        print (self.forward_leverage,self.backward_leverage)
#        print (self.forward_balance_size,self.backward_balance_size)
#        print (self.forward_catch_size,self.backward_catch_size)


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
#        if self.forward_leverage_alarm:
        if self.forward_leverage != self.forward_gap_level:
            forward_api_instance.update_position_leverage(contract=self.contract,settle='usdt',leverage = self.forward_gap_level)
            self.forward_leverage = self.forward_gap_level
#        if self.backward_leverage_alarm:
        if self.backward_leverage != self.backward_gap_level:
            backward_api_instance.update_position_leverage(contract=self.contract,settle='usdt',leverage = self.backward_gap_level)
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
                    forward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
                else:
                    if self.bid_1 > order_price:
#                        forward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
                        if self.forward_catch and self.forward_catch_size > 0:
                            forward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
#                            forward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = self.forward_catch_size, price = self.bid_1,tif='poc'))
                        elif (not self.forward_position_alarm and not self.forward_delta_alarm):
                            forward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
#                            forward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = order_size, price = self.bid_1,tif='poc'))
            elif order_size < 0:
                if self.forward_gap_balance:
                    if self.forward_gap < 0.0 and self.forward_position_size > 0 and order_price > self.ask_1:
#                        forward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
                        if self.balance_overflow > 0.0 and self.forward_balance_size < 0:
                            forward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
#                            forward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size =self.forward_balance_size, price = self.ask_1,tif='poc'))
                    elif self.forward_gap >= 0.0 and order_price > self.ask_1 and self.forward_position_size > 0:
                        forward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
#                        if self.forward_balance_size < 0:
#                            forward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size=self.forward_balance_size,price = self.ask_1,tif='poc'))
                    elif self.forward_position_size == 0 or order_price > self.ask_1:
                        forward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
                else:
                    forward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
        if not self.forward_increase_clear:
            if self.forward_position_size < self.forward_limit:
                if self.forward_catch and self.forward_catch_size > 0:
                    forward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = self.forward_catch_size, price = self.bid_1,tif='poc'))
                elif (not self.forward_position_alarm and not self.forward_delta_alarm):
                    forward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = self.tap * self.forward_leverage, price = self.bid_1,tif='poc'))
        if not self.forward_reduce_clear and self.forward_gap_balance:
            if self.forward_gap >= 0.0 and self.forward_position_size > 0:
                if self.forward_balance_size < 0:
                    forward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size=self.forward_balance_size,price = self.ask_1,tif='poc'))
            elif self.forward_gap < 0.0 and self.balance_overflow > 0.0 and self.forward_position_size > 0:
                if self.forward_balance_size < 0:
#                    if self.sleep_clear:
                    forward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = self.forward_balance_size, price = self.ask_1,tif='poc'))
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
                    backward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
                else:
                    if self.ask_1 < order_price:
#                        backward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
                        if self.backward_catch and self.backward_catch_size < 0:
                            backward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
#                            backward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = self.backward_catch_size, price = self.ask_1,tif='poc'))
                        elif (not self.backward_position_alarm and not self.backward_delta_alarm):
                            backward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
#                            backward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = order_size, price = self.ask_1,tif='poc'))
            elif order_size > 0:
                if self.backward_gap_balance:
                    if self.backward_gap < 0.0 and self.backward_position_size < 0 and order_price < self.bid_1:
#                        backward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
                        if self.balance_overflow > 0.0 and self.backward_balance_size > 0:
                            backward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
#                            backward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = self.backward_balance_size, price = self.bid_1,tif='poc'))
                    elif self.backward_gap >= 0.0 and order_price < self.bid_1 and self.backward_position_size < 0:
                        backward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
#                        if self.backward_balance_size > 0:
#                            backward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size=self.backward_balance_size,price = self.bid_1,tif='poc'))
                    elif self.backward_position_size == 0 or order_price < self.bid_1:
                        backward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
                else:
                    backward_api_instance.cancel_futures_order(settle='usdt',order_id=order_id)
        if not self.backward_increase_clear:
            if abs(self.backward_position_size) < self.backward_limit:
                if self.backward_catch and self.backward_catch_size < 0:
                    backward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = self.backward_catch_size, price = self.ask_1,tif='poc'))
                elif (not self.backward_position_alarm and not self.backward_delta_alarm):
                    backward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = -self.tap * self.backward_leverage, price = self.ask_1,tif='poc'))
        if not self.backward_reduce_clear and self.backward_gap_balance:
            if self.backward_gap >= 0.0 and self.backward_position_size < 0:
                if self.backward_balance_size > 0:
                    backward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size=self.backward_balance_size,price = self.bid_1,tif='poc'))
            elif self.backward_gap < 0.0 and self.balance_overflow > 0.0 and self.backward_position_size < 0:
                if self.backward_balance_size > 0:
#                    if self.sleep_clear:
                    backward_api_instance.create_futures_order(settle='usdt',futures_order=FuturesOrder(contract=self.contract,size = self.backward_balance_size, price = self.bid_1,tif='poc'))
#                        self.sleep_clear = False
#                    else:
#                        time.sleep(30)
#                        self.sleep_clear = True

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

