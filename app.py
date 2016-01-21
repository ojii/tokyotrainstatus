import datetime
import hashlib
import json
import logging

import asyncio
import os

import aiohttp
import aiohttp_jinja2
import jinja2
import pytz
from aiohttp import web
from bs4 import BeautifulSoup

import translate

UPDATE_URL = 'http://transit.loco.yahoo.co.jp/traininfo/area/4/'
INTERVAL = 30
TIMEZONE = pytz.timezone('Asia/Tokyo')
now = lambda: datetime.datetime.now(TIMEZONE).strftime('%H:%M:%S %Y-%m-%d')


def _group(lst, n):
    return zip(*[lst[i::n] for i in range(n)])


def _hash(name):
    return 'line-{}'.format(hashlib.md5(name.encode('utf8')).hexdigest())


def _status_to_level(status):
    if status == '運転見合わせ':
        return 2
    elif status != '平常運転':
        return 1
    else:
        return 0


def _transform(triples):
    for triple in triples:
        line_tag, status_tag, info_tag = triple
        line = line_tag.a.text
        line_en = translate.line(line)
        status = (
            status_tag.select('span.colTrouble')[0].text
            if status_tag.select('span.colTrouble')
            else status_tag.text
        ).strip()
        status_en = translate.status(status)
        level = _status_to_level(status)
        yield {
            'id': _hash(line),
            'line': line,
            'line_en': line_en,
            'status': status,
            'status_en': status_en,
            'level': level,
            'more': info_tag.text.strip(),
            'reason': translate.reason(info_tag.text.strip()),
            'severe': translate.is_severe(status),
        }


@aiohttp_jinja2.template('index.html')
async def index(request: web.Request) -> dict:
    return request.app['data']


async def update(request: web.Request) -> web.Response:
    return web.json_response(request.app['data'])


async def websocket(request: web.Request) -> web.WebSocketResponse:
    logging.info('New Websocket')
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    request.app['sockets'].append(ws)

    ws.send_str(json.dumps(request.app['data']))

    try:
        async for msg in ws:
            if msg.tp == aiohttp.MsgType.error:
                request.app['sockets'].remove(ws)
                break
    except aiohttp.WSClientDisconnectedError:
        request.app['sockets'].remove(ws)

    return ws


async def get_info(url: str) -> dict:
    response = await aiohttp.get(url)
    logging.info("Got response")
    data = await response.text()
    logging.info("Got response body")
    soup = BeautifulSoup(data, "html.parser")
    raw_triples = _group(soup.select('div.trouble table tr td'), 3)
    information = _transform(raw_triples)
    lines = list(
        sorted(
            information,
            key=lambda info: info['line_en']
        )
    )
    return lines


async def loop(app: web.Application):
    while app['running']:
        logging.info("Starting update of information")
        try:
            lines = await get_info(app['url'])
        except:
            logging.exception("Failed to update")
        else:
            app['data'] = {
                'lines': lines,
                'updated': now(),
                'live': True
            }

            try:
                json_data = json.dumps(app['data'])
            except:
                logging.exception("Failed to JSON encode")
            else:
                for socket in app['sockets']:
                    try:
                        socket.send_str(json_data)
                    except:
                        logging.exception("Failed to send to websocket")

        logging.info("Update complete")

        for _ in range(app['interval']):
            if not app['running']:
                break
            await asyncio.sleep(1)


async def logging_middleware_factory(app: web.Application, handler):
    async def logging_middleware(request: web.Request):
        logging.info('{request.method} {request.path}'.format(request=request))
        return await handler(request)
    return logging_middleware


def main(template_path: str, static_dir: str, update_url: str, interval: int,
         bind_host: str, port: int):
    app = web.Application(
        middlewares=[logging_middleware_factory]
    )
    app['url'] = update_url
    app['interval'] = interval
    app['data'] = {
        'lines': [],
        'updated': now(),
        'live': False,
    }
    app['sockets'] = []
    app['running'] = True
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(template_path))
    app.router.add_route('GET', '/', index)
    app.router.add_route('GET', '/update/', update)
    app.router.add_route('GET', '/ws/', websocket)
    app.router.add_static('/static/', static_dir)

    event_loop = asyncio.get_event_loop()
    handler = app.make_handler()
    future = event_loop.create_server(handler, bind_host, port)
    server = event_loop.run_until_complete(future)
    print('serving on', server.sockets[0].getsockname())
    looper = asyncio.ensure_future(loop(app), loop=event_loop)
    try:
        event_loop.run_forever()
    except KeyboardInterrupt:
        app['running'] = False
    finally:
        server.close()
        event_loop.run_until_complete(server.wait_closed())
        event_loop.run_until_complete(handler.finish_connections(1.0))
        event_loop.run_until_complete(app.finish())
        event_loop.run_until_complete(looper)
    event_loop.close()


def run():
    logging.basicConfig(level=logging.INFO)
    this_dir = os.path.abspath(os.path.dirname(__file__))
    template_path = os.path.join(this_dir, 'templates')
    static_dir = os.path.join(this_dir, 'static')
    bind_host = os.environ.get('BIND_HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5555))
    main(template_path, static_dir, UPDATE_URL, INTERVAL, bind_host, port)


if __name__ == '__main__':
    run()
