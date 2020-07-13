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
<<<<<<< HEAD
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
=======
        forward_orders = forward_api_instance.list_futures_orders(contract=Future_Handler.contract,settle=Future_Handler.settle,status='open',async_req=True)
        backward_orders = backward_api_instance.list_futures_orders(contract=Future_Handler.contract,settle=Future_Handler.settle,status='open',async_req=True)
        candles=backward_api_instance.list_futures_candlesticks(contract=Future_Handler.contract,settle=Future_Handler.settle,interval='1m',async_req=True)
        candles_5m=backward_api_instance.list_futures_candlesticks(contract=Future_Handler.contract,settle=Future_Handler.settle,interval='5m',async_req=True)
        candles_1h=backward_api_instance.list_futures_candlesticks(contract=Future_Handler.contract,settle=Future_Handler.settle,interval='1h',async_req=True)
        book = backward_api_instance.list_futures_order_book(contract=Future_Handler.contract,settle=Future_Handler.settle,async_req=True)
        forward_positions = forward_api_instance.get_position(contract=Future_Handler.contract,settle=Future_Handler.settle,async_req=True)
        backward_positions = backward_api_instance.get_position(contract=Future_Handler.contract,settle=Future_Handler.settle,async_req=True)
        self.forward_orders = forward_orders.get()
        self.backward_orders = backward_orders.get()
        candlesticks = candles.get()
        candlesticks_5m = candles_5m.get()
        candlesticks_1h = candles_1h.get()
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

        Future_Handler.rt_soft = Future_Handler.step_soft/self.entry_gap
        Future_Handler.rt_hard = Future_Handler.step_hard/self.entry_gap

        if self.forward_position_size > 0 and self.forward_entry_price > 0:
            Future_Handler.t_f = self.ask_1 - self.forward_entry_price
            self.forward_gap = Future_Handler.t_f/self.forward_entry_price
        else:
            Future_Handler.t_f = 0.0
            self.forward_gap = 0.0
        if self.backward_position_size < 0 and self.backward_entry_price > 0:
            Future_Handler.t_b = self.backward_entry_price - self.bid_1
            self.backward_gap = Future_Handler.t_b/self.backward_entry_price
        else:
            Future_Handler.t_b = 0.0
            self.backward_gap = 0.0

        self.forward_stable_price = True
        self.backward_stable_price = True
        if len(candlesticks) > 0:
            o = float(candlesticks[len(candlesticks)-1]._o)
            c = float(candlesticks[len(candlesticks)-1]._c)
            if (c - o)/self.bid_1 > 0.001:
#                if (self.bid_1 - c)/self.bid_1 > -0.001:
                self.forward_stable_price = False
            elif (c - o)/self.ask_1 < -0.001:
#                if (self.ask_1 - c)/self.ask_1 < 0.001:
                self.backward_stable_price = False

