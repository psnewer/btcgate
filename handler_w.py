# -*- coding: utf-8 -*-

from __future__ import print_function
import requests
import time
import math
import gate_api
<<<<<<< HEAD
import numpy as np
=======
>>>>>>> 30b82598ed68e8fe453d9adf424c77c5d009cde1
from gate_api import FuturesOrder
from gate_api import FuturesPriceTriggeredOrder
from gate_api import FuturesInitialOrder
from gate_api import FuturesPriceTrigger
from gate_api.rest import ApiException
from conf import *
from handler import *

class Handler_W(Future_Handler):
    def __init__(self):
        self.tip = 'w'

    def get_flag(self):
        forward_orders = forward_api_instance.list_futures_orders(contract=Future_Handler.contract,settle=Future_Handler.settle,status='open',async_req=True)
        backward_orders = backward_api_instance.list_futures_orders(contract=Future_Handler.contract,settle=Future_Handler.settle,status='open',async_req=True)
        candles=backward_api_instance.list_futures_candlesticks(contract=Future_Handler.contract,settle=Future_Handler.settle,interval='1m',async_req=True)
<<<<<<< HEAD
        candles_5m=backward_api_instance.list_futures_candlesticks(contract=Future_Handler.contract,settle=Future_Handler.settle,interval='5m',async_req=True)
=======
>>>>>>> 30b82598ed68e8fe453d9adf424c77c5d009cde1
        book = backward_api_instance.list_futures_order_book(contract=Future_Handler.contract,settle=Future_Handler.settle,async_req=True)
        forward_positions = forward_api_instance.get_position(contract=Future_Handler.contract,settle=Future_Handler.settle,async_req=True)
        backward_positions = backward_api_instance.get_position(contract=Future_Handler.contract,settle=Future_Handler.settle,async_req=True)
        self.forward_orders = forward_orders.get()
        self.backward_orders = backward_orders.get()
        candlesticks = candles.get()
<<<<<<< HEAD
        candlesticks_5m = candles_5m.get()
=======
>>>>>>> 30b82598ed68e8fe453d9adf424c77c5d009cde1
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

<<<<<<< HEAD
        self.forward_limit = Future_Handler.limit_size
        self.backward_limit = Future_Handler.limit_size
    
        if self.mark_price > Future_Handler.peak:
            Future_Handler.predict = 'backward'
        elif self.mark_price < Future_Handler.bottom:
            Future_Handler.predict = 'forward'
=======
        if Future_Handler.predict == 'forward' and self.bid_1 >= Future_Handler.end_point:
            Future_Handler.end_point = self.bid_1
        elif Future_Handler.predict == 'backward' and self.ask_1 <= Future_Handler.end_point:
            Future_Handler.end_point = self.ask_1

        self.forward_limit = Future_Handler.limit_size
        self.backward_limit = Future_Handler.limit_size
>>>>>>> 30b82598ed68e8fe453d9adf424c77c5d009cde1

        if self.forward_entry_price == 0:
            self.forward_entry_price = self.bid_1
        if self.backward_entry_price == 0:
            self.backward_entry_price = self.ask_1
        self.entry_gap = self.forward_entry_price - self.backward_entry_price

<<<<<<< HEAD
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
=======
        Future_Handler.rt_soft = Future_Handler.step_soft/self.entry_gap
        Future_Handler.rt_hard = Future_Handler.step_hard/self.entry_gap
>>>>>>> 30b82598ed68e8fe453d9adf424c77c5d009cde1

        self.forward_stable_price = True
        self.backward_stable_price = True
        if len(candlesticks) > 0:
            o = float(candlesticks[len(candlesticks)-1]._o)
            c = float(candlesticks[len(candlesticks)-1]._c)
            if (c - o)/self.bid_1 > 0.001:
<<<<<<< HEAD
#                if (self.bid_1 - c)/self.bid_1 > -0.001:
                self.forward_stable_price = False
            elif (c - o)/self.ask_1 < -0.001:
