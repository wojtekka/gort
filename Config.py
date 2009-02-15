# -*- coding: utf-8 -*-

#import os, sys, socket, signal, string, re, time, select, struct, getopt
import re

from ExtendedConfigParser import *
from Rule import *

class Config:
	"""Reads, stores and writes configuration."""

	appmsg_address = ("appmsg.gadu-gadu.pl", 80)
	local_address = (None, 0)
	server_address = (None, 0)
	saved_server_address = (None, 0)
	simulation = False

	gadu_port = 8074
	proxy_port = 8080
	hub_port = 80

	http_request_rules = []
	http_reply_rules = []
	client_packet_rules = []
	server_packet_rules = []

	_shared_state = {}

	def __init__(self):
		self.__dict__ = self._shared_state

	def read(self, path):
		"""Reads configuration from a file.

		Arguments:
		- path: configuration file path"""

		config = ExtendedConfigParser()
		config.read(path)
		
		tmp = config.getint("general", "gadu_port")
		if tmp:
			self.gadu_port = tmp

		tmp = config.getint("general", "proxy_port")
		if tmp:
			self.proxy_port = tmp

		tmp = config.getint("general", "hub_port")
		if tmp:
			self.hub_port = tmp

		tmp = config.getaddress("general", "appmsg_address", 80)
		if tmp:
			self.appmsg_address = tmp

		tmp = config.getaddress("general", "local_address", self.gadu_port)
		if tmp:
			self.local_address = tmp

		tmp = config.getaddress("general", "server_address", 8074)
		if tmp:
			self.server_address = tmp

		tmp = config.getboolean("general", "simulation")
		if tmp:
			self.simulation = tmp

		for section in config.sections():
			match = config.get(section, "match")
			replace = config.get(section, "replace")
			reply = config.get(section, "reply")

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

			for (name, value) in config.items(section):
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

			state = config.get(section, "state")
			new_state = config.get(section, "new_state")

			rule = Rule(match, replace, replies, state, new_state)

			if section[:15] == "http_request::":
				self.http_request_rules.append(rule)

			if section[:13] == "http_reply::":
				self.http_reply_rules.append(rule)

			if section[:15] == "client_packet::":
				self.client_packet_rules.append(rule)

			if section[:15] == "server_packet::":
				self.server_packet_rules.append(rule)

		del config

	def write(self, path):
		"""Writes configuration to a file.

		Arguments:
		- path: configuration file path"""

		f = open(path, 'w+')

		f.write("[general]\n")

		if self.appmsg_address != ("appmsg.gadu-gadu.pl", 80):
			f.write("appmsg_address=%s:%d\n" % self.appmsg_address)

		if self.local_address != (None, 0):
			f.write("local_address=%s:%d\n" % self.local_address)

		if self.server_address != (None, 0):
			f.write("server_address=%s:%d\n" % self.server_address)

		if self.simulation:
			f.write("simulation=true\n")

		if self.gadu_port != 8074:
			f.write("gadu_port=%d\n" % (self.gadu_port))

		if self.proxy_port != 8080:
			f.write("proxy_port=%d\n" % (self.proxy_port))

		if self.hub_port != 80:
			f.write("hub_port=%d\n" % (self.hub_port))

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

		return

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

Config().read("gort.conf")
