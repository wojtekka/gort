# -*- coding: utf-8 -*-

import pygtk, pango, gtk, random, gobject, time
pygtk.require('2.0')

class MainWindow:
	def on_start_menu_activate(self, widget):
		print "on_start_menu_activate"
		if self.app.start():
			self.builder.get_object("start_button").set_sensitive(False)
			self.builder.get_object("start_menu").set_sensitive(False)
			self.builder.get_object("pause_button").set_sensitive(True)
			self.builder.get_object("pause_menu").set_sensitive(True)

	def on_pause_menu_activate(self, widget):
		print "on_pause_menu_activate"
		if self.app.pause():
			self.builder.get_object("start_button").set_sensitive(True)
			self.builder.get_object("start_menu").set_sensitive(True)
			self.builder.get_object("pause_button").set_sensitive(False)
			self.builder.get_object("pause_menu").set_sensitive(False)

	def on_clear_menu_activate(self, widget):
		print "on_clear_menu_activate"

	def on_prefs_menu_activate(self, widget):
		self.add_tab(random.randint(1, 1000))
		print "on_prefs_menu_activate"

	def on_about_menu_activate(self, widget):
		print "on_about_menu_activate"

	def on_quit_menu_activate(self, widget):
		print "on_quit_menu_activate"
		gtk.main_quit()

	def on_window1_delete_event(self, widget, event, data=None):
		print "on_window1_delete_event"
		return False

	def on_window1_destroy(self, widget, data=None):
		print "on_window1_destroy"
		gtk.main_quit()

	def add_event(self, event):
		node = self.treestore2.append(None, [event.timestamp_str, event.type_str, None, None])
		if event.orig_details:
			self.treestore2.append(node, [None, event.orig_details.strip(), "monospace", "gray"])
		if event.details:
			self.treestore2.append(node, [None, event.details.strip(), "monospace", None])

	def on_treeview1_treeselection_changed(self, treeselection, data=None):
		(store, iter) = treeselection.get_selected()

		if not iter:
			return

		self.treestore2.clear()

		conn = store.get_value(iter, 4)

		for event in conn.events:
			self.add_event(event)

	def __init__(self, app):
		self.app = app

		self.builder = gtk.Builder()
		self.builder.add_from_file("gort.ui")
		self.builder.connect_signals(self)
		self.window1 = self.builder.get_object("window1")
		self.treeview1 = self.builder.get_object('treeview1')
		self.treeview2 = self.builder.get_object('treeview2')

		self.treeview1.get_selection().connect('changed', self.on_treeview1_treeselection_changed)

		self.builder.get_object("pause_menu").set_sensitive(False)	# XXX workaround

		self.liststore1 = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)
		self.treeview1.set_model(self.liststore1)

		self.treeview1.insert_column_with_attributes(0, 'Time', gtk.CellRendererText(), text=0, foreground=2, background=3)
		self.treeview1.insert_column_with_attributes(1, 'Address', gtk.CellRendererText(), text=1, foreground=2, background=3)

		self.treestore2 = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
		self.treeview2.set_model(self.treestore2)
		column = self.treeview2.insert_column_with_attributes(0, '', gtk.CellRendererText())
		column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
		column.set_fixed_width(16)	# XXX ugly
		self.treeview2.insert_column_with_attributes(1, 'Time', gtk.CellRendererText(), text=0)
		self.treeview2.insert_column_with_attributes(2, 'Information', gtk.CellRendererText(), text=1, font=2, foreground=3)

		self.on_start_menu_activate(None)	# XXX temporary

	def add_connection(self, conn):
		ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(conn.open_timestamp))
		(ip, port) = conn.source
		conn.iter = self.liststore1.insert(0, [ts, ip + ':' + str(port), None, None, conn])

	def update_connection(self, conn):
		if not conn.active:
			self.liststore1.set_value(conn.iter, 2, 'gray')
		if conn.type == 1:
			self.liststore1.set_value(conn.iter, 3, '#f0f8ff')
		elif conn.type == 2:
			self.liststore1.set_value(conn.iter, 3, '#f0fff0')

	def log_connection(self, conn, event):
		selection = self.treeview1.get_selection().get_selected()

		if not selection:
			return

		(store, iter) = selection

		if iter and store.get_value(iter, 3) == conn:
			self.add_event(event)

	def show(self):
		self.window1.show()

	def hide(self):
		self.window1.hide()

