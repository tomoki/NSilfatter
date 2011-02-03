#!/usr/bin/env python
#coding:utf-8

import re
import gtk
import webbrowser

URL_PATTERN = re.compile(r"https?://[A-Z|0-9|_|.|/|-|#|!|?|\-|=]*",re.IGNORECASE)

class UrlWindow(gtk.Window):
    def __init__(self,client):
        self.buttons = []
        self.urls = []
        gtk.Window.__init__(self)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.set_size_request(300,200)
        self.set_transient_for(client.window)
        self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.connect("delete_event",self.close_window)
        self.top = gtk.VBox()
        self.label = gtk.Label()
        self.top.pack_start(self.label,fill=False,expand=False)
        self.add(self.top)

    def close_window(self,widget,data=None):
        return self.hide_on_delete()

    def show_up(self,text):
        self.urls = []
        numofurl = 0
        for p in URL_PATTERN.finditer(text):
            self.urls.append(text[p.start():p.end()])
            numofurl = numofurl + 1

        if len(self.urls) > len(self.buttons):
            for x in range(len(self.urls)-len(self.buttons)):
                self.buttons.append([gtk.LinkButton("http://www.example.net"),False])

        for button in self.buttons:
            if button[1]==True:
                self.top.remove(button[0])
                button[1] = False

        for i,url in enumerate(self.urls):
            self.buttons[i][0].set_uri(url)
            self.buttons[i][0].set_label(url)
            self.buttons[i][1] = True
            self.top.pack_start(self.buttons[i][0],fill=False,expand=False)

        if numofurl == 0:
#            self.label.set_text(u"URLはないです＞＜")
#            self.show_all()
            pass

        elif numofurl == 1:
            webbrowser.open(self.urls[0])

        else:
            self.label.set_text(u"%dこのURLがありました"%numofurl)
            self.show_all()
