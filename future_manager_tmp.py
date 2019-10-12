# -*- coding: utf-8 -*-

from __future__ import print_function
from gate_api import FuturesOrder
from gate_api.rest import ApiException
from conf import *
from future_handler import *
import json
import gflags
import codecs
import requests
import time
import gate_api

class Future_Manager(object):
    def __init__(self):
	self.balance_signal = False
	f_exp = codecs.open('./experiment.conf', 'r', encoding='utf-8')
	data_algs = json.load(f_exp)
	contracts = data_algs['contract']
	self.handlers = []
	for contr in contracts:
	    handler = Future_Handler(contr,contracts[contr])
	    self.handlers.append(handler)
	    self.total_params = data_algs['total']
	f_exp.close()

    def check_position(self):
        current_position = 0
        current_index = 0
	for handler in self.handlers:
            current_position += abs(handler.position_size)/handler.leverage
        for idx,_size in enumerate(self.total_params['size_level']):
            if current_position < _size:
                current_index = idx
                self.minor_position = _size
                if idx == len(self.total_params['size_level']) - 1:
                    self.mayor_position = self.total_params['limit_position']
                else:
                    self.mayor_position = self.total_params['size_level'][idx + 1]
                break
        for handler in self.handlers:
            handler.minor_position = handler.position_level[current_idx]
            handler.gap = handler.gap_level[current_idx]
            if idx == len(handler.position_level) - 1:
                handler.mayor_position = self.total_params['limit_position']
            else:
                handler.mayor_position = handler.position_level[current_idx + 1]
            if abs(handler.position_size)/handler.leverage >= handler.position_level[0]:
                handler.tap = abs(abs(handler.position_size)/handler.leverage)
	account = api_instance.list_futures_accounts()
	current_insurance = float(account._available)
	if current_insurance <= self.total_params['minor_insurance']:
	    self.balance_signal = True
	else:
	    self.balance_signal = False

    def put_position(self,balance_signal):
	for handler in self.handlers:
	    handler.get_position(balance_signal)

    def cancel_position(self):
	for handler in self.handlers:
	    handler.cancel_position()

    def handle_position(self):
	if not self.balance_signal:
	    self.put_position(self.balance_signal)
	else:
	    self.cancel_position()
