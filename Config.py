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
	default_block_http = False
	default_hide_http = False
	default_hide_pings = False
	default_gadu_port = 8074
	default_proxy_port = 8080
	default_hub_port = 80

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
		
		self._read_int(parser, "gadu_port")
		self._read_int(parser, "proxy_port")
		self._read_int(parser, "hub_port")
		self._read_address(parser, "hub_address", 80)
		self._read_address(parser, "local_address", self.gadu_port)
		self._read_address(parser, "server_address", 8074)
		self._read_boolean(parser, "proxy")
		self._read_boolean(parser, "simulation")
		self._read_boolean(parser, "autostart")
		self._read_boolean(parser, "block_ssl")
		self._read_boolean(parser, "block_http")
		self._read_boolean(parser, "hide_http")
		self._read_boolean(parser, "hide_pings")

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
		self._write_address(f, "hub_address")
		self._write_address(f, "local_address")
		self._write_address(f, "server_address")
		self._write_boolean(f, "simulation")
		self._write_boolean(f, "proxy")
		self._write_boolean(f, "autostart")
		self._write_boolean(f, "block_ssl")
		self._write_boolean(f, "block_http")
		self._write_boolean(f, "hide_http")
		self._write_boolean(f, "hide_pings")
		self._write_int(f, "gadu_port")
		self._write_int(f, "proxy_port")
		self._write_int(f, "hub_port")

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

	def _set(self, name, value):
		if not value is None:
			setattr(self, name, value)
		else:
			setattr(self, name, getattr(self, "default_" + name))

	def _read_int(self, parser, name):
		self._set(name, parser.getint("general", name))

	def _read_address(self, parser, name, port):
		self._set(name, parser.getaddress("general", name, port))

	def _read_boolean(self, parser, name):
		self._set(name, parser.getboolean("general", name))

	def _write_boolean(self, f, name):
		value = getattr(self, name)

		if value != getattr(self, "default_" + name):
			if value:
				f.write("%s=true\n" % (name))
			else:
				f.write("%s=false\n" % (name))

	def _write_int(self, f, name):
		value = getattr(self, name)

		if value != getattr(self, "default_" + name):
			f.write("%s=%d\n" % (name, value))

	def _write_address(self, f, name):
		value = getattr(self, name)

		if value != getattr(self, "default_" + name):
			(addr, port) = value
			f.write("%s=%s:%d\n" % (name, addr, port))

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
