import sys
import json
import os
from urllib.parse import urlparse

from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QLineEdit, QToolBar, QAction, QFileDialog, QMessageBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo

SESSION_FILE = "session.json"

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

WHITELIST = [
    "vider.info", "aternos.org", "vider.pl"
]

def host_in_list(host, patterns):
    if not host:
        return False
    host = host.lower()
    for p in patterns:
        if host.endswith(p):
            return True
    return False


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

        if host_in_list(host, BLOCKED_HOSTS):
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


class BrowserTab(QWidget):
    def __init__(self, profile: QWebEngineProfile, url="about:blank"):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.view = QWebEngineView()
        page = QWebEnginePage(profile, self.view)
        self.view.setPage(page)
        self.view.setUrl(QUrl(url))
        self.layout.addWidget(self.view)
        self.setLayout(self.layout)

        self.view.urlChanged.connect(self.on_url_changed)
        self.view.loadFinished.connect(self.on_load_finished)

    def on_url_changed(self, qurl):
        # can be used to update UI externally
        pass

    def on_load_finished(self, ok):
        if not ok:
            return
        url = self.view.url().toString()
        # If YouTube, inject ad-skip JS
        if "youtube.com/watch" in url:
            js_skip = """
            (function(){
                try {
                    var skip = document.querySelector('.ytp-ad-skip-button, .ytp-ad-skip-button.ytp-button');
                    if(skip) { skip.click(); return; }
                    var v = document.querySelector('video');
                    if(v && v.duration && v.currentTime < v.duration) {
                        v.currentTime = Math.min(v.duration - 0.1, v.currentTime + 5);
                    }
                } catch(e) {}
            })();
            """
            self.view.page().runJavaScript(js_skip)


class BrowserWindow(QMainWindow):
    instances = []

    def __init__(self, profile: QWebEngineProfile, tabs_urls=None):
        super().__init__()
        self.profile = profile
        self.tabs_urls = tabs_urls or []
        self.setWindowTitle("LightBrowser")
        self.resize(1000, 700)

        # Toolbar
        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)

        self.addr = QLineEdit()
        self.addr.returnPressed.connect(self.load_from_bar)
        self.toolbar.addWidget(self.addr)

        new_tab_action = QAction("Nowa karta", self)
        new_tab_action.triggered.connect(self.add_tab)
        self.toolbar.addAction(new_tab_action)

        new_win_action = QAction("Nowe okno", self)
        new_win_action.triggered.connect(self.open_new_window)
        self.toolbar.addAction(new_win_action)

        save_action = QAction("Zapisz sesję", self)
        save_action.triggered.connect(save_full_session)
        self.toolbar.addAction(save_action)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_address_bar)
        self.setCentralWidget(self.tabs)

        if self.tabs_urls:
            for u in self.tabs_urls:
                self.add_tab(u)
        else:
            self.add_tab("https://www.google.com")

        BrowserWindow.instances.append(self)

    def add_tab(self, url="about:blank", *args, **kwargs):
        if isinstance(url, bool):
            url = "about:blank"
        tab = BrowserTab(self.profile, url)
        i = self.tabs.addTab(tab, "Nowa karta")
        self.tabs.setCurrentIndex(i)

        tab.view.titleChanged.connect(lambda title, t=tab: self.set_tab_title(t, title))
        tab.view.urlChanged.connect(lambda qurl, t=tab: self.set_tab_title(t, qurl.toString()))

    def set_tab_title(self, tab, title):
        idx = self.tabs.indexOf(tab)
        if idx != -1:
            self.tabs.setTabText(idx, title if title else "—")

    def close_tab(self, index):
        widget = self.tabs.widget(index)
        if widget:
            widget.deleteLater()
        self.tabs.removeTab(index)

        if self.tabs.count() == 0:
            self.close()

    def load_from_bar(self):
        text = self.addr.text().strip()
        if not text:
            return
        if not text.startswith("http"):
            text = "http://" + text
        cur = self.tabs.currentWidget()
        if cur:
            cur.view.setUrl(QUrl(text))

    def update_address_bar(self, index):
        cur = self.tabs.widget(index)
        if cur:
            self.addr.setText(cur.view.url().toString())

    def open_new_window(self):
        w = BrowserWindow(self.profile, tabs_urls=["https://www.google.com"])
        w.show()

    def closeEvent(self, event):
        # On close, remove from instances and if last, save session
        if self in BrowserWindow.instances:
            BrowserWindow.instances.remove(self)
        if not BrowserWindow.instances:
            save_full_session()
        event.accept()


def gather_session():
    data = []
    for w in BrowserWindow.instances:
        win_tabs = []
        for i in range(w.tabs.count()):
            tab = w.tabs.widget(i)
            url = tab.view.url().toString()
            win_tabs.append(url)
        data.append(win_tabs)
    return data

def save_full_session():
    data = gather_session()
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Session saved to", SESSION_FILE)
    except Exception as e:
        print("Error saving session:", e)

def load_session():
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print("Error loading session:", e)
        return None

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