#        std_mom = 10
#        if len(candlesticks_5m) > 10:
#            sum = []
#            for i in range(1,11):
#                o = float(candlesticks_5m[len(candlesticks_5m)-i]._o)
#                c = float(candlesticks_5m[len(candlesticks_5m)-i]._c)
#                sum.append(abs(c - o))
#            std_mom = np.max(sum)
#
#        std_max = 100
#        if len(candlesticks_1h) > 10:
#            sum = []
#            for i in range(1,11):
#                o = float(candlesticks_1h[len(candlesticks_1h)-i]._o)
#                c = float(candlesticks_1h[len(candlesticks_1h)-i]._c)
#                sum.append(abs(c - o))
#            std_max = np.max(sum)
#
#        Future_Handler.step_soft = std_mom
#        Future_Handler.step_hard = std_max
#        Future_Handler.rt_soft = Future_Handler.step_soft/self.entry_gap
#        Future_Handler.rt_hard = Future_Handler.step_hard/self.entry_gap
#        print('mom',std_mom,std_max)

        if self.forward_entry_price == 0:
            Future_Handler.forward_goods = 0.0
        else:
            Future_Handler.forward_goods = float(self.forward_positions._value)*(self.ask_1-self.forward_entry_price)/self.forward_entry_price
        if self.backward_entry_price == 0:
            Future_Handler.backward_goods = 0.0
        else:
            Future_Handler.backward_goods = float(self.backward_positions._value)*(self.backward_entry_price-self.bid_1)/self.backward_entry_price
        if self.forward_position_size > 0:
            Future_Handler.limit_goods = float(self.forward_positions._value)*self.limit_size/self.forward_position_size
        elif self.backward_position_size < 0:
            Future_Handler.limit_goods = float(self.backward_positions._value)*self.limit_size/abs(self.backward_position_size)
        else:
            Future_Handler.limit_goods = 0.0

        if Future_Handler.forward_account_from == 0:
            Future_Handler.forward_account_from = int(time.time())
        if Future_Handler.backward_account_from == 0:
            Future_Handler.backward_account_from = int(time.time())
        forward_account_book = forward_api_instance.list_futures_account_book(settle=Future_Handler.settle,_from=Future_Handler.forward_account_from)
        backward_account_book = backward_api_instance.list_futures_account_book(settle=Future_Handler.settle,_from=Future_Handler.backward_account_from)
        for item in forward_account_book:
            if Future_Handler.contract in item.text:
                Future_Handler.goods += float(item.change)
                if item.type == 'pnl':
                    Future_Handler.balance_overflow += float(item.change)
        for item in backward_account_book:
            if Future_Handler.contract in item.text:
                Future_Handler.goods += float(item.change)
                if item.type == 'pnl':
                    Future_Handler.balance_overflow += float(item.change)
>>>>>>> e6200964cf33145ddd157e2ce760721f1417d06a
        if len(forward_account_book) > 0:
            FH.forward_account_from = int(forward_account_book[0]._time) + 1
        if len(backward_account_book) > 0:
<<<<<<< HEAD
            FH.backward_account_from = int(backward_account_book[0]._time) + 1
        
        if FH.forward_gap < 0.0 and FH.backward_gap >= 0.0:
            FH._T = abs(float(FH.backward_position_size) / float(FH.forward_position_size))
        elif FH.backward_gap < 0.0 and FH.forward_gap >= 0.0:
            FH._T = abs(float(FH.forward_position_size) / float(FH.backward_position_size))
        elif FH.forward_gap < 0.0 and FH.backward_gap < 0.0:
            if FH.forward_gap > FH.backward_gap:
                FH._T = abs(float(FH.forward_position_size) / float(FH.backward_position_size))
=======
            Future_Handler.backward_account_from = int(backward_account_book[0]._time) + 1
        
        if self.forward_gap < 0.0 and self.backward_gap >= 0.0:
            Future_Handler._T = abs(float(self.backward_position_size) / float(self.forward_position_size))
        elif self.backward_gap < 0.0 and self.forward_gap >= 0.0:
            Future_Handler._T = abs(float(self.forward_position_size) / float(self.backward_position_size))
        elif self.forward_gap < 0.0 and self.backward_gap < 0.0:
            if self.forward_gap > self.backward_gap:
                Future_Handler._T = abs(float(self.forward_position_size) / float(self.backward_position_size))
>>>>>>> e6200964cf33145ddd157e2ce760721f1417d06a
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

<<<<<<< HEAD
        if FH.forward_gap < 0.0 and FH.backward_gap >= 0.0:
            FH.t = -FH.t_b/FH.t_f
            FH.T_std = 1.0 - 1.0*FH.t
            if -min(FH.t_f,FH.t_b) <= FH.step_hard:
                FH.t_tail = -0.5
            else:
                FH.t_tail = max(FH.t_tail,((1.0+FH.rt_hard)*FH.t-FH.rt_hard)/(1.0+FH.rt_hard*(FH.t-1.0)))
        elif FH.backward_gap < 0.0 and FH.forward_gap >= 0.0:
            FH.t = -FH.t_f/FH.t_b
            FH.T_std = 1.0 - 1.0*FH.t
            if -min(FH.t_f,FH.t_b) <= FH.step_hard:
                FH.t_tail = -0.5
            else:
                FH.t_tail = max(FH.t_tail,((1.0+FH.rt_hard)*FH.t-FH.rt_hard)/(1.0+FH.rt_hard*(FH.t-1.0)))
        elif FH.forward_gap < 0.0 and FH.backward_gap < 0.0:
            if FH.forward_gap > FH.backward_gap:
                FH.t = -FH.t_f/(FH.t_b+FH.t_f)
            else:
                FH.t = -FH.t_b/(FH.t_f+FH.t_b)
            FH.T_std = 1.0
