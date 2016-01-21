import logging
from re import compile as c

from lines import LINES

STATUSES = {
    '列車遅延': 'Delays',
    '運転見合わせ': 'Operations temporarily suspended',
    '運転状況': 'Delays and cancellations',
    '平常運転': 'Normal operations',
    '運転再開': 'Preparing to resume operations',
}

l = lambda s: lambda name, **kw: s.format(name=line(name.strip()), **kw)

REASONS = {
    c(r'^大雪災害の影響で'): 'due to heavy snow',
    c(r'台風(?P<number>\d+)号の影響で、'): 'due to typhoon #{number}',
    c(r'大雨の影響で、'): 'due to heavy rain',
    c(r'(?P<from>\w+)～(?P<to>\w+)駅間で踏切内点検を'): (
        'due to inspection between {from} and {to}'
    ),
    c(r'(?P<name>\w+線)内で踏切内点検を'): (
        l('due to inspection on the {name} line')
    ),
    c(r'\d{1,2}:\d{2}頃、(?P<station>\w+)駅で発生し'): (
        'due to problems near {station} station'
    ),
    c(r'\d{1,2}:\d{2}頃、(?P<from>\w+)～(?P<to>\w+)駅…$'): (
        'between {from} and {to} station'
    ),
    c(r'強風の影響で、'): 'due to strong winds',
    c(r'雪の影響で、',): 'due to snow',
    c(r'(?P<name>\w+線)内での雪の影響で'): l('due to snow on the {name} line'),
    c(r'(?P<name>\w+線)内で発生した人身事故'): l(
        'due to accident on the {name} line'
    ),
    c(r'(?P<station>\w+)駅で発生した人身事故'): (
        'due to accident at {station} station'
    ),
    c(r'倒木の影響で'): 'due to a tree falling on the tracks',
    c(r'(?P<station>\w+)駅で発生した倒木'): (
        'due to a tree falling on the tracks near {station} station'
    ),
    c(r'(?P<name>\w+線)内で発生した倒木'): (
        'due to a tree falling on the tracks of {name} line'
    ),
    c(r'(?P<station>\w+)駅で信号関係点検'): (
        'due to signal troubles at {station} station'
    ),
    c(r'(?P<name>\w+線)内で発生した架線支障'): (
        'due to overhead wire troubles on the {name} line'
    ),
    c(r'(?P<station>\w+)駅で発生した架線支障'): (
        'due to overhead wire troubles at {station} station'
    ),
    c(r'除雪作業の影響で'): 'due to snow removal',
    c(r'車両故障の影響で'): 'due to vehicle malfunction',
}

SEVERE = {
    '運転見合わせ',
}


def reason(ja):
    for key, value in REASONS.items():
        match = key.match(ja)
        if match:
            if callable(value):
                return value(**match.groupdict())
            else:
                return value.format(**match.groupdict())
    logging.info('No translation for %s' % ja)
    return ja


def is_severe(ja):
    return ja in SEVERE


def status(ja):
    return STATUSES.get(ja, ja)


def line(ja):
    try:
        return LINES[ja]
    except KeyError:
        logging.info('Line not found %s' % ja)
        return ja
