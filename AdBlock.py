from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
import re
from PyQt6.QtCore import QUrl


BLOCKED_HOSTS = [
    "doubleclick.net", "googlesyndication.com", "adservice.google.com",
    "googleadservices.com", "pagead2.googlesyndication.com",
    "ads.youtube.com", "adserver", "adsystem",
    "taboola", "outbrain", "scorecardresearch", "adsafeprotected.com",
    "criteo", "pubmatic", "rubiconproject", "adnxs.com"
]

BLOCKED_PATH_KEYWORDS = [
    "/doubleclick", "/banner", "pagead", "/api/stats/ads", "/get_video_info", "/youtubei/v1/log_event",
    "ptracking", "/generate_204", "/api/stats/qoe", "/adserver/", "/adsystem/", "?ad_", "&ad_"
]

YOUTUBE_AD_PATTERNS = [
    "youtube.com/api/stats/ads",
    "youtube.com/pagead",
    "youtube.com/ptracking",
    "youtube.com/get_midroll_",
    "ytimg.com/generate_204",
    "youtube.com/youtubei/v1/log_event"
]

ALWAYS_ALLOW_HOSTS = [
    "fonts.googleapis.com", "fonts.gstatic.com", "gstatic.com", "ytimg.com",
    "www.gstatic.com", "googleapis.com"
]


class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, whitelist=None):
        super().__init__()
        self.whitelist = whitelist or []

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        url_q = info.requestUrl()
        url = url_q.toString()
        host = info.requestUrl().host()
        full = url.lower()
        print(host)

        try:
            rtype = info.resourceType()
        except Exception:
            rtype = None

        for w in (self.whitelist or []) + ALWAYS_ALLOW_HOSTS:
            if host.endswith(w):
                return  # allow

        if rtype is not None:
            if int(rtype) in (0, 1):
                return

        if host.endswith("youtube.com") or host.endswith("www.youtube.com") or host.endswith("youtu.be") or host.endswith("ytimg.com"):
            for pattern in YOUTUBE_AD_PATTERNS:
                if pattern in full:
                    if rtype is None or int(rtype) not in (0, 1, 5):
                        info.block(True)
                        return
            return

        if self.host_in_list(host, BLOCKED_HOSTS):
            if rtype is None or int(rtype) not in (0, 1):
                info.block(True)
            return

        for kw in BLOCKED_PATH_KEYWORDS:
            if kw in full:
                if rtype is None or int(rtype) not in (0, 1):
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