#        elif FH.forward_gap >= 0.0 and FH.backward_gap >= 0.0:
#            FH.T_std = 0.61

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
            if FH.forward_position_size == 0 or FH.backward_position_size == 0:
                FH.catch = True
                FH.S_dn = FH.S_
                FH.S_dn_t = -FH.rt_soft
                FH.S_up = FH.rt_soft
                FH.S_up_t = 2*FH.rt_soft
            else:
                FH.balance = True
                FH.t_up = (1.0-FH.rt_soft)*FH.t+FH.rt_soft
                FH.t_dn = (1.0+FH.rt_soft)*FH.t-FH.rt_soft
                FH.t_up_S = (1.0-2*FH.rt_soft)*FH.t+2*FH.rt_soft
                FH.t_dn_S = (1.0+2*FH.rt_soft)*FH.t-2*FH.rt_soft
        
=======
        if self.forward_gap < 0.0 and self.backward_gap >= 0.0:
<<<<<<< HEAD
            Future_Handler.t = -Future_Handler.t_b/Future_Handler.t_f
            Future_Handler.T_std = 1.0 - 1.0*Future_Handler.t
            if -min(Future_Handler.t_f,Future_Handler.t_b) <= Future_Handler.step_hard:
                Future_Handler.t_tail = -0.5
            else:
                Future_Handler.t_tail = max(Future_Handler.t_tail,((1.0+Future_Handler.rt_hard)*Future_Handler.t-Future_Handler.rt_hard)/(1.0+Future_Handler.rt_hard*(Future_Handler.t-1.0)))
        elif self.backward_gap < 0.0 and self.forward_gap >= 0.0:
            Future_Handler.t = -Future_Handler.t_f/Future_Handler.t_b
            Future_Handler.T_std = 1.0 - 1.0*Future_Handler.t
<<<<<<< HEAD
            if -min(Future_Handler.t_f,Future_Handler.t_b) <= Future_Handler.step_hard:
                Future_Handler.t_tail = -0.5
            else:
                Future_Handler.t_tail = max(Future_Handler.t_tail,((1.0+Future_Handler.rt_hard)*Future_Handler.t-Future_Handler.rt_hard)/(1.0+Future_Handler.rt_hard*(Future_Handler.t-1.0)))
=======
            Future_Handler.t_tail = max(Future_Handler.t_tail,(1.0+Future_Handler.rt_hard)*Future_Handler.t-Future_Handler.rt_hard)
=======
            Future_Handler.t = -Future_Handler.t_b/(Future_Handler.t_f+Future_Handler.t_b)
            Future_Handler.T_std = 1.0 - 0.13*Future_Handler.t
            Future_Handler.t_tail = max(Future_Handler.t_tail,Future_Handler.t-2*Future_Handler.rt_hard)
        elif self.backward_gap < 0.0 and self.forward_gap >= 0.0:
            Future_Handler.t = -Future_Handler.t_f/(Future_Handler.t_b+Future_Handler.t_f)
            Future_Handler.T_std = 1.0 - 0.13*Future_Handler.t
            Future_Handler.t_tail = max(Future_Handler.t_tail,Future_Handler.t-2*Future_Handler.rt_hard)
>>>>>>> 7125560b86f91b4b770b11526d7264b85b401658
>>>>>>> 30b82598ed68e8fe453d9adf424c77c5d009cde1
        elif self.forward_gap < 0.0 and self.backward_gap < 0.0:
            if self.forward_gap > self.backward_gap:
                Future_Handler.t = -Future_Handler.t_f/(Future_Handler.t_b+Future_Handler.t_f)
            else:
                Future_Handler.t = -Future_Handler.t_b/(Future_Handler.t_f+Future_Handler.t_b)
            Future_Handler.T_std = 1.0
