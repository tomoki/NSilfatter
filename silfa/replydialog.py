#!/usr/bin/env python
#coding:utf-8

import gtk
import threading
from settings import *


class ReplyBox(gtk.HBox):
    def __init__(self,client):
        gtk.HBox.__init__(self)
        self.client = client

        post_view = gtk.TextView()
        post_view.set_wrap_mode(gtk.WRAP_CHAR)

        self.post_buffer = post_view.get_buffer()
        # When post_view edited.
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

        self.in_reply_id = None
        self.in_reply_user = None

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
            self.client.reply_window.emit("delete_event",None)
            gtk.gdk.threads_leave()
            self.client.api.status_update(text,
                    in_reply_to_status_id=self.in_reply_id)

        start,end = self.post_buffer.get_bounds()
        string = self.post_buffer.get_text(start,end)

        if string.strip() == "":
            return

        post_thread = threading.Thread(target=p,args=[string.strip()])
        post_thread.start()

class ReplyWindow(gtk.Window):
    def __init__(self,client):
        gtk.Window.__init__(self)
        self.client = client

        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.set_size_request(300,200)
        self.set_transient_for(client.window)
        self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.replybox = ReplyBox(client)
        self.connect("delete_event",self.close_window)
        top = gtk.HBox()
        top.pack_start(self.replybox,expand=True,fill=True)
        self.add(top)

    def close_window(self,widget,data=None):
        return self.hide_on_delete()

    def show_up(self,in_reply_to_status_id,rt=False):
        reply_status = self.client.statuses[in_reply_to_status_id]
        self.replybox.in_reply_id = in_reply_to_status_id
        self.replybox.in_reply_user_name = reply_status.user.screen_name
        if rt:
            self.replybox.post_buffer.set_text(" RT @%s: %s"
                    %(self.replybox.in_reply_user_name,
                      reply_status.text))

            self.replybox.post_buffer.place_cursor(
                    self.replybox.post_buffer.get_start_iter())
        else:
            self.replybox.post_buffer.set_text("@%s "
                    % self.replybox.in_reply_user_name)

        self.show_all()