#                if (self.ask_1 - c)/self.ask_1 < 0.001:
                self.backward_stable_price = False

        self.forward_mom = False
        self.backward_mom = False
        if len(candlesticks_5m) > 0:
            o = float(candlesticks_5m[len(candlesticks_5m)-1]._o)
            c = float(candlesticks_5m[len(candlesticks_5m)-1]._c)
            if (c - o)/self.bid_1 >= Future_Handler.std_mom:
                self.forward_mom = True
            elif (c - o)/self.ask_1 <= -Future_Handler.std_mom:
                self.backward_mom = True
#            if (c - o) >= std_max:
#                Future_Handler.sprint = True
#                Future_Handler.sprint = False
#            elif (c - o) <= -std_max:
#                Future_Handler.sprint = True
#                Future_Handler.sprint = False
            print(self.forward_mom,(c - o),Future_Handler.forward_sprint)
            print(self.backward_mom,(c - o),Future_Handler.backward_sprint)

#        Future_Handler.step_soft = std_mom
#        Future_Handler.step_hard = 10.0 * std_mom
#        Future_Handler.rt_soft = Future_Handler.step_soft/self.entry_gap
#        Future_Handler.rt_hard = Future_Handler.step_hard/self.entry_gap

        self.forward_close = 0
        self.backward_close = 0
        if self.forward_gap > 0.0015:
            self.forward_close = 2
        elif self.forward_gap > 0.0005:
            self.forward_close = 1
        if self.backward_gap > 0.0015:
            self.backward_close = 2
        elif self.backward_gap > 0.0005:
            self.backward_close = 1

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
=======
                if (self.bid_1 - c)/self.bid_1 > -0.001:
                    self.forward_stable_price = False
            elif (c - o)/self.ask_1 < -0.001:
                if (self.ask_1 - c)/self.ask_1 < 0.001:
                    self.backward_stable_price = False
>>>>>>> 30b82598ed68e8fe453d9adf424c77c5d009cde1

        if Future_Handler.forward_account_from == 0:
            Future_Handler.forward_account_from = int(time.time())
        if Future_Handler.backward_account_from == 0:
            Future_Handler.backward_account_from = int(time.time())
<<<<<<< HEAD
        forward_account_book = forward_api_instance.list_futures_account_book(settle=Future_Handler.settle,_from=Future_Handler.forward_account_from)
        backward_account_book = backward_api_instance.list_futures_account_book(settle=Future_Handler.settle,_from=Future_Handler.backward_account_from)
        for item in forward_account_book:
            if Future_Handler.contract in item.text:
                Future_Handler.goods += float(item.change)
                if item.type == 'pnl':
                    if Future_Handler.forward_goods+Future_Handler.backward_goods+Future_Handler.balance_overflow < Future_Handler.surplus_endure * Future_Handler.limit_goods: 
                        Future_Handler.balance_overflow += float(item.change)
                    else:
                        Future_Handler.balance_overflow += float(item.change) * Future_Handler.balance_rt
        for item in backward_account_book:
            if Future_Handler.contract in item.text:
                Future_Handler.goods += float(item.change)
                if item.type == 'pnl':
                    if Future_Handler.forward_goods+Future_Handler.backward_goods+Future_Handler.balance_overflow < Future_Handler.surplus_endure * Future_Handler.limit_goods:
                        Future_Handler.balance_overflow += float(item.change)
                    else:
                        Future_Handler.balance_overflow += float(item.change) * Future_Handler.balance_rt
=======
        forward_account_book = forward_api_instance.list_futures_account_book(settle=Future_Handler.settle,_from=Future_Handler.forward_account_from,type='pnl')
        backward_account_book = backward_api_instance.list_futures_account_book(settle=Future_Handler.settle,_from=Future_Handler.backward_account_from,type='pnl')
        for item in forward_account_book:
            if Future_Handler.contract in item.text:
                if float(item.change) > 0.0:
                    Future_Handler.goods_w += float(item.change) * Future_Handler.balance_rt
                else:
                    Future_Handler.goods_w += float(item.change)
        for item in backward_account_book:
            if Future_Handler.contract in item.text:
                if float(item.change) > 0.0:
                    Future_Handler.goods_w += float(item.change) * Future_Handler.balance_rt
                else:
                    Future_Handler.goods_w += float(item.change)
