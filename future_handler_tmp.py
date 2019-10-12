# -*- coding: utf-8 -*-

from __future__ import print_function
import requests
import time
import gate_api
from gate_api import FuturesOrder
from gate_api.rest import ApiException
from conf import *

class Future_Handler(object):
    def __init__(self,contract = '',contract_params = {}):
	self.contract = contract
        positions = api_instance.get_position(contract=self.contract)
        self.position_level = contract_params['position_level']
        self.gap_level = contract_params['gap_level']
        self.position_size = positions._size
        self.tap = contract_params['tap']
        self.gap = None
        self.limit_gap = contract_params['limit_gap']
        self.minor_position = None
        self.mayor_position = None
        self.leverage = contract_params['leverage']
        self.size_inc = contract_params['size_inc']
        self.follow = contract_params['follow']
        self.balance = contract_params['balance']

    def get_position(self,balance_signal):
        orders = api_instance.list_futures_orders(contract=self.contract,status='open',async_req=True)
        positions = api_instance.get_position(contract=self.contract,async_req=True)
        book = api_instance.list_futures_order_book(contract=self.contract,async_req=True)
        orders = orders.get()
        positions = positions.get()
        book = book.get()
        entry_price = float(positions._entry_price)
        mark_price = float(positions._mark_price)
        liq_price = float(positions._liq_price)
        position_size = positions._size
	self.position_size = position_size
	if position_size == 0:
		api_instance.update_position_leverage(contract=self.contract,leverage = self.leverage) 
        ask_1 = float(book._asks[0]._p)
        bid_1 = float(book._bids[0]._p)
        if position_size > 0 and entry_price > 0:
            gap = (entry_price - ask_1)/entry_price
        elif position_size < 0 and entry_price > 0:
            gap = (bid_1 - entry_price)/entry_price
        else:
            gap = 0.0
        duo_clear = False
        kong_clear = False
        bias = 1.0/self.leverage*0.2
        if abs((mark_price - ask_1)/mark_price) > bias or abs((mark_price - bid_1)/mark_price) > bias:
            return
        for order in orders:
            order_price = float(order._price)
            order_size = order._size
            order_id = order._id
            if order_size < 0:
                kong_clear = True
            elif order_size > 0:
                duo_clear = True
            if abs(position_size) < self.minor_position * self.leverage and not balance_signal:
                if position_size < 0:
                    if order_size < 0:
                        if (order_price - ask_1) / ask_1 > self.follow:
                            api_instance.cancel_futures_order(order_id)
                            api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -self.tap * self.leverage, price = ask_1,tif='poc'))
                    elif order_size > 0:
                        if bid_1 > entry_price:
                            api_instance.cancel_futures_order(order_id)
                        elif bid_1 < entry_price and (bid_1 - order_price) / bid_1 > self.balance:
                            api_instance.cancel_futures_order(order_id)
                            api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -position_size, price = bid_1,tif='poc'))
                elif position_size > 0:
                    if order_size > 0:
                        if (bid_1 - order_price) / bid_1 > self.follow:
                            api_instance.cancel_futures_order(order_id)
                            api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = self.tap * self.leverage, price = bid_1,tif='poc'))
                    elif order_size < 0:
                        if ask_1 < entry_price:
                            api_instance.cancel_futures_order(order_id)
                        elif ask_1 > entry_price and (order_price - ask_1) / ask_1 > self.balance:
                            api_instance.cancel_futures_order(order_id)
                            api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -position_size, price = ask_1,tif='poc'))
                elif position_size == 0:
                    if order_size > 0:
                        if (bid_1 - order_price) / bid_1 > self.follow:
                            api_instance.cancel_futures_order(order_id)
                            api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = self.tap * self.leverage, price = bid_1,tif='poc'))
                    elif order_size < 0:
                        if (order_price - ask_1) / ask_1 > self.follow:
                            api_instance.cancel_futures_order(order_id)
                            api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -self.tap * self.leverage, price = ask_1,tif='poc'))
            elif abs(position_size) < self.mayor_position * self.leverage and not balance_signal:
                if abs(gap) >= self.gap and abs(gap) < self.limit_gap and abs(position_size) * self.size_inc <= self.mayor_position * self.leverage:
                    if position_size < 0:
                        if order_size < 0:
                            if order_price > ask_1:
                                api_instance.cancel_futures_order(order_id)
                                api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = position_size * self.size_inc, price = ask_1,tif='poc'))
                        elif order_size > 0:
                            if bid_1 < entry_price and (bid_1 - order_price) / bid_1 > self.balance:
                                api_instance.cancel_futures_order(order_id)
                                api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -position_size, price = bid_1,tif='poc'))
                            elif bid_1 > entry_price:
                                api_instance.cancel_futures_order(order_id)
                    elif position_size > 0:
                        if order_size > 0:
                            if order_price < bid_1:
                                api_instance.cancel_futures_order(order_id)
                                api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = position_size * self.size_inc, price = bid_1,tif='poc'))
                        elif order_size < 0:
                            if ask_1 > entry_price and (order_price - ask_1) / ask_1 > self.balance:
                                api_instance.cancel_futures_order(order_id)
                                api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -position_size, price = ask_1,tif='poc'))
                            elif ask_1 < entry_price:
                                api_instance.cancel_futures_order(order_id)
                elif abs(gap) < self.gap:
                    if position_size < 0:
                        if order_size > 0:
                            if bid_1 < entry_price and (bid_1 - order_price) / bid_1 > self.balance:
                                api_instance.cancel_futures_order(order_id)
                                api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -position_size, price = bid_1,tif='poc'))
                            elif bid_1 > entry_price:
                                api_instance.cancel_futures_order(order_id)
                    elif position_size > 0:
                        if order_size < 0:
                            if ask_1 > entry_price and (order_price - ask_1) / ask_1 > self.balance:
                                api_instance.cancel_futures_order(order_id)
                                api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -position_size, price = ask_1,tif='poc'))
                            elif ask_1 < entry_price:
                                api_instance.cancel_futures_order(order_id)
        if not duo_clear:
            if position_size < 0:
                if bid_1 < entry_price:
                    api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -position_size, price = bid_1,tif='poc'))
            elif position_size > 0:
                if abs(position_size) < self.minor_position * self.leverage and not balance_signal:
                    api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = self.tap * self.leverage, price = bid_1,tif='poc'))
                elif abs(position_size) < self.mayor_position * self.leverage and not balance_signal:
                    if abs(gap) >= self.gap and abs(gap) < self.limit_gap and abs(position_size) * self.size_inc <= self.mayor_position * self.leverage:
                        api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = position_size * self.size_inc, price = bid_1,tif='poc'))
            elif position_size == 0:
                api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = self.tap * self.leverage, price = bid_1,tif='poc'))
        if not kong_clear:
            if position_size > 0:
                if ask_1 > entry_price:
                    api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -position_size, price = ask_1,tif='poc'))
            elif position_size < 0:
                if abs(position_size) < self.minor_position * self.leverage and not balance_signal:
                    api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -self.tap * self.leverage, price = ask_1,tif='poc'))
                elif abs(position_size) < self.mayor_position * self.leverage and not balance_signal:
                    if abs(gap) >= self.gap and abs(gap) < self.limit_gap and abs(position_size) * self.size_inc <= self.mayor_position * self.leverage:
                        api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = position_size * self.size_inc, price = ask_1,tif='poc'))
            elif position_size == 0:
                api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -self.tap * self.leverage, price = ask_1,tif='poc'))

    def cancel_position(self):
	orders = api_instance.list_futures_orders(contract=self.contract,status='open',async_req=True)
	positions = api_instance.get_position(contract=self.contract,async_req=True)
        book = api_instance.list_futures_order_book(contract=self.contract,async_req=True)
        orders = orders.get()
        positions = positions.get()
        book = book.get()
        entry_price = float(positions._entry_price)
        position_size = positions._size
        ask_1 = float(book._asks[0]._p)
        bid_1 = float(book._bids[0]._p)
        if position_size > 0 and entry_price > 0:
            gap = (entry_price - ask_1)/entry_price
        elif position_size < 0 and entry_price > 0:
            gap = (bid_1 - entry_price)/entry_price
        kong_clear = False
        duo_clear = False
        for order in orders:
	    order_price = float(order._price)
	    order_size = order._size
	    order_id = order._id
	    if order_size < 0:
	        kong_clear = True
	    elif order_size > 0:
	        duo_clear = True
	    if position_size > 0:
	        if order_size > 0 and gap <= self.minor_gap:
		    api_instance.cancel_futures_order(order_id)
	        elif order_size < 0:
	            if ask_1 < entry_price or order_price > ask_1:
		        api_instance.cancel_futures_order(order_id)
		    elif ask_1 >= entry_price and order_price > ask_1:
                        api_instance.cancel_futures_order(order_id)
		        api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -position_size, price = ask_1,tif='poc'))
	    elif position_size < 0:
	        if order_size < 0 and gap < self.minor_gap:
		    api_instance.cancel_futures_order(order_id)
	        elif order_size > 0:
		    if bid_1 > entry_price or order_price < bid_1:
		        api_instance.cancel_futures_order(order_id)
		    elif bid_1 <= entry_price and order_price < bid_1:
                        api_instance.cancel_futures_order(order_id)
		        api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -position_size, price = bid_1,tif='poc'))	
        if not duo_clear:
	    if position_size < 0:
	        if bid_1 <= entry_price:
		    api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -position_size, price = bid_1,tif='poc'))
        if not kong_clear:
	    if position_size > 0:
	        if ask_1 >= entry_price:
	            api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -position_size, price = ask_1,tif='poc'))		
