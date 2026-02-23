#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
#########################################################
#                                                       #
#  Vavoo Stream Live Plugin                             #
#  Created by Lululla (https://github.com/Belfagor2005) #
#  License: CC BY-NC-SA 4.0                             #
#  https://creativecommons.org/licenses/by-nc-sa/4.0    #
#  Last Modified: 20260122                              #
#                                                       #
#  Credits:                                             #
#  - Original concept by Lululla                        #
#  - Special thanks to @KiddaC for support              #
#  - Background images by @oktus                        #
#  - Additional contributions by Qu4k3                  #
#  - Linuxsat-support.com & Corvoboys communities       #
#                                                       #
#  Usage of this code without proper attribution        #
#  is strictly prohibited.                              #
#  For modifications and redistribution,                #
#  please maintain this credit header.                  #
#########################################################
"""

import sys

plugin_path = "/usr/lib/enigma2/python/Plugins/Extensions/vavoo"
if plugin_path not in sys.path:
    sys.path.append(plugin_path)

try:
    try:
        from .vavoo_proxy import start_proxy
    except Exception:
        from vavoo_proxy import start_proxy
    print("Starting Vavoo proxy...")
    start_proxy()
except Exception as e:
    print("Proxy startup error: " + str(e))
    import traceback
    traceback.print_exc()
