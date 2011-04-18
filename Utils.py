# -*- coding: utf-8 -*-

def parse_ip_and_port(text, default_port = None):
	if not text:
		return (None, 0)
	tmp = text.split(':')
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

def hex_dump(data):
	result = ""
	offset = ""
	hex = ""
	chars = ""

	for i in range(len(data)):
		if i % 16 == 0:
			offset = "%04x: " % i
			hex = ""
			chars = ""

		hex = hex + "%02x" % ord(data[i])

		if data[i] < ' ' or data[i] > '~':
			chars = chars + "."
		else:
			chars = chars + data[i]

		if i % 16 == 15:
			result = result + offset + hex + "  " + chars + "\r\n"
			offset = ""
			hex = ""
			chars = ""
			
		if i + 1 < len(data):
			hex = hex + " "

	if hex and chars and offset:
		hex = hex + "   " * (16 - (len(data) % 16))

		result = result + offset + hex + "  " + chars + "\r\n"

	return result


