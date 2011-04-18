# -*- coding: utf-8 -*-

import struct
from Utils import *
import GaduPacket

class Field:
	value = None
	label = None

	def fetch(self, buf):
		raise IndexError

	def apply_context(self, ctx):
		pass

	def store_context(self, ctx):
		pass
	
	def format(self):
		return None

class NumericField(Field):
	signed = False

	def __init__(self):
		self.value = 0

	def fetch(self, buf):
		if len(buf) < self.size:
			raise IndexError

		self.value = 0

		for i in range(self.size):
			self.value = self.value + (ord(buf[i]) << (i * 8))

		if self.signed and self.value & (1 << (self.size * 8 - 1)):
			self.value = self.value - (1 << (self.size * 8))

		return buf[self.size:]

	def format(self):
		return str(self.value)

class IntField(Field):
	size = 4

class ShortField(Field):
	size = 2

class ByteField(Field):
	size = 1

class StringField(Field):
	size = -1

	def fetch(self, buf):
		if self.size == -1:
			self.size = buf.find('\0')

			if self.size == -1:
				self.size = len(buf)

		if len(buf) < self.size and self.size > 0:
			raise IndexError

		self.value = buf[:self.size]

		return buf[self.size:]

	def format(self):
		return "\"" + self.value.encode("string-escape") + "\""

class BinaryField(Field):
	size = -1
	display_size = None

	def fetch(self, buf):
		if self.size == -1:
			self.size = len(buf)

		if len(buf) < self.size and self.size > 0:
			raise IndexError

		self.value = [i for i in buf[:self.size]]

		return buf[self.size:]

	def format(self):
		if self.display_size is None:
			length = len(self.value)
		else:
			length = self.display_size

		return " ".join(["%02x" % ord(i) for i in self.value[:length]])

class DecimalField(NumericField):
	def format(self):
		if self.signed:
			fmt = "%d"
		else:
			fmt = "%u"

		return fmt % (self.value)

class HexadecimalField(NumericField):
	def format(self):
		fmt = "0x%%0%dx" % (self.size * 2)
		return fmt % (self.value)

class BitmapField(NumericField):
	bits = [] 
	mask = None

	def format(self):
		bit = 0
		result = ""
		tmp_value = self.value
		if not self.mask is None:
			tmp_value = tmp_value & self.mask

		while tmp_value > 0:
			if self.bits.has_key(bit):
				label = self.bits[bit]
			else:
				label = "Unknown"

			if tmp_value & 1:
				if result:
					result = result + ", "
				result = result + label

			bit = bit + 1
			tmp_value = tmp_value >> 1

		fmt = "%%s (0x%%0%dx)" % (self.size * 2)

		if not result:
			result = "None"

		return fmt % (result, self.value)

class IntBitmapField(BitmapField, IntField):
	pass

class ShortBitmapField(BitmapField, ShortField):
	pass

class ByteBitmapField(BitmapField, ByteField):
	pass

class EnumField(NumericField):
	enum = []
	mask = None

	def format(self):
		value = self.value
		if not self.mask is None:
			value = value & self.mask
		if self.enum.has_key(value):
			label = self.enum[self.value & value]
		else:
			label = "Unknown"

		return "%s (%d)" % (label, self.value)

class DecimalIntField(DecimalField, IntField):
	pass

class DecimalShortField(DecimalField, ShortField):
	pass

class DecimalByteField(DecimalField, ByteField):
	pass

class HexadecimalIntField(HexadecimalField, IntField):
	pass

class HexadecimalShortField(HexadecimalField, ShortField):
	pass

class HexadecimalByteField(HexadecimalField, ByteField):
	pass

class RecipientField(DecimalIntField):
	label = "Recipient"

class SequenceField(DecimalIntField):
	label = "Sequence Number"

class NonceField(HexadecimalIntField):
	label = "Nonce"

class MessageClassField(IntBitmapField):
	label = "Message class"
	bits = {0: "Queued", 3: "Message", 4: "Chat", 8: "No acknowledgment required"}

class OffsetPlainField(DecimalIntField):
	label = "Plain-text message offset"

class OffsetAttributesField(DecimalIntField):
	label = "Attributes offset"

class HtmlTextField(StringField):
	label = "HTML message"

class PlainTextField(StringField):
	label = "Plain-text message"

class MsgAttributesField(BinaryField):
	label = "Attributes"

class UnknownDecimalIntField(DecimalIntField):
	label = "Unknown"

class UnknownDecimalByteField(DecimalByteField):
	label = "Unknown"

