#!/usr/bin/env python

import hashlib, sys

print hashlib.md5(sys.argv[1]).hexdigest()


