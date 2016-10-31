#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from sysdig_tracers import Tracer, Args, ReturnValue

# sorry, using simple stuff rather than Twisted, Tornado or Python3 asyncio
from SocketServer import ThreadingMixIn
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

import os
import sys
import gzip
import random
import tempfile
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@Tracer(enter_args={"n": Args(0)}, exit_args={"ret": ReturnValue})
def fib(n):
    a, b = 1, 1
    for i in range(n-1):
        a, b = b, a+b
    return a


def scratch(file_path, size):
    f = os.open(file_path, os.O_RDWR|os.O_CREAT)
    for i in range(size):
        rnd = file('/dev/urandom', 'rb').read(1024)
        os.write(f, rnd)
        os.fsync(f) # don't buffer, stress IO
    os.close(f)


class MyRequestHandler(BaseHTTPRequestHandler):

    def do_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

    def fib_handler(self, num):
        with Tracer("fib_handler") as t:
            with t.span("fib_headers"):
                self.do_headers()
    
            with t.span("fib_write"):
            	result = fib(num)
                self.wfile.write(result)
    
    def scratch_handler(self, num):
        with Tracer("scratch_handler") as t:
            with t.span("scratch_headers"):
                self.do_headers()
    
            with t.span("scratch_write"):
                _, file_path = tempfile.mkstemp(dir='/tmp')
                scratch(file_path, 96)
                os.remove(file_path)
                self.wfile.write("That's all folks!")

    def empty_handler(self, num):
        with Tracer("empty_handler") as t:
            with t.span("empty_headers"):
                self.do_headers()
    
            with t.span("empty_write"):
                self.wfile.write("")

    def download_handler(self, num):
        with Tracer("download_handler") as t:
            with t.span("download_headers"):
                self.do_headers()
    
            with t.span("download_write"):
                filename = '/tmp/blob.bin.{}'.format(random.randint(1,4))
                with open(filename, 'r') as f:
                    self.wfile.write(f.read())

    def do_GET(self):
        _, driver, num = self.path.split('/')
        num = int(num)

        if driver == 'fib':
            self.fib_handler(num)

        if driver == 'scratch':
            self.scratch_handler(num)

        if driver == 'empty':
            self.empty_handler(num)

        if driver == 'download':
            self.download_handler(num)


class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
    logger.info('Listening for connections...')
    pass


def init_file(file_path, size, compress=False):
    file_raw_path = file_path+'.raw'
    with open(file_raw_path, "wb") as out:
       out.truncate(1024 * size)
    if compress:
        f_in = open(file_raw_path)
        f_out = gzip.open(file_path, 'wb')
        f_out.writelines(f_in)
        f_out.close()
        f_in.close()
    else:
        os.rename(file_raw_path, file_path)

def init_server():
    logger.info('Creating static files...')
    init_file('/tmp/blob.bin.1', 1024)
    init_file('/tmp/blob.bin.2', 1536)
    init_file('/tmp/blob.bin.3', 1280)
    init_file('/tmp/blob.bin.4', 1024*512)

def main():

    host = '0.0.0.0'
    port = 8888

    init_server()
    server = ThreadingSimpleServer((host, port), MyRequestHandler)
    server.serve_forever()

if __name__ == '__main__':
    main()
