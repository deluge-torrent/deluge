"""Local WSS tracker for WebTorrent integration tests."""

import asyncio
import json
import ssl
import subprocess
import threading
from pathlib import Path


class RelayWssTracker:
    """Relay WebRTC offers and answers between WSS tracker clients."""

    def __init__(self, directory):
        self.directory = Path(directory)
        self.ready = threading.Event()
        self.port = None
        self.error = None
        self.offers_relayed = 0
        self.answers_relayed = 0

    def start(self):
        cert = self.directory / 'cert.pem'
        key = self.directory / 'key.pem'
        subprocess.run(
            [
                'openssl',
                'req',
                '-x509',
                '-newkey',
                'rsa:2048',
                '-nodes',
                '-days',
                '1',
                '-subj',
                '/CN=localhost',
                '-addext',
                'subjectAltName=IP:127.0.0.1',
                '-keyout',
                str(key),
                '-out',
                str(cert),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(str(cert), str(key))
        self.thread = threading.Thread(target=self.run, args=(context,), daemon=True)
        self.thread.start()
        if not self.ready.wait(10):
            raise RuntimeError('WSS server startup timeout')
        if self.error:
            raise self.error

    def stop(self):
        async def close():
            self.server.close()
            await self.server.wait_closed()

        try:
            asyncio.run_coroutine_threadsafe(close(), self.loop).result(10)
        finally:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join(timeout=10)
        if self.thread.is_alive():
            raise RuntimeError('WSS tracker thread did not stop')

    def run(self, context):
        from websockets.legacy.server import serve

        peers = {}
        pending_offers = {}

        async def handler(websocket):
            owned = set()
            try:
                async for payload in websocket:
                    request = json.loads(payload)
                    if request.get('action') != 'announce':
                        continue

                    info_hash = request['info_hash']
                    peer_id = request['peer_id']

                    if 'answer' in request:
                        target = peers.get((info_hash, request['to_peer_id']))
                        if target is not None:
                            await target.send(
                                json.dumps(
                                    {
                                        'action': 'announce',
                                        'info_hash': info_hash,
                                        'peer_id': peer_id,
                                        'offer_id': request['offer_id'],
                                        'answer': request['answer'],
                                    }
                                )
                            )
                            self.answers_relayed += 1
                        continue

                    key = (info_hash, peer_id)
                    peers[key] = websocket
                    owned.add(key)
                    await websocket.send(
                        json.dumps(
                            {
                                'action': 'announce',
                                'info_hash': info_hash,
                                'interval': 120,
                                'min_interval': 60,
                            }
                        )
                    )

                    for offer in pending_offers.get(info_hash, []):
                        if offer['peer_id'] != peer_id:
                            await websocket.send(json.dumps(offer))
                            self.offers_relayed += 1

                    # One offer per announce is sufficient for this two-peer
                    # test; limiting it avoids hundreds of redundant ICE peers.
                    for offer in request.get('offers', [])[:1]:
                        forwarded = {
                            'action': 'announce',
                            'info_hash': info_hash,
                            'peer_id': peer_id,
                            'offer_id': offer['offer_id'],
                            'offer': offer['offer'],
                        }
                        pending_offers.setdefault(info_hash, []).append(forwarded)
                        for (other_hash, other_id), other in list(peers.items()):
                            if other_hash == info_hash and other_id != peer_id:
                                await other.send(json.dumps(forwarded))
                                self.offers_relayed += 1
            finally:
                for key in owned:
                    if peers.get(key) is websocket:
                        peers.pop(key)

        async def start_server():
            self.server = await serve(handler, '127.0.0.1', 0, ssl=context)
            self.port = self.server.sockets[0].getsockname()[1]

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(start_server())
        except Exception as exc:
            self.error = exc
        finally:
            self.ready.set()
        if self.error:
            self.loop.close()
            return
        self.loop.run_forever()
        self.loop.close()