>>>>>>> 30b82598ed68e8fe453d9adf424c77c5d009cde1
        if len(forward_account_book) > 0:
            Future_Handler.forward_account_from = int(forward_account_book[0]._time) + 1
        if len(backward_account_book) > 0:
            Future_Handler.backward_account_from = int(backward_account_book[0]._time) + 1

<<<<<<< HEAD
        self.forward_reap = False
        self.backward_reap = False
        self.forward_sow = False
        self.backward_sow = False
        if self.forward_mom:
            if not Future_Handler.forward_sprint:
                self.forward_sow = True
            if self.backward_close > 0:
                self.backward_reap = True
        elif self.backward_mom:
            if not Future_Handler.backward_sprint:
                self.backward_sow = True
            if self.forward_close > 0:
                self.forward_reap = True

        self.forward_gap_balance = False
        self.backward_gap_balance = False
        if self.forward_reap and self.forward_stable_price:
            self.forward_gap_balance = True
            self.forward_balance_size = - self.forward_position_size
        elif self.backward_reap and self.backward_stable_price:
            self.backward_gap_balance = True
            self.backward_balance_size = - self.backward_position_size

        self.forward_catch = False
        self.backward_catch = False
        if self.forward_sow and self.backward_stable_price:
            self.forward_catch = True
            self.forward_catch_size = self.limit_size - self.forward_position_size
        elif self.backward_sow and self.forward_stable_price:
            self.backward_catch = True
            self.backward_catch_size = -self.limit_size - self.backward_position_size

        if self.forward_gap_balance:
            if self.forward_close == 2:
                self.forward_tif = 'gtc'
            elif self.forward_close == 1:
                self.forward_tif = 'poc'
        elif self.backward_gap_balance:
            if self.backward_close == 2:
                self.backward_tif = 'gtc'
            elif self.backward_close == 1:
                self.backward_tif = 'poc'
    
        if self.backward_band_clear and (self.backward_band_price - self.ask_1)/self.backward_band_price >= Future_Handler.std_sprint:
            Future_Handler.forward_sprint = False
            Future_Handler.backward_sprint = True
        elif self.forward_band_clear and (self.bid_1 - self.forward_band_price)/self.forward_band_price >= Future_Handler.std_sprint:
            Future_Handler.backward_sprint = False
            Future_Handler.forward_sprint = True

        if self.forward_mom:
            if not self.forward_band_clear:
                self.forward_band_price = self.ask_1
                self.forward_band_clear = True
            self.backward_band_clear = False
        elif self.backward_mom:
            if not self.backward_band_clear:
                self.backward_band_price = self.bid_1
                self.backward_band_clear = True
            self.forward_band_clear = False
