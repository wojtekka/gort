# -*- coding: utf-8 -*-

import sys
import pygtk
pygtk.require('2.0')
import gtk

from MainWindow import *
from ServerThread import *
from ProxyHandler import *
from Config import *
from Connection import *

class Application:
	gadu_thread = False
	proxy_thread = False
	hub_thread = False

	def start(self):
		try:
			self.proxy_thread = ServerThread(self, 8080, ProxyHandler)
			self.proxy_thread.start()
		except socket.error, msg:
			self.proxy_thread = None
			(errno, strerror) = msg
			message = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, "Unable to bind to port 8080 (%s)" % (strerror))
			message.run()
			message.destroy()	# XXX doesn't work as expected

		return True

	def pause(self):
		if self.proxy_thread:
			self.proxy_thread.shutdown()

		return True

	def add_connection(self, source):
		conn = Connection(source)
		self.main_window.add_connection(conn)
		return conn

	def update_connection(self, conn):
		self.main_window.update_connection(conn)

	def log_connection(self, conn, type, details=None, orig_details=None):
		event = conn.append(type, details, orig_details)
		self.main_window.log_connection(conn, event)

	def finish_connection(self, conn):
		conn.close()
		self.main_window.update_connection(conn)

	def main(self):
		gtk.gdk.threads_init()
		self.main_window = MainWindow(self)
		self.main_window.show()
		gtk.gdk.threads_enter()
		try:
			gtk.main()
		except KeyboardInterrupt:
			sys.exit()
		gtk.gdk.threads_leave()