class UnknownDecimalShortField(DecimalShortField):
	label = "Unknown"

class LoginFailedIntField(DecimalIntField):
	label = "Reason"

class LoginFailedByteField(DecimalByteField):
	label = "Reason"

class IdField(DecimalIntField):
	label = "Identifier"

class LanguageField(StringField):
	size = 2
	label = "Language"

class IntEnumField(EnumField, IntField):
	pass

class ShortEnumField(EnumField, ShortField):
	pass

class ByteEnumField(EnumField, ByteField):
	pass

class HashTypeField(ByteEnumField):
	label = "Password hash type"
	enum = {1: "GG32", 2: "SHA-1"}

	def store_context(self, ctx):
		ctx.hash_type = self.value

class HashField(BinaryField):
	label = "Password hash"
	size = 64

	def apply_context(self, ctx):
		if ctx.hash_type == 1:
			self.display_size = 4
		elif ctx.hash_type == 2:
			self.display_size = 20

class StatusField(IntEnumField):
	label = "Status"
	enum = {0x01: "Offline",
		0x15: "Offline",
		0x17: "Free for chat",
		0x18: "Free for chat",
		0x02: "Online",
		0x04: "Online",
		0x03: "Busy",
		0x05: "Busy",
		0x21: "Do not disturb",
		0x22: "Do not disturb",
		0x14: "Invisible",
		0x16: "Invisible",
		0x06: "Blocked"}
	mask = 0xff

	def format(self):
		res = IntEnumField.format(self)

		if self.value & 0x0100:
			res = res + ", Image"
		if self.value & 0x0400:
			res = res + ", Adaptive"
		if self.value & 0x4000:
			res = res + ", Description"
		if self.value & 0x8000:
			res = res + ", Buddies only"

		return res

class StatusFlagsField(IntBitmapField):
	bits = {0: "Audio calls", 1: "Video calls", 20: "Mobile", 23: "No spam filter"}
	label = "Flags"

class FeaturesField(IntBitmapField):
	label = "Features"
	mask = 0xfffffff8
	bits = {4: "DND, FFC", 5: "Image status", 9: "User data", 10: "Message acks", 13: "Typing notification", 14: "Multilogon"}

	def format(self):
		if self.value & 7 == 7:
			res = "New protocol"
		else:
			res = "Beta protocol"

		tmp = IntBitmapField.format(self)

		if tmp:
			res = res + ", "

		return res + tmp

class AddressField(BinaryField):
	size = 4
	label = "Address"

	def format(self):
		return ".".join("%d" % (ord(i)) for i in self.value[:4])

class PortField(DecimalShortField):
	label = "Port"
	
class AddressPortField(Field):
	def __init__(self):
		self.address = AddressField()
		self.port = PortField()

	def fetch(self, buf):
		buf = self.address.fetch(buf)
		buf = self.port.fetch(buf)
		return buf

	def format(self):
		return self.address.format() + ":" + self.port.format()

class LocalAddressPortField(AddressPortField):
	label = "Local address"

class ExternalAddressPortField(AddressPortField):
	label = "External address"

class ImageSizeField(DecimalByteField):
	label = "Maximum image size"

class IntLengthField(DecimalIntField):
	def store_context(self, ctx):
		ctx.length = self.value

class LengthStringField(StringField):
	def apply_context(self, ctx):
		self.size = ctx.length

class VersionField(LengthStringField):
	label = "Client version"

class SizedDescrField(LengthStringField):
	label = "Description"

class DescrField(StringField):
	label = "Description"

class ContactTypeField(ByteEnumField):
	label = "Contact type"
	enum = {1: "Restricted",
		3: "Regular",
		4: "Blocked",
		5: "Blocked",
		6: "Blocked",
		7: "Blocked"}

class NotifyField(Field):
	label = "Contact"

	def __init__(self):
		self.id = IdField()
		self.type = ContactTypeField()

	def fetch(self, buf):
		return self.type.fetch(self.id.fetch(buf))

	def format(self):
		return self.id.format() + ", " + self.type.format()

class RepeatField:
	pass

class RepeatPacket:
	pass

