# -*- coding: utf-8 -*-

import socket, time, threading

from SocketServer import ThreadingTCPServer

class MyThreadingTCPServer(ThreadingTCPServer):
	def __init__(self, bind, handler):
		self.shutdown_flag = False
		self.allow_reuse_address = True
		self.daemon_threads = True
		ThreadingTCPServer.__init__(self, bind, handler)
		self.socket.setblocking(0)

	def serve_forever(self, poll_interval = 0.5):
		while not self.shutdown_flag:
			self.handle_request()
			time.sleep(poll_interval)

	def shutdown(self):
		self.shutdown_flag = True

class ServerThread(threading.Thread):
	"""TCP server thread."""

	def __init__(self, app, port, handler):
		self.server = MyThreadingTCPServer(('', port), handler)
		self.server.app = app
		self.daemon = False
		threading.Thread.__init__(self)
		self.daemon = False

	def run(self):
		self.server.serve_forever()
		del self.server

	def shutdown(self):
		self.server.shutdown()

