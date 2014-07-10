#!/usr/bin/env python3
from raven.base import Client
client = Client()

import asyncio
import datetime
from functools import partial
import hashlib
import json
import logging
import mimetypes
import os
import pytz

from aiohttp import EofStream
from aiohttp import HttpErrorException
from aiohttp import Response
from aiohttp import request
from aiohttp import websocket
from aiohttp.server import ServerHttpProtocol
from bs4 import BeautifulSoup
from jinja2 import Template

import translate


TIMEZONE = pytz.timezone('Asia/Tokyo')
now = lambda: datetime.datetime.now(TIMEZONE).strftime('%H:%M:%S %Y-%m-%d')


def _build_static_files(directory):
    for name in os.listdir(directory):
        path = os.path.join(directory, name)
        if os.path.isdir(path):
            yield from _build_static_files(path)
        else:
            with open(path, 'rb') as fobj:
                content = fobj.read()
                length = len(content)
                content_type = mimetypes.guess_type(path)[0]
                if not content_type:
                    content_type = 'application/octet-stream'
            yield path, (length, content, content_type)


def _group(lst, n):
    return zip(*[lst[i::n] for i in range(n)])


def _hash(name):
    return 'line-{}'.format(hashlib.md5(name.encode('utf8')).hexdigest())


def _classes_to_level(classes):
    if 'important' in classes:
        return 2
    elif 'resume' in classes:
        return 1
    else:
        return 0


def _transform(triples):
    for triple in triples:
        line_tag, status_tag, info_tag = triple
        line = line_tag.a.text
        line_en = translate.line(line)
        status = (
            status_tag.span.text if status_tag.span else status_tag.text
        ).strip()
        status_en = translate.status(status)
        classes = status_tag.span['class'] if status_tag.span else []
        level = _classes_to_level(classes)
        yield {
            'id': _hash(line),
            'line': line,
            'line_en': line_en,
            'status': status,
            'status_en': status_en,
            'classes': classes,
            'level': level,
            'more': info_tag.text.strip(),
            'reason': translate.reason(info_tag.text.strip()),
            'severe': translate.is_severe(status),
        }


class HttpServer(ServerHttpProtocol):
    def __init__(self, app, *args, **kwargs):
        self.app = app
        super().__init__(*args, **kwargs)

    @asyncio.coroutine
    def handle_request(self, message, payload):
        upgrade = False
        for hdr, val in message.headers:
            if hdr == 'UPGRADE':
                upgrade = 'websocket' in val.lower()
                break

        if upgrade:
            yield from self._handle_websocket(message, payload)
        else:
            yield from self._handle_http(message, payload)

    @asyncio.coroutine
    def _handle_http(self, message, payload):
        logging.info("{} {}".format(message.method, message.path))
        path = message.path

        if path in self.app.static_files:
            return self._serve_static(path)

        elif path == '/':
            return self._index()
        elif path == '/update':
            return self._update()
        else:
            raise HttpErrorException(404)

    @asyncio.coroutine
    def _handle_websocket(self, message, payload):
        # websocket handshake
        logging.info("WS Connect")
        status, headers, parser, writer = websocket.do_handshake(
            message.method, message.headers, self.transport)

        resp = Response(self.transport, status)
        resp.add_headers(*headers)
        resp.send_headers()

        # install websocket parser
        dataqueue = self.stream.set_parser(parser)

        # notify everybody
        self.app.websockets.append(writer)

        # chat dispatcher
        while True:
            try:
                msg = yield from dataqueue.read()
            except EofStream:
                # client droped connection
                break
            if msg.tp == websocket.MSG_PING:
                writer.pong()
            elif msg.tp == websocket.MSG_CLOSE:
                break

        # notify everybody
        logging.info("WS Disconnect")
        self.app.websockets.remove(writer)

    def _serve_static(self, path):
        self._send(*self.app.static_files[path])

    def _index(self):
        self._send(self.app.index_page_length, self.app.index_page_html)

    def _update(self):
        self._send(
            self.app.update_json_length,
            self.app.update_json,
            'application/json'
        )

    def _send(self, length, content, content_type='text/html'):
        response = Response(self.transport, 200)
        response.add_header('Content-type', content_type)
        response.add_header('Content-length', str(length))
        response.send_headers()
        response.write(content)
        response.write_eof()
        if response.keep_alive():
            self.keep_alive(True)


class App(object):
    url = 'http://transit.loco.yahoo.co.jp/traininfo/area/4/'
    _index_page_html = 'Restarting...'.encode('utf8')
    index_page_length = len(_index_page_html)
    _update_json = json.dumps({'lines': [], 'updated': now()}).encode('utf8')
    update_json_length = len(_update_json)
    update_speed = 30

    def __init__(self, template_path, static_dir):
        self.event_loop = asyncio.get_event_loop()

        self.websockets = []

        self.troubled_lines = {
            'lines': [],
            'updated': now(),
            'live': False,
        }

        with open(template_path, 'r') as file_obj:
            self.template = Template(file_obj.read())
        self.index_page_html = self.template.render(**self.troubled_lines)

        self.static_files = {}
        for path, data in _build_static_files(static_dir):
            rel_path = os.path.relpath(path, static_dir)
            self.static_files['/static/{}'.format(rel_path)] = data

    def run(self, host, port):
        self.event_loop.run_until_complete(
            self.event_loop.create_server(
                lambda: HttpServer(app=self, loop=self.event_loop),
                host,
                port
            )
        )
        logging.info('Running on {}:{}'.format(host, port))
        self.event_loop.run_until_complete(self.update_loop())
        try:
            self.event_loop.run_forever()
        except KeyboardInterrupt:
            self.event_loop.stop()

    @property
    def index_page_html(self):
        return self._index_page_html

    @index_page_html.setter
    def index_page_html(self, value):
        self._index_page_html = value.encode('utf8')
        self.index_page_length = len(self._index_page_html)

    @property
    def update_json(self):
        return self._update_json

    @update_json.setter
    def update_json(self, value):
        self._update_json = value.encode('utf8')
        self.update_json_length = len(self._update_json)

    @asyncio.coroutine
    def update_loop(self):
        logging.info("Starting update of information")
        response = yield from request('GET', self.url)
        data = yield from response.read()
        response.close()
        soup = BeautifulSoup(data)
        raw_triples = _group(soup.select('table.trouble-list tr td'), 3)
        information = _transform(raw_triples)

        self.troubled_lines = {
            'lines': list(
                sorted(
                    information,
                    key=lambda info: info['line_en']
                )
            ),
            'updated': now(),
            'live': True
        }

        self.index_page_html = self.template.render(**self.troubled_lines)
        self.update_json = json.dumps(self.troubled_lines)
        for socket in self.websockets:
            socket.send(self.update_json)
        logging.info("Update complete")
        self.event_loop.call_later(
            self.update_speed,
            partial(asyncio.async, self.update_loop(), loop=self.event_loop)
        )


def run():
    logging.basicConfig(level=logging.INFO)
    this_dir = os.path.abspath(os.path.dirname(__file__))
    template_path = os.path.join(this_dir, 'index.html')
    static_dir = os.path.join(this_dir, 'static')
    app = App(template_path, static_dir)
    app.run(
        os.environ.get('BIND_HOST', '0.0.0.0'),
        int(os.environ.get('PORT', 8000))
    )


if __name__ == '__main__':
    run()
