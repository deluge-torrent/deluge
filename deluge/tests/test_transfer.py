# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Bro <bro.development@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import print_function, unicode_literals

import base64

import rencode
from twisted.trial import unittest

import deluge.log
from deluge.transfer import DelugeTransferProtocol

deluge.log.setup_logger('none')


class TransferTestClass(DelugeTransferProtocol):
    def __init__(self):
        DelugeTransferProtocol.__init__(self)
        self.transport = self
        self.messages_out = []
        self.messages_in = []
        self.packet_count = 0

    def write(self, message):
        """
        Called by DelugeTransferProtocol class
        This simulates the write method of the self.transport in DelugeTransferProtocol.
        """
        self.messages_out.append(message)

    def message_received(self, message):
        """
        This method overrides message_received is DelugeTransferProtocol and is
        called with the complete message as it was sent by DelugeRPCProtocol
        """
        self.messages_in.append(message)

    def get_messages_out_joined(self):
        return b''.join(self.messages_out)

    def get_messages_in(self):
        return self.messages_in

    def data_received_old_protocol(self, data):
        """
        This is the original method logic (as close as possible) for handling data receival on the client

        :param data: a zlib compressed string encoded with rencode.

        """
        import zlib

        print('\n=== New Data Received ===\nBytes received:', len(data))

        if self._buffer:
            # We have some data from the last dataReceived() so lets prepend it
            print('Current buffer:', len(self._buffer) if self._buffer else '0')
            data = self._buffer + data
            self._buffer = None

        self.packet_count += 1
        self._bytes_received += len(data)

        while data:
            print('\n-- Handle packet data --')

            print('Bytes received:', self._bytes_received)
            print('Current data:', len(data))

            if self._message_length == 0:
                # handle_new_message uses _buffer so set data to _buffer.
                self._buffer = data
                self._handle_new_message()
                data = self._buffer
                self._buffer = None
                self.packet_count = 1
                print('New message of length:', self._message_length)

            dobj = zlib.decompressobj()
            try:
                request = rencode.loads(dobj.decompress(data))
                print('Successfully loaded message', end=' ')
                print(
                    ' - Buffer length: %d, data length: %d, unused length: %d'
                    % (
                        len(data),
                        len(data) - len(dobj.unused_data),
                        len(dobj.unused_data),
                    )
                )
                print('Packet count:', self.packet_count)
            except Exception as ex:
                # log.debug('Received possible invalid message (%r): %s', data, e)
                # This could be cut-off data, so we'll save this in the buffer
                # and try to prepend it on the next dataReceived()
                self._buffer = data
                print(
                    'Failed to load buffer (size %d): %s' % (len(self._buffer), str(ex))
                )
                return
            else:
                data = dobj.unused_data
                self._message_length = 0

            self.message_received(request)


