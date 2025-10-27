import json
import os

from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QWidget
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtCore import QUrl


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

        title = "Nowa Karta"
        path = os.path.join(os.getcwd(), "session_titles.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                title = data.get(self.url, "Nowa Karta")
            except Exception:
                pass

        icon = None
        host = QUrl(self.url).host().replace(":", "_")
        icon_path = os.path.join(os.getcwd(), "session_icons", f"{host}.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                icon = QIcon(pixmap)

        self.view = LazyBrowserTab.DummyView(self.url)
        self.loaded = loaded
        self.cached_title = title
        self.cached_icon = icon

    def setUrl(self, url):
        self.url = url
        if self.view:
            self.view._url = QUrl(url)