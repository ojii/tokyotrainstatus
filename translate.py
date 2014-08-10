from re import compile as c

from lines import LINES

STATUSES = {
    '列車遅延': 'Delays',
    '運転見合わせ': 'Operations temporarily suspended',
    '運転状況': 'Delays and cancellations',
    '平常運転': 'Normal operations',
    '運転再開': 'Preparing to resume operations',
}

REASONS = {
    c(r'^大雪災害の影響で'): 'due to heavy snow',
    c(r'台風(?P<number>\d+)号の影響で、'): 'due to typhoon #{number}',
    c(r'大雨の影響で、'): 'due to heavy rain',
    c(r'(?P<from>\w+)～(?P<to>\w+)駅間で踏切内点検を'): 'due to inspection '
                                              'between {from} and {to}',
    c(r'(?P<line>\w+)線内で踏切内点検を'): 'due to inspection on the {line} '
                                  'line',
    c(r'\d{1,2}:\d{2}頃、(?P<station>\w+)駅で発生し'): 'due to problems near '
                                              '{station} station',
    c(r'\d{1,2}:\d{2}頃、(?P<from>\w+)～(?P<to>\w+)駅…$'): 'between {from} '
                                              'and {to} station',
    c(r'強風の影響で、', 'due to strong winds'),
}

SEVERE = {
    '運転見合わせ',
}


def reason(ja):
    for key, value in REASONS.items():
        match = key.match(ja)
        if match:
            return value.format(**match.groupdict())
    return ja


def is_severe(ja):
    return ja in SEVERE


def status(ja):
    return STATUSES.get(ja, ja)


def line(ja):
    return LINES.get(ja, ja)