class DelugeTransferProtocolTestCase(unittest.TestCase):
    def setUp(self):  # NOQA: N803
        """
        The expected messages corresponds to the test messages (msg1, msg2) after they've been processed
        by DelugeTransferProtocol.send, which means that they've first been encoded with rencode,
        and then compressed with zlib.
        The expected messages are encoded in base64 to easily including it here in the source.
        So before comparing the results with the expected messages, the expected messages must be decoded,
        or the result message be encoded in base64.

        """
        self.transfer = TransferTestClass()
        self.msg1 = (
            0,
            1,
            {'key_int': 1242429423},
            {'key_str': b'some string'},
            {'key_bool': True},
        )
        self.msg2 = (
            2,
            3,
            {'key_float': 12424.29423},
            {'key_unicode': 'some string'},
            {'key_dict_with_tuple': {'key_tuple': (1, 2, 3)}},
            {'keylist': [4, '5', 6.7]},
        )

        self.msg1_expected_compressed_base64 = (
            b'AQAAADF4nDvKwJjenp1aGZ+ZV+Lgxfv9PYRXXFLU'
            b'XZyfm6oAZGTmpad3gAST8vNznAEAJhSQ'
        )
        self.msg2_expected_compressed_base64 = (
            b'AQAAAF14nDvGxJzemZ1aGZ+Wk59Y4uTmpKib3g3il+ZlJuenpH'
            b'YX5+emKhSXFGXmpadPBkmkZCaXxJdnlmTEl5QW5KRCdIOZhxmB'
            b'hrUDuTmZxSWHWRpNnRyupaUBAHYlJxI='
        )

    def test_send_one_message(self):
        """
        Send one message and test that it has been sent correctoly to the
        method 'write' in self.transport.

        """
        self.transfer.transfer_message(self.msg1)
        # Get the data as sent by DelugeTransferProtocol
        messages = self.transfer.get_messages_out_joined()
        base64_encoded = base64.b64encode(messages)
        self.assertEqual(base64_encoded, self.msg1_expected_compressed_base64)

    def test_receive_one_message(self):
        """
        Receive one message and test that it has been sent to the
        method 'message_received'.

        """
        self.transfer.dataReceived(
            base64.b64decode(self.msg1_expected_compressed_base64)
        )
        # Get the data as sent by DelugeTransferProtocol
        messages = self.transfer.get_messages_in().pop(0)
        self.assertEqual(rencode.dumps(self.msg1), rencode.dumps(messages))

    def test_receive_old_message(self):
        """
        Receive an old message (with no header) and verify that the data is discarded.

        """
        self.transfer.dataReceived(rencode.dumps(self.msg1))
        self.assertEqual(len(self.transfer.get_messages_in()), 0)
        self.assertEqual(self.transfer._message_length, 0)
        self.assertEqual(len(self.transfer._buffer), 0)

    def test_receive_two_concatenated_messages(self):
        """
        This test simply concatenates two messsages (as they're sent over the network),
        and lets DelugeTransferProtocol receive the data as one string.

        """
        two_concatenated = base64.b64decode(
            self.msg1_expected_compressed_base64
        ) + base64.b64decode(self.msg2_expected_compressed_base64)
        self.transfer.dataReceived(two_concatenated)

        # Get the data as sent by DelugeTransferProtocol
        message1 = self.transfer.get_messages_in().pop(0)
        self.assertEqual(rencode.dumps(self.msg1), rencode.dumps(message1))
        message2 = self.transfer.get_messages_in().pop(0)
        self.assertEqual(rencode.dumps(self.msg2), rencode.dumps(message2))

    def test_receive_three_messages_in_parts(self):
        """
        This test concatenates three messsages (as they're sent over the network),
        and lets DelugeTransferProtocol receive the data in multiple parts.

        """
        msg_bytes = (
            base64.b64decode(self.msg1_expected_compressed_base64)
            + base64.b64decode(self.msg2_expected_compressed_base64)
            + base64.b64decode(self.msg1_expected_compressed_base64)
        )
        packet_size = 40

        one_message_byte_count = len(
            base64.b64decode(self.msg1_expected_compressed_base64)
        )
        two_messages_byte_count = one_message_byte_count + len(
            base64.b64decode(self.msg2_expected_compressed_base64)
        )
        three_messages_byte_count = two_messages_byte_count + len(
            base64.b64decode(self.msg1_expected_compressed_base64)
        )

        for d in self.receive_parts_helper(msg_bytes, packet_size):
            bytes_received = self.transfer.get_bytes_recv()

            if bytes_received >= three_messages_byte_count:
                expected_msgs_received_count = 3
            elif bytes_received >= two_messages_byte_count:
                expected_msgs_received_count = 2
            elif bytes_received >= one_message_byte_count:
                expected_msgs_received_count = 1
            else:
                expected_msgs_received_count = 0
            # Verify that the expected number of complete messages has arrived
            self.assertEqual(
                expected_msgs_received_count, len(self.transfer.get_messages_in())
            )

        # Get the data as received by DelugeTransferProtocol
        message1 = self.transfer.get_messages_in().pop(0)
        self.assertEqual(rencode.dumps(self.msg1), rencode.dumps(message1))
        message2 = self.transfer.get_messages_in().pop(0)
        self.assertEqual(rencode.dumps(self.msg2), rencode.dumps(message2))
        message3 = self.transfer.get_messages_in().pop(0)
        self.assertEqual(rencode.dumps(self.msg1), rencode.dumps(message3))

    # Remove underscore to enable test, or run the test directly:
    # tests $ trial test_transfer.DelugeTransferProtocolTestCase._test_rencode_fail_protocol
    def _test_rencode_fail_protocol(self):
        """
        This test tries to test the protocol that relies on errors from rencode.

        """
        msg_bytes = (
            base64.b64decode(self.msg1_expected_compressed_base64)
            + base64.b64decode(self.msg2_expected_compressed_base64)
            + base64.b64decode(self.msg1_expected_compressed_base64)
        )
        packet_size = 149

        one_message_byte_count = len(
            base64.b64decode(self.msg1_expected_compressed_base64)
        )
        two_messages_byte_count = one_message_byte_count + len(
            base64.b64decode(self.msg2_expected_compressed_base64)
        )
        three_messages_byte_count = two_messages_byte_count + len(
            base64.b64decode(self.msg1_expected_compressed_base64)
        )

        print()

        print(
            'Msg1 size:',
            len(base64.b64decode(self.msg1_expected_compressed_base64)) - 4,
        )
        print(
            'Msg2 size:',
            len(base64.b64decode(self.msg2_expected_compressed_base64)) - 4,
        )
        print(
            'Msg3 size:',
            len(base64.b64decode(self.msg1_expected_compressed_base64)) - 4,
        )

        print('one_message_byte_count:', one_message_byte_count)
        print('two_messages_byte_count:', two_messages_byte_count)
        print('three_messages_byte_count:', three_messages_byte_count)

        for d in self.receive_parts_helper(
            msg_bytes, packet_size, self.transfer.data_received_old_protocol
        ):
            bytes_received = self.transfer.get_bytes_recv()

            if bytes_received >= three_messages_byte_count:
                expected_msgs_received_count = 3
            elif bytes_received >= two_messages_byte_count:
                expected_msgs_received_count = 2
            elif bytes_received >= one_message_byte_count:
                expected_msgs_received_count = 1
            else:
                expected_msgs_received_count = 0
            # Verify that the expected number of complete messages has arrived
            if expected_msgs_received_count != len(self.transfer.get_messages_in()):
                print(
                    'Expected number of messages received is %d, but %d have been received.'
                    % (
                        expected_msgs_received_count,
                        len(self.transfer.get_messages_in()),
                    )
                )

        # Get the data as received by DelugeTransferProtocol
        message1 = self.transfer.get_messages_in().pop(0)
        self.assertEqual(rencode.dumps(self.msg1), rencode.dumps(message1))
        message2 = self.transfer.get_messages_in().pop(0)
        self.assertEqual(rencode.dumps(self.msg2), rencode.dumps(message2))
        message3 = self.transfer.get_messages_in().pop(0)
        self.assertEqual(rencode.dumps(self.msg1), rencode.dumps(message3))

    def test_receive_middle_of_header(self):
        """
        This test concatenates two messsages (as they're sent over the network),
        and lets DelugeTransferProtocol receive the data in two parts.
        The first part contains the first message, plus two bytes of the next message.
        The next part contains the rest of the message.

        This is a special case, as DelugeTransferProtocol can't start parsing
        a message until it has at least 5 bytes (the size of the header) to be able
        to read and parse the size of the payload.

        """
        two_concatenated = base64.b64decode(
            self.msg1_expected_compressed_base64
        ) + base64.b64decode(self.msg2_expected_compressed_base64)
        first_len = len(base64.b64decode(self.msg1_expected_compressed_base64))

        # Now found the entire first message, and half the header of the next message  (2 bytes into the header)
        self.transfer.dataReceived(two_concatenated[: first_len + 2])

        # Should be 1 message in the list
        self.assertEqual(1, len(self.transfer.get_messages_in()))

        # Send the rest
        self.transfer.dataReceived(two_concatenated[first_len + 2 :])

        # Should be 2 messages in the list
        self.assertEqual(2, len(self.transfer.get_messages_in()))

        # Get the data as sent by DelugeTransferProtocol
        message1 = self.transfer.get_messages_in().pop(0)
        self.assertEqual(rencode.dumps(self.msg1), rencode.dumps(message1))
        message2 = self.transfer.get_messages_in().pop(0)
        self.assertEqual(rencode.dumps(self.msg2), rencode.dumps(message2))

    # Needs file containing big data structure e.g. like thetorrent list as it is transfered by the daemon
    # def test_simulate_big_transfer(self):
    #    filename = '../deluge.torrentlist'
    #
    #    f = open(filename, 'r')
    #    data = f.read()
    #    message_to_send = eval(data)
    #    self.transfer.transfer_message(message_to_send)
    #
    # Get the data as sent to the network by DelugeTransferProtocol
    #    compressed_data = self.transfer.get_messages_out_joined()
    # packet_size = 16000 # Or something smaller...
    #
    #    for d in self.receive_parts_helper(compressed_data, packet_size):
    #        bytes_recv = self.transfer.get_bytes_recv()
    #        if bytes_recv < len(compressed_data):
    #            self.assertEqual(len(self.transfer.get_messages_in()), 0)
    #        else:
    #            self.assertEqual(len(self.transfer.get_messages_in()), 1)
    # Get the data as received by DelugeTransferProtocol
    #    transfered_message = self.transfer.get_messages_in().pop(0)
    # Test that the data structures are equal
    # self.assertEqual(transfered_message, message_to_send)
    # self.assertTrue(transfered_message == message_to_send)
    #
    # f.close()
    # f = open('rencode.torrentlist', 'w')
    # f.write(str(transfered_message))
    # f.close()

    def receive_parts_helper(self, data, packet_size, receive_func=None):
        byte_count = len(data)
        sent_bytes = 0
        while byte_count > 0:
            to_receive = packet_size if byte_count > packet_size else byte_count
            sent_bytes += to_receive
            byte_count -= to_receive
            if receive_func:
                receive_func(data[:to_receive])
            else:
                self.transfer.dataReceived(data[:to_receive])
            data = data[to_receive:]
            yield
