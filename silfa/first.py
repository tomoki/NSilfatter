#!/usr/bin/env python
#coding:utf-8

import gtk
import webbrowser
from settings import *
import twoauth
import sys

DESCRIPTION = \
u"""Silfatterへようこそ！
まず最初にTwitterの認証が必要です。
下のボタンからTwitterにアクセスしてください。
"""

HOWTO = \
u"""許可したら暗証番号を下のエントリーに
コピペしてください。そしてボタンをポチッと。
"""

TITLE = u"ようこそ！"
ACCESS_LABEL = u"あくせす"
AUTH_LABEL = u"認証！"

class first(object):
    def __init__(self):
        self.success = False
        self.oa = twoauth.oauth(CONSUMER_KEY,CONSUMER_SECRET)
        self.window = gtk.Window()
        self.window.connect("delete_event",self.close)
        self.window.set_title(TITLE)

        self.main_vbox = gtk.VBox()
        self.window.add(self.main_vbox)

        self.descript_label = gtk.Label()
        self.descript_label.set_label(DESCRIPTION)
        self.descript_label.set_line_wrap(gtk.WRAP_CHAR)
        self.access_button = gtk.Button()
        self.access_button.set_label(ACCESS_LABEL)
        self.access_button.connect("clicked",self.access)

        entry_box = gtk.HBox()
        self.pin_entry = gtk.Entry()
        self.pin_button = gtk.Button()
        self.pin_button.set_label(AUTH_LABEL)
        self.pin_button.connect("clicked",self.pin)
        self.pin_button.set_sensitive(False)

        entry_box.pack_start(self.pin_entry,expand=True,fill=True)
        entry_box.pack_start(self.pin_button,expand=False,fill=True)

        self.main_vbox.pack_start(self.descript_label,expand=False,fill=True)
        self.main_vbox.pack_start(self.access_button,expand=False,fill=True)
        self.main_vbox.pack_start(entry_box,expand=False,fill=True)
        self.window.show_all()

    def access(self,widget):
        self.req_token = self.oa.request_token()
        auth_url = self.oa.authorize_url(self.req_token)

        webbrowser.open(auth_url)
        self.descript_label.set_label(HOWTO)
        self.pin_button.set_sensitive(True)

    def pin(self,widget):
        try:
            pin = self.pin_entry.get_text().strip()
            acc_token = self.oa.access_token(self.req_token,pin)
            token = acc_token["oauth_token"]
            token_secret = acc_token["oauth_token_secret"]
            f = open(OAUTH_FILE,"w")
            f.write(token + "\n")
            f.write(token_secret)
            self.success = True
            self.window.emit("delete_event",None)
        except :
            self.descript_label.set_label(u"おや！なにかがおかしいです\n%s\nもう一回最初から試してください"%(sys.exc_info()[0]))

    def close(self,widget,data=None):
        if self.success:
            widget.hide()
            gtk.main_quit()
        else:
            gtk.main_quit()



def main():
    first()
    gtk.main()

if __name__ == "__main__":
    main()
