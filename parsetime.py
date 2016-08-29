from datetime import timedelta, datetime

def getmaand(x):
    now = datetime.now()
    return now.replace(month=now.month+x)

def getjaar(x):
    now = datetime.now()
    return now.replace(year=now.year+x)

tokens = {
    'jaar': getjaar,
    'jaren': getjaar,
    'maand': getmaand,
    'maanden': getmaand,
    'week': lambda x: timedelta(weeks=1) * x,
    'weken': lambda x: timedelta(weeks=1) * x,
    'dag': lambda x: timedelta(days=1) * x,
    'morgen': lambda: timedelta(days=1),
    'gisteren': lambda: timedelta(days=-1),
    'dagen': lambda x: timedelta(days=1) * x,
    'uur': lambda x: timedelta(hours=1) * x,
    'uren': lambda x: timedelta(hours=1) * x,
    'minuut': lambda x: timedelta(minutes=1) * x,
    'minuten': lambda x: timedelta(minutes=1) * x,
    'seconde': lambda x: timedelta(seconds=1) * x,
    'seconden': lambda x: timedelta(seconds=1) * x,
}

def parsetime(n: int, token: str) -> datetime:
    if token not in tokens:
        raise RuntimeError()

    ding = tokens[token](int(n))
    if type(ding) == datetime:
        return ding
    elif type(ding) == timedelta:
        return datetime.now() + ding
    else:
        raise RuntimeError()

def parsegetal(token: str) -> int:
    pass