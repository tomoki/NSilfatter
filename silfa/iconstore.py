#!/usr/bin/env python
#coding:utf-8

import pygtk
import gtk
import sys
import threading
import urllib
import time
import pynotify
from settings import *
import twoauth

class IconStore(object):
    def __init__(self):
        self.data = {}
        self.raw_data = {}
        self.stores = []
        self.semaphore = threading.BoundedSemaphore(5)

        self.default_icon = gtk.gdk.pixbuf_new_from_file(ERROR_ICON)
        self.default_icon = self.default_icon.scale_simple(ICON_SIZE[0],ICON_SIZE[1],gtk.gdk.INTERP_BILINEAR)

    def get(self,user):
        if user.profile_image_url in self.data:
            return self.data[user.profile_image_url]
        else:
            self.new(user)
            return self.default_icon

    def new(self,user):
        self.data[user.profile_image_url] = self.default_icon
        newico = NewIcon(user,self.stores,self.data,self.raw_data,self.semaphore)
        try:
            newico.start()
        except:
            pass

    def notify(self,event_data):
        if isinstance(event_data,twoauth.status.TwitterStatus):
            if event_data.user.profile_image_url in self.raw_data:
                n = pynotify.Notification(
                        event_data.user.screen_name,
                        event_data.text,
                        self.raw_data[event_data.user.profile_image_url]
                        )
                n.show()
            else:
                n = pynotify.Notification(
                        event_data.user.screen_name,
                        event_data.text,
                        None,
                        )
                n.show()

    def add_store(self,timeline):
        self.stores.append(timeline)

class NewIcon(threading.Thread):
    def __init__(self,user,timelines,icons,raw_data,semaphore,mode="normal"):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.setName("IconGetting :%s"%user.screen_name)
        self.user = user
        self.timelines = timelines
        self.icons = icons
        self.mode = mode
        self.raw_data = raw_data
        self.semaphore = semaphore

    def run(self):
        self.semaphore.acquire()
        for i in range(3):
            try:
                ico = urllib.urlretrieve(str(self.user.profile_image_url))[0]
                break
            except:
                ico = None

        self.semaphore.release()

        try:
            pix = gtk.gdk.pixbuf_new_from_file(ico)
        except:
            pix = None
            return

        pix = pix.scale_simple(ICON_SIZE[0],ICON_SIZE[1],
                gtk.gdk.INTERP_BILINEAR)

        if pix == None:
            return


        self.icons[self.user.profile_image_url] = pix
        self.raw_data[self.user.profile_image_url] = ico
        time.sleep(1)

        for timeline in self.timelines:
            i = timeline.store.get_iter_first()
            n = 0
            while i:
                status = timeline.get_status(n)
                if not status.retweeted_status == None:
                    status = status.retweeted_status

                url = status.user.profile_image_url
                if url == self.user.profile_image_url:
                    gtk.gdk.threads_enter()
                    timeline.store.set_value(i,0,pix)
                    gtk.gdk.threads_leave()
                i = timeline.store.iter_next(i)
                n = n + 1
