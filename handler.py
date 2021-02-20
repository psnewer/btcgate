# -*- coding: utf-8 -*-

from __future__ import print_function
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

class FH(object):
    balance_overflow = 0.111
    forward_account_from = 0
    backward_account_from = 0
    forward_trigger_liq = -1
    backward_trigger_liq = -1
    quanto = None
    goods = 0.0
    forward_goods = 0.0
    backward_goods = 0.0
    catch = False
    balance = False
    forward_sprint = False
    backward_sprint = False
    forward_band_price = -1.0
    backward_band_price = -1.0
    T_D = True
    T_limit = 0.0
    T_rt_pre = 0.0
    T_guide = 1.0
    _T = None
    T_std = 1.0
    S_up = 0.0
    S_dn = 0.0
    t_up = 0.0
    t_dn = 0.0
    S_up_t = 0.0
    S_dn_t = 0.0
    t_up_S = 0.0
    t_dn_S = 0.0
    pre_side = 'biside'

    def __init__(self,contract = '',contract_params = {}):
        FH.contract = contract
        FH.settle = contract_params['settle']
        FH.D_rt = contract_params['D_rt']
        FH.L_rt = contract_params['L_rt']
        FH.TL_rt = contract_params['TL_rt']
        FH.T_level = contract_params['T_level']
        FH.tap = contract_params['tap']
        FH.level = contract_params['level']
        FH.limit_size = contract_params['limit_size']
        FH.limit_spread = contract_params['limit_spread']
        FH.quanto = contract_params['quanto']
        FH.balance_rt = contract_params['balance_rt']
        FH.step_soft_std = contract_params['step_soft']
        FH.step_hard_std = contract_params['step_hard']
        FH.surplus_abandon = contract_params['surplus_abandon']
        FH.surplus_endure = contract_params['surplus_endure']
        FH.std_mom_std = contract_params['std_mom']
        FH.std_sprint_std = contract_params['std_sprint']

    def get_std_flag(self):
        forward_orders = forward_api_instance.list_futures_orders(contract=FH.contract,settle=FH.settle,status='open',_request_timeout=10,async_req=True)
        backward_orders = backward_api_instance.list_futures_orders(contract=FH.contract,settle=FH.settle,status='open',_request_timeout=10,async_req=True)
        candles=backward_api_instance.list_futures_candlesticks(contract=FH.contract,settle=FH.settle,interval='1m',_request_timeout=10,async_req=True)
        candles_5m=backward_api_instance.list_futures_candlesticks(contract=FH.contract,settle=FH.settle,interval='5m',_request_timeout=10,async_req=True)
        candles_1h=backward_api_instance.list_futures_candlesticks(contract=FH.contract,settle=FH.settle,interval='1h',_request_timeout=10,async_req=True)
        book = backward_api_instance.list_futures_order_book(contract=FH.contract,settle=FH.settle,_request_timeout=10,async_req=True)
        forward_positions = forward_api_instance.get_position(contract=FH.contract,settle=FH.settle,_request_timeout=10,async_req=True)
        backward_positions = backward_api_instance.get_position(contract=FH.contract,settle=FH.settle,_request_timeout=10,async_req=True)
        FH.forward_orders = forward_orders.get()
        FH.backward_orders = backward_orders.get()
        candlesticks = candles.get()
        candlesticks_5m = candles_5m.get()
        candlesticks_1h = candles_1h.get()
        FH.book = book.get()
        FH.forward_positions = forward_positions.get()
        FH.backward_positions = backward_positions.get()
        FH.forward_entry_price = float(FH.forward_positions._entry_price)
        FH.backward_entry_price = float(FH.backward_positions._entry_price)
        FH.forward_liq_price = float(FH.forward_positions._liq_price)
        FH.backward_liq_price = float(FH.backward_positions._liq_price)
        FH.forward_position_size = float(FH.forward_positions._size)
        FH.backward_position_size = float(FH.backward_positions._size)
        FH.forward_leverage = float(FH.forward_positions._leverage)
        FH.backward_leverage = float(FH.backward_positions._leverage)
        FH.mark_price = float(FH.forward_positions._mark_price)
        FH.ask_1 = float(FH.book._asks[0]._p)
        FH.bid_1 = float(FH.book._bids[0]._p)
        FH.forward_value = float(FH.forward_positions._value)
        FH.backward_value = float(FH.backward_positions._value)
        FH.tick_price = (FH.ask_1 + FH.bid_1)/2

        FH.forward_limit = FH.limit_size
        FH.backward_limit = FH.limit_size

        if FH.forward_entry_price == 0:
            FH.forward_entry_price = FH.bid_1
        if FH.backward_entry_price == 0:
            FH.backward_entry_price = FH.ask_1

        if FH.forward_entry_price == 0:
            FH.forward_goods = 0.0
        else:
            FH.forward_goods = FH.forward_value/FH.mark_price * (FH.bid_1 - FH.forward_entry_price)
        if FH.backward_entry_price == 0:
            FH.backward_goods = 0.0
        else:
            FH.backward_goods = FH.backward_value/FH.mark_price * (FH.backward_entry_price - FH.ask_1)
        if FH.forward_position_size > 0:
            FH.limit_value = FH.forward_value/FH.mark_price*FH.tick_price*FH.limit_size/FH.forward_position_size
        elif FH.backward_position_size < 0:
            FH.limit_value = FH.backward_value/FH.mark_price*FH.tick_price*FH.limit_size/abs(FH.backward_position_size)
        else:
            FH.limit_value = 0.0
        FH.abandon_goods = FH.surplus_abandon/FH.tick_price * FH.limit_value
        FH.endure_goods = FH.surplus_endure/FH.tick_price * FH.limit_value

        if FH.forward_position_size > 0 and FH.forward_entry_price > 0:
            FH.t_f = FH.tick_price - FH.forward_entry_price
            FH.forward_gap = FH.t_f/FH.forward_entry_price
        else:
            FH.t_f = 0.0
            FH.forward_gap = 0.0
        if FH.backward_position_size < 0 and FH.backward_entry_price > 0:
            FH.t_b = FH.backward_entry_price - FH.tick_price
            FH.backward_gap = FH.t_b/FH.backward_entry_price
        else:
            FH.t_b = 0.0
            FH.backward_gap = 0.0

        FH.forward_stable_price = False
        FH.backward_stable_price = False
        FH.stable_spread = False
        if FH.ask_1 - FH.bid_1 < FH.limit_spread:
            FH.stable_spread = True
            if len(candlesticks) > 0:
                o = float(candlesticks[len(candlesticks)-1]._o)
                c = float(candlesticks[len(candlesticks)-1]._c)
                if (c - o)/c <= 0:
                    FH.forward_stable_price = True
                if (c - o)/c >= 0:
                    FH.backward_stable_price = True
        if len(candlesticks) > 10:
            abs1m = []
            for i in range(2, 12):
                o = float(candlesticks[len(candlesticks) - i]._o)
                c = float(candlesticks[len(candlesticks) - i]._c)
                abs1m.append(abs(c - o))
            abs1m = np.nan_to_num(abs1m)
            max_1m = np.max(abs1m)
            FH.step_soft = max(FH.step_soft_std, max_1m)

        if len(candlesticks_5m) > 10:
            abs5m = []
            for i in range(2,12):
                o = float(candlesticks_5m[len(candlesticks_5m)-i]._o)
                c = float(candlesticks_5m[len(candlesticks_5m)-i]._c)
                abs5m.append(abs(c - o))
            abs5m = np.nan_to_num(abs5m)
            med_5m = np.median(abs5m)
            max_5m = np.max(abs5m)
            #FH.step_soft = max(FH.step_soft_std,max_5m)
            FH.std_mom = max(FH.std_mom_std,med_5m)

        if len(candlesticks_1h) > 10:
            abs1h = []
            for i in range(1,11):
                o = float(candlesticks_1h[len(candlesticks_1h)-i]._o)
                c = float(candlesticks_1h[len(candlesticks_1h)-i]._c)
                abs1h.append(abs(c - o))
            abs1h = np.nan_to_num(abs1h)
            max_1h = np.max(abs1h)
            med_1h = np.median(abs1h)
            FH.std_sprint = max(FH.std_sprint_std,med_1h)
            FH.step_hard = max(FH.step_hard_std,max_1h)

        FH.forward_mom = False
        FH.backward_mom = False
        FH.co = 0.0
        if len(candlesticks_5m) > 1:
            o = float(candlesticks_5m[len(candlesticks_5m)-2]._o)
            c = float(candlesticks_5m[len(candlesticks_5m)-2]._c)
            FH.co = (c - o)
            if FH.co >= FH.std_mom:
                FH.forward_mom = True
            elif FH.co <= -FH.std_mom:
                FH.backward_mom = True

        if FH.forward_goods > FH.backward_goods:
            FH.current_side = 'forward'
        elif FH.forward_goods < FH.backward_goods:
            FH.current_side = 'backward'
            FH.step_soft = -FH.step_soft
            FH.step_hard = -FH.step_hard
        else:
            FH.current_side = 'biside'

        if FH.current_side != FH.pre_side:
            FH.pre_side = FH.current_side
            FH.pre_t = 't'
            FH.t_tail = -1
            FH.catch = False
            FH.balance = False

        print ('step',FH.step_soft,FH.step_hard)

        if FH.forward_mom:
            if FH.forward_band_price < 0.0:
                FH.forward_band_price = FH.ask_1
            if FH.backward_band_price > 0 and (FH.backward_band_price - FH.ask_1) >= FH.std_sprint:
                FH.forward_sprint = False
                FH.backward_sprint = True
            FH.backward_band_price = -1.0
        elif FH.backward_mom:
            if FH.backward_band_price < 0.0:
                FH.backward_band_price = FH.bid_1
            if FH.forward_band_price > 0 and (FH.bid_1 - FH.forward_band_price) >= FH.std_sprint:
                FH.backward_sprint = False
                FH.forward_sprint = True
            FH.forward_band_price = -1.0

        print(FH.forward_mom,FH.co,FH.forward_sprint)
        print(FH.backward_mom,FH.co,FH.backward_sprint)
        print(FH.std_mom,FH.std_sprint,FH.forward_band_price,FH.backward_band_price)

        if FH.forward_goods <= FH.backward_goods:
            if FH.forward_goods != 0:
                FH._T = abs(FH.backward_position_size) / float(FH.forward_position_size)
            else:
                FH._T = 1.0
            FH.D = FH.forward_position_size - abs(FH.backward_position_size)
        elif FH.forward_goods >= FH.backward_goods:
            if FH.backward_goods != 0:
                FH._T = float(FH.forward_position_size) / abs(FH.backward_position_size)
            else:
                FH._T = 1.0
            FH.D = abs(FH.backward_position_size) - FH.forward_position_size

        if FH.forward_position_size <= 0 and abs(FH.backward_position_size) <= 0:
            FH.balance_overflow = 0.0

        if FH.forward_position_size > 0 and FH.forward_entry_price > 0:
            FH.forward_liq_gap = (FH.mark_price - FH.forward_entry_price)/FH.forward_entry_price
        else:
            FH.forward_liq_gap = 0.0
        if FH.backward_position_size < 0 and FH.backward_entry_price > 0:
            FH.backward_liq_gap = (FH.backward_entry_price - FH.mark_price)/FH.backward_entry_price
        else:
            FH.backward_liq_gap = 0.0

        gap_levels = sorted(FH.level)
        for gap_level in gap_levels:
            if max(-FH.forward_liq_gap,-FH.forward_gap) < float(gap_level):
                FH.forward_gap_level = FH.level[gap_level]['leverage']
                break

        for gap_level in gap_levels:
            if max(-FH.backward_liq_gap,-FH.backward_gap) < float(gap_level):
                FH.backward_gap_level = FH.level[gap_level]['leverage']
                break

        if FH.forward_account_from == 0:
            FH.forward_account_from = int(time.time())
        if FH.backward_account_from == 0:
            FH.backward_account_from = int(time.time())
        forward_account_book = forward_api_instance.list_futures_account_book(settle=FH.settle,_from=FH.forward_account_from,_request_timeout=10)
        backward_account_book = backward_api_instance.list_futures_account_book(settle=FH.settle,_from=FH.backward_account_from,_request_timeout=10)
        for item in forward_account_book:
            if FH.contract in item.text:
                FH.goods += float(item.change)
                if item.type == 'pnl':
                    if float(item.change) > 0.0:
                        FH.balance_overflow += FH.balance_rt * float(item.change)
                    else:
                        FH.balance_overflow += float(item.change)
        for item in backward_account_book:
            if FH.contract in item.text:
                FH.goods += float(item.change)
                if item.type == 'pnl':
                    if float(item.change) > 0.0:
                        FH.balance_overflow += FH.balance_rt * float(item.change)
                    else:
                        FH.balance_overflow += float(item.change)
        if len(forward_account_book) > 0:
            FH.forward_account_from = int(forward_account_book[0]._time) + 1
        if len(backward_account_book) > 0:
            FH.backward_account_from = int(backward_account_book[0]._time) + 1

        if FH.forward_position_size == 0:
            FH.forward_trigger_liq = 0
        if FH.backward_position_size == 0:
            FH.backward_trigger_liq = 0
        if FH.forward_position_size > 0 and FH.forward_liq_price < FH.mark_price and (FH.forward_trigger_liq < 0 or (FH.forward_trigger_liq <= (1.0+1.0/FH.forward_leverage*0.05)*FH.forward_liq_price or FH.forward_trigger_liq >= (1.0+1.0/FH.forward_leverage*0.2)*FH.forward_liq_price)):
            FH.forward_liq_flag = True
        else:
            FH.forward_liq_flag = False
        if FH.backward_position_size < 0 and FH.backward_liq_price > FH.mark_price and (FH.backward_trigger_liq < 0 or (FH.backward_trigger_liq <= (1.0-1.0/FH.backward_leverage*0.2)*FH.backward_liq_price or FH.backward_trigger_liq >= (1.0-1.0/FH.backward_leverage*0.05)*FH.backward_liq_price)):
            FH.backward_liq_flag = True
        else:
            FH.backward_liq_flag = False
