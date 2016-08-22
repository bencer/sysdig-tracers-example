#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from Queue import Queue
from threading import Thread
import urllib2
import random
import sys

concurrent = 8
requests = 800000
host = '127.0.1.1:8888'

def randomURL():
    drivers = ['fib', 'empty', 'download']
    driver = random.choice(drivers)
    number = random.randint(1, 1024)
    url = 'http://{}/{}/{}'.format(host, driver, number)
    return url

def dequeue():
    while True:
        url = q.get()
        print "GET: {}".format(url)
        do_request(url)
        q.task_done()

def do_request(url):
    try:
        response = urllib2.urlopen(url)
        body = response.read()
        response.close()
    except urllib2.URLError, e:
        print e.reason

q = Queue(requests)
for i in range(concurrent):
    t = Thread(target=dequeue)
    t.daemon = True
    t.start()
try:
    for x in range(requests):
        q.put(randomURL())
    q.join()
except KeyboardInterrupt:
    sys.exit(1)
