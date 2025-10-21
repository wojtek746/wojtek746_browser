from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QLineEdit, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QShortcut
from PyQt5.QtWebEngineWidgets import QWebEngineProfile
from PyQt5.QtCore import QUrl

from session import save_full_session
from BrowserTab import BrowserTab
from TabBar import TabBar

SRTART_TAB = "https://www.google.com"

class BrowserWindow(QMainWindow):
    instances = []

    def __init__(self, profile: QWebEngineProfile, tabs_urls=None):
        super().__init__()
        self.profile = profile
        self.tabs_urls = tabs_urls or []
        self.setWindowTitle("Wojtek746 Browser")
        self.resize(1400, 700)

        # ---------------- Tabs (QTabWidget + CustomTabBar) ----------------
        self.custom_tab_bar = TabBar()
        self.custom_tab_bar.addTabRequested.connect(lambda: self.add_tab(SRTART_TAB))
        self.custom_tab_bar.closeTabRequested.connect(self.close_tab)
        self.custom_tab_bar.currentChanged.connect(lambda idx: self.tabs.setCurrentIndex(idx))

        # ---------------- URL/navigation row (back/forward/refresh + adres) ----------------
        urls = QWidget()
        urls_layout = QHBoxLayout(urls)
        urls_layout.setContentsMargins(0, 4, 0, 0)
        urls_layout.setSpacing(0)

        back_btn = QPushButton("◀")
        back_btn.setFixedSize(22, 22)
        back_btn.clicked.connect(self.go_back)
        back_btn.setContentsMargins(0, 0, 0, 0)

        forward_btn = QPushButton("▶")
        forward_btn.setFixedSize(22, 22)
        forward_btn.clicked.connect(self.go_forward)
        forward_btn.setContentsMargins(0, 0, 0, 0)

        refresh_btn = QPushButton("⟳")
        refresh_btn.setFixedSize(22, 22)
        refresh_btn.clicked.connect(self.refresh_tab)
        refresh_btn.setContentsMargins(0, 0, 0, 0)

        self.addr = QLineEdit()
        self.addr.returnPressed.connect(self.load_from_bar)
        self.addr.setContentsMargins(0, 0, 0, 0)

        urls_layout.addWidget(back_btn)
        urls_layout.addWidget(forward_btn)
        urls_layout.addWidget(refresh_btn)
        urls_layout.addWidget(self.addr)


        # ---------------- Container: tabs header, actual tabs, url row ----------------
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().hide()
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_address_bar)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        container_layout.addWidget(self.custom_tab_bar)
        container_layout.addWidget(urls)
        container_layout.addWidget(self.tabs)

        self.setCentralWidget(container)
        self.showMaximized()

        if self.tabs_urls:
            for u in self.tabs_urls:
                self.add_tab(u)
        else:
            self.add_tab(SRTART_TAB)

        shortcut_new = QShortcut(QKeySequence("Ctrl+N"), self)
        shortcut_new.activated.connect(lambda: self.add_tab(SRTART_TAB))

        BrowserWindow.instances.append(self)

    def add_tab(self, url="about:blank", *args, **kwargs):
        if isinstance(url, bool):
            url = "about:blank"
        if not isinstance(url, str):
            url = "about:blank"
        tab = BrowserTab(self.profile, url)
        i = self.tabs.addTab(tab, "")
        self.tabs.setCurrentIndex(i)

        idx = self.custom_tab_bar.addTab("Nowa Karta")
        self.custom_tab_bar.setCurrentIndex(idx)

        def on_title_changed(new_title, t=tab, pos=idx):
            title_text = new_title if new_title else QUrl(t.view.url().toString()).host()
            if pos < self.custom_tab_bar.count():
                self.custom_tab_bar.setTabText(pos, title_text)

        def on_icon_changed(icon, t=tab, pos=idx):
            if icon.isNull():
                return
            if pos < self.custom_tab_bar.count():
                self.custom_tab_bar.setTabIcon(pos, icon)

        def on_url_changed(qurl, t=tab, pos=idx):
            if self.tabs.currentIndex() == pos:
                self.addr.setText(qurl.toString())
            if pos < self.custom_tab_bar.count():
                self.custom_tab_bar.setTabToolTip(pos, qurl.toString())

        tab.view.iconChanged.connect(on_icon_changed)
        tab.view.titleChanged.connect(on_title_changed)
        tab.view.urlChanged.connect(on_url_changed)

        if idx is not None:
            self.custom_tab_bar.setTabToolTip(idx, url)

    def close_tab(self, index):
        widget = self.tabs.widget(index)
        if widget:
            widget.deleteLater()
        self.tabs.removeTab(index)

        if 0 <= index < self.custom_tab_bar.count():
            self.custom_tab_bar.removeTab(index)

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
        if cur and hasattr(cur, "view"):
            self.addr.setText(cur.view.url().toString())
        else:
            self.addr.setText("")

    def open_new_window(self):
        w = BrowserWindow(self.profile, tabs_urls=["https://www.google.com"])
        w.show()

    def closeEvent(self, event):
        save_full_session()
        if self in BrowserWindow.instances:
            BrowserWindow.instances.remove(self)
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