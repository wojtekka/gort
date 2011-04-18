# -*- coding: utf-8 -*-

import pygtk, pango, gtk, gobject
from Utils import *
pygtk.require('2.0')

class Preferences:
	options = ["combobox_mode", "entry_proxy_port", "entry_hub_port",
		"entry_gadu_port", "check_autostart", "check_simulation",
		"check_block_ssl", "entry_hub_address", "entry_server_address",
		"entry_local_address", "check_block_http", "check_hide_http",
		"check_hide_pings"]

	def __init__(self, app):
		self.app = app

	def create(self):
		self.window = self.app.builder.get_object("dialog_prefs")
		for i in self.options:
			setattr(self, i, self.app.builder.get_object(i))

	def error(self, msg):
		message = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, msg)
		message.run()
		message.destroy()

	def on_combobox_mode_changed(self, widget):
		if widget.get_active() == 0:
			proxy = True
		else:
			proxy = False

		self.entry_proxy_port.set_sensitive(proxy)
		self.check_block_ssl.set_sensitive(proxy)
		self.check_block_http.set_sensitive(proxy)
		self.check_hide_http.set_sensitive(proxy)
		self.entry_hub_port.set_sensitive(not proxy)
		self.entry_gadu_port.set_sensitive(not proxy)
		self.entry_hub_address.set_sensitive(not proxy)

	def on_button_prefs_rules_clicked(self, widget):
		print "on_button_prefs_rules_clicked"

	def on_button_prefs_ok_clicked(self, widget):
		try:
			proxy_port = int(self.entry_proxy_port.get_text())
		except ValueError:
			self.error("Invalid proxy port value")
			return

		try:
			hub_port = int(self.entry_hub_port.get_text())
		except ValueError:
			self.error("Invalid hub port value")
			return

		try:
			gadu_port = int(self.entry_gadu_port.get_text())
		except ValueError:
			self.error("Invalid service port value")
			return

		hub_address = parse_ip_and_port(self.entry_hub_address.get_text())
		if not hub_address:
			self.error("Invalid hub address")

		local_address = parse_ip_and_port(self.entry_local_address.get_text())
		if not hub_address:
			self.error("Invalid local address")

		server_address = parse_ip_and_port(self.entry_server_address.get_text())
		if not server_address:
			self.error("Invalid server address")

		if self.combobox_mode.get_active() == 0:
			proxy = True
		else:
			proxy = False

		reconnect = False

		if self.app.config.proxy != proxy:
			reconnect = True
		if self.app.config.proxy and self.app.config.proxy_port != proxy_port:
			reconnect = True
		if not self.app.config.proxy and (self.app.config.hub_port != hub_port or self.app.config.gadu_port != gadu_port):
			reconnect = True

		self.app.config.proxy = proxy
		self.app.config.proxy_port = proxy_port
		self.app.config.hub_port = hub_port
		self.app.config.gadu_port = gadu_port
		self.app.config.autostart = self.check_autostart.get_active()
		self.app.config.simulation = self.check_simulation.get_active()
		self.app.config.block_ssl = self.check_block_ssl.get_active()
		self.app.config.block_http = self.check_block_http.get_active()
		self.app.config.hide_http = self.check_hide_http.get_active()
		self.app.config.hide_pings = self.check_hide_pings.get_active()
		self.app.config.hub_address = hub_address
		self.app.config.server_address = server_address
		self.app.config.local_address = local_address

		self.app.config.write()

		if reconnect:
			self.app.pause()
			self.app.main_window.update_state()

		self.hide()

	def on_button_prefs_cancel_clicked(self, widget):
		self.hide()

	def on_dialog_prefs_delete_event(self, widget, event, data=None):
		self.on_button_prefs_cancel_clicked(widget)
		return True

	def show(self):
		if self.app.config.proxy:
			self.combobox_mode.set_active(0)
		else:
			self.combobox_mode.set_active(1)
		
		self.on_combobox_mode_changed(self.combobox_mode)
		self.entry_proxy_port.set_text(str(self.app.config.proxy_port))
		self.entry_hub_port.set_text(str(self.app.config.hub_port))
		self.entry_gadu_port.set_text(str(self.app.config.gadu_port))
		self.check_autostart.set_active(self.app.config.autostart)
		self.check_simulation.set_active(self.app.config.simulation)
		self.check_block_ssl.set_active(self.app.config.block_ssl)
		self.check_block_http.set_active(self.app.config.block_http)
		self.check_hide_http.set_active(self.app.config.hide_http)
		self.check_hide_pings.set_active(self.app.config.hide_pings)
		if self.app.config.hub_address != (None, 0):
			self.entry_hub_address.set_text("%s:%d" % self.app.config.hub_address)
		else:
			self.entry_hub_address.set_text("")

		if self.app.config.server_address != (None, 0):
			self.entry_server_address.set_text("%s:%d" % self.app.config.server_address)
		else:
			self.entry_server_address.set_text("")

		if self.app.config.local_address != (None, 0):
			self.entry_local_address.set_text("%s:%d" % self.app.config.local_address)
		else:
			self.entry_local_address.set_text("")

		self.window.show()

	def hide(self):
		self.window.hide()

