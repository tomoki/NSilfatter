#!/usr/bin/env python
#coding:utf-8

import gtk
import threading
import pango
import re
import gobject
import time
import pynotify
import twoauth
from settings import *

(
    #Pixbuf
    USER_ICON,
    #str
    MESSAGE,
    #str
    USER_ICON_URL,
    INDEX,
) = range(4)

name_template = u"<b>%s<small> %s</small></b>"
favorited_template = FAV_TEXT + u"%s\n%s"
retweeted_template =  RT_TEXT + u"%s\n%s"

class Eventline(gtk.TreeView):
    # keypressed Event.
    __gsignals__= {
            "keypressed":(gobject.SIGNAL_RUN_LAST|gobject.SIGNAL_ACTION,
                         None,
                         (str,),)
            }

    def __init__(self,client,*args,**kwargs):
        gtk.TreeView.__init__(self,*args,**kwargs)
        self.liststore = gtk.ListStore(gtk.gdk.Pixbuf,str,
                                       str,gobject.TYPE_INT64)

        self.store = gtk.ListStore(gtk.gdk.Pixbuf,str)
        self.event_list = []
        self.added = False
        self.client = client
        self.client.iconstore.add_store(self.liststore)
        self.iconstore = self.client.iconstore

        self.api = self.client.api
        self.statuses = self.client.statuses
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
    def get_selected_event(self):
        (path,column) = self.get_cursor()
        print path
        if path != None:
            return self.get_event(path)
        else:
            return None

    def get_status_from_event(self,x,y):
        path = self.get_path_at_pos(x,y)
        if path != None:
            return self.get_event(path)
        else:
            return None

    def get_event(self,path):
        ite = self.liststore.get_iter(path)
        index = self.liststore.get_value(ite,INDEX)
        return self.event_list[index]

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
        # Retweeted_list
        rt_list = []
        for st_id in new_ids:
            st = self.statuses[st_id]
            if not st.retweeted_status == None:
                if st.retweeted_status.user.screen_name == self.client.my_name:
                    rt_list.append(self.event_pack(st))
                    self.added = True

        gtk.gdk.threads_enter()
        for rt_event in rt_list:
            self.liststore.prepend(rt_event)
        gtk.gdk.threads_leave()

    def prepend_new_events(self,events):
        new_e = []
        for e in events:
            new_e.append(self.event_pack(e))
            self.added = True

        gtk.gdk.threads_enter()
        for e in new_e:
            if not e == None:
                self.liststore.prepend(e)
        gtk.gdk.threads_leave()

    # make status packed for prepend to treeview.
    def event_pack(self,event):
        if isinstance(event,twoauth.status.TwitterStatus):
            rtstatus = event.retweeted_status
            name = name_template % (event.user.screen_name,event.user.name)
            text = self._replace_amp(rtstatus.text)
            message = retweeted_template % (name,text)
            index = len(self.event_list)
            return_data = (self.iconstore.get(event.user),
                           message,
                           event.user.profile_image_url,
                           index,
                          )
            self.event_list.append(return_data)
            return return_data

        elif isinstance(event,twoauth.event.favorite):
            source = event.source
            target = event.target
            target_object = event.target_object
            name = name_template %(source.screen_name,source.name)
            text = self._replace_amp(target_object.text)
            message = favorited_template % (name,text)

            index = len(self.event_list)
            return_data = (self.iconstore.get(source),
                           message,
                           source.profile_image_url,
                           index,
                          )
            self.event_list.append(return_data)
            return return_data


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

        elif what == "a":
            self.client.post_window.show_up()

        elif what == "h":
            self.client.lines_note_book.prev_page()

        elif what == "l":
            self.client.lines_note_book.next_page()


# when j is pressed,call keypressed event.
gtk.binding_entry_add_signal(Eventline,gtk.keysyms.J,
        0,"keypressed",str,"j")

# when k is pressed,call keypressed event.
gtk.binding_entry_add_signal(Eventline,gtk.keysyms.K,
        0,"keypressed",str,"k")

# when g is pressed,call keypressed event.
gtk.binding_entry_add_signal(Eventline,gtk.keysyms.G,
        0,"keypressed",str,"g")

# when G is pressed,call keypressed event.
# Shift_Mask.not g but G.
gtk.binding_entry_add_signal(Eventline,gtk.keysyms.G,
        gtk.gdk.SHIFT_MASK,"keypressed",str,"G")

# when r is pressed,call keypressed event.
gtk.binding_entry_add_signal(Eventline,gtk.keysyms.R,
        0,"keypressed",str,"r")

# when t is pressed,call keypressed event.
gtk.binding_entry_add_signal(Eventline,gtk.keysyms.A,
        0,"keypressed",str,"a")

# when h is pressed,call keypressed event.
gtk.binding_entry_add_signal(Eventline,gtk.keysyms.H,
        0,"keypressed",str,"h")

# when l is pressed,call keypressed event.
gtk.binding_entry_add_signal(Eventline,gtk.keysyms.L,
        0,"keypressed",str,"l")

# when u is pressed,call keypressed event.
gtk.binding_entry_add_signal(Eventline,gtk.keysyms.U,
        0,"keypressed",str,"u")

# when t is pressed,call keypressed event.
gtk.binding_entry_add_signal(Eventline,gtk.keysyms.T,
        0,"keypressed",str,"t")

# when f is pressed,call keypressed event.
gtk.binding_entry_add_signal(Eventline,gtk.keysyms.F,
        0,"keypressed",str,"f")

# when r is pressed,call keypressed event.
# Shift_Mask.not r but R
gtk.binding_entry_add_signal(Eventline,gtk.keysyms.R,
        gtk.gdk.SHIFT_MASK,"keypressed",str,"R")

class Eventlinesw(gtk.ScrolledWindow):
    def __init__(self,client):
        gtk.ScrolledWindow.__init__(self)

        self.view = Eventline(client)
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
            if len(self.view.store) != 0:
                self.view.scroll_to_cell((0,))
                self.view.added = False
        self.vadj_upper = adj.upper
        self.vadj_len = len(self.view.store)

    def on_vadjustment_value_changed(self,adj):
        if adj.value == 0.0:
            self.vadj_lock = False

        elif self.vadj_upper == adj.upper and not self.view.added:
            self.vadj_lock = True
