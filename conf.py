# -*- coding: utf-8 -*-

from __future__ import print_function
import requests
import time
import gate_api
from gate_api.rest import ApiException

forward_configuration = gate_api.Forward_Configuration()
backward_configuration = gate_api.Backward_Configuration()
forward_api_instance = gate_api.FuturesApi(gate_api.ApiClient(forward_configuration))
backward_api_instance = gate_api.FuturesApi(gate_api.ApiClient(backward_configuration))

