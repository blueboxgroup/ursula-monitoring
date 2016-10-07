#!/usr/bin/env python

# -*- coding: utf-8 -*-
from __future__ import print_function

import argparse
import fcntl
import socket
import struct
import sys
import time
from collections import Mapping

import requests

OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3


def get_ip_address(ifname):
    # https://stackoverflow.com/questions/24196932/how-can-i-get-the-ip-address-of-eth0-in-python  #noqa
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


class SwiftMetricsParser(object):
    def __init__(self, metrics):
        self.metrics = metrics

    def _generate(self, path, data):
        """ Recurses through the metrics, given a path (str) and data (a dict),
        to provide paths (like Graphite metrics paths) and values

        :param path: str, dot-notated path representing a val
        :param data: dictionary of data, in form of {path: data}
        :returns: generator producing tuples in form of (path, value)
        """
        if isinstance(data, Mapping):
            for p, d in data.iteritems():
                if isinstance(d, Mapping):
                    newpath = "{}.{}".format(path, p)
                    for result in self._generate(newpath, d):
                        yield result
                else:
                    yield "{}.{}".format(path, p), d
        elif isinstance(data, list):
            if path == 'diskusage':
                for disk in data:
                    newpath = "{}.{}".format(path, disk['device'])
                    del disk['device']
                    for result in self._generate(newpath, disk):
                        yield result
        else:
            yield path, data

    def parse(self):
        """ Takes metrics, produces Graphite-like paths and values.

        :return: generator producing tuples in form of (path, value)
        """
        for path, data in self.metrics.iteritems():
            gen = self._generate(path.replace('/', '.'), data)
            while True:
                try:
                    yield next(gen)
                except StopIteration:
                    break


class SwiftMetrics(object):
    def __init__(self, ip, port):
        self.baseurl = "http://{}:{}/recon/{{path}}".format(ip, port)
        self.reconpaths = (
            'diskusage',
            'quarantined',
            'sockstat',
            'async',
            'replication/account',
            'replication/container',
            'replication/object',
            'updater/container',
            'updater/object',
        )
        self._data = {}

    @property
    def metrics(self):
        if not self._data:
            for path in self.reconpaths:
                url = self.baseurl.format(path=path)
                resp = requests.get(url)
                self._data[path] = resp.json()
        return self._data

    def graphite_print(self, parser):
        utime = time.time()
        metric_path = "recon.swift.{name}"
        outstr = "{metric_path} {value} {time}"

        for path, val in parser.parse():
            mpath = metric_path.format(name=path)
            print(outstr.format(metric_path=mpath, value=val, time=utime))

    def run(self):
        parser = SwiftMetricsParser(self.metrics)
        self.graphite_print(parser)


def parse_args():
    parser = argparse.ArgumentParser()
    mutex = parser.add_mutually_exclusive_group(required=True)
    mutex.add_argument(
        '--interface',
        metavar='bond0',
        help='Interface from which to get IP address'
    )
    mutex.add_argument('--ip-addr', help='Specific IP to use')
    parser.add_argument(
        '--port',
        metavar='6000',
        default='6000',
        help='Swift Recon API port'
    )
    return parser.parse_args()


def process_args(args):
    if args.ip_addr:
        ip = args.ip_addr
    else:
        ip = get_ip_address(args.interface)
    return ip, args.port


def main():
    args = parse_args()
    sm = SwiftMetrics(*process_args(args))
    sm.run()


if __name__ == '__main__':
    main()
