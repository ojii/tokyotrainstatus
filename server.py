#!/usr/bin/env python3
from raven.base import Client
client = Client()
import datetime
from functools import partial
import json
import logging
import mimetypes
from aiohttp import HttpErrorException, Response, request
from aiohttp.server import ServerHttpProtocol
import asyncio
from bs4 import BeautifulSoup
import hashlib
from jinja2 import Template
import os
import pytz


TIMEZONE = pytz.timezone('Asia/Tokyo')
now = lambda: datetime.datetime.now(TIMEZONE).strftime('%H:%M:%S %Y-%m-%d')


LINES = {
    'いすみ鉄道いすみ線': 'Isumi Line',
    'こどもの国線': 'Kodomo-no-Kuni Line',
    'つくばエクスプレス': 'Tsukuba Express',
    'みなとみらい線': 'Minatomirai Line',
    'ゆりかもめ線': 'Yurikamome',
    'りんかい線': 'Rinkai Line',
    'グリーンライン': 'Green Line',
    'ニューシャトル': 'New Shuttle',
    'ブルーライン': 'Blue Line',
    'ユーカリが丘線': 'Yukarigaoka Line',
    '上越線[高崎～水上]': 'Joetsu Line [Takasaki - Minakami]',
    '両毛線': 'Ryomo Line',
    '中央本線[高尾～大月]': 'Chuo Line [Takao - Otsuki]',
    '中央総武線(各停)': 'Chuo Sobu (Local)',
    '中央線(快速)[東京～高尾]': 'Chuo Line (Rapid) [Tokyo - Takao]',
    '久留里線': 'Kururi Line',
    '五日市線': 'Itsukaichi Line',
    '京急久里浜線': 'Keikyu Kurihama Line',
    '京急大師線': 'Keikyu Daishi Line',
    '京急本線': 'Keikyu Main Line',
    '京急空港線': 'Keikyu Airport Line',
    '京急逗子線': 'Keikyu Zushi Line',
    '京成千原線': 'Keisei Chihara Line',
    '京成千葉線': 'Keisei Chiba Line',
    '京成押上線': 'Keisei Oshiage Line',
    '京成本線': 'Keisei Main Line',
    '京成東成田線': 'Keisei Higashinarita Line',
    '京成金町線': 'Keisei Kanamachi Line',
    '京浜東北根岸線': 'Keihin Tohoku Negishi Line',
    '京王井の頭線': 'Keio Inokashira Line',
    '京王動物園線': 'Keio Dobutsuen Line',
    '京王新線': 'Keio New Line',
    '京王相模原線': 'Keio Sagamihara Line',
    '京王競馬場線': 'Keio Keibajo Line',
    '京王線': 'Keio Line',
    '京王高尾線': 'Keio Takao Line',
    '京葉線': 'Keiyo Line',
    '伊東線': 'Ito Line',
    '伊豆急行線': 'Izukyuko Line',
    '伊豆箱根鉄道大雄山線': 'Izuhakone Daiyuzan Line',
    '信越本線[高崎～横川]': 'Shinetsu Line [Takasaki - Yokogawa]',
    '八高川越線[八王子～川越]': 'Hachi-daka Kawagoe Line [Hachioji-Kawagoe]',
    '八高線[高麗川～高崎]': 'Hachiko Line [Komagawa - Takasaki]',
    '内房線': 'Uchibo Line',
    '北総線': 'Hokuso Line',
    '千葉都市モノレール1号線': 'Chiba Monorail Line 1',
    '千葉都市モノレール2号線': 'Chiba Monorail Line 2',
    '南武線[尻手～浜川崎]': 'Nambu Line [Shitte-Hamakawasaki]',
    '南武線[川崎～立川]': 'Nambu Line [Kawasaki-Tachikawa]',
    '吾妻線': 'Agatsuma Line',
    '埼京川越線[大崎～川越]': 'Saikyo Kawagoe Line [Osaki - Kawagoe]',
    '埼玉高速鉄道線': 'Saitama Rapid Railway Line',
    '外房線': 'Sotobo Line',
    '多摩都市モノレール線': 'Tama Monorail',
    '宇都宮線[上野～宇都宮]': 'Utsunomiya Line [Ueno-Utsunomiya]',
    '宇都宮線[宇都宮～黒磯]': 'Utsunomiya Line [Utsunomiya-Kuroiso]',
    '富士急行線': 'Fuji Kyuko Line',
    '小湊鉄道線': 'Kominato Line',
    '小田急多摩線': 'Odakyu Tama Line',
    '小田急小田原線': 'Odakyu Odawara Line',
    '小田急江ノ島線': 'Odakyu Main Line',
    '山手線': 'Yamanote Line',
    '常磐線(各停)': 'Joban Line (Kakutei)',
    '常磐線(快速)[上野～取手]': 'Joban Line (Rapid) [Ueno-Toride]',
    '常磐線[勝田～いわき]': 'Joban Line [Katsuta - Iwaki]',
    '常磐線[取手～土浦]': 'Joban Line [Toride-Tsuchiura]',
    '常磐線[土浦～勝田]': 'Joban Line [Tsuchiura - Katsuta]',
    '成田スカイアクセス': 'Narita Sky Access Line',
    '成田線[佐倉～成田空港・銚子]': 'Narita Line [Sakura-Narita/Choshi]',
    '成田線[我孫子～成田]': 'Narita Line [Abiko-Narita]',
    '新京成線': 'New Keisei Line',
    '日光線': 'Nikko Line',
    '日暮里・舎人ライナー': 'Nippori Toneri Liner',
    '東京メトロ丸ノ内線': 'Tokyo Metro Marunouchi Line',
    '東京メトロ副都心線': 'Tokyo Metro Fukutoshin',
    '東京メトロ千代田線': 'Tokyo Metro Chiyoda Line',
    '東京メトロ半蔵門線': 'Tokyo Metro Hanzomon',
    '東京メトロ南北線': 'Tokyo Metro Nanboku Line',
    '東京メトロ日比谷線': 'Tokyo Metro Hibiya Line',
    '東京メトロ有楽町線': 'Tokyo Metro Yurakucho Line',
    '東京メトロ東西線': 'Tokyo Metro Tozai Line',
    '東京メトロ銀座線': 'Tokyo Metro Ginza Line',
    '東京モノレール線': 'Tokyo Monorail',
    '東急世田谷線': 'Tokyu Setagaya Line',
    '東急多摩川線': 'Tokyu Tamagawa Line',
    '東急大井町線': 'Tokyu Oimachi Line',
    '東急東横線': 'Tokyu Toyoko Line',
    '東急池上線': 'Tokyu Ikegami Line',
    '東急田園都市線': 'Tokyu Den-en-toshi Line',
    '東急目黒線': 'Tokyu Meguro Line',
    '東武亀戸線': 'Tobu Kameido Line',
    '東武伊勢崎線': 'Tobu Isesaki Line',
    '東武佐野線': 'Tobu Sano Line',
    '東武大師線': 'Tobu Daishi Line',
    '東武宇都宮線': 'Tobu Utsunomiya Line',
    '東武小泉線': 'Tobu Koizumi Line',
    '東武日光線': 'Tobu Nikko Line',
    '東武東上線': 'Tobu Tojo Line',
    '東武桐生線': 'Tobu Kiryu Line',
    '東武越生線': 'Tobu Ogose Line',
    '東武野田線': 'Tobu Noda Line',
    '東武鬼怒川線': 'Tobu Kinugawa Line',
    '東海道本線[東京～熱海]': 'Tokaido Line [Tokyo - Atami]',
    '東葉高速線': 'Toyo Rapid Line',
    '東金線': 'Togane Line',
    '横浜線': 'Yokohama Line',
    '横須賀線': 'Yokosuka Line',
    '武蔵野線': 'Musashino Line',
    '水戸線': 'Mito Line',
    '水郡線': 'Suigun Line',
    '江ノ島電鉄線': 'Enoshima Line',
    '流鉄流山線': 'Nagareyama Line',
    '湘南モノレール線': 'Shonan Monorail',
    '湘南新宿ライン': 'Shonan Shinjuku Line',
    '烏山線': 'Karasuyama Line',
    '相模線': 'Sagami Line',
    '相鉄いずみ野線': 'Sotetsu Izumino Line',
    '相鉄本線': 'Sotetsu Main Line',
    '秩父鉄道線': 'Chichibu Railway Line',
    '箱根登山鉄道線': 'Tozan Line',
    '総武本線[千葉～銚子]': 'Sobu Main Line [Chiba-Choshi]',
    '総武線(快速)[東京～千葉]': 'Sobu Line (Rapid) [Tokyo and Chiba]',
    '西武国分寺線': 'Seibu Kokubunji Line',
    '西武多摩川線': 'Seibu Tamagawa Line',
    '西武多摩湖線': 'Seibu Tamako Line',
    '西武山口線': 'Seibu Yamaguchi Line',
    '西武拝島線': 'Seibu Haijima Line',
    '西武新宿線': 'Seibu Shinjuku Line',
    '西武有楽町線': 'Seibu Yurakucho Line',
    '西武池袋線': 'Seibu Ikebukuro Line',
    '西武狭山線': 'Seibu Sayama Line',
    '西武秩父線': 'Seibu Chichibu Line',
    '西武西武園線': 'Seibu Main Line',
    '西武豊島線': 'Seibu Toshima Line',
    '都営三田線': 'Toei Mita Line',
    '都営大江戸線': 'Toei Oedo Line',
    '都営新宿線': 'Toei Shinjuku Line',
    '都営浅草線': 'Toei Asakusa Line',
    '都電荒川線': 'Arakawa Streetcar',
    '金沢シーサイドライン': 'Kanazawa Seaside Line',
    '関東鉄道常総線': 'Joso Line',
    '関東鉄道竜ケ崎線': 'Ryugasaki Line',
    '青梅線[立川～青梅]': 'Ome Line [Tachikawa-Ome]',
    '青梅線[青梅～奥多摩]': 'Ome Line [Ome - Okutama]',
    '高崎線': 'Takasaki Line',
    '鶴見線': 'Tsurumi Line',
    '鹿島線': 'Kashima Line'
}


STATUSES = {
    '列車遅延': 'Delays',
    '運転見合わせ': 'Operations temporarily suspended',
    '運転状況': 'Delays and cancellations',
    '平常運転': 'Normal operations',
}

REASONS = {
    '大雪災害の影響で': 'due to heavy snow',
}

SEVERE = [
    '運転見合わせ',
]


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


def _reason(ja):
    for key, value in REASONS.items():
        if ja.startswith(key):
            return value
    return ja


def _transform(triples):
    for triple in triples:
        line_tag, status_tag, info_tag = triple
        line = line_tag.a.text
        line_en = LINES.get(line, line)
        status = (
            status_tag.span.text if status_tag.span else status_tag.text
        ).strip()
        status_en = STATUSES.get(status, status)
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
            'reason': _reason(info_tag.text.strip()),
            'severe': status in SEVERE,
        }


class HttpServer(ServerHttpProtocol):
    def __init__(self, app, *args, **kwargs):
        self.app = app
        super().__init__(*args, **kwargs)

    @asyncio.coroutine
    def handle_request(self, message, payload):
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

