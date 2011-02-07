#!/usr/bin/env python
#coding:utf-8

import gtk
import threading
import gobject
from settings import *

class PostView(gtk.TextView):
    __gsignals__= {
            "keypressed":(gobject.SIGNAL_RUN_LAST|gobject.SIGNAL_ACTION,
                         None,
                         (str,),)
            }


gtk.binding_entry_add_signal(PostView,gtk.keysyms.Escape,
        0,"keypressed",str,"esc")

gtk.binding_entry_add_signal(PostView,gtk.keysyms.Return,
        gtk.gdk.CONTROL_MASK,"keypressed",str,"C-Enter")


class PostBox(gtk.HBox):
    def __init__(self,client):
        gtk.HBox.__init__(self)
        self.client = client

        post_view = PostView()
        post_view.connect("keypressed",self.keypressed)
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
        self.in_reply_user_name = None
        self.mode = "post"

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
            self.client.post_window.emit("delete_event",None)
            gtk.gdk.threads_leave()
            if self.mode == "post":
                self.client.api.status_update(text)
            elif self.mode == "reply" or self.mode == "rt":
                self.client.api.status_update(text,
                        in_reply_to_status_id=self.in_reply_id)

        start,end = self.post_buffer.get_bounds()
        string = self.post_buffer.get_text(start,end)

        if string.strip() == "":
            return

        post_thread = threading.Thread(target=p,args=[string.strip()])
        post_thread.start()

    def keypressed(self,widget,what=None):
        if what == "esc":
            self.client.post_window.emit("delete_event",None)
        elif what == "C-Enter":
            self.post(None)


class PostWindow(gtk.Window):
    def __init__(self,client):
        gtk.Window.__init__(self)
        self.client = client

        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.set_size_request(300,200)
        self.set_transient_for(client.window)
        self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.postbox = PostBox(client)
        self.connect("delete_event",self.close_window)
        top = gtk.HBox()
        top.pack_start(self.postbox,expand=True,fill=True)
        self.add(top)
        self.mode = "post"

    def close_window(self,widget,data=None):
        return self.hide_on_delete()

    def change_mode(self,mode):
        self.mode = mode
        self.postbox.mode = mode

    def show_up(self,reply=False,rt=False,in_reply_to_status_id=None):
        if not in_reply_to_status_id == None:
            reply_status = self.client.statuses[in_reply_to_status_id]
            self.postbox.in_reply_id = in_reply_to_status_id
            self.postbox.in_reply_user_name = reply_status.user.screen_name

            if rt:
                self.postbox.post_buffer.set_text(" RT @%s: %s"
                        %(self.postbox.in_reply_user_name,
                          reply_status.text))

                self.postbox.post_buffer.place_cursor(
                        self.postbox.post_buffer.get_start_iter())
                self.change_mode("rt")
            else:
                self.postbox.post_buffer.set_text("@%s "
                        % self.postbox.in_reply_user_name)
                self.change_mode("reply")

        # if self.in_reply_id == None
        else:
            self.postbox.in_reply_id == None
            self.postbox.in_reply_user_name == None
            self.postbox.post_buffer.set_text("")
            self.change_mode("post")

        self.show_all()
