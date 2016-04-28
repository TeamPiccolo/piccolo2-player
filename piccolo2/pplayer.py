#!/usr/bin/env python
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
