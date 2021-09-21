# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Bro <bro.development@gmail.com>
# Copyright (C) 2018 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import struct
import zlib

import rencode
from twisted.internet.protocol import Protocol

log = logging.getLogger(__name__)

PROTOCOL_VERSION = 1
MESSAGE_HEADER_FORMAT = '!BI'
MESSAGE_HEADER_SIZE = struct.calcsize(MESSAGE_HEADER_FORMAT)


class DelugeTransferProtocol(Protocol, object):
    """
    Deluge RPC wire protocol.

    Data messages are transferred with a header containing a protocol version
    and the length of the data to be transferred (payload).

    The format is::

            ubyte    uint4     bytestring
        |.version.|..size..|.....body.....|

    The version is an unsigned byte that indicates the protocol version.
    The size is a unsigned 32-bit integer that is equal to the length of the body bytestring.
    The body is the compressed rencoded byte string of the data object.
    """

    def __init__(self):
        self._buffer = b''  # TODO: Look into using bytearray instead of byte string.
        self._message_length = 0
        self._bytes_received = 0
        self._bytes_sent = 0

    def transfer_message(self, data):
        """
        Transfer the data.

        :param data: data to be transferred in a data structure serializable by rencode.
        """
        body = zlib.compress(rencode.dumps(data))
        body_len = len(body)
        message = struct.pack(
            '{}{}s'.format(MESSAGE_HEADER_FORMAT, body_len),
            PROTOCOL_VERSION,
            body_len,
            body,
        )
        self._bytes_sent += len(message)
        self.transport.write(message)

    def dataReceived(self, data):  # NOQA: N802
        """
        This method is called whenever data is received.

        :param data: a message as transferred by transfer_message, or a part of such
                     a message.

        Global variables:
            _buffer         - contains the data received
            _message_length - the length of the payload of the current message.

        """
        self._buffer += data
        self._bytes_received += len(data)

        while len(self._buffer) >= MESSAGE_HEADER_SIZE:
            if self._message_length == 0:
                self._handle_new_message()
            # We have a complete packet
            if len(self._buffer) >= self._message_length:
                self._handle_complete_message(self._buffer[: self._message_length])
                # Remove message data from buffer
                self._buffer = self._buffer[self._message_length :]
                self._message_length = 0
            else:
                break

    def _handle_new_message(self):
        """
        Handle the start of a new message. This method is called only when the
        beginning of the buffer contains data from a new message (i.e. the header).

        """
        try:
            # Read the first bytes of the message (MESSAGE_HEADER_SIZE bytes)
            header = self._buffer[:MESSAGE_HEADER_SIZE]
            # Extract the length stored as an unsigned 32-bit integer
            version, self._message_length = struct.unpack(MESSAGE_HEADER_FORMAT, header)
            if version != PROTOCOL_VERSION:
                raise Exception(
                    'Received invalid protocol version: {}. PROTOCOL_VERSION is {}.'.format(
                        version, PROTOCOL_VERSION
                    )
                )
            # Remove the header from the buffer
            self._buffer = self._buffer[MESSAGE_HEADER_SIZE:]
        except Exception as ex:
            log.warning('Error occurred when parsing message header: %s.', ex)
            log.warning(
                'This version of Deluge cannot communicate with the sender of this data.'
            )
            self._message_length = 0
            self._buffer = b''

    def _handle_complete_message(self, data):
        """
        Handles a complete message as it is transferred on the network.

        :param data: a zlib compressed string encoded with rencode.

        """
        try:
            self.message_received(
                rencode.loads(zlib.decompress(data), decode_utf8=True)
            )
        except Exception as ex:
            log.warning(
                'Failed to decompress (%d bytes) and load serialized data with rencode: %s',
                len(data),
                ex,
            )

    def get_bytes_recv(self):
        """
        Returns the number of bytes received.

        :returns: the number of bytes received
        :rtype: int

        """
        return self._bytes_received

    def get_bytes_sent(self):
        """
        Returns the number of bytes sent.

        :returns: the number of bytes sent
        :rtype: int

        """
        return self._bytes_sent

    def message_received(self, message):
        """Override this method to receive the complete message"""
        pass
