# -*- coding: utf-8 -*-

#import os, sys, socket, signal, string, re, time, select, struct, getopt

import re, socket, string
from SocketServer import BaseRequestHandler
from GaduHandler import *
from HubHandler import *
from threading import *
from Application import *

class ProxyHandler(BaseRequestHandler, HubHandler, GaduHandler):
	"""Handles incoming proxy requests."""

	def setup(self):
		self.remote_address = self.request.getpeername()
		self.conn = self.server.app.add_connection(self.remote_address)
		# XXX log connection?

	def finish(self):
		self.server.app.finish_connection(self.conn)
		# XXX log disconnection?

	def handle(self):
		"""Handles incoming connection."""

		self.client = self.request.makefile("w+")

		# Store local address if not forced

		self.local_address = Config().local_address

		if self.local_address == (None, 0):
			self.local_address = self.request.getsockname()

		# Read HTTP headers

		self.headers = []

		while True:
			line = self.client.readline()

			if not line:
				# XXX log error?
				return

			self.headers.append(line)
		
			if line == "\r\n":
				break

		self.server.app.log_connection(self.conn, Connection.PROXY_REQUEST, "".join(self.headers))

		# Handle HTTP method
	
		if len(self.headers) < 1:
			self.bad_request()
			return

		if self.headers[0][:8] == "CONNECT ":
			# Pass connection to GaduHandler class

			fields = self.headers[0].split(' ')

			if len(fields) != 3:
				self.bad_request()
				return

			server = fields[1].split(':')

			if len(server) != 2:
				self.bad_request()
				return

			try:
				port = int(server[1])
			except ValueError:
				self.bad_request()
				return

			self.address = (server[0], port)

			if port == 8074 or port == 443:
				self.good_request()
				self.client.close() # self.request still valid
				GaduHandler.handle(self)

			elif port == 80:
				self.headers = []

				self.good_request()

				while True:
					line = self.client.readline()

					if not line:
						# XXX log error?
						return

					self.headers.append(line)
				
					if line == "\r\n":
						break

				HubHandler.handle(self)

			else:
				self.bad_request()

		elif self.headers[0][:11] == "GET http://" or self.headers[0][:12] == "POST http://":
			self.request.close() # self.client is still valid

			if self.headers[0][:11] == "GET http://":
				method = "GET"
			else:
				method = "POST"

			tmp = string.split(self.headers[0][len(method)+8:], '/', 1)

			if len(tmp) != 2:
				self.bad_request()
				return

			host = tmp[0]
			rest = "/" + tmp[1]

			host_found = False

			for i in range(len(self.headers)):
				if self.headers[i][:5].lower() == "host:":
					host_found = True

			if host_found == False:
				self.headers.insert(1, "Host: " + host + "\r\n")

			self.headers[0] = method + " " + rest

			if host.find(":") != -1:
				tmp = host.split(":", 1)
				self.address = (tmp[0], int(tmp[1]))
			else:
				self.address = (host, 80)

			HubHandler.handle(self)

		else:
			self.bad_request()

	def good_request(self):
		reply = "HTTP/1.0 200 OK\r\n\r\n"
		self.server.app.log_connection(self.conn, Connection.PROXY_REPLY, reply)
		self.client.write(reply)
		self.client.flush()

	def bad_request(self):
		# XXX log error?
		reply = "HTTP/1.0 400 Bad Request\r\n\r\n"
		self.server.app.log_connection(self.conn, Connection.PROXY_REPLY, reply)
		self.client.write(reply)
		self.client.flush()
		
