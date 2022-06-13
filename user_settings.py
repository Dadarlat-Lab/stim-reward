# -*- coding: utf-8 -*-
import datetime, time, logging

PYBPOD_API_LOG_LEVEL = None
PYBPOD_API_LOG_FILE  = 'logs/pybpod-api.log'


PYBPOD_SESSION_PATH = 'logs'
PYBPOD_SESSION 		= datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

PYBPOD_SERIAL_PORT 	= '/dev/ttyACM0'

BPOD_BNC_PORTS_ENABLED 		= [True, True]
BPOD_WIRED_PORTS_ENABLED 	= [True, True]
BPOD_BEHAVIOR_PORTS_ENABLED = [True, True, True, False, False, False, False, False]

PYBPOD_PROTOCOL     = 'STIM-REWARD' # Executed protocol
PYBPOD_CREATOR      = 'THOMAS MAKIN; KATHLEEN KISKER' # Name of the user
PYBPOD_PROJECT      = 'STIM-REWARD' # Name of the project
PYBPOD_EXPERIMENT   = 'STIM/NO-STIM' # Name of the experiment
PYBPOD_BOARD        = 'STATE MACHINE V2.2' # Board name
PYBPOD_SETUP        = 'STIM-REWARD' # Setup name
