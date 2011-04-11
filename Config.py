# -*- coding: utf-8 -*-

#import os, sys, socket, signal, string, re, time, select, struct, getopt
import re

from ExtendedConfigParser import *
from Rule import *

class Config:
	"""Reads, stores and writes configuration."""

	path = None
	saved_server_address = (None, 0)

	default_hub_address = ("appmsg.gadu-gadu.pl", 80)
	default_local_address = (None, 0)
	default_server_address = (None, 0)
	default_proxy = True
	default_simulation = False
	default_autostart = True
	default_block_ssl = True
	default_gadu_port = 8074
	default_proxy_port = 8080
	default_hub_port = 80
	default_http_traffic = 0
	
	hub_address = default_hub_address
	local_address = default_local_address
	server_address = default_server_address
	proxy = default_proxy
	simulation = default_simulation
	autostart = default_autostart
	block_ssl = default_block_ssl
	gadu_port = default_gadu_port
	proxy_port = default_proxy_port
	hub_port = default_hub_port
	http_traffic = default_http_traffic

	http_request_rules = []
	http_reply_rules = []
	client_packet_rules = []
	server_packet_rules = []

	def read(self, path):
		"""Reads configuration from a file.

		Arguments:
		- path: configuration file path"""

		parser = ExtendedConfigParser()
		parser.read(path)
		
		tmp = parser.getint("general", "gadu_port")
		if not tmp is None:
			self.gadu_port = tmp

		tmp = parser.getint("general", "proxy_port")
		if not tmp is None:
			self.proxy_port = tmp

		tmp = parser.getint("general", "hub_port")
		if not tmp is None:
			self.hub_port = tmp

		tmp = parser.getaddress("general", "hub_address", 80)
		if not tmp is None:
			self.hub_address = tmp

		tmp = parser.getaddress("general", "local_address", self.gadu_port)
		if not tmp is None:
			self.local_address = tmp

		tmp = parser.getaddress("general", "server_address", 8074)
		if not tmp is None:
			self.server_address = tmp

		tmp = parser.getboolean("general", "proxy")
		if not tmp is None:
			self.proxy = tmp

		tmp = parser.getboolean("general", "simulation")
		if not tmp is None:
			self.simulation = tmp

		tmp = parser.getboolean("general", "autostart")
		if not tmp is None:
			self.autostart = tmp

		tmp = parser.getboolean("general", "block_ssl")
		if not tmp is None:
			self.block_ssl = tmp

		tmp = parser.getint("general", "http_traffic")
		if not tmp is None:
			self.http_traffic = tmp

		for section in parser.sections():
			match = parser.get(section, "match")
			replace = parser.get(section, "replace")
			reply = parser.get(section, "reply")

			try:
				if match:
					match = match.decode('string_escape')
				if replace:
					replace = replace.decode('string_escape')
				if reply:
					reply = reply.decode('string_escape')
			except ValueError:
				log.error("Invalid rule in section " + section)
				continue

			replies = []

			for (name, value) in parser.items(section):
				if name[:5] != "reply":
					continue

				if not value:
					continue

				try:
					reply = value.decode('string_escape')
				except ValueError:
					log.error("Invalid rule in section " + section)
					continue

				replies.append(reply)

			state = parser.get(section, "state")
			new_state = parser.get(section, "new_state")

			rule = Rule(match, replace, replies, state, new_state)

			if section[:15] == "http_request::":
				self.http_request_rules.append(rule)

			if section[:13] == "http_reply::":
				self.http_reply_rules.append(rule)

			if section[:15] == "client_packet::":
				self.client_packet_rules.append(rule)

			if section[:15] == "server_packet::":
				self.server_packet_rules.append(rule)

		self.path = path

	def write(self, path = None):
		"""Writes configuration to a file.

		Arguments:
		- path: configuration file path"""

		if not path:
			path = self.path

		f = open(path, 'w+')

		f.write("[general]\n")

		if self.hub_address != self.default_hub_address:
			f.write("hub_address=%s:%d\n" % self.hub_address)

		if self.local_address != self.default_local_address:
			f.write("local_address=%s:%d\n" % self.local_address)

		if self.server_address != self.default_server_address:
			f.write("server_address=%s:%d\n" % self.server_address)

		if self.simulation != self.default_simulation:
			if self.simulation:
				f.write("simulation=true\n")
			else:
				f.write("simulation=false\n")

		if self.proxy != self.default_proxy:
			if self.proxy:
				f.write("proxy=true\n")
			else:
				f.write("proxy=false\n")

		if self.autostart != self.default_autostart:
			if self.autostart:
				f.write("autostart=true\n")
			else:
				f.write("autostart=false\n")

		if self.block_ssl != self.default_block_ssl:
			if self.block_ssl:
				f.write("block_ssl=true\n")
			else:
				f.write("block_ssl=false\n")

		if self.gadu_port != self.default_gadu_port:
			f.write("gadu_port=%d\n" % (self.gadu_port))

		if self.proxy_port != self.default_proxy_port:
			f.write("proxy_port=%d\n" % (self.proxy_port))

		if self.hub_port != self.default_hub_port:
			f.write("hub_port=%d\n" % (self.hub_port))

		if self.http_traffic != self.default_http_traffic:
			f.write("http_traffic=%d\n" % (self.http_traffic))

		index = 1

		sections = [(self.http_request_rules, "http_request"),
			    (self.http_reply_rules, "http_reply"),
			    (self.client_packet_rules, "client_packet"),
			    (self.server_packet_rules, "server_packet")]

		for section in sections:
			(rules, name) = section
			for rule in rules:
				f.write("\n[%s::%d]\n" % (name, index))
				if rule.state:
					f.write("state=%s\n" % (rule.state))
				if rule.match:
					f.write("match=%s\n" % (rule.match.encode('string_escape')))
				if rule.replace:
					f.write("replace=%s\n" % (rule.replace.encode('string_escape')))
				if len(rule.replies) == 1:
					f.write("reply=%s\n" % (rule.replies[0].encode('string_escape')))
				else:
					idx = 1
					for reply in rule.replies:
						f.write("reply%d=%s\n" % (idx, reply.encode('string_escape')))
						idx = idx + 1

				if rule.new_state:
					f.write("new_state=%s\n" % (rule.new_state))
				index = index + 1

		f.close()

	def get_server_address(self):
		"""Returns server address. If address is not forced in
		configuration, returns saved address retrieved from hub."""

		if self.server_address != (None, 0):
			return self.server_address
		else:
			return self.saved_server_address
	
	def set_server_address(self, address):
		"""Saves server address retrieved from original hub."""

		self.saved_server_address = address