=======
        Future_Handler.balance_overflow = 1.0 * Future_Handler.goods_w

        if self.forward_entry_price == 0:
            Future_Handler.forward_goods = 0.0
        else:
            Future_Handler.forward_goods = float(self.forward_positions._value)*(self.ask_1-self.forward_entry_price)/self.forward_entry_price
        if self.backward_entry_price == 0:
            Future_Handler.backward_goods = 0.0
        else:
            Future_Handler.backward_goods = float(self.backward_positions._value)*(self.backward_entry_price-self.bid_1)/self.backward_entry_price
           
        if Future_Handler.forward_goods + Future_Handler.backward_goods + Future_Handler.goods >= Future_Handler.surplus*Future_Handler.limit_size:
            self.abandon = True
        else:
            self.abandon = False

        self.reap = False

        if Future_Handler.forward_goods + Future_Handler.backward_goods >= Future_Handler.goods_w and Future_Handler.goods_w <= Future_Handler.surplus_bottom*Future_Handler.limit_size:
            self.reap = True

        if Future_Handler.predict == 'forward':
            retreat = (Future_Handler.start_point - self.bid_1)/(Future_Handler.start_point - Future_Handler.end_point)
        elif Future_Handler.predict == 'backward':
            retreat = (Future_Handler.start_point - self.ask_1)/(Future_Handler.start_point - Future_Handler.end_point)
        if retreat > 0.0 and Future_Handler.retreat < Future_Handler.retreat_endure:
            self.reap = True

        if Future_Handler.predict == 'forward' and self.bid_1 >= self.peak:
            self.reap = True
            Future_Handler.predict = 'backward'
        elif Future_Handler.predict == 'backward' and self.ask_1 <= self.bottom:
            self.reap = True
            Future_Handler.predict = 'forward'

        self.sow = False
        if Future_Handler.predict == 'forward' and self.forward_position_size < Future_Handler.limit_size and self.bid_1 < Future_Handler.sow_endure:
            if not self.reap:
                self.sow = True
        if Future_Handler.predict == 'backward' and -self.forward_position_size < Future_Handler.limit_size and self.ask_1 > Future_Handler.sow_endure:
            if not self.reap:
                self.sow = True

        if self.forward_position_size == 0 and self.backward_position_size == 0:
            if self.bid_1 < Future_Handler.sow_endure:
                Future_Handler.predict = 'forward'
                self.sow = True
            elif self.ask_1 > Future_Handler.sow_endure:
                Future_Handler.predict = 'backward'
                self.sow = True

        self.forward_gap_balance = False
        self.backward_gap_balance = False
        if self.predict == 'forward':
            if self.abandon:
                if self.backward_position_size < 0 and self.backward_stable_price:
                    self.backward_gap_balance = True
            if self.reap:
                if self.forward_position_size > 0 and self.forward_stable_price:
                    self.forward_gap_balance = True
        elif self.predict = 'backward':
            if self.abandon:
                if self.forward_position_size > 0 and self.forward_stable_price:
                    self.forward_gap_balance = True
            if self.reap:
                if self.backward_position_size < 0 and self.backward_stable_price:
                    self.backward_gap_balance = True

        self.forward_catch = False
        self.backward_catch = False
        if self.predict == 'forward':
            if self.sow and self.backward_stable_price:
                self.forward_catch_size = self.limit_size - self.forward_position_size
        elif self.predict == 'backward':
            if self.sow and self.forward_stable_price:
                self.backward_catch_size = -self.limit_size - self.backward_position_size
>>>>>>> 30b82598ed68e8fe453d9adf424c77c5d009cde1

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
                if not self.forward_catch or self.forward_position_size >= self.forward_limit:
                    forward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
                elif self.forward_catch and self.forward_catch_size <= 0:
                    forward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
                elif self.bid_1 > order_price:
                    forward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
            elif order_size < 0:
                if self.forward_gap_balance:
<<<<<<< HEAD
                    if (order_price > self.ask_1 and self.forward_tif=='poc') or (order_price > self.bid_1 and self.forward_tif=='gtc') or self.forward_balance_size >= 0:
=======
                    if order_price > self.ask_1 or self.forward_balance_size >= 0:
>>>>>>> 30b82598ed68e8fe453d9adf424c77c5d009cde1
                        forward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
                else:
                    forward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
        if not self.forward_increase_clear:
            if self.forward_position_size < self.forward_limit:
                if self.forward_catch and self.forward_catch_size > 0:
<<<<<<< HEAD
                    forward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size = self.forward_catch_size, price = self.ask_1,tif='gtc'))
        if not self.forward_reduce_clear and self.forward_gap_balance:
            if self.forward_position_size > 0:
                if self.forward_balance_size < 0:
                    if self.forward_tif == 'poc':
                        forward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size=self.forward_balance_size,price = self.ask_1,tif='poc'))
                    elif self.forward_tif == 'gtc':
                        forward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size=self.forward_balance_size,price = self.bid_1,tif='gtc'))
                        
=======
                    forward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size = self.forward_catch_size, price = self.bid_1,tif='poc'))
        if not self.forward_reduce_clear and self.forward_gap_balance:
            if self.forward_position_size > 0:
                if self.forward_balance_size < 0:
                    forward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size=self.forward_balance_size,price = self.ask_1,tif='poc'))

>>>>>>> 30b82598ed68e8fe453d9adf424c77c5d009cde1
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
                if not self.backward_catch or abs(self.backward_position_size) >= self.backward_limit:
                    backward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
                elif self.backward_catch and self.backward_catch_size >= 0:
                    backward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
                elif self.ask_1 < order_price:
                    backward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
            elif order_size > 0:
                if self.backward_gap_balance:
<<<<<<< HEAD
                    if (order_price < self.bid_1 and self.backward_tif=='poc') or (order_price < self.ask_1 and self.backward_tif=='gtc') or self.backward_balance_size <= 0:
