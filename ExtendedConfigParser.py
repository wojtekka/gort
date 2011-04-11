# -*- coding: utf-8 -*-

from ConfigParser import ConfigParser, NoOptionError, NoSectionError
from Utils import *
import string

class ExtendedConfigParser(ConfigParser):
	"""Adds basic exception handling to ConfigParser. Adds a method
	to parse IP address and store it in a tuple."""

	def getaddress(self, section, option, default_port = None):
		"""Gets IP address with port and stores it in a tuple.
		Returns None on invalid format or exceptions."""

		result = parse_ip_and_port(self.get(section, option), default_port)

		if result == (None, 0):
			result = None

		return result

	def get(self, section, option):
		"""Gets string value. Returns None on exceptions."""

		try:
			return ConfigParser.get(self, section, option)
		except (NoSectionError, NoOptionError):
			return None

	def getint(self, section, option):
		"""Gets integer value. Returns None on exceptions."""

		try:
			return ConfigParser.getint(self, section, option)
		except (NoSectionError, NoOptionError, TypeError, ValueError):
			return None

	def getboolean(self, section, option):
		"""Gets boolean value. Returns None on exceptions."""

		try:
			tmp = ConfigParser.get(self, section, option)
			if tmp and tmp.lower() == "true":
				return True
			else:
				return False
		except (NoSectionError, NoOptionError):
			return None
