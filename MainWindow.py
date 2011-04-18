# -*- coding: utf-8 -*-

import pygtk, pango, gtk, random, gobject, time
pygtk.require('2.0')
from Connection import *

class MainWindow:
	foreground_closed = "gray"
	background_http = "#f0f8ff"
	background_gadu = "#f0fff0"
	background_server = "#f8fff0"
	background_client = "#fff8f0"
	background_simulated = "gray"

	def _update_state(self):
		if self.app.is_started():
			self.start_button.set_sensitive(False)
			self.start_menu.set_sensitive(False)
			self.pause_button.set_sensitive(True)
			self.pause_menu.set_sensitive(True)
		else:
			self.start_button.set_sensitive(True)
			self.start_menu.set_sensitive(True)
			self.pause_button.set_sensitive(False)
			self.pause_menu.set_sensitive(False)

	def on_start_menu_activate(self, widget):
		self.app.start()
		self._update_state()

	def on_pause_menu_activate(self, widget):
		self.app.pause()
		self._update_state()

	def on_clear_menu_activate(self, widget):
		print "XXX on_clear_menu_activate"

	def on_prefs_menu_activate(self, widget):
		self.app.show_preferences()

	def on_about_menu_activate(self, widget):
		print "XXX on_about_menu_activate"

	def on_quit_menu_activate(self, widget):
		gtk.main_quit()

	def on_window1_delete_event(self, widget, event, data=None):
		return False

	def on_window1_destroy(self, widget, data=None):
		gtk.main_quit()

	def _add_event(self, event):
		background = None

		node = self.treestore2.append(None, [event.timestamp_str, event.type_str, None, None, background])
		
		if event.details:
			details = event.details

			if not isinstance(details, list):
				details = [details]

			for d in details:
				self.treestore2.append(node, [None, d.strip(), "monospace", None, background])

	def on_treeview1_treeselection_changed(self, treeselection, data=None):
		(store, iter) = treeselection.get_selected()

		if not iter:
			return

		self.treestore2.clear()

		conn = store.get_value(iter, 0)

		for event in conn.events:
			self._add_event(event)

	def __init__(self, app):
		self.app = app

	def create(self):
		self.window = self.app.builder.get_object("main_window")
		self.treeview1 = self.app.builder.get_object("treeview1")
		self.treeview2 = self.app.builder.get_object("treeview2")
		self.start_button = self.app.builder.get_object("start_button")
		self.start_menu = self.app.builder.get_object("start_menu")
		self.pause_button = self.app.builder.get_object("pause_button")
		self.pause_menu = self.app.builder.get_object("pause_menu")

		self.treeview1.get_selection().connect('changed', self.on_treeview1_treeselection_changed)

		self.pause_menu.set_sensitive(False)	# XXX workaround

		self.liststore1 = gtk.ListStore(gobject.TYPE_PYOBJECT, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
		self.treeview1.set_model(self.liststore1)

		self.treeview1.insert_column_with_attributes(0, 'Time', gtk.CellRendererText(), text=1, foreground=3, background=4)
		self.treeview1.insert_column_with_attributes(1, 'Address', gtk.CellRendererText(), text=2, foreground=3, background=4)

		self.treestore2 = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
		self.treeview2.set_model(self.treestore2)
		column = self.treeview2.insert_column_with_attributes(0, '', gtk.CellRendererText())
		column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
		column.set_fixed_width(16)	# XXX ugly
		self.treeview2.insert_column_with_attributes(1, 'Time', gtk.CellRendererText(), text=0)
		self.treeview2.insert_column_with_attributes(2, 'Information', gtk.CellRendererText(), text=1, font=2, foreground=3, background=4)

		if self.app.config.autostart:
			self.on_start_menu_activate(None)

	def add_connection(self, conn):
		ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(conn.open_timestamp))
		(ip, port) = conn.source
		conn.iter = self.liststore1.insert(0, [conn, ts, ip + ':' + str(port), None, None])

	def remove_connection(self, conn):
		self.liststore1.remove(conn.iter)
		conn.iter = None

	def update_connection(self, conn):
		if not conn.iter:
			return

		if not conn.active:
			self.liststore1.set_value(conn.iter, 3, self.foreground_closed)

		if conn.type == Connection.HTTP:
			self.liststore1.set_value(conn.iter, 4, self.background_http)
		elif conn.type == Connection.GADU:
			self.liststore1.set_value(conn.iter, 4, self.background_gadu)

	def log_event(self, conn, event):
		if not conn.iter:
			return

		selection = self.treeview1.get_selection()

		if not selection:
			return

		selected = selection.get_selected()

		if not selected:
			return

		(store, iter) = selected

		if iter and store.get_value(iter, 0) == conn:
			self._add_event(event)

	def show(self):
		self.window.show()

	def hide(self):
		self.window.hide()

