# -*- coding: utf-8 -*-

from __future__ import print_function
import requests
import time
import math
import gate_api
import numpy as np
from gate_api import FuturesOrder
from gate_api import FuturesPriceTriggeredOrder
from gate_api import FuturesInitialOrder
from gate_api import FuturesPriceTrigger
from gate_api.rest import ApiException
from conf import *
from handler import *

class Handler_W(FH):
    def __init__(self):
        self.tip = 'w'

    def get_flag(self):
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
        if len(forward_account_book) > 0:
            FH.forward_account_from = int(forward_account_book[0]._time) + 1
        if len(backward_account_book) > 0:
            FH.backward_account_from = int(backward_account_book[0]._time) + 1

        self.forward_reap = False
        self.backward_reap = False
        if self.forward_gap > 0.0:
            self.forward_reap = True
        elif self.backward_gap > 0.0:
            self.backward_reap = True
        elif self.forward_gap < 0.0:
            self.forward_reap = True
        elif self.backward_gap < 0.0:
            self.backward_reap = True

        self.forward_gap_balance = False
        self.backward_gap_balance = False
        if self.forward_reap and FH.forward_stable_price:
            self.forward_gap_balance = True
            self.forward_balance_size = - FH.forward_position_size
        elif self.backward_reap and FH.backward_stable_price:
            self.backward_gap_balance = True
            self.backward_balance_size = - FH.backward_position_size
        
        self.forward_catch = False
        self.backward_catch = False

        if self.forward_gap_balance:
            self.forward_tif = 'poc'
        elif self.backward_gap_balance:
            self.backward_tif = 'poc'
    
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
                if not self.forward_catch or FH.forward_position_size >= FH.forward_limit:
                    forward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
                elif self.forward_catch and self.forward_catch_size <= 0:
                    forward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
                elif FH.bid_1 > order_price:
                    forward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
            elif order_size < 0:
                if self.forward_gap_balance:
                    if (order_price > FH.ask_1 and self.forward_tif=='poc') or (order_price > FH.bid_1 and self.forward_tif=='ioc') or self.forward_balance_size >= 0:
                        forward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
                else:
                    forward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
        if not self.forward_increase_clear:
            if FH.forward_position_size < FH.forward_limit:
                if self.forward_catch and self.forward_catch_size > 0:
                    forward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size = self.forward_catch_size, price = FH.bid_1,tif='poc'))
        if not self.forward_reduce_clear and self.forward_gap_balance:
            if FH.forward_position_size > 0:
                if self.forward_balance_size < 0:
                    if self.forward_tif == 'poc':
                        forward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size=self.forward_balance_size,price = FH.ask_1,tif='poc'))
                    elif self.forward_tif == 'ioc':
                        forward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size=self.forward_balance_size,price = FH.bid_1*0.9999,tif='ioc'))
                        
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
                if not self.backward_catch or abs(FH.backward_position_size) >= FH.backward_limit:
                    backward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
                elif self.backward_catch and self.backward_catch_size >= 0:
                    backward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
                elif FH.ask_1 < order_price:
                    backward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
            elif order_size > 0:
                if self.backward_gap_balance:
                    if (order_price < FH.bid_1 and self.backward_tif=='poc') or (order_price < FH.ask_1 and self.backward_tif=='ioc') or self.backward_balance_size <= 0:
                        backward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
                else:
                    backward_api_instance.cancel_futures_order(settle=FH.settle,order_id=order_id)
        if not self.backward_increase_clear:
            if abs(FH.backward_position_size) < FH.backward_limit:
                if self.backward_catch and self.backward_catch_size < 0:
                    backward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size = self.backward_catch_size, price = FH.ask_1,tif='poc'))
        if not self.backward_reduce_clear and self.backward_gap_balance:
            if FH.backward_position_size < 0:
                if self.backward_balance_size > 0:
                    if self.backward_tif == 'poc':
                        backward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size=self.backward_balance_size,price = FH.bid_1,tif='poc'))
                    elif self.backward_tif == 'ioc':
                        backward_api_instance.create_futures_order(settle=FH.settle,futures_order=FuturesOrder(contract=FH.contract,size=self.backward_balance_size,price = FH.ask_1*1.0001,tif='ioc'))

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

