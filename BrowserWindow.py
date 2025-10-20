from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QLineEdit, QToolBar, QAction,
        QPushButton, QWidget, QVBoxLayout, QTabBar)
from PyQt5.QtWebEngineWidgets import QWebEngineProfile
from PyQt5.QtCore import QUrl, Qt

from session import save_full_session
from BrowserTab import BrowserTab

class BrowserWindow(QMainWindow):
    instances = []

    def __init__(self, profile: QWebEngineProfile, tabs_urls=None):
        super().__init__()
        self.profile = profile
        self.tabs_urls = tabs_urls or []
        self.setWindowTitle("LightBrowser")
        self.resize(1000, 700)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setTabBar(CustomTabBar())
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_address_bar)
        self.setCentralWidget(self.tabs)

        # + button
        plus_btn = QPushButton("+")
        plus_btn.setFixedSize(20, 20)
        plus_btn.clicked.connect(lambda: self.add_tab("about:blank"))
        self.tabs.setCornerWidget(plus_btn, Qt.TopRightCorner)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        container_layout.addWidget(self.tabs)

        self.addr = QLineEdit()
        self.addr.returnPressed.connect(self.load_from_bar)
        container_layout.addWidget(self.addr)
        self.setCentralWidget(container)

        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)
        back_act = QAction("◀", self);
        back_act.triggered.connect(self.go_back)
        forward_act = QAction("▶", self);
        forward_act.triggered.connect(self.go_forward)
        refresh_act = QAction("⟳", self);
        refresh_act.triggered.connect(self.refresh_tab)
        self.toolbar.addAction(back_act)
        self.toolbar.addAction(forward_act)
        self.toolbar.addAction(refresh_act)

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
            save_full_session(BrowserWindow.instances)
        event.accept()

    def current_view(self):
        cur = self.tabs.currentWidget()
        return cur.view if cur else None

    def go_back(self):
        v = self.current_view()
        if v and v.history().canGoBack():
            v.back()

    def go_forward(self):
        v = self.current_view()
        if v and v.history().canGoForward():
            v.forward()

    def refresh_tab(self):
        v = self.current_view()
        if v:
            v.reload()

class CustomTabBar(QTabBar):
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            idx = self.tabAt(event.pos())
            if idx != -1:
                self.parent().tabCloseRequested.emit(idx)
                return
        super().mouseReleaseEvent(event)