#coding:utf-8

import gtk
import threading
from settings import *


class PostBox(gtk.HBox):
    def __init__(self,client):
        gtk.HBox.__init__(self)
        self.client = client

        post_view = gtk.TextView()
        post_view.set_wrap_mode(gtk.WRAP_CHAR)

        self.post_buffer = post_view.get_buffer()
        self.post_buffer.connect("changed",self.post_buffer_changed)

        self.post_scrolled_window = gtk.ScrolledWindow()
        self.post_scrolled_window.add(post_view)
        self.post_scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
                gtk.POLICY_AUTOMATIC)
        self.post_scrolled_window.set_placement(gtk.CORNER_BOTTOM_RIGHT)
        self.post_scrolled_window.set_size_request(10,10)

        self.post_button = gtk.Button("000")
        self.post_button.connect("clicked",self.post)
        self.post_button.set_sensitive(False)

        self.pack_start(self.post_scrolled_window,expand=True,fill=True)
        self.pack_start(self.post_button,expand=False,fill=True)

    # self.post_buffer_changed 
    def post_buffer_changed(self,b):
        number = b.get_char_count()
        self.post_button.set_label("%03d"%(number))
        if number > 140 or number == 0:
            if self.post_button.get_sensitive():
                self.post_button.set_sensitive(False)

        elif number <= 140 and number != 0:
            if not self.post_button.get_sensitive():
                self.post_button.set_sensitive(True)

    # self.post_button is clicked
    def post(self,button):
        def p(text):
            gtk.gdk.threads_enter()
            self.post_buffer.set_text("")
            gtk.gdk.threads_leave()
            self.client.api.status_update(text)

        start,end = self.post_buffer.get_bounds()
        string = self.post_buffer.get_text(start,end)

        if string.strip() == "":
            return

        post_thread = threading.Thread(target=p,args=[string.strip()])
        post_thread.start()

