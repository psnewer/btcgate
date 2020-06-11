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
    contract = None
    settle = None
    tap = None
    level = None
    limit_position = None
    limit_delta = None
    limit_size = None
    balance_overflow = None
    forward_account_from = None
    backward_account_from = None
    forward_trigger_liq = -1
    backward_trigger_liq = -1
    quanto = None
    retreat = False
    balance_rt = 1.0
    goods = 0.117272087275
    forward_goods = 0.0
    backward_goods = 0.0
    t = 0.0
    _T = None
    T_std = None

    def __init__(self,contract = '',contract_params = {}):
	Future_Handler.contract = contract
        Future_Handler.settle = contract_params['settle']
        Future_Handler.tap = contract_params['tap']
        Future_Handler.level = contract_params['level']
        Future_Handler.limit_position = contract_params['limit_position']
        Future_Handler.limit_delta = contract_params['limit_delta']
        Future_Handler.limit_size = contract_params['limit_size']
        Future_Handler.balance_overflow = 0.0
        Future_Handler.forward_account_from = 0
        Future_Handler.backward_account_from = 0
        Future_Handler.forward_trigger_liq = -1
        Future_Handler.backward_trigger_liq = -1
        Future_Handler.quanto = contract_params['quanto']
        Future_Handler.catch = False
        Future_Handler.balance = False
        Future_Handler.retreat = contract_params['retreat']
        Future_Handler.balance_rt = contract_params['balance_rt']
        Future_Handler.forward_goods = 0.0
        Future_Handler.backward_goods = 0.0
        Future_Handler._S = 0.0
        Future_Handler.S_ = 0.0
        Future_Handler.S_up = 0.0
        Future_Handler.S_dn = 0.0
        Future_Handler.t_up = 0.0
        Future_Handler.t_dn = 0.0
        Future_Handler.t_head = 0.0
        Future_Handler.t_tail = 0.0

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
            self._T = abs(float(self.backward_position_size) / float(self.forward_position_size))
        elif self.backward_gap < 0.0 and self.forward_gap >= 0.0:
            self._T = abs(float(self.forward_position_size) / float(self.backward_position_size))
        elif self.forward_gap < 0.0 and self.backward_gap < 0.0:
            if self.forward_gap > self.backward_gap:
                self._T = abs(float(self.forward_position_size) / float(self.backward_position_size))
            else:
                self._T = abs(float(self.backward_position_size) / float(self.forward_position_size))
        elif self.forward_gap >= 0.0 and self.backward_gap >= 0.0:
            self._T = 0.61

        if self.forward_gap < 0.0 and self.backward_gap >= 0.0:
            Future_Handler._S = -Future_Handler.balance_overflow/Future_Handler.forward_goods
            Future_Handler.S_ = -Future_Handler.backward_goods/Future_Handler.forward_goods
        elif self.backward_gap < 0.0 and self.forward_gap >= 0.0:
            Future_Handler._S = -Future_Handler.balance_overflow/Future_Handler.backward_goods
            Future_Handler.S_ = -Future_Handler.forward_goods/Future_Handler.backward_goods
        elif self.forward_gap < 0.0 and self.backward_gap < 0.0:
            Future_Handler._S = 0.0
            Future_Handler.S_ = 0.0

    def put_position(self):
        pass
