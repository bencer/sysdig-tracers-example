#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from Queue import Queue
from threading import Thread
import urllib2
import random
import os
import sys
import time
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

host = os.environ['SERVER_HOST'] + ':' + os.environ['SERVER_PORT']
concurrent = 4

def randomURL():
    drivers = ['fib', 'empty', 'download']
    driver = random.choice(drivers)
    number = random.randint(1, 1024)
    url = 'http://{}/{}/{}'.format(host, driver, number)
    return url

def dequeue():
    while True:
        url = q.get()
        logger.info("GET {}".format(url))
        do_request(url)
        q.task_done()

def do_request(url):
    try:
        response = urllib2.urlopen(url)
        body = response.read()
        response.close()
    except urllib2.URLError, e:
        logger.error(e.reason)

q = Queue()
for i in range(concurrent):
    t = Thread(target=dequeue)
    t.daemon = True
    t.start()
    while True:
        q.put(randomURL())
    q.join()
