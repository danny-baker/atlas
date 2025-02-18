
#use debug flag to determine whether to pull data from cloud or repo
# invoke with
# python3.12 -d blah.py

#successfully used brotli to compress master file hard from 97MB to 54MB. Nice.
#going forward this means could periodically download titanium container and put into repo.

#can't download folders directly from storage explorer (maybe on the proper app version??) but not
# in browser version. Maybe make script that does this so it can be done easily in future?

# script: pull titanium subfolders to new folder location called snapshot in /data/data_snapshot

# 1. Get snapshot of processed data into repo
# 2 Test debug mode can succesfully pull from different sources
# 3 Begin the process of refactoring and rebuilding. First update to latest dash version etc. 

import sys

debug_mode = sys.flags.debug
print(debug_mode)



