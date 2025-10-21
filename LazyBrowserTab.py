from PyQt5.QtWidgets import QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile
from PyQt5.QtCore import QUrl, pyqtSignal


class LazyBrowserTab(QWidget):
    class DummyView:
        def __init__(self, url):
            self._url = QUrl(url)
        def url(self):
            return self._url
        def title(self):
            return ""
        def icon(self):
            return None

    def __init__(self, profile: QWebEngineProfile, url="about:blank", loaded: bool = False):
        super().__init__()
        self.profile = profile
        self.url = url or "about:blank"
        self.view = LazyBrowserTab.DummyView(self.url)
        self.loaded = loaded

    def setUrl(self, url):
        self.url = url
        if self.view:
            self.view.url(QUrl(url))