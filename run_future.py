# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import time
import gate_api
import json
from future_manager import *
from gate_api import FuturesOrder
from gate_api.rest import ApiException

f = open('log/LOG_BTC.txt', 'a')
sys.stdout = f
sys.stderr = f

if __name__ == "__main__":
    future_manager = Future_Manager()
    while True:
        future_manager.run()
