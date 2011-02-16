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
import timeline

class IconStore(object):
    def __init__(self):
        # key is url.data is (pixbuf,raw_data)
        self.data_dict = {}
        self.stores = []
        self.semaphore = threading.BoundedSemaphore(5)

        self.default_icon = gtk.gdk.pixbuf_new_from_file(ERROR_ICON)
        self.default_icon = self.default_icon.scale_simple(ICON_SIZE[0],
                ICON_SIZE[1],gtk.gdk.INTERP_BILINEAR)

    def get(self,user):
        if user.profile_image_url in self.data_dict:
            return self.data_dict[user.profile_image_url][0]
        else:
            self.new(user)
            return self.default_icon

    def new(self,user):
        self.data_dict[user.profile_image_url] = (self.default_icon,None)
        newico = NewIcon(user,self.stores,self.data_dict,self.semaphore)
        try:
            newico.start()
        except:
            raise

    def notify(self,event_data):
        time.sleep(3)
        if isinstance(event_data,twoauth.status.TwitterStatus):
            if event_data.user.profile_image_url in self.data_dict:
                n = pynotify.Notification(
                        event_data.user.screen_name,
                        event_data.text,
                        self.data_dict[event_data.user.profile_image_url][1]
                        )
                n.show()
            else:
                n = pynotify.Notification(
                        event_data.user.screen_name,
                        event_data.text,
                        None,
                        )
                n.show()

    def add_store(self,store):
        self.stores.append(store)

class NewIcon(threading.Thread):
    def __init__(self,user,stores,data_dict,semaphore,mode="normal"):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.setName("IconGetting :%s"%user.screen_name)
        self.user = user
        self.stores = stores
        self.mode = mode
        self.data_dict = data_dict
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


        self.data_dict[self.user.profile_image_url] = (pix,ico)
        time.sleep(1)

        for store in self.stores:
            ite = store.get_iter_first()
            while ite:
                url = store.get_value(ite,timeline.USER_ICON_URL)
                if url == self.user.profile_image_url:
                    gtk.gdk.threads_enter()
                    store.set_value(ite,timeline.USER_ICON,pix)
                    gtk.gdk.threads_leave()
                ite = store.iter_next(ite)
