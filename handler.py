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

class FH(object):
    balance_overflow = 0.025035103538
    forward_account_from = 0
    backward_account_from = 0
    forward_trigger_liq = -1
    backward_trigger_liq = -1
    quanto = None
    balance_rt = 1.0
    goods = 0.724711806514
    forward_goods = 0.0
    backward_goods = 0.0
    limit_goods = 0.0
    catch = False
    balance = False
    forward_sprint = True
    backward_sprint = False
    forward_band_price = 11363.0
    backward_band_price = -1.0
    t = 0.0
    _T = None
    T_std = None
    _S = 0.0
    S_ = 0.0
    S_up = 0.0
    S_dn = 0.0
    t_up = 0.0
    t_dn = 0.0
    S_up_t = 0.0
    S_dn_t = 0.0
    t_up_S = 0.0
    t_dn_S = 0.0
    rt_soft = 0.0
    rt_hard = 0.0
    t_head = 1.0 
    t_tail = 1000000.0
    pre_side = 'biside'

    def __init__(self,contract = '',contract_params = {}):
	FH.contract = contract
        FH.settle = contract_params['settle']
        FH.tap = contract_params['tap']
        FH.level = contract_params['level']
        FH.limit_size = contract_params['limit_size']
        FH.quanto = contract_params['quanto']
        FH.balance_rt = contract_params['balance_rt']
        FH.step_soft_std = contract_params['step_soft']
        FH.step_hard_std = contract_params['step_hard']
        FH.surplus_abandon = contract_params['surplus_abandon']
        FH.surplus_endure = contract_params['surplus_endure']
        FH.surplus_switch = contract_params['surplus_switch']
        FH.std_mom_std = contract_params['std_mom']
        FH.std_sprint_std = contract_params['std_sprint']
        FH.std_fin = contract_params['std_fin']
        FH.std_fout = contract_params['std_fout']
        FH.peak = contract_params['peak']
        FH.bottom = contract_params['bottom']
        FH.pre_t = contract_params['pre_t']

    def get_std_flag(self):
        forward_orders = forward_api_instance.list_futures_orders(contract=FH.contract,settle=FH.settle,status='open',async_req=True)
        backward_orders = backward_api_instance.list_futures_orders(contract=FH.contract,settle=FH.settle,status='open',async_req=True)
        candles=backward_api_instance.list_futures_candlesticks(contract=FH.contract,settle=FH.settle,interval='1m',async_req=True)
        candles_5m=backward_api_instance.list_futures_candlesticks(contract=FH.contract,settle=FH.settle,interval='5m',async_req=True)
        candles_1h=backward_api_instance.list_futures_candlesticks(contract=FH.contract,settle=FH.settle,interval='1h',async_req=True)
        book = backward_api_instance.list_futures_order_book(contract=FH.contract,settle=FH.settle,async_req=True)
        forward_positions = forward_api_instance.get_position(contract=FH.contract,settle=FH.settle,async_req=True)
        backward_positions = backward_api_instance.get_position(contract=FH.contract,settle=FH.settle,async_req=True)
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
        FH.forward_position_size = FH.forward_positions._size
        FH.backward_position_size = FH.backward_positions._size
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
        FH.entry_gap = FH.forward_entry_price - FH.backward_entry_price


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

        if FH.forward_gap > FH.backward_gap:
            FH.current_side = 'forward'
        elif FH.forward_gap < FH.backward_gap:
            FH.current_side = 'backward'
        else:
            FH.current_side = 'biside'

        if FH.current_side != FH.pre_side:
            FH.pre_side = FH.current_side
            FH.pre_t = 't'
            FH.catch = False
            FH.balance = False

        FH.forward_stable_price = False
        FH.backward_stable_price = False
        if len(candlesticks) > 0:
            o = float(candlesticks[len(candlesticks)-1]._o)
            c = float(candlesticks[len(candlesticks)-1]._c)
            if (c - o)/c < 0.001:
                FH.forward_stable_price = True
            if (c - o)/c > -0.001:
                FH.backward_stable_price = True

        if len(candlesticks_5m) > 10:
            abs5m = []
            for i in range(2,12):
                o = float(candlesticks_5m[len(candlesticks_5m)-i]._o)
                c = float(candlesticks_5m[len(candlesticks_5m)-i]._c)
                abs5m.append(abs(c - o))
            abs5m = np.nan_to_num(abs5m)
            med_5m = np.median(abs5m)
            max_5m = np.max(abs5m)
            FH.step_soft = max(FH.step_soft_std,max_5m)
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

        print ('step',FH.step_soft,FH.step_hard)
        FH.rt_soft = FH.step_soft/abs(FH.entry_gap)
        FH.rt_hard = FH.step_hard/abs(FH.entry_gap)

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

        if FH.forward_entry_price == 0:
            FH.forward_goods = 0.0
        else:
            FH.forward_goods = FH.forward_value/FH.mark_price * (FH.tick_price - FH.forward_entry_price)
        if FH.backward_entry_price == 0:
            FH.backward_goods = 0.0
        else:
            FH.backward_goods = FH.backward_value/FH.mark_price * (FH.backward_entry_price - FH.tick_price)
        if FH.forward_position_size > 0:
            FH.limit_goods = FH.forward_value/FH.mark_price*FH.tick_price*FH.limit_size/FH.forward_position_size
        elif FH.backward_position_size < 0:
            FH.limit_goods = FH.backward_value/FH.mark_price*FH.tick_price*FH.limit_size/abs(FH.backward_position_size)
        else:
            FH.limit_goods = 0.0
        FH.abandon_goods = FH.surplus_abandon/FH.tick_price * max(FH.forward_value,FH.backward_value)
        FH.endure_goods = FH.surplus_endure/FH.tick_price * max(FH.forward_value,FH.backward_value)
        FH.switch_goods = FH.surplus_switch/FH.tick_price * max(FH.forward_value,FH.backward_value)

        if FH.forward_gap < 0.0 and FH.backward_gap >= 0.0:
            FH.t = -FH.t_b/FH.t_f
        elif FH.backward_gap < 0.0 and FH.forward_gap >= 0.0:
            FH.t = -FH.t_f/FH.t_b
        elif FH.forward_gap < 0.0 and FH.backward_gap < 0.0:
            if FH.forward_gap > FH.backward_gap:
                FH.t = -FH.t_f/(FH.t_b+FH.t_f)
            else:
                FH.t = -FH.t_b/(FH.t_f+FH.t_b)

        if FH.forward_gap < 0.0 and FH.backward_gap >= 0.0:
            FH._T = abs(float(FH.backward_position_size) / float(FH.forward_position_size))
        elif FH.backward_gap < 0.0 and FH.forward_gap >= 0.0:
            FH._T = abs(float(FH.forward_position_size) / float(FH.backward_position_size))
        elif FH.forward_gap < 0.0 and FH.backward_gap < 0.0:
            if FH.forward_gap > FH.backward_gap:
                FH._T = abs(float(FH.forward_position_size) / float(FH.backward_position_size))
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

        if FH.forward_gap >= 0.0 and FH.backward_gap >= 0.0:
            FH.balance_overflow = 0.0

        if FH.forward_position_size > 0 and FH.forward_entry_price > 0:
            FH.forward_liq_gap = (FH.mark_price - FH.forward_entry_price)/FH.forward_entry_price
        else:
            FH.forward_liq_gap = 0.0
        if FH.backward_position_size < 0 and FH.backward_entry_price > 0:
            FH.backward_liq_gap = (FH.backward_entry_price - FH.mark_price)/FH.backward_entry_price
        else:
            FH.backward_liq_gap = 0.0
        gap_levels = FH.level.keys()
        gap_levels.sort()
        for gap_level in gap_levels:
            if max(-FH.forward_liq_gap,-FH.forward_gap) < float(gap_level):
                FH.forward_gap_level = FH.level[gap_level]['leverage']
                break

        for gap_level in gap_levels:
            if max(-FH.backward_liq_gap,-FH.backward_gap) < float(gap_level):
                FH.backward_gap_level = FH.level[gap_level]['leverage']
                break

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
