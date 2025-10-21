from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtCore import QUrl

class BrowserTab(QWidget):
    def __init__(self, profile: QWebEngineProfile, url="about:blank"):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.view = QWebEngineView()
        page = QWebEnginePage(profile, self.view)
        self.view.setPage(page)
        self.view.setUrl(QUrl(url))
        self.layout.addWidget(self.view)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.view.iconChanged.connect(self._on_icon_changed)
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

    def _on_icon_changed(self, icon):
        parent_tabs = self.parent().parent()
        if parent_tabs:
            idx = parent_tabs.indexOf(self)
            if idx != -1:
                parent_tabs.setTabIcon(idx, icon)