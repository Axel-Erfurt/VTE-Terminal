#!/usr/bin/python3
# -*- coding: utf-8 -*-
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Vte", "2.91")
from gi.repository import Gtk, Vte, Gdk
from gi.repository import GLib
import os
import webbrowser


class Terminal(Vte.Terminal):

    def __init__(self):
        super(Vte.Terminal, self).__init__()

        self.spawn_async(Vte.PtyFlags.DEFAULT, 
            os.path.expanduser("~"),
            ["/bin/bash"],
            None,
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None,
            None,
            -1,
            None,
            None
            )
            
        self.set_font_scale(0.9)
        self.set_scroll_on_output(True)
        self.set_scroll_on_keystroke(True)
        palette = [Gdk.RGBA(0.4, 0.8, 1.0, 1.0)] * 16
        self.set_colors(Gdk.RGBA(1.0, 1.0, 1.0, 1.0), Gdk.RGBA(0.2, 0.2, 0.2, 1.0), palette)
        self.set_color_highlight(Gdk.RGBA(0.3, 0.3, 0.9, 1.0))
        self.set_color_highlight_foreground(Gdk.RGBA(0.8, 0.8, 0.8, 1.0))
        self.connect("key_press_event", self.copy_or_paste)

        self.set_scrollback_lines(-1)
        self.set_audible_bell(0)

    def copy_or_paste(self, widget, event):
        control_key = Gdk.ModifierType.CONTROL_MASK
        shift_key = Gdk.ModifierType.SHIFT_MASK
        if event.type == Gdk.EventType.KEY_PRESS:
            if event.state == shift_key | control_key:
                if event.keyval == 67:
                    self.copy_clipboard_format(1)
                elif event.keyval == 86:
                    self.paste_clipboard()
                return True
                

class MyWindow(Gtk.Window):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__()
        self.dnd_list = [Gtk.TargetEntry.new("text/uri-list", 0, 80), Gtk.TargetEntry.new("text/plain", 0, 4294967293)]
        self.dnd_text = Gtk.TargetEntry.new("text/plain", 0, 4294967293)

    def main(self):
        self.set_icon_name("utilities-terminal-symbolic")
        self.terminal = Terminal()
        self.terminal.drag_dest_set(Gtk.DestDefaults.ALL, self.dnd_list, Gdk.DragAction.COPY)
        self.terminal.drag_dest_set_target_list(self.dnd_list)
        self.terminal.connect('button-press-event', self.on_buttonpress)
        self.terminal.connect('popup-menu', self.popup_menu)
        self.terminal.connect("drag_data_received", self.on_drag_data_received)
        self.cb = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY)   
        self.cb.wait_for_text()
#        self.cb.set_text("cd /tmp", -1)        
        self.connect('delete-event', Gtk.main_quit)
        self.scrolled_win = Gtk.ScrolledWindow()
        self.scrolled_win.add(self.terminal)
        self.add(self.scrolled_win)
        self.set_title("VTE-Terminal")
        self.resize(900, 400)
        self.move(0, 0)
        self.show_all()
        self.terminal.grab_focus()
        
    ### drop file or text
    def on_drag_data_received(self, widget, context, x, y, selection, target_type, timestamp):
        myfile = ""
        if target_type == 80:
            uri = str(selection.get_data().decode().rstrip()).replace("file://", "")
            self.cb.set_text(f"'{uri}'", -1) 
            self.terminal.paste_primary()
        else:
            dropped_text = str(selection.get_data().decode().rstrip())
            self.cb.set_text(dropped_text, -1) 
            self.terminal.paste_primary()

    def on_buttonpress(self, widget, event):
        """Handler for mouse events"""
        widget.grab_focus()

        if event.button == 1:
            if (event.state & Gdk.ModifierType.CONTROL_MASK) == 0:
                return(False)
        elif event.button == 2:
            self.terminal.paste_primary()
            return(True)
        elif event.button == 3:
            if (event.state & Gdk.ModifierType.CONTROL_MASK) == 0:
                self.popup_menu(widget, event)
                return(True)

        return(False)
    
    def popup_menu(self, widget, event=None):
        """Display the context menu"""
        menu = Gtk.Menu()
        copy_icon = Gtk.Image.new_from_icon_name("edit-copy-symbolic", 16)
        copy_menu = Gtk.ImageMenuItem(label = "Copy (Shift+Ctrl+C)", image = copy_icon)
        copy_menu.connect("activate", lambda x: self.terminal.copy_clipboard_format(1))
        menu.append(copy_menu)
        
        paste_icon = Gtk.Image.new_from_icon_name("edit-paste-symbolic", 16)
        paste_menu = Gtk.ImageMenuItem(label = "Paste (Shift+Ctrl+V)", image = paste_icon)
        paste_menu.connect("activate", lambda x: self.terminal.paste_clipboard())
        menu.append(paste_menu)
        
        sep = Gtk.SeparatorMenuItem()
        menu.append(sep)
        
        find_icon = Gtk.Image.new_from_icon_name("edit-find-symbolic", 16)
        find_menu = Gtk.ImageMenuItem(label = "find with Google", image = find_icon)
        find_menu.connect("activate", self.find_with_browser)
        menu.append(find_menu)
        
        menu.show_all()
        menu.popup(None, None, None, None, 0, Gtk.get_current_event_time())
        
    def find_with_browser(self, *args):
        self.terminal.copy_clipboard_format(1)
        searchterm = self.cb.wait_for_text()
        url = f"http://www.google.com/search?q='{searchterm}'"
        webbrowser.open(url)
        
        
if __name__ == "__main__":
    win = MyWindow()
    win.main()
    Gtk.main()