_empty_packet = []
_welcome_packet = [NonceField]
_send_msg80_packet = [RecipientField, SequenceField, MessageClassField, OffsetPlainField, OffsetAttributesField, HtmlTextField, PlainTextField, MsgAttributesField]
_login80_packet = [IdField, LanguageField, HashTypeField, HashField, StatusField, StatusFlagsField, FeaturesField, LocalAddressPortField, ExternalAddressPortField, ImageSizeField, UnknownDecimalByteField, IntLengthField, VersionField, IntLengthField, SizedDescrField]
_login80_ok_packet = [UnknownDecimalIntField]
_login80_failed_packet = [LoginFailedIntField]
_login_failed_packet = [LoginFailedByteField]
_notify_packet = [NotifyField, RepeatField]
_new_status_packet = [StatusField, DescrField]
_new_status80_packet = [StatusField, StatusFlagsField, IntLengthField, SizedDescrField]
_notify_reply80_packet = [IdField, StatusField, FeaturesField, ExternalAddressPortField, ImageSizeField, UnknownDecimalByteField, StatusFlagsField, IntLengthField, SizedDescrField, RepeatPacket]

_from_client = {
	GaduPacket.NEW_STATUS: ('NEW_STATUS', _new_status_packet),
	GaduPacket.PONG: ('PONG', _empty_packet),
	GaduPacket.PING: ('PING', _empty_packet),
	GaduPacket.SEND_MSG: ('SEND_MSG', _empty_packet),
	GaduPacket.LOGIN: ('LOGIN', _empty_packet),
	GaduPacket.ADD_NOTIFY: ('ADD_NOTIFY', _empty_packet),
	GaduPacket.REMOVE_NOTIFY: ('REMOVE_NOTIFY', _empty_packet),
	GaduPacket.NOTIFY_FIRST: ('NOTIFY_FIRST', _notify_packet),
	GaduPacket.NOTIFY_LAST: ('NOTIFY_LAST', _notify_packet),
	GaduPacket.LIST_EMPTY: ('LIST_EMPTY', _empty_packet),
	GaduPacket.LOGIN_EXT: ('LOGIN_EXT', _empty_packet),
	GaduPacket.PUBDIR50_REQUEST: ('PUBDIR50_REQUEST', _empty_packet),
	GaduPacket.LOGIN60: ('LOGIN60', _empty_packet),
	GaduPacket.USERLIST_REQUEST: ('USERLIST_REQUEST', _empty_packet),
	GaduPacket.LOGIN70: ('LOGIN70', _empty_packet),
	GaduPacket.DCC7_ID_REQUEST: ('DCC7_ID_REQUEST', _empty_packet),
	GaduPacket.DCC7_UNKNOWN: ('DCC7_UNKNOWN', _empty_packet),
	GaduPacket.DCC7_ABORT: ('DCC7_ABORT', _empty_packet),
	GaduPacket.NEW_STATUS80BETA: ('NEW_STATUS80BETA', _new_status_packet),
	GaduPacket.LOGIN80BETA: ('LOGIN80BETA', _empty_packet),
	GaduPacket.SENG_MSG80: ('SENG_MSG80', _send_msg80_packet),
	GaduPacket.USERLIST_REQUEST80: ('USERLIST_REQUEST80', _empty_packet),
	GaduPacket.LOGIN80: ('LOGIN80', _login80_packet),
	GaduPacket.NEW_STATUS80: ('NEW_STATUS80', _new_status80_packet),
	GaduPacket.USERLIST_REQUEST100: ('USERLIST_REQUEST100', _empty_packet),
	GaduPacket.RECV_MSG_ACK: ('RECV_MSG_ACK', _empty_packet),
	GaduPacket.OWN_DISCONNECT: ('OWN_DISCONNECT', _empty_packet),
}

