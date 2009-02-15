# -*- coding: utf-8 -*-

from ConfigParser import ConfigParser, NoOptionError, NoSectionError
import string

class ExtendedConfigParser(ConfigParser):
	"""Adds basic exception handling to ConfigParser. Adds a method
	to parse IP address and store it in a tuple."""

	def getaddress(self, section, option, default_port = None):
		"""Gets IP address with port and stores it in a tuple.
		Returns None on exceptions."""

		text = self.get(section, option)
		if not text:
			return None
		tmp = string.split(text, ':')
		if len(tmp) < 1 or len(tmp) > 2:
			return None
		if len(tmp) == 1:
			if default_port:
				return (text, default_port)
			else:
				return None
		try:
			return (tmp[0], int(tmp[1]))
		except:
			return None

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
		except (NoSectionError, NoOptionError, TypeError):
			return None

	def getboolean(self, section, option):
		"""Gets boolean value. Returns None on exceptions."""

		try:
			return ConfigParser.getboolean(self, section, option)
		except (NoSectionError, NoOptionError, AttributeError):
			return None
