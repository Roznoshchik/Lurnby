"""
This module contains compatibility helpers for Python 2/3 interoperability.

It mainly exists because their are certain incompatibilities in the Python
syntax that can only be solved by conditionally importing different functions.
"""
import sys
if sys.version_info[0] == 2:
    bytes_ = str
    str_ = unicode
    
elif sys.version_info[0] == 3:
    bytes_ = bytes
    str_ = str
