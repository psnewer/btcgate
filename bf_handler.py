# -*- coding: utf-8 -*-

from __future__ import print_function
import requests
import time
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
        self.tap = contract_params['tap']
        self.level = contract_params['level']
        self.limit_position = contract_params['limit_position']
        self.limit_delta = contract_params['limit_delta']
        self.limit_gap = contract_params['limit_gap']
        self.follow_gap = contract_params['follow_gap']
        self.balance_gap = contract_params['balance_gap']
        self.profit_gap = contract_params['profit_gap']
        self.mark_total_flag = False
        self.balance_overflow = 0
        self.N_contract = 2
        self.forward_trigger_liq = -1
        self.backward_trigger_liq = -1
        self.quanto = contract_params['quanto']
        self.chase = contract_params['chase']
        self.chase_gap = contract_params['chase_gap']
        self.chase_margin = contract_params['chase_margin']
        self.settle = contract_params['settle']
        self.forward_chase = False
        self.backward_chase = False

    def get_flag(self):
        forward_accounts = forward_api_instance.list_futures_accounts(settle=self.settle,async_req=True)
        forward_positions = forward_api_instance.get_position(contract=self.contract,settle=self.settle,async_req=True)
        backward_accounts = backward_api_instance.list_futures_accounts(settle=self.settle,async_req=True)
        backward_positions = backward_api_instance.get_position(contract=self.contract,settle=self.settle,async_req=True)
        book = backward_api_instance.list_futures_order_book(contract=self.contract,settle=self.settle,async_req=True)
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

        if self.forward_position_margin >= self.limit_position:
            self.forward_position_alarm = True
        else:
            self.forward_position_alarm = False
        if self.backward_position_margin >= self.limit_position:
            self.backward_position_alarm = True
        else:
            self.backward_position_alarm = False

        if self.forward_position_size > 0 and self.forward_entry_price > 0:
            self.forward_gap = abs(self.forward_entry_price - self.ask_1)/self.forward_entry_price
        elif self.forward_position_size < 0 and self.forward_entry_price > 0:
            self.forward_gap = abs(self.bid_1 - self.forward_entry_price)/self.forward_entry_price
        else:
            self.forward_gap = 0.0
        if self.forward_gap > self.limit_gap:
            self.forward_gap_alarm = True
        else:
            self.forward_gap_alarm = False
        if self.forward_gap > self.follow_gap:
            self.forward_follow_alarm = True
        else:
            self.forward_follow_alarm = False
        if self.backward_position_size > 0 and self.backward_entry_price > 0:
            self.backward_gap = abs(self.backward_entry_price - self.ask_1)/self.backward_entry_price 
        elif self.backward_position_size < 0 and self.backward_entry_price > 0:
            self.backward_gap = abs(self.bid_1 - self.backward_entry_price)/self.backward_entry_price
        else:
            self.backward_gap = 0.0
        if self.backward_gap > self.limit_gap:
            self.backward_gap_alarm = True
        else:
            self.backward_gap_alarm = False
        if self.backward_gap > self.follow_gap:
            self.backward_follow_alarm = True
        else:
            self.backward_follow_alarm = False

        self.forward_total = self.forward_accounts._total
        self.backward_total = self.backward_accounts._total
        if self.forward_follow_alarm or self.backward_follow_alarm:
            if not self.mark_total_flag:
                self.mark_total = float(self.forward_total) + float(self.backward_total)
                self.current_mark_total = self.mark_total
            else: 
                self.current_mark_total = float(self.forward_total) + float(self.backward_total)
                self.balance_overflow = self.current_mark_total - self.mark_total
            self.mark_total_flag = True
        else:
            self.mark_total_flag = False

        delta = self.forward_position_margin - self.backward_position_margin
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
            if self.forward_gap < float(gap_level):
                self.forward_gap_level = self.level[gap_level]['leverage']
                if self.forward_gap_level != self.forward_leverage:
                    self.forward_leverage_alarm = True
                else:
                    self.forward_leverage_alarm = False
                break

        for gap_level in gap_levels:
            if self.backward_gap < float(gap_level):
                self.backward_gap_level = self.level[gap_level]['leverage']
                if self.backward_gap_level != self.backward_leverage:
                    self.backward_leverage_alarm = True
                else:
                    self.backward_leverage_alarm = False
                break

        if self.chase:
            if self.forward_gap >= self.chase_gap and self.forward_position_margin < self.chase_margin:
                candlesticks=forward_api_instance.list_futures_candlesticks(contract=self.contract,settle=self.settle,limit=1,interval='5m')
                if len(candlesticks) > 0:
                    h = float(candlesticks[0]._h)
                    l = float(candlesticks[0]._l)
                    if abs(h - l)/self.mark_price < 0.005:
                        self.forward_chase = True
                    else:
                        self.forward_chase = False
                else:
                    self.forward_chase = False
            else:
                self.forward_chase = False
            if self.backward_gap >= self.chase_gap and self.backward_position_margin < self.chase_margin:
                candlesticks=backward_api_instance.list_futures_candlesticks(contract=self.contract,settle=self.settle,limit=1,interval='5m')
                if len(candlesticks) > 0:
                    h = float(candlesticks[0]._h)
                    l = float(candlesticks[0]._l)
                    if abs(h - l)/self.mark_price < 0.005:
                        self.backward_chase = True
                    else:
                        self.backward_chase = False
                else:
                    self.backward_chase = False
            else:
                self.backward_chase = False
        else:
            self.forward_chase = False
            self.backward_chase = False

        if self.forward_position_size == 0:
            self.forward_trigger_liq = 0
        if self.backward_position_size == 0:
            self.backward_trigger_liq = 0
        if self.forward_position_size > 0 and (self.forward_trigger_liq < 0 or (self.forward_trigger_liq <= (1.0+1.0/self.forward_leverage*0.05)*self.forward_liq_price or self.forward_trigger_liq >= (1.0+1.0/self.forward_leverage*0.2)*self.forward_liq_price)):
            self.forward_liq_flag = True
        else:
            self.forward_liq_flag = False
        if self.backward_position_size < 0 and (self.backward_trigger_liq < 0 or (self.backward_trigger_liq <= (1.0-1.0/self.backward_leverage*0.2)*self.backward_liq_price or self.backward_trigger_liq >= (1.0-1.0/self.backward_leverage*0.05)*self.backward_liq_price)):
            self.backward_liq_flag = True
        else:
            self.backward_liq_flag = False

    def put_position(self):
        if self.forward_leverage_alarm:
            if self.forward_leverage != self.forward_gap_level:
                forward_api_instance.update_position_leverage(contract=self.contract,settle=self.settle,leverage = self.forward_gap_level)
                self.forward_leverage = self.forward_gap_level
        if self.backward_leverage_alarm:
            if self.backward_leverage != self.backward_gap_level:
                backward_api_instance.update_position_leverage(contract=self.contract,settle=self.settle,leverage = self.backward_gap_level)
                self.backward_leverage = self.backward_gap_level

        self.forward_orders = forward_api_instance.list_futures_orders(contract=self.contract,settle=self.settle,status='open')
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
                if (self.forward_position_alarm or self.forward_delta_alarm or self.forward_follow_alarm or self.forward_gap_alarm) and not self.forward_chase:
                    forward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
                else:
                    if self.bid_1 > order_price:
                        forward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
                        forward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size = self.tap * self.forward_leverage, price = self.bid_1,tif='poc'))
            elif order_size < 0:
                if self.ask_1 < self.forward_entry_price:
                    if self.forward_gap_alarm:
                        forward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
                    elif self.forward_follow_alarm:
                        if self.balance_overflow > 10.0:
                            un_pnl = float(self.forward_positions._unrealised_pnl)
                            _size = min(int(self.forward_position_size * (self.balance_overflow/abs(un_pnl)/self.N_contract)),self.forward_position_size)
                            if _size > 0 and order_price > self.ask_1:
                                forward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
                                forward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size = -_size, price = self.ask_1,tif='poc'))
                    elif order_price >= self.forward_entry_price and self.ask_1 < self.forward_entry_price*(1 - self.balance_gap):
                        forward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
                elif self.ask_1 >= self.forward_entry_price and order_price > self.ask_1:
                    forward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
                    if self.forward_position_size > 0:
                        forward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size=-self.forward_position_size,reduce_only=True, price = self.ask_1,tif='poc'))
        if not forward_increase_clear:
            if (not self.forward_position_alarm and not self.forward_delta_alarm and not self.forward_follow_alarm and not self.forward_gap_alarm) or self.forward_chase:
                forward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size = self.tap * self.forward_leverage, price = self.bid_1,tif='poc'))
        if not forward_reduce_clear:
            if self.ask_1 >= self.forward_entry_price and self.forward_position_size > 0:
                forward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size=-self.forward_position_size,reduce_only=True, price = self.ask_1,tif='poc'))
            elif self.ask_1 >= self.forward_entry_price*(1 - self.balance_gap) and self.forward_position_size > 0:
                forward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size=-self.forward_position_size,reduce_only=True, price = self.forward_entry_price*(1 + self.profit_gap), tif='poc'))
            elif not self.forward_gap_alarm and self.forward_follow_alarm and self.ask_1 < self.forward_entry_price:
                if self.balance_overflow > 10.0:
                    un_pnl = float(self.forward_positions._unrealised_pnl)
                    _size = min(int(self.forward_position_size * (self.balance_overflow/abs(un_pnl)/self.N_contract)),self.forward_position_size)
                    if _size > 0:
                        forward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size = -_size, price = self.ask_1,tif='poc'))


        self.backward_orders = backward_api_instance.list_futures_orders(contract=self.contract,settle=self.settle,status='open')
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
                if (self.backward_position_alarm or self.backward_delta_alarm or self.backward_follow_alarm or self.backward_gap_alarm) and not self.backward_chase:
                    backward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
                else:
                    if self.ask_1 < order_price:
                        backward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
                        backward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size = -self.tap * self.backward_leverage, price = self.ask_1,tif='poc'))
            elif order_size > 0:
                if self.bid_1 > self.backward_entry_price:
                    if self.backward_gap_alarm:
                        backward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
                    elif self.backward_follow_alarm:
                        if self.balance_overflow > 10.0:
                            un_pnl = float(self.backward_positions._unrealised_pnl)
                            _size = max(int(self.backward_position_size * (self.balance_overflow/abs(un_pnl)/self.N_contract)),self.backward_position_size)
                            if order_price < self.bid_1 and _size < 0:
                                backward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
                                backward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size = -_size, price = self.bid_1,tif='poc'))
                    elif order_price <= self.backward_entry_price and self.bid_1 > self.backward_entry_price*(1 + self.balance_gap):
                        backward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
                elif self.bid_1 <= self.backward_entry_price and order_price < self.bid_1:
                    backward_api_instance.cancel_futures_order(settle=self.settle,order_id=order_id)
                    if self.backward_position_size < 0:
                        backward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size=-self.backward_position_size,reduce_only=True, price = self.bid_1,tif='poc'))
        if not backward_increase_clear:
            if (not self.backward_position_alarm and not self.backward_delta_alarm and not self.backward_follow_alarm and not self.backward_gap_alarm) or self.backward_chase:
                backward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size = -self.tap * self.backward_leverage, price = self.ask_1,tif='poc'))
        if not backward_reduce_clear:
            if self.bid_1 <= self.backward_entry_price and self.backward_position_size < 0:
                backward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size=-self.backward_position_size,reduce_only=True, price = self.bid_1,tif='poc'))
            elif self.bid_1 <= self.backward_entry_price*(1 + self.balance_gap) and self.backward_position_size < 0:
                backward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size=-self.backward_position_size,reduce_only=True, price = self.backward_entry_price*(1 - self.profit_gap), tif='poc'))
            elif not self.backward_gap_alarm and self.backward_follow_alarm and self.bid_1 > self.backward_entry_price:
                if self.balance_overflow > 10.0:
                    un_pnl = float(self.backward_positions._unrealised_pnl)
                    _size = max(int(self.backward_position_size * (self.balance_overflow/abs(un_pnl)/self.N_contract)),self.backward_position_size)
                    if _size < 0:
                        backward_api_instance.create_futures_order(settle=self.settle,futures_order=FuturesOrder(contract=self.contract,size = -_size, price = self.bid_1,tif='poc'))

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