#        elif self.forward_gap >= 0.0 and self.backward_gap >= 0.0:
#            Future_Handler.T_std = 0.61

        if Future_Handler.balance and not Future_Handler.catch:
            Future_Handler.t_up = min(Future_Handler.t_up,(1.0-Future_Handler.rt_soft)*Future_Handler.t+Future_Handler.rt_soft)
            Future_Handler.t_up_S = min(Future_Handler.t_up_S,(1.0-2*Future_Handler.rt_soft)*Future_Handler.t+2*Future_Handler.rt_soft)
            Future_Handler.t_dn = max(Future_Handler.t_dn,(1.0+Future_Handler.rt_soft)*Future_Handler.t-Future_Handler.rt_soft)
            Future_Handler.t_dn_S = max(Future_Handler.t_dn_S,(1.0+2*Future_Handler.rt_soft)*Future_Handler.t-2*Future_Handler.rt_soft)
            if Future_Handler.t >= Future_Handler.t_up_S:
                Future_Handler.balance = False
                Future_Handler.catch = True
                Future_Handler.S_up = Future_Handler.S_
<<<<<<< HEAD
                Future_Handler.S_up_t = (1.0-Future_Handler.rt_soft)*Future_Handler.S_+Future_Handler.rt_soft*Future_Handler._T
                Future_Handler.S_dn = (1.0+Future_Handler.rt_soft)*Future_Handler.S_-Future_Handler.rt_soft*Future_Handler._T
                Future_Handler.S_dn_t = (1.0+2*Future_Handler.rt_soft)*Future_Handler.S_-2*Future_Handler.rt_soft*Future_Handler._T
=======
<<<<<<< HEAD
                Future_Handler.S_up_t = compute_ps(Future_Handler.rt_soft*Future_Handler._T,Future_Handler.S_)
                Future_Handler.S_dn = compute_ps(-Future_Handler.rt_soft*Future_Handler._T,Future_Handler.S_)
                Future_Handler.S_dn_t = compute_ps(-2*Future_Handler.rt_soft*Future_Handler._T,Future_Handler.S_)
=======
                Future_Handler.S_up_t = ((1.0-Future_Handler.rt_soft)*Future_Handler.S_+Future_Handler.rt_soft*Future_Handler._T)/(1.0+Future_Handler.rt_soft*(Future_Handler._T-Future_Handler.S_))
                Future_Handler.S_dn = ((1.0+Future_Handler.rt_soft)*Future_Handler.S_-Future_Handler.rt_soft*Future_Handler._T)/(1.0-Future_Handler.rt_soft*(Future_Handler._T-Future_Handler.S_))
                Future_Handler.S_dn_t = ((1.0+2*Future_Handler.rt_soft)*Future_Handler.S_-2*Future_Handler.rt_soft*Future_Handler._T)/(1.0-2*Future_Handler.rt_soft*(Future_Handler._T-Future_Handler.S_))
>>>>>>> 7125560b86f91b4b770b11526d7264b85b401658
>>>>>>> 30b82598ed68e8fe453d9adf424c77c5d009cde1
            elif Future_Handler.t <= Future_Handler.t_dn_S:
                Future_Handler.balance = False
                Future_Handler.catch = True
                Future_Handler.S_dn = Future_Handler.S_
<<<<<<< HEAD
                Future_Handler.S_dn_t = (1.0+Future_Handler.rt_soft)*Future_Handler.S_-Future_Handler.rt_soft*Future_Handler._T
                Future_Handler.S_up = (1.0-Future_Handler.rt_soft)*Future_Handler.S_+Future_Handler.rt_soft*Future_Handler._T
                Future_Handler.S_up_t = (1.0-2*Future_Handler.rt_soft)*Future_Handler.S_+2*Future_Handler.rt_soft*Future_Handler._T
=======
<<<<<<< HEAD
                Future_Handler.S_dn_t = compute_ps(-Future_Handler.rt_soft*Future_Handler._T,Future_Handler.S_)
                Future_Handler.S_up = compute_ps(Future_Handler.rt_soft*Future_Handler._T,Future_Handler.S_)
                Future_Handler.S_up_t = compute_ps(2*Future_Handler.rt_soft*Future_Handler._T,Future_Handler.S_)
