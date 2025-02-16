
#use debug flag to determine whether to pull data from cloud or repo
# invoke with
# python3.12 -d blah.py

import sys
print(sys.flags.debug)


#successfully used brotli to compress master file hard from 97MB to 54MB. Nice.
#going forward this means could periodically download titanium container and put into repo.


