import json
import os

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtCore import QUrl, Qt

from ContextMenu import CustomContextMenu


class BrowserTab(QWidget):
    def __init__(self, profile: QWebEngineProfile, url="about:blank"):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.view = QWebEngineView()
        page = QWebEnginePage(profile, self.view)
        self.view.setPage(page)
        self.view.setUrl(QUrl(url))
        self.layout.addWidget(self.view)
        self.layout.setContentsMargins(0, 3, 0, 0)
        self.setLayout(self.layout)

        self.view.iconChanged.connect(self._on_icon_changed)
        self.view.loadFinished.connect(self.on_load_finished)

        self.menu = CustomContextMenu()
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self._context_menu)

    def _context_menu(self, pos):
        self.menu._context_menu(self, pos)

    def on_load_finished(self, ok):
        if not ok:
            return
        url = self.view.url().toString()
        title = self.view.title()
        path = os.path.join(os.getcwd(), "session_titles.json")
        try:
            data = {}
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data[url] = title
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

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

    def _on_icon_changed(self, icon):
        parent_tabs = self.parent().parent()
        if parent_tabs:
            idx = parent_tabs.indexOf(self)
            if idx != -1:
                parent_tabs.setTabIcon(idx, icon)
        try:
            path = os.path.join(os.getcwd(), "session_icons")
            os.makedirs(path, exist_ok=True)
            url = self.view.url().toString()
            host = QUrl(url).host().replace(":", "_")
            if not host:
                return
            icon_path = os.path.join(path, f"{host}.png")
            pixmap = icon.pixmap(32, 32)
            if not pixmap.isNull():
                pixmap.save(icon_path, "PNG")
        except Exception:
            pass