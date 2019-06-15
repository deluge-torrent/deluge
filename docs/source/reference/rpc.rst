Deluge RPC
==========
---------------
Message Formats
---------------
DelugeRPC is a protocol used for daemon/client communication. There are four
types of messages involved in the protocol: RPC Request, RPC Response,
RPC Error and Event. All messages are zlib compressed with rencode encoded strings
and their data formats are detailed below.

"""""""""""
RPC Request
"""""""""""
This message is created and sent by the client to the server requesting that a
remote method be called. Multiple requests can be bundled in a list.

**[[request_id, method, [args], {kwargs}], ...]**

**request_id** (int)
    An integer determined by the client that is used in replies from the server.
    This is used to ensure the client knows which request the data is in
    response to. Another alternative would be to respond in the same order the
    requests come in, but this could cause lag if an earlier request takes
    longer to process.

**method** (str)
    The name of the remote method to call. This name can be in dotted format to
    call other objects or plugins methods.

**args** (list)
    The arguments to call the method with.

**kwargs** (dict)
    The keyword arguments to call the method with.

""""""""""""
RPC Response
""""""""""""
This message is created and sent in response to a RPC Request from a client. It
will hold the return value of the requested method call. In the case of an
error, a RPC Error message will be sent instead.

**[message_type, request_id, [return_value]]**

**message_type** (int)
    This will be a RPC_RESPONSE type id. This is used on the client side to
    determine what kind of message is being received from the daemon.

**request_id** (int)
    The request_id is the same as the one sent by the client in the initial
    request. It used on the client side to determine what message this is in
    response to.

**return_value** (list)
    The return value of the method call.

"""""""""
RPC Error
"""""""""
This message is created in response to an error generated while processing a
RPC Request and will serve as a replacement for a RPC Response message.

**[message_type, request_id, exception_type, exception_msg, traceback]**

**message_type** (int)
    This will be a RPC_ERROR type id.

**request_id** (int)
    The request_id is the same as the one sent by the client in the initial
    request.

**exception_type** (str)
    The type of exception raised.

**exception_msg** (str)
    The message as to why the exception was raised.

**traceback** (str)
    The traceback of the generated exception.

"""""
Event
"""""
This message is created by the daemon and sent to the clients without being in
response to a RPC Request. Events are generally sent for changes in the
daemon's state that the clients need to be made aware of.

**[message_type, event_name, data]**

**message_type** (int)
    This will be a RPC_EVENT type id.

**event_name** (str)
    This is the name of the event being emitted by the daemon.

**data** (list)
    Additional data to be sent with the event. This is dependent upon the event
    being emitted.
