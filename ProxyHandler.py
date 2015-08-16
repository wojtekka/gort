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
		self.conn = Connection(self.remote_address)
		self.server.app.add_connection(self.conn)
		# XXX log connection?

	def finish(self):
		self.conn.close()
		self.server.app.update_connection(self.conn)
		# XXX log disconnection?

	def handle(self):
		"""Handles incoming connection."""

		self.server.app.log_connection(self.conn, Connection.PROXY_CONNECTED, self.remote_address[0] + ":" + str(self.remote_address[1]))

		self.client = self.request.makefile("w+")

		# Store local address if not forced

		self.local_address = self.server.app.config.local_address

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

		# Read POST request body if available

		self.body = ""

		if self.headers[0].startswith("POST "):
			# collect POST request body

			body_len = 0

			for i in range(len(self.headers)):
				if self.headers[i].lower().startswith("content-length:"):
					try:
						body_len = int(self.headers[i][15:].strip())
					except ValueError:
						self.bad_request()
						return

			while len(self.body) < body_len:
				chunk = self.client.read(body_len - len(self.body))

				if not chunk:
					# XXX log error?
					return

				self.body = self.body + chunk

		# Do some logging

		self.server.app.log_connection(self.conn, Connection.PROXY_REQUEST, "".join(self.headers) + self.body)

		# Handle HTTP method
	
		if len(self.headers) < 1:
			self.bad_request()
			return

		if self.headers[0].startswith("CONNECT "):
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

			if port == 8074 or port == 8063:
				self.client = None
				GaduHandler.handle(self)

			elif port == 443:
				if self.server.app.config.block_ssl:
					self.forbidden()
					return
				else:
					self.client = None
					GaduHandler.handle(self)

			elif port == 80:
				# Simulate connection to get headers
				self.reply_connected()

				self.headers = []

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

		elif self.headers[0].startswith("GET http://") or self.headers[0].startswith("POST http://"):
			words = self.headers[0].split()

			if len(words) != 3:
				self.bad_request()
				return

			method = words[0]
			url = words[1]
			version = words[2]

			url_slash = url.find("/", 7)

			if url_slash == -1:
				host = url[7:]
				path = "/"
			else:
				host = url[7:url_slash]
				path = url[url_slash:]

			host_found = False

			for i in range(len(self.headers)):
				if self.headers[i].lower().startswith("host:"):
					host_found = True

			if host_found == False:
				self.headers.insert(1, "Host: " + host + "\r\n")

			self.headers[0] = method + " " + path + " " + version + "\r\n"

			if host.find(":") != -1:
				tmp = host.split(":", 1)
				self.address = (tmp[0], int(tmp[1]))
			else:
				self.address = (host, 80)

			# TODO Zamienić na map/grep/cokolwiek
			tmp = self.headers
			self.headers = []
			for header in tmp:
				if not header.lower().startswith("Proxy"):
					self.headers.append(header)

			if self.server.app.config.block_http:
				if host != self.server.app.config.hub_address[0]:
					self.forbidden()
					return

			HubHandler.handle(self)

		else:
			self.bad_request()

	def reply_connected(self):
		reply = "HTTP/1.0 200 OK\r\n\r\n"
		self.server.app.log_connection(self.conn, Connection.PROXY_REPLY, reply)
		self.request.send(reply)

	def reply_error(self):
		reply = "HTTP/1.0 503 Service Unavailable\r\n\r\n"
		self.server.app.log_connection(self.conn, Connection.PROXY_REPLY, reply)
		self.request.send(reply)

	def bad_request(self):
		# XXX log error?
		reply = "HTTP/1.0 400 Bad Request\r\n\r\n"
		self.server.app.log_connection(self.conn, Connection.PROXY_REPLY, reply)
		self.request.send(reply)

	def forbidden(self):
		reply = "HTTP/1.0 403 Forbidden\r\n\r\n"
		self.server.app.log_connection(self.conn, Connection.PROXY_REPLY, reply)
		self.request.send(reply)
		