>>>>>>> 30b82598ed68e8fe453d9adf424c77c5d009cde1
            print ('balance',Future_Handler.t,Future_Handler.t_up_S,Future_Handler.t_up,Future_Handler.t_dn,Future_Handler.t_dn_S)
=======
                Future_Handler.S_dn_t = ((1.0+Future_Handler.rt_soft)*Future_Handler.S_-Future_Handler.rt_soft*Future_Handler._T)/(1.0-Future_Handler.rt_soft*(Future_Handler._T-Future_Handler.S_))
                Future_Handler.S_up = ((1.0-Future_Handler.rt_soft)*Future_Handler.S_+Future_Handler.rt_soft*Future_Handler._T)/(1.0+Future_Handler.rt_soft*(Future_Handler._T-Future_Handler.S_))
                Future_Handler.S_up_t = ((1.0-2*Future_Handler.rt_soft)*Future_Handler.S_+2*Future_Handler.rt_soft*Future_Handler._T)/(1.0+2*Future_Handler.rt_soft*(Future_Handler._T-Future_Handler.S_))
            print ('balance',Future_Handler.t,Future_Handler.t_up,Future_Handler.t_dn)
>>>>>>> 7125560b86f91b4b770b11526d7264b85b401658
        elif not Future_Handler.balance and Future_Handler.catch:
            Future_Handler.S_up = min(Future_Handler.S_up,(1.0-Future_Handler.rt_soft)*Future_Handler.S_+Future_Handler.rt_soft*Future_Handler._T)
            Future_Handler.S_up_t = min(Future_Handler.S_up_t,(1.0-2*Future_Handler.rt_soft)*Future_Handler.S_+2*Future_Handler.rt_soft*Future_Handler._T)
            Future_Handler.S_dn = max(Future_Handler.S_dn,(1.0+Future_Handler.rt_soft)*Future_Handler.S_-Future_Handler.rt_soft*Future_Handler._T)
            Future_Handler.S_dn_t = max(Future_Handler.S_dn_t,(1.0+2*Future_Handler.rt_soft)*Future_Handler.S_-2*Future_Handler.rt_soft*Future_Handler._T)
            if Future_Handler.S_ >= Future_Handler.S_up_t:
                Future_Handler.catch = False
                Future_Handler.balance = True
                Future_Handler.t_up = Future_Handler.t
<<<<<<< HEAD
                Future_Handler.t_dn = (1.0+Future_Handler.rt_soft)*Future_Handler.t-Future_Handler.rt_soft
                Future_Handler.t_up_S = (1.0-Future_Handler.rt_soft)*Future_Handler.t+Future_Handler.rt_soft
                Future_Handler.t_dn_S = (1.0+2*Future_Handler.rt_soft)*Future_Handler.t-2*Future_Handler.rt_soft
=======
<<<<<<< HEAD
                Future_Handler.t_dn = compute_ps(-Future_Handler.rt_soft,Future_Handler.t)
                Future_Handler.t_up_S = compute_ps(Future_Handler.rt_soft,Future_Handler.t)
                Future_Handler.t_dn_S = compute_ps(-2*Future_Handler.rt_soft,Future_Handler.t)
=======
                Future_Handler.t_dn = Future_Handler.t-Future_Handler.rt_soft
                Future_Handler.t_up_S = Future_Handler.t+Future_Handler.rt_soft
                Future_Handler.t_dn_S = Future_Handler.t-2*Future_Handler.rt_soft
>>>>>>> 7125560b86f91b4b770b11526d7264b85b401658
>>>>>>> 30b82598ed68e8fe453d9adf424c77c5d009cde1
            elif Future_Handler.S_ <= Future_Handler.S_dn_t:
                Future_Handler.catch = False
                Future_Handler.balance = True
                Future_Handler.t_dn = Future_Handler.t
<<<<<<< HEAD
                Future_Handler.t_up = (1.0-Future_Handler.rt_soft)*Future_Handler.t+Future_Handler.rt_soft
                Future_Handler.t_dn_S = (1.0+Future_Handler.rt_soft)*Future_Handler.t-Future_Handler.rt_soft
                Future_Handler.t_up_S = (1.0-2*Future_Handler.rt_soft)*Future_Handler.t+2*Future_Handler.rt_soft
