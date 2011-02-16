#!/usr/bin/env python
#coding:utf-8

import gtk
import pango
import time
import gobject
import re
import threading
from settings import *

# DetaStoreDefine.
(
    #Pixbuf
    USER_ICON,
    #str
    MESSAGE,
    #str
    USER_ICON_URL,
    #float
    TWEET_ID,
    #bool
    FAVING,
) = range(5)

name_template = u"%s<small> %s</small>"
retweeted_name_template = u"%s<small> %s Re by %s</small>"
message_template = u"<b>%s</b>\n%s"
in_template = u"<small><b>-->%s</b>\n%s</small>"
adding_template = u"%s\n%s"


class Timeline(gtk.TreeView):
    # keypressed Event.
    __gsignals__= {
            "keypressed":(gobject.SIGNAL_RUN_LAST|gobject.SIGNAL_ACTION,
                         None,
                         (str,),)
            }

    def __init__(self,client,mode="home",*args,**kwargs):
        gtk.TreeView.__init__(self,*args,**kwargs)
        # model That save Column data.
        self.liststore = gtk.ListStore(gtk.gdk.Pixbuf,str,
                                       str,gobject.TYPE_INT64,
                                       gobject.TYPE_BOOLEAN,
                                       )
        self.client = client
        self.mode = mode

        self.client.iconstore.add_store(self.liststore)
        self.client.reply_getter.add_timeline(self)

        self.iconstore = self.client.iconstore
        self.reply_getter = self.client.reply_getter
        self.twtool = self.client.twtool
        self.api = self.client.api
        self.statuses = self.client.statuses
        self.id_list = []
        self.added = False

        # When keypressed,call self.keypressed.
        self.connect("keypressed",self.keypressed)

        # make headers hide.
        self.set_headers_visible(False)
        # make rules True.
        self.set_rules_hint(True)

        # when size changed,call self.on_size_changed.
        self.connect("size-allocate",self.on_size_changed)

        self.set_resize_mode(gtk.RESIZE_IMMEDIATE)

        # when row_activated(row_clicked,enter pressed,and so on.)
        # call self.on_treeview_row_activated.
        self.connect("row_activated",self.on_treeview_row_activated)

        self.set_model(self.liststore)

        # cell_p is cellrenderer for icons.
        self.cell_p = gtk.CellRendererPixbuf()
        # col_p is treeviewcolumn for icons.
        # This is first column.
        self.col_p = gtk.TreeViewColumn("ICON",
                                        self.cell_p,
                                        pixbuf=USER_ICON,
                                       )

        # cell_t is cellrenderer for text.
        self.cell_t = gtk.CellRendererText()
        self.cell_t.set_property("wrap_mode",pango.WRAP_CHAR)

        # col_t is treeviewcolumn for text.
        # This is second column.
        self.col_t = gtk.TreeViewColumn("TEXT",
                                        self.cell_t,
                                        markup=MESSAGE,
                                        )

        # Size propertys for col_t.
        self.col_t.set_property("sizing",gtk.TREE_VIEW_COLUMN_FIXED)
        self.col_t.set_expand(True)

        self.noent_amp = re.compile(u"""&(?![A-Za-z]+;)""")

        self.append_column(self.col_p)
        self.append_column(self.col_t)

    # Get Status located in cursor now.
    def get_selected_status(self):
        (path,column) = self.get_cursor()
        if path != None:
            return self.get_status(path)
        else:
            return None

    def get_status_from_point(self,x,y):
        path = self.get_path_at_pos(x,y)
        if path != None:
            return self.get_status(path)
        else:
            return None

    def get_status(self,path):
        ite = self.liststore.get_iter(path)
        tweet_id = self.liststore.get_value(ite,TWEET_ID)
        return self.statuses[tweet_id]

    # replace &amp; to &
    def _replace_amp(self,string):
        amp = string.find(u"&")
        if amp == -1:
            return string

        entity_match = self.noent_amp.finditer(string)
        for i,e in enumerate(entity_match):
            string = u"%s&amp;%s"%(
                    string[:e.start() + (4*i)],
                    string[e.start() + (4*i) + 1:])
        return string

    def prepend_new_statuses(self,new_ids,first=False):
        # (id,packed_status) list
        toappends = []

        for st_id in new_ids:
            st = self.statuses[st_id]
            if not st_id in self.id_list:
                if self.mode == "home":
                    if not st_id in self.id_list:
                        toappends.append((st_id,self.status_pack(st_id)))
                        self.added = True

                elif self.mode == "mention":
                    if self.client.my_name.lower() in st.text.lower():
                        toappends.append((st_id,self.status_pack(st_id)))
                        if not first:
                            self.iconstore.notify(st)
                        self.added = True

        gtk.gdk.threads_enter()
        for st_tuple in toappends:
            self.id_list.append(st_tuple[0])
            self.liststore.prepend(st_tuple[1])
        gtk.gdk.threads_leave()

    # make status packed for prepend to treeview.
    def status_pack(self,i):
        status = self.statuses[i]

        if status.retweeted_status != None:
            rtstatus = status.retweeted_status
            name = retweeted_name_template % (rtstatus.user.screen_name,
                                       rtstatus.user.name,
                                       status.user.screen_name,
                                      )

            text = self._replace_amp(rtstatus.text)
            message = message_template%(name,text)
            message = self.twtool.get_colored_url(message)
            message = self.twtool.get_colored_user(message)

            if not rtstatus.in_reply_to_status_id == None:
                in_s = self.reply_getter.get(rtstatus)
                if not in_s == None:
                    in_name = name_template % (in_s.user.screen_name,
                                               in_s.user.name
                                              )

                    in_text = self._replace_amp(in_s.text)
                    in_message = in_template % (in_name,in_text)

                    message = adding_template % (message,in_message)

            if rtstatus.favorited:
                message = FAV_TEXT + message

            return(self.iconstore.get(rtstatus.user),
                   message,
                   rtstatus.user.profile_image_url,
                   rtstatus.id,
                   False,
                   )
        else:
            name = name_template % (status.user.screen_name,
                                  status.user.name,
                                 )

            text = self._replace_amp(status.text)
            message = message_template%(name,text)
            message = self.twtool.get_colored_url(message)
            message = self.twtool.get_colored_user(message)

            if not status.in_reply_to_status_id == None:
                in_s = self.reply_getter.get(status)
                if not in_s == None:
                    in_name = name_template % (in_s.user.screen_name,
                                               in_s.user.name
                                              )

                    in_text = self._replace_amp(in_s.text)
                    in_message = in_template % (in_name,in_text)

                    message = adding_template % (message,in_message)

            if status.favorited:
                message = FAV_TEXT + message

            return(self.iconstore.get(status.user),
                   message,
                   status.user.profile_image_url,
                   status.id,
                   False,
                   )

    def add_reply_to(self,in_s,ite):
        before_message = self.liststore.get_value(ite,MESSAGE).decode(u"utf-8")

        in_name = name_template % (in_s.user.screen_name,
                                   in_s.user.name,
                                  )

        in_text = self._replace_amp(in_s.text)

        in_message = in_template % (in_name,in_text)

        message = adding_template % (before_message,in_message)

        gtk.gdk.threads_enter()
        self.liststore.set_value(ite,MESSAGE,message)
        gtk.gdk.threads_leave()

    # When size changed,call this.
    def on_size_changed(self,treeview,allocate):
        width = treeview.get_allocation().width
        columns = treeview.get_columns()
        width2 = 0
        #     |pix|text|
        #         <---->
        for c in columns[:MESSAGE]+columns[MESSAGE+1:]:
            width2 = width2 + c.get_property("width")

        cell_r = columns[MESSAGE].get_cell_renderers()
        cell_r[0].set_property("wrap-width",width-width2-10)
        def refresh_text():
            i = self.liststore.get_iter_first()
            while i:
                txt = self.liststore.get_value(i,MESSAGE)
                gtk.gdk.threads_enter()
                self.liststore.set_value(i,MESSAGE,txt)
                gtk.gdk.threads_leave()
                i = self.liststore.iter_next(i)

        t = threading.Thread(target=refresh_text)
        t.setName("RefreshText")
        t.start()

    def on_treeview_row_activated(self,treeview,path,view_column):
        pass

    # keypressed event.
    # what is str(what key pressed)
    def keypressed(self,tv, what):
        # if j pressed,Scroll to next cell.
        if what == "j":
            # this is ((x,),gtkColumn)
            now = self.get_cursor()
            if not now == (None,None):
                if not now[0][0] == len(self.liststore)-1:
                    self.set_cursor(now[0][0]+1)

        # if k pressed,Scroll to previous cell.
        elif what == "k":
            now = self.get_cursor()
            if not now == (None,None):
                if not now[0][0] == 0:
                    self.set_cursor(now[0][0]-1)

        # if g pressed,Scroll to first cell.
        elif what == "g":
            now = self.get_cursor()
            if not now == (None,None):
                self.set_cursor(0)

        # if G pressed,Scroll to last cell.
        elif what == "G":
            now = self.get_cursor()
            if not now == (None,None):
                self.set_cursor(len(self.liststore)-1)

        # if r pressed,show reply window.
        elif what == "r":
            st = self.get_selected_status()

            self.client.post_window.show_up(reply=True,
                        in_reply_to_status_id=st.id)

        elif what == "R":
            st = self.get_selected_status()

            self.client.post_window.show_up(rt=True,
                        in_reply_to_status_id=st.id)

        elif what == "a":
            self.client.post_window.show_up()

        elif what == "h":
            self.client.lines_note_book.prev_page()

        elif what == "l":
            self.client.lines_note_book.next_page()

        elif what == "u":
            s = self.get_selected_status()
            if not s == None:
                self.client.url_window.show_up(s.text)

        elif what == "t":
            s = self.get_selected_status()
            if not s == None and not s.user.screen_name == self.client.my_name:
                dialog = gtk.MessageDialog(self.client.window,gtk.DIALOG_MODAL,
                        gtk.MESSAGE_QUESTION,
                        gtk.BUTTONS_OK_CANCEL,
                        u"公式リツイートします")

                r = dialog.run()
                dialog.destroy()
                if r == gtk.RESPONSE_OK:
                    def retweet():
                        self.client.api.status_retweet(s.id)
                    t = threading.Thread(target=retweet)
                    t.start()

        elif what == "f":
            s = self.get_selected_status()


            if not s == None:
                (path,column) = self.get_cursor()
                ite = self.liststore.get_iter(path)
                faving = self.liststore.get_value(ite,FAVING)
                if not faving:
                    if not s.favorited:
                        fav = True
                        def favorite():
                            self.liststore.set_value(ite,FAVING,True)
                            new_s = self.api.favorite_create(s.id)
                            self.statuses[new_s.id] = new_s
                            self.liststore.set_value(ite,FAVING,False)
                            self.liststore.set_value(ite,TWEET_ID,new_s.id)
                        t = threading.Thread(target=favorite)
                        t.start()
                    else:
                        fav = False
                        def unfavorite():
                            self.liststore.set_value(ite,FAVING,True)
                            new_s = self.api.favorite_destroy(s.id)
                            self.statuses[new_s.id] = new_s
                            self.liststore.set_value(ite,FAVING,False)
                            self.liststore.set_value(ite,TWEET_ID,new_s.id)

                        t = threading.Thread(target=unfavorite)
                        t.start()

                    before_text = self.liststore.get_value(ite,MESSAGE).decode("utf-8")
                    if fav:
                        self.liststore.set_value(ite,MESSAGE,
                                FAV_TEXT+before_text)
                    else:
                        self.liststore.set_value(ite,MESSAGE,
                                before_text[len(FAV_TEXT):])

