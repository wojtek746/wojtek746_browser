from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo

BLOCKED_HOSTS = [
    "doubleclick.net", "googlesyndication.com", "adservice.google.com",
    "googleadservices.com", "pagead2.googlesyndication.com",
    "ads.youtube.com", "ytimg.com/ytad", "adserver", "adsystem",
    "taboola", "outbrain", "scorecardresearch", "adsafeprotected.com",
    "criteo", "pubmatic", "rubiconproject", "adnxs.com"
]

BLOCKED_PATH_KEYWORDS = [
    "/ads", "/adserver", "/ad?", "/doubleclick", "doubleclick.net",
    "/banner", "pagead", "/videoad", "/ad(s|vert)"
]


class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, whitelist=None):
        super().__init__()
        self.whitelist = whitelist or []

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        url = info.requestUrl().toString()
        host = info.requestUrl().host()
        path = info.requestUrl().path() or ""
        full = url.lower()

        for w in self.whitelist:
            if host.endswith(w):
                return  # allow

        if self.host_in_list(host, BLOCKED_HOSTS):
            info.block(True)
            return

        for kw in BLOCKED_PATH_KEYWORDS:
            if kw in full:
                info.block(True)
                return

        q = info.requestUrl().query()
        if "ad=" in q or "?ad" in full or "&ad" in full:
            info.block(True)
            return

    def host_in_list(self, host, patterns):
        if not host:
            return False
        host = host.lower()
        for p in patterns:
            if host.endswith(p):
                return True
        return False