from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QLineEdit, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, \
    QShortcut, QDockWidget
from PyQt5.QtWebEngineWidgets import QWebEngineProfile, QWebEngineView, QWebEnginePage
from PyQt5.QtCore import QUrl, Qt

from LazyBrowserTab import LazyBrowserTab
from session import save_full_session
from BrowserTab import BrowserTab
from TabBar import TabBar

SRTART_TAB = "https://www.google.com"

class BrowserWindow(QMainWindow):
    instances = []

    def __init__(self, profile: QWebEngineProfile, tabs_urls=None):
        super().__init__()
        self.profile = profile
        self.profile.setHttpCacheType(QWebEngineProfile.DiskHttpCache)
        self.profile.setCachePath("cache")
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
        self.tabs_urls = tabs_urls or []
        self.setWindowTitle("Wojtek746 Browser")
        self.resize(1400, 700)

        # ---------------- CustomTabBar ----------------
        self.custom_tab_bar = TabBar()
        self.custom_tab_bar.addTabRequested.connect(lambda: self.add_tab(SRTART_TAB))
        self.custom_tab_bar.closeTabRequested.connect(self.close_tab)
        self.custom_tab_bar.copyTabRequested.connect(lambda idx: self.copy_tab(idx))
        self.custom_tab_bar.currentChanged.connect(lambda idx: self.tabs.setCurrentIndex(idx))
        self.custom_tab_bar.tabMoved.connect(self._on_tab_moved)


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
            self.tabs.blockSignals(True)
            self.custom_tab_bar.blockSignals(True)

            self.add_tab("about:blank", suspended=False)
            for u in self.tabs_urls:
                self.add_tab(u, True)

            self.tabs.blockSignals(False)
            self.custom_tab_bar.blockSignals(False)

            self.tabs.setCurrentIndex(0)
            self.custom_tab_bar.setCurrentIndex(0)
        else:
            self.add_tab(SRTART_TAB)

        # ---------------- Skróty klawiszowe ----------------

        shortcut_new = QShortcut(QKeySequence("Ctrl+N"), self)
        shortcut_new.activated.connect(lambda: self.add_tab(SRTART_TAB))

        shortcut_devtools = QShortcut(QKeySequence("F12"), self)
        shortcut_devtools.activated.connect(self.open_devtools)

        shortcut_devtools2 = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
        shortcut_devtools2.activated.connect(self.open_devtools)

        refresh_tab = QShortcut(QKeySequence("F5"), self)
        refresh_tab.activated.connect(self.refresh_tab)

        BrowserWindow.instances.append(self)

    def add_tab(self, url="about:blank", suspended=False, *args, **kwargs):
        if isinstance(url, bool):
            url = "about:blank"
        if not isinstance(url, str):
            url = "about:blank"

        if suspended:
            tab = LazyBrowserTab(self.profile, url, loaded=False)
            title = getattr(tab, "cached_title", "Nowa Karta")
            icon = getattr(tab, "cached_icon", None)
        else:
            tab = BrowserTab(self.profile, url)
            title = "Nowa Karta"
            icon = None

        i = self.tabs.addTab(tab, "")
        self.tabs.setCurrentIndex(i)

        idx = self.custom_tab_bar.addTab(title)
        self.custom_tab_bar.setCurrentIndex(idx)
        if icon:
            self.custom_tab_bar.setTabIcon(idx, icon)

        if not suspended:
            tab.view.titleChanged.connect(lambda new_title, t=tab: self._set_tab_text_safe(t))
            tab.view.iconChanged.connect(lambda icon, t=tab: self._set_tab_icon_safe(t, icon))
            tab.view.urlChanged.connect(
                lambda qurl, t=tab: (self.addr.setText(qurl.toString()) if self.tabs.currentWidget() is t else None))

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

    def copy_tab(self, index):
        cur = self.tabs.widget(index)
        if cur and hasattr(cur, "view"):
            url = cur.view.url().toString()
            self.add_tab(url)
            c = self.tabs.count()
            self.move_tab(c - 1, index)

    def move_tab(self, from_index, to_index):
        if from_index == to_index:
            return

        widget = self.tabs.widget(from_index)
        icon = self.custom_tab_bar.tabIcon(from_index)
        text = self.custom_tab_bar.tabText(from_index)

        self.tabs.removeTab(from_index)
        self.tabs.insertTab(to_index, widget, "")
        self.custom_tab_bar.removeTab(from_index)
        self.custom_tab_bar.insertTab(to_index, icon, text)
        self.custom_tab_bar.setCurrentIndex(to_index)
        self.tabs.setCurrentIndex(to_index)

    def _on_tab_moved(self, from_index, to_index):
        if from_index == to_index:
            return

        widget = self.tabs.widget(from_index)

        self.tabs.removeTab(from_index)
        self.tabs.insertTab(to_index, widget, "")
        self.tabs.setCurrentIndex(to_index)

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

        if type(cur).__name__ == "LazyBrowserTab" and not cur.loaded and hasattr(cur, "url"):
            try:
                lazy = cur
                lazy.loaded = True
                cur_idx = index
                real_tab = BrowserTab(self.profile, lazy.url)
                self.tabs.insertTab(cur_idx, real_tab, "Ładuję...")
                self.tabs.setCurrentIndex(cur_idx)
                self.tabs.removeTab(cur_idx + 1)

                real_tab.view.titleChanged.connect(lambda new_title, rt=real_tab: self._set_tab_text_safe(rt))
                real_tab.view.iconChanged.connect(lambda icon, rt=real_tab: self._set_tab_icon_safe(rt, icon))
                real_tab.view.urlChanged.connect(lambda qurl, rt=real_tab: (self.addr.setText(qurl.toString()) if self.tabs.currentWidget() is rt else None))
            except Exception:
                pass
        self._update_devtools_target(index)


    def _update_devtools_target(self, index):
        if not hasattr(self, "_devtools_dock") or not self._devtools_dock:
            return
        if not hasattr(self, "_devtools_page"):
            return

        cur = self.tabs.widget(index)
        if cur and hasattr(cur, "view"):
            self._devtools_page.setInspectedPage(cur.view.page())

    def open_devtools(self):
        view = self.current_view()
        if not view:
            return

        if hasattr(self, "_devtools_dock") and self._devtools_dock:
            self._devtools_dock.hide()
            self._devtools_dock = None
            return

        dev_view = QWebEngineView(self)
        dev_page = QWebEnginePage(self.profile, self)
        dev_view.setPage(dev_page)
        dev_page.setInspectedPage(view.page())

        dock = QDockWidget("DevTools", self)
        dock.setWidget(dev_view)
        dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setFloating(False)

        self._devtools_dock = dock
        self._devtools_page = dev_page
        self.resizeDocks([dock], [int(2/5*self.width())], Qt.Horizontal)

    def open_new_window(self):
        w = BrowserWindow(self.profile, tabs_urls=["https://www.google.com"])
        w.show()

    def closeEvent(self, event):
        save_full_session()
        for w in BrowserWindow.instances[:]:
            w.close()
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

    def _set_tab_text_safe(self, tab_obj, text=None):
        try:
            idx = self.tabs.indexOf(tab_obj)
            if idx == -1:
                return
            if text is None:
                # spróbuj pobrać tytuł z view, potem host z url
                if hasattr(tab_obj, "view") and tab_obj.view:
                    t = tab_obj.view.title()
                    text = t if t else QUrl(tab_obj.view.url().toString()).host()
                else:
                    text = QUrl(getattr(tab_obj, "url", "") or "").host()
            # jeśli masz custom_tab_bar, aktualizuj jego etykietę, inaczej QTabWidget
            if hasattr(self, "custom_tab_bar"):
                if idx < self.custom_tab_bar.count():
                    self.custom_tab_bar.setTabText(idx, text)
            else:
                self.tabs.setTabText(idx, text)
        except Exception:
            pass

    def _set_tab_icon_safe(self, tab_obj, icon):
        try:
            idx = self.tabs.indexOf(tab_obj)
            if idx == -1:
                return
            if icon is None:
                return
            if hasattr(self, "custom_tab_bar"):
                if idx < self.custom_tab_bar.count():
                    self.custom_tab_bar.setTabIcon(idx, icon)
            else:
                self.tabs.setTabIcon(idx, icon)
        except Exception:
            pass