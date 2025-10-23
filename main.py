import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineProfile

from AdBlock import AdBlockInterceptor
from session import load_session
from BrowserWindow import BrowserWindow

import os
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-logging"

WHITELIST = [
    "vider.info", "aternos.org", "vider.pl"
]

def main():
    app = QApplication(sys.argv)

    profile = QWebEngineProfile.defaultProfile()

    interceptor = AdBlockInterceptor(whitelist=WHITELIST)
    try:
        profile.setUrlRequestInterceptor(interceptor)
    except AttributeError:
        try:
            profile.setRequestInterceptor(interceptor)
        except Exception:
            pass

    cache_path = os.path.join(os.getcwd(), "browser_cache")
    profile.setCachePath(cache_path)
    profile.setPersistentStoragePath(cache_path)
    profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
    profile.setHttpCacheType(QWebEngineProfile.DiskHttpCache)

    sess = load_session()
    if sess:
        for win_tabs in sess:
            w = BrowserWindow(profile, tabs_urls=win_tabs)
            w.show()
    else:
        w = BrowserWindow(profile)
        w.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()