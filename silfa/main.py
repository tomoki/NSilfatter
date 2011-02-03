#!/usr/bin/env python
#coding:utf-8

from client import client
from first import first
import sys
import gtk

from settings import *

def start_client():
    if sys.platform == "win32":
        gobject.threads_init()
    else:
        gtk.gdk.threads_init()
    client()
    gtk.main()

def start_first():
    first()
    gtk.main()

def main():
    if os.path.isfile(OAUTH_FILE):
        start_client()
    else:
        start_first()
        if os.path.isfile(OAUTH_FILE):
            start_client()

if __name__ == "__main__":
    main()