=======
                    if order_price < self.bid_1 or self.backward_balance_size <= 0:
>>>>>>> 30b82598ed68e8fe453d9adf424c77c5d009cde1
                        backward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
                else:
                    backward_api_instance.cancel_futures_order(settle=Future_Handler.settle,order_id=order_id)
        if not self.backward_increase_clear:
            if abs(self.backward_position_size) < self.backward_limit:
                if self.backward_catch and self.backward_catch_size < 0:
<<<<<<< HEAD
                    backward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size = self.backward_catch_size, price = self.bid_1,tif='gtc'))
        if not self.backward_reduce_clear and self.backward_gap_balance:
            if self.backward_position_size < 0:
                if self.backward_balance_size > 0:
                    if self.backward_tif == 'poc':
                        backward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size=self.backward_balance_size,price = self.bid_1,tif='poc'))
                    elif self.backward_tif == 'gtc':
                        backward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size=self.backward_balance_size,price = self.ask_1,tif='gtc'))
=======
                    backward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size = self.backward_catch_size, price = self.ask_1,tif='poc'))
        if not self.backward_reduce_clear and self.backward_gap_balance:
            if self.backward_position_size < 0:
                if self.backward_balance_size > 0:
                    backward_api_instance.create_futures_order(settle=Future_Handler.settle,futures_order=FuturesOrder(contract=Future_Handler.contract,size=self.backward_balance_size,price = self.bid_1,tif='poc'))
>>>>>>> 30b82598ed68e8fe453d9adf424c77c5d009cde1

        if self.forward_liq_flag:
            forward_api_instance.cancel_price_triggered_order_list(contract=Future_Handler.contract,settle=Future_Handler.settle)
            if self.forward_liq_price > 0:
<<<<<<< HEAD
                forward_api_instance.create_price_triggered_order(settle=Future_Handler.settle,futures_price_triggered_order=FuturesPriceTriggeredOrder(initial=FuturesInitialOrder(contract=Future_Handler.contract,size=0,price=str(0),close=True,tif='ioc',text='api'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=2,price=str(round(self.forward_liq_price*(1.0+0.1*1.0/self.forward_leverage),Future_Handler.quanto)),expiration=2592000)))
=======
                forward_api_instance.create_price_triggered_order(settle=Future_Handler.settle,futures_price_triggered_order=FuturesPriceTriggeredOrder(initial=FuturesInitialOrder(contract=Future_Handler.contract,size=0,price=str(0),close=True,tif='ioc',text='api'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=2,price=str(round(self.forward_liq_price*(1.0+0.1*1.0/self.forward_leverage),Future_Handler.quanto)),expiration=2015360)))
>>>>>>> 30b82598ed68e8fe453d9adf424c77c5d009cde1
                Future_Handler.forward_trigger_liq = self.forward_liq_price*(1.0+0.1*1.0/self.forward_leverage)
        if self.backward_liq_flag:
            backward_api_instance.cancel_price_triggered_order_list(contract=Future_Handler.contract,settle=Future_Handler.settle)
            if self.backward_liq_price > 0:
<<<<<<< HEAD
                backward_api_instance.create_price_triggered_order(settle=Future_Handler.settle,futures_price_triggered_order=FuturesPriceTriggeredOrder(initial=FuturesInitialOrder(contract=Future_Handler.contract,size=0,price=str(0),close=True,tif='ioc',text='api'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=1,price=str(round(self.backward_liq_price*(1.0-0.1*1.0/self.backward_leverage),Future_Handler.quanto)),expiration=2592000)))
=======
                backward_api_instance.create_price_triggered_order(settle=Future_Handler.settle,futures_price_triggered_order=FuturesPriceTriggeredOrder(initial=FuturesInitialOrder(contract=Future_Handler.contract,size=0,price=str(0),close=True,tif='ioc',text='api'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=1,price=str(round(self.backward_liq_price*(1.0-0.1*1.0/self.backward_leverage),Future_Handler.quanto)),expiration=2015360)))
>>>>>>> 30b82598ed68e8fe453d9adf424c77c5d009cde1
                Future_Handler.backward_trigger_liq = self.backward_liq_price*(1.0-0.1*1.0/self.backward_leverage)

