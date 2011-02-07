#!/usr/bin/env python
#coding:utf-8

import gtk
import threading
import pango
import re
import gboject
import time
import pynotify
from settings import *

class Eventline(gtk.TreeView):
    # keypressed Event.
    __gsignals__= {
            "keypressed":(gobject.SIGNAL_RUN_LAST|gobject.SIGNAL_ACTION,
                         None,
                         (str,),)
            }
    # Column defines.
    # |icon|text|
    (
        COLUMN_ICON,
        COLUMN_TEXT,
    ) = range(2)

    def __init__(self,client,*args,**kwargs):
        gtk.TreeView.__init__(self,*args,**kwargs)
        self.store = gtk.ListStore(gtk.gdk.Pixbuf,str)
        self.event_list = []
        self.client = client
        self.client.store.add_store(self)
        self.iconstore = self.client.store

