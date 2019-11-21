# -*- coding: utf-8 -*-

from __future__ import print_function
import requests
import time
import gate_api
import json
from future_manager import *
from future_handler import *
from gate_api import FuturesOrder
from gate_api.rest import ApiException

if __name__ == "__main__":
    future_manager = Future_Manager()
    while True:
        future_manager.run()