# when j is pressed,call keypressed event.
gtk.binding_entry_add_signal(Timeline,gtk.keysyms.J,
        0,"keypressed",str,"j")

# when k is pressed,call keypressed event.
gtk.binding_entry_add_signal(Timeline,gtk.keysyms.K,
        0,"keypressed",str,"k")

# when g is pressed,call keypressed event.
gtk.binding_entry_add_signal(Timeline,gtk.keysyms.G,
        0,"keypressed",str,"g")

# when G is pressed,call keypressed event.
# Shift_Mask.not g but G.
gtk.binding_entry_add_signal(Timeline,gtk.keysyms.G,
        gtk.gdk.SHIFT_MASK,"keypressed",str,"G")

# when r is pressed,call keypressed event.
gtk.binding_entry_add_signal(Timeline,gtk.keysyms.R,
        0,"keypressed",str,"r")

# when t is pressed,call keypressed event.
gtk.binding_entry_add_signal(Timeline,gtk.keysyms.A,
        0,"keypressed",str,"a")

# when h is pressed,call keypressed event.
gtk.binding_entry_add_signal(Timeline,gtk.keysyms.H,
        0,"keypressed",str,"h")

# when l is pressed,call keypressed event.
gtk.binding_entry_add_signal(Timeline,gtk.keysyms.L,
        0,"keypressed",str,"l")

