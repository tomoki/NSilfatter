import gtk
from settings import *

class ClientWindow(gtk.Window):
    def __init__(self):
        self.visible = True
        self.window_size = (400,400)
        self.window_position = (0,0)

        gtk.Window.__init__(self)
        self.accel_group = gtk.AccelGroup()
        self.add_accel_group(self.accel_group)

        self.set_title(u"NSilfatter")
        self.set_icon_from_file(WINDOW_ICON)
        self.connect("delete_event",self.close_window)
        self.set_default_size(400,400)

        self.tray_icon = gtk.StatusIcon()
        self.tray_icon.set_from_file(TRAY_ICON)
        self.tray_icon.connect("activate",self.tray_clicked)

        self.tray_menu = gtk.Menu()
        self.tray_icon.connect("popup_menu",self.show_menu)

        item_quit = gtk.ImageMenuItem(stock_id=gtk.STOCK_QUIT)
        item_quit.connect("activate",gtk.main_quit)
        self.tray_menu.append(item_quit)
        self.tray_menu.show_all()

    def close_window(self,widget,event):
        self.visible = False
        self.window_size = self.get_size()
        self.window_position = self.get_position()
        return self.hide_on_delete()

    def show_menu(self,widget,button,time):
        self.tray_menu.popup(None,None,gtk.status_icon_position_menu,
                button,time,self.tray_icon)

    def tray_clicked(self,tray):
        if self.visible:
            self.visible = False
            self.emit("delete_event",None)
        else:
            self.visible = True
            (x,y) = self.window_position
            (w,h) = self.window_size
            self.move(x,y)
            self.resize(w,h)
            self.show_all()
