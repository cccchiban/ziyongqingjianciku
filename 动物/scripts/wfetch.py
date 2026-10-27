import urllib.error
import urllib.parse
import urllib.request
import time

UA = {'User-Agent': 'AnimalNameTableBot/1.0 (local dictionary build; contact: local)'}
BASE = 'https://zh.wikipedia.org/zh-hans/'
BACKOFF = [0, 5, 20, 60]


def sec0(title):
    """返回条目首段 wikitext；404 -> 'MISSING'；限流时退避重试；仍失败返回 'ERROR'"""
    u = BASE + urllib.parse.quote(title) + '?action=raw&section=0'
    for delay in BACKOFF:
        if delay:
            time.sleep(delay)
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=45)
            return r.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 'MISSING'
            if e.code != 429 and e.code < 500:
                return 'ERROR'
        except Exception:
            pass
    return 'ERROR'
