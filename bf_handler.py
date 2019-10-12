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
        self.tap = contract_params['tap']
        self.level = contract_params['level']
        self.limit_position = contract_params['limit_position']
        self.limit_delta = contract_params['limit_delta']
        self.leverage = contract_params['leverage']
        self.limit_gap = contract_params['limit_gap']
        self.follow_gap = contract_params['follow_gap']
        self.N_contract = 1
        self.forward_trigger_liq = -1
        self.backward_trigger_liq = -1

    def get_flag(self):
        forward_orders = forward_api_instance.list_futures_orders(contract=self.contract,status='open',async_req=True)
        forward_accounts = forward_api_instance.list_futures_accounts()
        forward_positions = forward_api_instance.get_position(contract=self.contract,async_req=True)
        backward_orders = backward_api_instance.list_futures_orders(contract=self.contract,status='open',async_req=True)
        backward_accounts = backward_api_instance.list_futures-accounts()
        backward_positions = backward_api_instance.get_position(contract=self.contract,async_req=True)
        book = backward_api_instance.list_futures_order_book(contract=self.contract,async_req=True)
        self.forward_orders = forward_orders.get()
        self.forward_accounts = forward_accounts.get()
        self.forward_positions = forward_positions.get()
        self.backward_orders = backward_orders.get()
        self.backward_accounts = backward_accounts.get()
        self.backward_positions = backward_positions.get()
        self.book = book.get()
        self.forward_entry_price = float(forward_positions._entry_price)
        self.backward_entry_price = float(backward_positions._entry_price)
        self.forward_liq_price = float(forward_oositions._liq_price)
        self.backward_liq_price = float(backward_positions._liq_price)
        self.forward_position_size = forward_positions._size
        self.backward_position_size = backward_positions._size
        self.forward_leverage = forward_positions._leverage
        self.backward_leverage = backward_positions._leverage
        self.mark_price = float(forward_positions._mark_price)
        self.ask_1 = float(book._asks[0]._p)
        self.bid_1 = float(book._bids[0]._p)

        if self.forward_position_size >= self.limit_position:
            self.forward_position_alarm = True
        else:
            self.forward_position_alarm = False
        if self.backward_position_size >= self.limit_position:
            self.backward_position_alarm = True
        else:
            self.backward_position_alarm = False

        if self.forward_position_size > 0 and self.forward_entry_price > 0:
            self.forward_gap = (self.forward_entry_price - self.ask_1)/self.forward_entry_price
        elif self.forward_position_size < 0 and self.forward_entry_price > 0:
            self.forward_gap = (self.bid_1 - self.forward_entry_price)/self.forward_entry_price
        else:
            self.forward_gap = 0.0
        if abs(self.forward_gap) > self.limit_gap:
            self.forward_gap_alarm = True
        else:
            self.forward_gap_alarm = False
        if abs(self.forward_gap) > self.follow_gap:
            self.forward_follow_alarm = True
        else:
            self.forward_follow_alarm = False
        if self.backward_position_size > 0 and self.backward_entry_price > 0:
            self.backward_gap = (self.backward_entry_price - self.ask_1)/self.backward_entry_price
        elif self.backward_position_size < 0 and self.backward_entry_price > 0:
            self.backward_gap = (self.bid_1 - self.backward_entry_price)/self.backward_entry_price
        else:
            self.backward_gap = 0.0
        if abs(self.backward_gap) > self.limit_gap:
            self.backward_gap_alarm = True
        else:
            self.backward_gap_alarm = False
        if abs(self.backward_gap) > self.follow_gap:
            self.backward_follow_alarm = True
        else:
            self.backward_follow_alarm = False

        self.forward_total = self.forward_accounts._total
        self.backward_total = self.backward_accounts._total
        if self.forward_gap_alarm or self.backward_gap_alarm:
            if not self.mark_total_flag:
                self.mark_total = current_mark_total
                self.mark_total = forward_total + backward_total
            else: 
                self.balance_overflow = current_mark_total - self.mark_total
            self.mark_total_flag = True
        else:
            self.mark_total_flag = False

        delta = forward_position_size - backward_position_size
        if delta >= self.limit_delta:
            self.forward_delta_alarm = True
        else:
            self.forward_delta_alarm = False

        if delta <= -self.limit_delta:
            self.backward_delta_alarm = True
        else:
            self.backward_delta_alarm = False

        for gap_level in self.level:
            if self.forward_gap < gap_level:
                self.forward_gap_level = self.level[gap_level]['leverage']
                if self.forward_gap_level != forward_leverage:
                    self.forward_leverage_alarm = True
                else:
                    self.forward_leverage_alarm = False
                break
        for gap_level in self.level:
            if self.backward_gap < gap_level:
                self.backward_gap_level = self.level[gap_level]['leverage']
                if self.backward_gap_level != backward_leverage:
                    self.backward_leverage_alarm = True
                else:
                    self.backward_leverage_alarm = False
                break

        if self.forward_position_size > 0 and (self.forward_trigger_liq < 0 or (self.forward_trigger_liq <= (1.0/self.forward_leverage*0.2+1.0)*forward_liq_price or self.forward_trigger_liq >= (1.0/self.forward_leverage*0.5+1.0)*forward_liq_price)):
            self.forward_liq_flag = True
        else:
            self.forward_liq_falg = False
        if self.backward_position_size < 0 and (self.backward_trigger_liq < 0 or (self.backward_trigger_liq <= (1.0-1.0/self.backword_leverage*0.5)*backward_liq_price or self.backward_trigger_liq >= (1.0-1.0/self.backword_leverage*0.2)*backward_liq_price)):
            self.backward_liq_flag = True
        else:
            self.backward_liq_flag = False

    def put_position(self):
        if self.forward_leverage_alarm:
            if self.forward_leverage < self.forward_gap_level:
                self.forward_api_instance.update_position_leverage(contract=self.contract,leverage = self.forward_gap_level)
        if self.backward_leverage_alarm:
            if self.backward_leverage < self.backward_gap_level:
                self.backward_api_instance.update_position_leverage(contract=self.contract,leverage = self.backward_gap_level)

        forword_increase_clear = False
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
                if forward_position_alarm or self.forward_delta_alarm or self.forward_follow_alarm or self.forward_gap_alarm:
                    forward_api_instance.cancel_futures_order(order_id)
                else:
                    if bid_1 > order_price:
                        forward_api_instance.cancel_futures_order(order_id)
                        forward_api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = self.tap * self.forward_leverage, price = bid_1,tif='poc'))
            elif order_size < 0:
                if ask_1 < forword_entry_price
                    if self.forward_gap_alarm:
                        forward_api_instance.cancel_futures_order(order_id)
                    elif not self.forward_follow_alarm:
                        if balance_overflow > 0:
                            un_pnl = self.forward_positions._unrealised_pnl
                            _size = min(int(self.forward_position_size * (balance_overflow/abs(un_pnl)/self.N_contract)),self.forward_position_size)
                            if order_size > ask_1:
                                forward_api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -_size, price = ask_1,tif='poc'))
                elif ask_1 >= forward_entry_price and order_price > ask_1:
                    forward_api_instance.cancel_futures_order(order_id)
                    forward_api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -self.forward_position_size, price = ask_1,tif='poc'))
        if not forward_increase_clear:
            if not self.forward_position_alarm and not self.forward_delta_alarm and not self.forward_follow_alarm and not self.forward_gap_alarm:
                forward_api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = self.tap * self.forward_leverage, price = bid_1,tif='poc'))
        if not forward_reduce_clear:
            if ask_1 >= self.forward_entry_price:
                forward_api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -self.forward_position_size, price = ask_1,tif='poc'))
            elif ask_1 >= self.forward_entry_price*(1 - self.balance_gap):
                forward_api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -self.forward_position_size, price = self.forward_entry_price*(1 + profit_gap), tif='poc'))
            elif not self.forward_gap_alarm and not self.forward_follow_alarm and ask_1 < self.forward_entry_price:
                if balance_overflow > 0:
                    un_pnl = self.forward_positions._unrealised_pnl
                    _size = min(int(forward_position_size * (balance_overflow/abs(un_pnl)/self.N_contract)),self.forward_position_size)
                    if _size > 0:
                        forward_api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -_size, price = ask_1,tif='poc'))


        backword_increase_clear = False
        backward_reduce_clear = False
        for order in self.backward_orders:
            order_price = float(order._price)
            order_size = order._size
            order_id = order._id
            if order_size > 0:
                backward_increase_clear = True
            elif order_size < 0:
                backward_reduce_clear = True
            if order_size > 0:
                if backward_position_alarm or self.backward_delta_alarm or self.backward_follow_alarm or self.backward_gap_alarm:
                    backward_api_instance.cancel_futures_order(order_id)
                else:
                    if bid_1 > order_price:
                        backward_api_instance.cancel_futures_order(order_id)
                        backward_api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = self.tap * self.backward_leverage, price = bid_1,tif='poc'))
            elif order_size < 0:
                if ask_1 < backword_entry_price
                    if self.backward_gap_alarm:
                        backward_api_instance.cancel_futures_order(order_id)
                    elif not self.backward_follow_alarm:
                        if balance_overflow > 0:
                            un_pnl = self.backward_positions._unrealised_pnl
                            _size = min(int(self.backward_position_size * (balance_overflow/abs(un_pnl)/self.N_contract)),self.backward_position_size)
                            if order_size > ask_1:
                                backward_api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -_size, price = ask_1,tif='poc'))
                elif ask_1 >= backward_entry_price and order_price > ask_1:
                    backward_api_instance.cancel_futures_order(order_id)
                    backward_api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -self.backward_position_size, price = ask_1,tif='poc'))
        if not backward_increase_clear:
            if not self.backward_position_alarm and not self.backward_delta_alarm and not self.backward_follow_alarm and not self.backward_gap_alarm:
                backward_api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = self.tap * self.backward_leverage, price = bid_1,tif='poc'))
        if not backward_reduce_clear:
            if ask_1 >= self.backward_entry_price:
                backward_api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -self.backward_position_size, price = ask_1,tif='poc'))
            elif ask_1 >= self.backward_entry_price*(1 - self.balance_gap):
                backward_api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -self.backward_position_size, price = self.backward_entry_price*(1 + profit_gap), tif='poc'))
            elif not self.backward_gap_alarm and not self.backward_follow_alarm and ask_1 < self.backward_entry_price:
                if balance_overflow > 0:
                    un_pnl = self.backward_positions._unrealised_pnl
                    _size = max(int(backward_position_size * (balance_overflow/abs(un_pnl)/self.N_contract)),self.backward_position_size)
                    if _size < 0:
                        backward_api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -_size, price = ask_1,tif='poc'))

        if self.forward_trigger_flag:
            if self.forward_trigger_liq != -1:
                forward_api_instance.cancel_price_triggered_order(self.forward_trigger_jian_id)
                backward_api_instance.cancel_price_triggered_order(self.backward_trigger_jia_id)
            else:
                forward_api_instance.cancel_price_triggered_order_list(contract=self.contract)
                backward_api_instance.cancel_price_triggered_order_list(contract=self.contract)
            self.forward_trigger_jian_id = forward_api_instance.create_price_triggered_order(futures_price_triggered_order(initial=FuturesInitialOrder(contract='BTC_USD',size=0,price=0,close=True,tif='ioc'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=2,price=self.forward_liq_price*(1.0+0.4*1.0/self.forward_leverage))))._id
            self.backward_trigger_jia_id = backward_api_instance.create_price_triggered_order(futures_price_triggered_order(initial=FuturesInitialOrder(contract='BTC_USD',size=0,price=0,close=True,tif='ioc'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=2,price=self.forward_liq_price*(1.0+0.4*1.0/self.forward_leverage))))._id
            self.forward_trigger_liq = self.forward_liq_price
        if self.backward_trigger_flag:
            if self.forward_trigger_liq != -1:
                forward_api_instance.cancel_price_triggered_order(self.forward_trigger_jia_id)
                backward_api_instance.cancel_price_triggered_order(self.backward_trigger_jian_id)
            else:
                forward_api_instance.cancel_price_triggered_order_list(contract=self.contract)
                backward_api_instance.cancel_price_triggered_order_list(contract=self.contract)
            forward_api_instance.cancel_price_triggered_order_list(contract='BTC_USD')
            backward_api_instance.cancel_price_triggered_order_list(contract='BTC_USD')
            self.forward_trigger_jia_id = forward_api_instance.create_price_triggered_order(futures_price_triggered_order(initial=FuturesInitialOrder(contract='BTC_USD',size=0,price=0,close=True,tif='ioc'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=1,price=backward_liq_price*(1.0-0.4*1.0/self.backward_leverage))))._id
            self.backward_trigger_jian_id = backward_api_instance.create_price_triggered_order(futures_price_triggered_order(initial=FuturesInitialOrder(contract='BTC_USD',size=0,price=0,close=True,tif='ioc'),trigger=FuturesPriceTrigger(strategy_type=0,price_type=1,rule=1,price=backward_liq_price*(1.0-0.4*1.0/self.backward_leverage))))._id
            self.backward_trigger_liq = self.backward_liq_price



    def get_position(self,follow_signal,balance_signal):
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
            if abs(position_size) < self.minor_position * self.leverage and follow_signal and not balance_signal:
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
            elif abs(position_size) < self.limit_position * self.leverage and not follow_signal and not balance_signal:
                if abs(gap) >= self.mayor_gap and abs(gap) < self.limit_gap and abs(position_size) * self.size_inc <= self.limit_position * self.leverage:
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
                elif abs(gap) < self.mayor_gap:
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
                if abs(position_size) < self.minor_position * self.leverage and follow_signal and not balance_signal:
                    api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = self.tap * self.leverage, price = bid_1,tif='poc'))
                elif abs(position_size) < self.limit_position * self.leverage and not follow_signal and not balance_signal:
                    if abs(gap) >= self.mayor_gap and abs(gap) < self.limit_gap and abs(position_size) * self.size_inc <= self.limit_position * self.leverage:
                        api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = position_size * self.size_inc, price = bid_1,tif='poc'))
            elif position_size == 0:
                api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = self.tap * self.leverage, price = bid_1,tif='poc'))
        if not kong_clear:
            if position_size > 0:
                if ask_1 > entry_price:
                    api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -position_size, price = ask_1,tif='poc'))
            elif position_size < 0:
                if abs(position_size) < self.minor_position * self.leverage and follow_signal and not balance_signal:
                    api_instance.create_futures_order(FuturesOrder(contract=self.contract,size = -self.tap * self.leverage, price = ask_1,tif='poc'))
                elif abs(position_size) < self.limit_position * self.leverage and not follow_signal and not balance_signal:
                    if abs(gap) >= self.mayor_gap and abs(gap) < self.limit_gap and abs(position_size) * self.size_inc <= self.limit_position * self.leverage:
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
