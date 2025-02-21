
#use debug flag to determine whether to pull data from cloud or repo
# invoke with
# python3.12 -d blah.py

#successfully used brotli to compress master file hard from 97MB to 54MB. Nice.
#going forward this means could periodically download titanium container and put into repo.

#can't download folders directly from storage explorer (maybe on the proper app version??) but not
# in browser version. Maybe make script that does this so it can be done easily in future?

# script: pull titanium subfolders to new folder location called snapshot in /data/data_snapshot

# 1. Get snapshot of processed data into repo (DONE)
# 2 Test debug mode can succesfully pull from different sources
# See if can do this via docker (i.e. can I run docker image in debug mode from cmd line? for other users)
# 3 Begin the process of refactoring and rebuilding. First update to latest dash version etc. 


import sys
from global_constants import *
import logging

#from . import data_processing_runtime as data  # run-time helpers (needed when running from wsgi.py in normal operation)
import data  # run-time helpers

# add atlas/data folder to path (so we can access paths in /data/data_paths.py)
sys.path.append('/usr/src/app/data') #working dir for built container (see /Dockerfile)
sys.path.append('/home/dan/atlas/data') #testing on local machine (no docker)
from data_paths import * 

# Get debug flag 
debug_mode = sys.flags.debug # determines if cloud or local data ingested
debug_mode = 0

# setup logger to console
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("atlas")


# load app data into memory
pop = data.load(debug_mode)

print('Data successfully loaded....blahpidy')

t = pop.globe_land_hires
m = pop.globe_land_lowres
