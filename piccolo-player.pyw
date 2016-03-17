#!/usr/bin/env python
import piccolo_player
import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-u','--piccolo-url',metavar='URL',default='http://localhost:8080',help='set the URL of the piccolo server, default http://localhost:8080')
    args = parser.parse_args()

    connection = ('http',args.piccolo_url)

    piccolo_player.main(connection)
