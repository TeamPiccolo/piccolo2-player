#!/usr/bin/env python

# Copyright 2014-2016 The Piccolo Team
#
# This file is part of piccolo2-player.
#
# piccolo2-player is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# piccolo2-player is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with piccolo2-player.  If not, see <http://www.gnu.org/licenses/>.

import player
import argparse

def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-u','--piccolo-url',metavar='URL',default='http://localhost:8080',help='set the URL of the piccolo server, default http://localhost:8080')
    group.add_argument('-x','--xbee-address',metavar='ADR',help="the address of the xbee radio")
    args = parser.parse_args()

    if args.xbee_address != None:
        connection = ('xbee',args.xbee_address)
    else:
        connection = ('http',args.piccolo_url)

    player.main(connection)

if __name__ == '__main__':
    main()