# when u is pressed,call keypressed event.
gtk.binding_entry_add_signal(Timeline,gtk.keysyms.U,
        0,"keypressed",str,"u")

# when t is pressed,call keypressed event.
gtk.binding_entry_add_signal(Timeline,gtk.keysyms.T,
        0,"keypressed",str,"t")

# when f is pressed,call keypressed event.
gtk.binding_entry_add_signal(Timeline,gtk.keysyms.F,
        0,"keypressed",str,"f")

# when r is pressed,call keypressed event.
# Shift_Mask.not r but R
gtk.binding_entry_add_signal(Timeline,gtk.keysyms.R,
        gtk.gdk.SHIFT_MASK,"keypressed",str,"R")

class Timelinesw(gtk.ScrolledWindow):
    def __init__(self,client,mode="home"):
        gtk.ScrolledWindow.__init__(self)

        self.view = Timeline(client,mode)
        self.add(self.view)
        self.set_policy(gtk.POLICY_NEVER,gtk.POLICY_ALWAYS)

        self.vadj = self.get_vadjustment()
        self.vadj_upper = self.vadj.upper
        self.vadj_lock = False
        self.vadj_len = 0

        self.vadj.connect("changed",self.on_vadjustment_changed)
        self.vadj.connect("value-changed",self.on_vadjustment_value_changed)
        self.show_all()

    def on_vadjustment_changed(self,adj):
        if not self.vadj_lock and self.vadj_upper < adj.upper:
            if len(self.view.liststore) != 0:
                self.view.scroll_to_cell((0,))
                self.view.added = False
        self.vadj_upper = adj.upper
        self.vadj_len = len(self.view.liststore)-1

    def on_vadjustment_value_changed(self,adj):
        if adj.value == 0.0:
            self.vadj_lock = False

        elif self.vadj_upper == adj.upper and not self.view.added:
            self.vadj_lock = True
