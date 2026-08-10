# -*- coding: utf-8 -*-
"""

    Copyright (C) 2016-2018 script.module.python.twitch

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

# Localhost HTTP service for rewritten Twitch master playlists.
# InputStream Adaptive refuses non-HTTP manifests (it requires an HTTP status
# line), so the master built in utils.isa_manifest_url() has to be served over
# HTTP instead of being read from disk.

import http.server
import os
import socketserver
import threading

import xbmcvfs

from .common import log_utils

EB_HTTP_HOST = '127.0.0.1'
EB_HTTP_PORT = 48664
EB_MANIFEST_FILENAME = 'plugin.video.twitch-eb-master.m3u8'


class _ManifestHandler(http.server.BaseHTTPRequestHandler):
    def _serve(self, send_body):
        if self.path != '/' + EB_MANIFEST_FILENAME:
            self.send_error(404)
            return
        path = os.path.join(xbmcvfs.translatePath('special://temp/'), EB_MANIFEST_FILENAME)
        try:
            with open(path, 'rb') as f:
                data = f.read()
        except OSError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        if send_body:
            self.wfile.write(data)

    def do_GET(self):
        self._serve(send_body=True)

    def do_HEAD(self):
        self._serve(send_body=False)

    def log_message(self, format, *args):  # keep kodi.log clean
        pass


class _Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start():
    """Start the manifest server in a daemon thread. Returns the server or None."""
    try:
        server = _Server((EB_HTTP_HOST, EB_HTTP_PORT), _ManifestHandler)
    except OSError as e:
        log_utils.log('EB manifest server: bind to %s:%d failed |%s|' %
                      (EB_HTTP_HOST, EB_HTTP_PORT, e), log_utils.LOGWARNING)
        return None
    threading.Thread(target=server.serve_forever, name='eb-manifest-server', daemon=True).start()
    log_utils.log('EB manifest server: listening on %s:%d' % (EB_HTTP_HOST, EB_HTTP_PORT),
                  log_utils.LOGDEBUG)
    return server


def stop(server):
    if server:
        server.shutdown()
        server.server_close()