=======
<<<<<<< HEAD
                Future_Handler.t_up = compute_ps(Future_Handler.rt_soft,Future_Handler.t)
                Future_Handler.t_dn_S = compute_ps(-Future_Handler.rt_soft,Future_Handler.t)
                Future_Handler.t_up_S = compute_ps(2*Future_Handler.rt_soft,Future_Handler.t)
>>>>>>> 30b82598ed68e8fe453d9adf424c77c5d009cde1
            print ('catch',Future_Handler.S_,Future_Handler.S_up_t,Future_Handler.S_up,Future_Handler.S_dn,Future_Handler.S_dn_t)
        elif not Future_Handler.balance and not Future_Handler.catch:
            if self.forward_position_size == 0 or self.backward_position_size == 0:
                Future_Handler.catch = True
                Future_Handler.S_dn = Future_Handler.S_
                Future_Handler.S_dn_t = -Future_Handler.rt_soft
                Future_Handler.S_up = Future_Handler.rt_soft
                Future_Handler.S_up_t = 2*Future_Handler.rt_soft
            else:
                Future_Handler.balance = True
                Future_Handler.t_up = (1.0-Future_Handler.rt_soft)*Future_Handler.t+Future_Handler.rt_soft
                Future_Handler.t_dn = (1.0+Future_Handler.rt_soft)*Future_Handler.t-Future_Handler.rt_soft
                Future_Handler.t_up_S = (1.0-2*Future_Handler.rt_soft)*Future_Handler.t+2*Future_Handler.rt_soft
                Future_Handler.t_dn_S = (1.0+2*Future_Handler.rt_soft)*Future_Handler.t-2*Future_Handler.rt_soft
        
=======
                Future_Handler.t_up = Future_Handler.t+Future_Handler.rt_soft
                Future_Handler.t_dn_S = Future_Handler.t-Future_Handler.rt_soft
                Future_Handler.t_up_S = Future_Handler.t+2*Future_Handler.rt_soft
            print ('catch',Future_Handler.S_,Future_Handler.S_up,Future_Handler.S_dn)
        elif not Future_Handler.balance and not Future_Handler.catch:
            Future_Handler.balance = True
            Future_Handler.t_up = Future_Handler.t+Future_Handler.rt_soft
            Future_Handler.t_dn = Future_Handler.t-Future_Handler.rt_soft
            Future_Handler.t_up_S = Future_Handler.t+2*Future_Handler.rt_soft
            Future_Handler.t_dn_S = Future_Handler.t-2*Future_Handler.rt_soft

>>>>>>> 7125560b86f91b4b770b11526d7264b85b401658
>>>>>>> e6200964cf33145ddd157e2ce760721f1417d06a
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
                        if FH.t <= FH.t_dn:
                            self.backward_gap_balance = True
                else:
<<<<<<< HEAD
                    if FH.forward_stable_price and FH._T < FH.T_std:
                        if FH.t <= FH.t_dn:
=======
                    if self.forward_stable_price and Future_Handler._T < Future_Handler.T_std:
                        if Future_Handler.t <= Future_Handler.t_dn:
>>>>>>> e6200964cf33145ddd157e2ce760721f1417d06a
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
        
<<<<<<< HEAD
=======
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

>>>>>>> e6200964cf33145ddd157e2ce760721f1417d06a
        self.forward_catch = False
        self.forward_catch_size = 0
        self.backward_catch = False
        self.backward_catch_size = 0
<<<<<<< HEAD
        print (FH._T,FH.T_std)
        if FH.catch:
            if FH.forward_gap < 0.0 and FH.backward_gap >= 0.0:
                if FH._T > FH.T_std:
                    if FH.backward_stable_price and FH.S_ >= FH.S_up:
=======
        print (Future_Handler._T,Future_Handler.T_std)
        if Future_Handler.catch:
            if self.forward_gap < 0.0 and self.backward_gap >= 0.0:
                if Future_Handler._T > Future_Handler.T_std:
                    if self.backward_stable_price and Future_Handler.S_ >= Future_Handler.S_up:
