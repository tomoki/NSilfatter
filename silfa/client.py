#!/usr/bin/env python
#coding:utf-8

import gtk
from postbox import PostBox
from cwindow import ClientWindow
from iconstore import IconStore
from replydialog import ReplyWindow
from urldialog import UrlWindow
from timeline import *
import pango
import twoauth
import sys
from settings import *
import pynotify
from timelinethread import StreamingThread,RestThread

class client(object):
    def __init__(self):
        key,secret = self.load_auth()
        self.api = twoauth.api(CONSUMER_KEY,CONSUMER_SECRET,key,secret)
        self.me = self.api.verify_credentials()
        self.my_name = self.me.screen_name
        pynotify.init("Silfatter")
        self.statuses = {}
        self.store = IconStore()

        self.window = ClientWindow()

        self.accelgroup = gtk.AccelGroup()
        self.window.add_accel_group(self.accelgroup)
        stream = StreamingThread(self)
        rest = RestThread(self)

        main_vbox = gtk.VBox()
        post_box = PostBox(self)

        self.lines_note_book = gtk.Notebook()
        self.home_timeline_sw = Timelinesw(self,"home")
        self.mention_timeline_sw = Timelinesw(self,"mention")
#        self.event_timeline_sw = Timelinesw(self,"event")

        stream.add(self.home_timeline_sw.view)
        stream.add(self.mention_timeline_sw.view)
#        stream.add(self.event_timeline_sw.view)

        rest.add(self.home_timeline_sw.view)
        rest.add(self.mention_timeline_sw.view)

        self.reply_window = ReplyWindow(self)
        self.url_window = UrlWindow(self)

        self.lines_note_book.append_page(self.home_timeline_sw,gtk.Label("Home"))
        self.lines_note_book.append_page(self.mention_timeline_sw,gtk.Label("Mention"))
#        self.lines_note_book.append_page(self.event_timeline_sw,gtk.Label("Event"))

        self.window.add(main_vbox)
        self.window.set_size_request(300,300)

        main_vbox.pack_start(post_box,expand=False,fill=True)
        main_vbox.pack_start(self.lines_note_book,expand=True,fill=True)

        stream.start()
        rest.start()
        self.window.show_all()

    def load_auth(self):
        f = open(OAUTH_FILE)
        key = f.readline().strip()
        secret = f.readline().strip()
        return(key,secret)
