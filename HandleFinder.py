# -*- coding: utf-8 -*-

class HandleFinder(object):
	"""Searches for handler implementations across multiple objects.
	"""
	# See <http://stackoverflow.com/questions/4637792> for why this is
	# necessary.

	def __init__(self, backing_objects):
		self.backing_objects = backing_objects

	def __getattr__(self, name):
		for o in self.backing_objects:
			if hasattr(o, name):
				return getattr(o, name)
		else:
			raise AttributeError("%r not found on any of %r" % (name, self.backing_objects))

