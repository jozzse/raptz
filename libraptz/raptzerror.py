#!/usr/bin/python

class RaptzException(Exception):
	def __init__(self, msg):
		self._msg = msg
		print self._msg
	
	def __str__(self):
		return self._msg
