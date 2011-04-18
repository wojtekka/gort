# -*- coding: utf-8 -*-

import sys
import pygtk
pygtk.require('2.0')
import gtk

from MainWindow import *
from Preferences import *
from ServerThread import *
from ProxyHandler import *
from HubHandler import *
from GaduHandler import *
from Config import *
from Connection import *
from HandleFinder import *

class Application:
	ui_file = "gort.ui"
	config_path = "gort.conf"

	proxy_thread = None
	hub_thread = None
	gadu_thread = None

	def is_started(self):
		if self.proxy_thread or (self.hub_thread and self.gadu_thread):
			return True
		else:
			return False

	def start(self):
		if self.config.proxy:
			try:
				self.proxy_thread = ServerThread(self, self.config.proxy_port, ProxyHandler)
				self.proxy_thread.start()
			except socket.error, msg:
				self.proxy_thread = None
				(errno, strerror) = msg
				message = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, "Unable to bind to port %d (%s)" % (self.config.proxy_port, strerror))
				message.run()
				message.destroy()
				return False

		else:
			try:
				self.hub_thread = ServerThread(self, self.config.hub_port, HubHandler)
				self.hub_thread.start()
			except socket.error, msg:
				self.hub_thread = None
				(errno, strerror) = msg
				message = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, "Unable to bind to port %d (%s)" % (self.config.hub_port, strerror))
				message.run()
				message.destroy()
				return False

			try:
				self.gadu_thread = ServerThread(self, self.config.gadu_port, HubHandler)
				self.gadu_thread.start()
			except socket.error, msg:
				self.hub_thread.shutdown()
				self.hub_thread = None
				self.gadu_thread = None
				(errno, strerror) = msg
				message = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, "Unable to bind to port %d (%s)" % (self.config.gadu_port, strerror))
				message.run()
				message.destroy()
				return False

		return True

	def stop_all_threads(self):
		if self.proxy_thread:
			self.proxy_thread.shutdown()
			self.proxy_thread = None
		
		if self.hub_thread:
			self.hub_thread.shutdown()
			self.hub_thread = None
		
		if self.gadu_thread:
			self.gadu_thread.shutdown()
			self.gadu_thread = None

	def pause(self):
		self.stop_all_threads()
		return True

	def add_connection(self, conn):
		self.main_window.add_connection(conn)

	def update_connection(self, conn):
		self.main_window.update_connection(conn)

	def remove_connection(self, conn):
		self.main_window.remove_connection(conn)

	def log_connection(self, conn, type, details=None):
		event = conn.append(type, details)
		self.main_window.log_event(conn, event)

	def show_preferences(self):
		self.preferences.show()

	def main(self):
		gtk.gdk.threads_init()

		self.builder = gtk.Builder()
		self.builder.add_from_file(self.ui_file)

		self.config = Config()
		self.config.read(self.config_path)

		self.preferences = Preferences(self)
		self.main_window = MainWindow(self)

		self.handle_finder = HandleFinder([self.preferences, self.main_window])
		self.builder.connect_signals(self.handle_finder)

		self.preferences.create()
		self.main_window.create()
		self.main_window.show()

		gtk.gdk.threads_enter()

		try:
			gtk.main()
		except KeyboardInterrupt:
			pass

		gtk.gdk.threads_leave()

		self.stop_all_threads()

