# -*- coding: utf-8 -*-

import pygtk, pango, gtk, gobject
pygtk.require('2.0')

class Preferences:
	def __init__(self, app):
		self.app = app
		self.app.builder.connect_signals(self)
		self.window = self.app.builder.get_object("dialog1")

	def show(self):
		self.window.show()

	def hide(self):
		self.window.hide()

