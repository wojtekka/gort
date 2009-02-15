# -*- coding: utf-8 -*-

class Rule:
	"""Stores information about one packet mangling rule."""

	def __init__(self, match, replace, replies = None, state = None, new_state = None):
		self.match = match
		self.replace = replace
		self.replies = replies
		self.state = state
		self.new_state = new_state

