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
	self.follow_signal = True
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
	for handler in self.handlers:
            current_position += abs(handler.position_size)/handler.leverage
        if current_position >= self.total_params['minor_size']:
	    self.follow_signal = False
	else:
	    self.follow_signal = True
	account = api_instance.list_futures_accounts()
	current_insurance = float(account._available)
	if current_insurance <= self.total_params['minor_insurance']:
	    self.balance_signal = True
	else:
	    self.balance_signal = False

    def put_position(self,follow_signal,balance_signal):
	for handler in self.handlers:
	    handler.get_position(follow_signal,balance_signal)

    def cancel_position(self):
	for handler in self.handlers:
	    handler.cancel_position()

    def handle_position(self):
	if not self.balance_signal:
	    self.put_position(self.follow_signal,self.balance_signal)
	else:
	    self.cancel_position()