>>>>>>> e6200964cf33145ddd157e2ce760721f1417d06a
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
                        if FH.backward_stable_price and FH.S_ <= FH.S_dn:
                            self.forward_catch = True
                            self.forward_catch_size = int(min(-FH.backward_position_size*FH.T_std-FH.forward_position_size,FH.forward_limit-FH.forward_position_size))
                            print ('cccc',-FH.backward_position_size*FH.T_std-FH.forward_position_size,FH.forward_limit-FH.forward_position_size)
                    else:
                        if FH.forward_stable_price and FH.S_ <= FH.S_dn:
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
<<<<<<< HEAD
                if (not self.forward_catch) or FH.forward_position_size >= FH.forward_limit:
                    forward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
=======
                if (not self.forward_catch) or self.forward_position_size >= self.forward_limit:
                    forward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
>>>>>>> e6200964cf33145ddd157e2ce760721f1417d06a
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
<<<<<<< HEAD
                    forward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size = self.forward_catch_size, price = FH.bid_1,tif='poc'))
        if not self.forward_reduce_clear and self.forward_gap_balance:
            if FH.forward_position_size > 0:
                if self.forward_balance_size < 0:
                    forward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size=self.forward_balance_size,price = FH.ask_1,tif='poc'))
=======
                    forward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size = self.forward_catch_size, price = self.bid_1,tif='poc'))
        if not self.forward_reduce_clear and self.forward_gap_balance:
            if self.forward_position_size > 0:
                if self.forward_balance_size < 0:
                    forward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size=self.forward_balance_size,price = self.ask_1,tif='poc'))
>>>>>>> e6200964cf33145ddd157e2ce760721f1417d06a

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
<<<<<<< HEAD
                if (not self.backward_catch) or abs(FH.backward_position_size) >= FH.backward_limit:
                    backward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
=======
                if (not self.backward_catch) or abs(self.backward_position_size) >= self.backward_limit:
                    backward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
>>>>>>> e6200964cf33145ddd157e2ce760721f1417d06a
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
<<<<<<< HEAD
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
=======
                    backward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size = self.backward_catch_size, price = self.ask_1,tif='poc'))
        if not self.backward_reduce_clear and self.backward_gap_balance:
            if self.backward_position_size < 0:
                if self.backward_balance_size > 0:
                    backward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size=self.backward_balance_size,price = self.bid_1,tif='poc'))

        if self.forward_liq_flag:
            forward_api_instance.cancel_price_triggered_order_list(contract=Future_Handler.contract,settle=Future_Handler.settle)
            if self.forward_liq_price > 0:
                forward_api_instance.create_price_triggered_order(settle=Future_Handler.settle,futures_price_triggered_order=FuturesPriceTriggeredOrder(initial=FuturesInitialOrder(contract=Future_Handler.contract,size=0,price=str(0),close=True,tif='ioc',text='api'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=2,price=str(round(self.forward_liq_price*(1.0+0.1*1.0/self.forward_leverage),Future_Handler.quanto)),expiration=2592000)))
                Future_Handler.forward_trigger_liq = self.forward_liq_price*(1.0+0.1*1.0/self.forward_leverage)
        if self.backward_liq_flag:
            backward_api_instance.cancel_price_triggered_order_list(contract=Future_Handler.contract,settle=Future_Handler.settle)
            if self.backward_liq_price > 0:
                backward_api_instance.create_price_triggered_order(settle=Future_Handler.settle,futures_price_triggered_order=FuturesPriceTriggeredOrder(initial=FuturesInitialOrder(contract=Future_Handler.contract,size=0,price=str(0),close=True,tif='ioc',text='api'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=1,price=str(round(self.backward_liq_price*(1.0-0.1*1.0/self.backward_leverage),Future_Handler.quanto)),expiration=2592000)))
                Future_Handler.backward_trigger_liq = self.backward_liq_price*(1.0-0.1*1.0/self.backward_leverage)
>>>>>>> e6200964cf33145ddd157e2ce760721f1417d06a

