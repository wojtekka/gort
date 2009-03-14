#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Gort v0.1
# Wojtek Kaniewski <wojtekka@toxygen.net>
# Public Domain
#
# Some code from http://code.activestate.com/recipes/66012/ by Jürgen Hermann

import os, sys, socket, signal, string, re, time, select, struct, getopt

from SocketServer import BaseRequestHandler
from threading import *
from Config import *
from Connection import *

class GaduHandler(BaseRequestHandler):
	"""Handles incoming Gadu-Gadu connection."""

	def mangle_packet(self, data, rules):
		"""Mangles incoming packet.

		Argument:
		- data: Packet data
		- rules: List of rules
		
		Returns a tuple containing mangled packet (or original packet
		if no rule matched) and reply to sender (or None if no rule
		matched)."""

		reply = None

		for rule in rules:
			if rule.state and not re.match(rule.state, self.state):
				continue

			if rule.match and not re.match(rule.match, data):
				continue

			if rule.match and rule.replace:
				data = re.sub(rule.match, rule.replace, data)

			for r in rule.replies:
				tmp = re.sub(rule.match, r, data)

				if tmp[4:8] == "####":
					reply_type = tmp[0:4]
					reply_data = tmp[8:]
					reply_length = struct.pack("<I", len(reply_data))
					tmp = reply_type + reply_length + reply_data

				if not reply:
					reply = tmp
				else:
					reply = reply + tmp

			if rule.new_state:
				self.server.app.log_connection(self.conn, Connection.GADU_STATE, rule.new_state)
				self.state = rule.new_state

			break

		return (data, reply)


	def handle(self):
		"""Handles incoming connection."""

		self.conn.type = Connection.GADU
		self.server.app.update_connection(self.conn)

		self.state = "default"

		if self.address == (None, 0):
			self.address = Config.get_server_address()

		if not Config().simulation and self.address == (None, 0):
			# XXX log error?
			return

		client = self.request
		client_data = ""

		if Config().simulation:
			(new_packet, reply) = self.mangle_packet("", Config().client_packet_rules)

			if reply:
				self.server.app.log_connection(self.conn, Connection.GADU_SIMULATED_SERVER, reply)
				client.send(reply)

		else:
			server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			server_data = ""

			self.server.app.log_connection(self.conn, Connection.GADU_CONNECTING, "%s:%d" % self.address)
	
			try:
				server.connect(self.address)
			except socket.error, msg:
				(errno, strerror) = msg
				self.server.app.log_connection(self.conn, Connection.GADU_FAILED, strerror)
				return

			self.server.app.log_connection(self.conn, Connection.GADU_CONNECTED)
		
		client_active = True

		while True:
			socks = []

			if client_active:
				socks.append(client)

			if not Config().simulation:
				socks.append(server)

			(iwtd, owtd, ewtd) = select.select(socks, [], [])

			if client in iwtd:
				tmp = client.recv(4096)

				if not tmp:
					# XXX log?
					break

				client_data = client_data + tmp

				while len(client_data) >= 8:
					(type, length) = struct.unpack("<II", client_data[:8])
					if len(client_data) < length + 8:
						break

					packet = client_data[:length+8]
					orig_packet = packet

					(packet, reply) = self.mangle_packet(packet, Config().client_packet_rules)

					self.server.app.log_connection(self.conn, Connection.GADU_CLIENT, packet)

					if not Config().simulation and packet:
						server.send(packet)

					if reply:
						self.server.app.log_connection(self.conn, Connection.GADU_SIMULATED_SERVER, reply)
						client.send(reply)

					client_data = client_data[length+8:]

			if not Config().simulation and server in iwtd:
				tmp = server.recv(4096)

				if not tmp:
					# XXX log?
					break

				server_data = server_data + tmp

				while len(server_data) >= 8:
					(type, length) = struct.unpack("<II", server_data[:8])
					if len(server_data) < length + 8:
						break

					packet = server_data[:length+8]
					orig_packet = packet

					(packet, reply) = self.mangle_packet(packet, Config().server_packet_rules)

					self.server.app.log_connection(self.conn, Connection.GADU_SERVER, packet, orig_packet)

					if packet:
						client.send(packet)

					if reply:
						self.server.app.log_connection(self.conn, Connection.GADU_SIMULATED_CLIENT, reply)
						server.send(reply)

					server_data = server_data[length+8:]

		client.close()

		if not Config().simulation:
			server.close()

		return