_from_server = {
	GaduPacket.WELCOME: ('WELCOME', _welcome_packet),
	GaduPacket.STATUS: ('STATUS', _empty_packet),
	GaduPacket.LOGIN_OK: ('LOGIN_OK', _empty_packet),
	GaduPacket.SEND_MSG_ACK: ('SEND_MSG_ACK', _empty_packet),
	GaduPacket.PONG: ('PONG', _empty_packet),
	GaduPacket.PING: ('PING', _empty_packet),
	GaduPacket.LOGIN_FAILED: ('LOGIN_FAILED', _login_failed_packet),
	GaduPacket.RECV_MSG: ('RECV_MSG', _empty_packet),
	GaduPacket.DISCONNECTING: ('DISCONNECTING', _empty_packet),
	GaduPacket.NOTIFY_REPLY: ('NOTIFY_REPLY', _empty_packet),
	GaduPacket.DISCONNECT_ACK: ('DISCONNECT_ACK', _empty_packet),
	GaduPacket.PUBDIR50_REPLY: ('PUBDIR50_REPLY', _empty_packet),
	GaduPacket.STATUS60: ('STATUS60', _empty_packet),
	GaduPacket.USERLIST_REPLY: ('USERLIST_REPLY', _empty_packet),
	GaduPacket.NOTIFY_REPLY60: ('NOTIFY_REPLY60', _empty_packet),
	GaduPacket.NEED_EMAIL: ('NEED_EMAIL', _empty_packet),
	GaduPacket.LOGIN_HASH_TYPE_INVALID: ('LOGIN_HASH_TYPE_INVALID', _empty_packet),
	GaduPacket.STATUS77: ('STATUS77', _empty_packet),
	GaduPacket.NOTIFY_REPLY77: ('NOTIFY_REPLY77', _empty_packet),
	GaduPacket.DCC7_ID_REPLY: ('DCC7_ID_REPLY', _empty_packet),
	GaduPacket.DCC7_ABORTED: ('DCC7_ABORTED', _empty_packet),
	GaduPacket.XML_EVENT: ('XML_EVENT', _empty_packet),
	GaduPacket.STATUS80BETA: ('STATUS80BETA', _empty_packet),
	GaduPacket.NOTIFY_REPLY80BETA: ('NOTIFY_REPLY80BETA', _empty_packet),
	GaduPacket.XML_ACTION: ('XML_ACTION', _empty_packet),
	GaduPacket.RECV_MSG80: ('RECV_MSG80', _empty_packet),
	GaduPacket.USERLIST_REPLY80: ('USERLIST_REPLY80', _empty_packet),
	GaduPacket.LOGIN_OK80: ('LOGIN_OK80', _login80_ok_packet),
	GaduPacket.STATUS80: ('STATUS80', _notify_reply80_packet),
	GaduPacket.NOTIFY_REPLY80: ('NOTIFY_REPLY80', _notify_reply80_packet),
	GaduPacket.USERLIST_REPLY100: ('USERLIST_REPLY100', _empty_packet),
	GaduPacket.LOGIN80_FAILED: ('LOGIN80_FAILED', _login80_failed_packet),
	GaduPacket.USER_DATA: ('USER_DATA', _empty_packet),
	GaduPacket.OWN_MESSAGE: ('OWN_MESSAGE', _empty_packet),
	GaduPacket.OWN_RESOURCE_INFO: ('OWN_RESOURCE_INFO', _empty_packet),
}

_from_both = {
	GaduPacket.DCC7_INFO: ('DCC7_INFO', _empty_packet),
	GaduPacket.DCC7_NEW: ('DCC7_NEW', _empty_packet),
	GaduPacket.DCC7_ACCEPT: ('DCC7_ACCEPT', _empty_packet),
	GaduPacket.DCC7_REJECT: ('DCC7_REJECT', _empty_packet),
	GaduPacket.TYPING_NOTIFY: ('TYPING_NOTIFY', _empty_packet),
}

def _get_packet_data(id, from_server):
	if from_server:
		packets = _from_server
	else:
		packets = _from_client
	
	if packets.has_key(id):
		return packets[id]

	if _from_both.has_key(id):
		return _from_both[id]

	return None	

class ParserContext:
	pass

class PacketParser:
	def __init__(self, buf, from_server):
		self.buf = buf
		(self.id,) = struct.unpack("<I", buf[:4])
		data = _get_packet_data(self.id, from_server)

		if data:
			(self.name, self.parsers) = data
		else:
			(self.name, self.parsers) = None

	def get_name(self):
		res = "0x%02x" % (self.id)

		if self.name:
			res = res + " (%s)" % (self.name)

		return res

	def get_data(self):
		res = ""

		if self.parsers:
			buf = self.buf[8:]	# skip header
			ctx = ParserContext()
			last_parser = None
			i = 0

			while i < len(self.parsers):
				if self.parsers[i] == RepeatField:
					print "Repeating field",
					repeating = True
				elif self.parsers[i] == RepeatPacket:
					res = res + "\n"
					print "Repeating packet"
					i = 0
					continue
				else:
					last_parser = self.parsers[i]
					i = i + 1
					repeating = False
					
				print str(last_parser)
				parser = last_parser()

				parser.apply_context(ctx)

				try:
					buf = parser.fetch(buf)
				except IndexError:
					if repeating:
						break

					if i == 1 and len(self.parsers) > 1 and self.parsers[-1] == RepeatPacket:
						break

					res = res + "Packet too short\n"
					break

				parser.store_context(ctx)

				print parser.label
				if parser.label:
					tmp = parser.format()
					print tmp

					if not tmp is None:
						res = res + parser.label + ": " + tmp + "\n"

			res = res.strip() + "\n\n"

		res = res + hex_dump(self.buf)

		return res


