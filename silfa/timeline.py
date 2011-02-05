#/usr/bin/env python
#coding:utf-8

import gtk
import threading
import pango
import re
import time
import gobject
import pynotify
from settings import *

class Timeline(gtk.TreeView):
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

    def __init__(self,client,mode="home",*args,**kwargs):
        # Store That save Column data.
        self.store = gtk.ListStore(gtk.gdk.Pixbuf,str)
        self.id_list = []

        self.client = client
        self.mode = mode
        self.client.store.add_store(self)
        self.client.reply_getter.add_timeline(self)
        self.iconstore = self.client.store
        self.reply_getter = self.client.reply_getter

        gtk.TreeView.__init__(self,*args,**kwargs)

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

        self.set_model(self.store)

        # cell_p is cellrenderer for icons.
        self.cell_p = gtk.CellRendererPixbuf()
        # col_p is treeviewcolumn for icons.
        # This is first column.
        self.col_p = gtk.TreeViewColumn("ICON",
                                        self.cell_p,
                                        pixbuf=self.COLUMN_ICON,
                                       )

        # cell_t is cellrenderer for text.
        self.cell_t = gtk.CellRendererText()
        self.cell_t.set_property("wrap_mode",pango.WRAP_CHAR)

        # col_t is treeviewcolumn for text.
        # This is second column.
        self.col_t = gtk.TreeViewColumn("TEXT",
                                        self.cell_t,
                                        markup=self.COLUMN_TEXT,
                                        )

        # Size propertys for col_t.
        self.col_t.set_property("sizing",gtk.TREE_VIEW_COLUMN_FIXED)
        self.col_t.set_expand(True)

        self.noent_amp = re.compile(u"""&(?![A-Za-z]+;)""")
        self._old_path = None
        self.added = False

        self.append_column(self.col_p)
        self.append_column(self.col_t)

    # Get Status located in cursor now.
    def get_selected_status(self):
        (path,column) = self.get_cursor()
        if path != None:
            return self.get_status(path[0])
        else:
            return None

    def get_status_from_point(self,x,y):
        path = self.get_path_at_pos(x,y)
        if path != None:
            return self.get_status(path)
        else:
            return None

    def get_status(self,path):
        return self.client.statuses[self.id_list[path]]

    # keypressed event.
    # what is str(what key pressed)
    def keypressed(self,tv, what):
        # if j pressed,Scroll to next cell.
        if what == "j":
            # this is ((x,),gtkColumn)
            now = self.get_cursor()
            if not now == (None,None):
                if not now[0][0] == len(self.store)-1:
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
                self.set_cursor(len(self.store)-1)

        # if r pressed,show reply window.
        elif what == "r":
            now = self.get_cursor()
            st = self.get_status(now[0][0])

            if st.retweeted_status == None:
                self.client.reply_window.show_up(st.id)
            else:
                self.client.reply_window.show_up(st.retweeted_status.id)

        elif what == "R":
            now = self.get_cursor()
            st = self.get_status(now[0][0])

            if st.retweeted_status == None:
                self.client.reply_window.show_up(st.id,rt=True)
            else:
                self.client.reply_window.show_up(st.retweeted_status.id,rt=True)

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
            if not s == None:
                if not s.user.screen_name==self.client.my_name:
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
            st = self.client.statuses[st_id]
            if self.mode == "home":
                if not st_id in self.id_list:
                    toappends.append((st_id,self.status_pack(st_id)))
                    self.added = True

            elif self.mode == "mention":
                if ("@" + self.client.my_name).lower() in st.text.lower():
                    if not st_id in self.id_list:
                        toappends.append((st_id,self.status_pack(st_id)))
                        if not first:
                            self.iconstore.notify(st)
                        self.added = True

            elif self.mode == "event":
                pass

        gtk.gdk.threads_enter()
        for st_tuple in toappends:
            self.id_list.insert(0,st_tuple[0])
            self.store.prepend(st_tuple[1])
        gtk.gdk.threads_leave()

    # make status packed for prepend to treeview.
    def status_pack(self,i):
        status = self.client.statuses[i]
        name = status.user.screen_name + "<span foreground='#333333'><small> %s</small></span>"%status.user.name

        # if status is retweeted event.
        if status.retweeted_status != None:
            rtstatus = status
            status = status.retweeted_status
            name = "%s <span foreground='#333333'><small> %s Re by %s</small></span>" %(
                    status.user.screen_name,status.user.name,rtstatus.user.screen_name)

        text = self._replace_amp(status.text)

        tmpl = u"<b>%s</b>\n%s"

        message = tmpl % (name,text)
        if not status.in_reply_to_status_id == None:
            s = self.reply_getter.get(status)
            if not s == None:
                in_name = s.user.screen_name + "<span foreground='#333333'><small> %s</small></span>"%s.user.name

                in_text = self._replace_amp(s.text)

                in_tmpl = u"--→<b>%s</b>\n%s"

                in_message = in_tmpl % (in_name,in_text)

                message = "%s\n%s"%(message,in_message)


        # return (pixbuf,text)
        return(self.iconstore.get(status.user),
                message)

    def add_reply_to(self,in_status,ite,n):
        status = self.get_status(n)

        name = status.user.screen_name + "<span foreground='#333333'><small> %s</small></span>"%status.user.name
        in_name = in_status.user.screen_name + "<span foreground='#333333'><small> %s</small></span>"%in_status.user.name


        # if status is retweeted event.
        if status.retweeted_status != None:
            rtstatus = status
            status = status.retweeted_status
            name = "%s <span foreground='#333333'><small> %s Re by %s</small></span>" %(
                    status.user.screen_name,status.user.name,rtstatus.user.screen_name)

        text = self._replace_amp(status.text)
        in_text = self._replace_amp(in_status.text)

        tmpl = u"<b>%s</b>\n%s"
        in_tmpl = u"--→<b>%s</b>\n%s"

        message = tmpl % (name,text)
        in_message = in_tmpl % (in_name,in_text)

        message = "%s\n%s"%(message,in_message)

        gtk.gdk.threads_enter()
        self.store.set_value(ite,1,message)
        gtk.gdk.threads_leave()


    # When size changed,call this.
    def on_size_changed(self,treeview,allocate):
        width = treeview.get_allocation().width
        columns = treeview.get_columns()
        width2 = 0
        #     |pix|text|
        #         <---->
        for c in columns[:self.COLUMN_TEXT]+columns[self.COLUMN_TEXT+1:]:
            width2 = width2 + c.get_property("width")

        cell_r = columns[self.COLUMN_TEXT].get_cell_renderers()
        cell_r[0].set_property("wrap-width",width-width2-10)
        def refresh_text():
            i = self.store.get_iter_first()
            while i:
                txt = self.store.get_value(i,self.COLUMN_TEXT)
                gtk.gdk.threads_enter()
                self.store.set_value(i,self.COLUMN_TEXT,txt)
                gtk.gdk.threads_leave()
                i = self.store.iter_next(i)

        t = threading.Thread(target=refresh_text)
        t.setName("RefreshText")
        t.start()

    def on_treeview_row_activated(self,treeview,path,view_column):
        status = self.get_status(path[0])

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
