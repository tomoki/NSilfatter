#!/usr/bin/env python
#coding:utf-8

import gtk
from cwindow import ClientWindow
from iconstore import IconStore
from replygetter import InReplyGetter
from postdialog import PostWindow
from urldialog import UrlWindow
from timeline import *
from eventline import *
import pango
import twoauth
import sys
from settings import *
import pynotify
from timelinethread import StreamingThread,RestThread
import twittertool

class client(object):
    def __init__(self):
        key,secret = self.load_auth()
        self.api = twoauth.api(CONSUMER_KEY,CONSUMER_SECRET,key,secret)
        self.me = self.api.verify_credentials()
        self.my_name = self.me.screen_name
        pynotify.init("Silfatter")
        self.statuses = {}

        self.iconstore = IconStore()
        self.reply_getter = InReplyGetter(self)
        self.twtool = twittertool.TwitterTool()

        self.window = ClientWindow()

        self.accelgroup = gtk.AccelGroup()
        self.window.add_accel_group(self.accelgroup)
        stream = StreamingThread(self)
        rest = RestThread(self)

        main_vbox = gtk.VBox()

        self.lines_note_book = gtk.Notebook()
        self.home_timeline_sw = Timelinesw(self,"home")
        self.mention_timeline_sw = Timelinesw(self,"mention")
        self.event_timeline_sw = Eventlinesw(self)

        stream.add_timeline(self.home_timeline_sw.view)
        stream.add_timeline(self.mention_timeline_sw.view)
        stream.add_eventline(self.event_timeline_sw.view)

        rest.add(self.home_timeline_sw.view)
        rest.add(self.mention_timeline_sw.view)

        self.post_window = PostWindow(self)
        self.url_window = UrlWindow(self)

        self.lines_note_book.append_page(self.home_timeline_sw,gtk.Label("Home"))
        self.lines_note_book.append_page(self.mention_timeline_sw,gtk.Label("Mention"))
        self.lines_note_book.append_page(self.event_timeline_sw,gtk.Label("Event"))

        self.window.add(main_vbox)
        self.window.set_size_request(300,300)

        main_vbox.pack_start(self.lines_note_book,expand=True,fill=True)

        stream.start()
        rest.start()
        self.window.show_all()

    def load_auth(self):
        f = open(OAUTH_FILE)
        key = f.readline().strip()
        secret = f.readline().strip()
        return(key,secret)
