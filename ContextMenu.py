from PyQt5.QtWidgets import QMenu

class CustomContextMenu:
    def _context_menu(self, tab, pos):
        data = tab.view.page().contextMenuData()
        menu = QMenu(tab)

        #dodać więcej opcji (kopiuj link, zapisz jako)
        if data.mediaType() == data.MediaTypeImage and data.mediaUrl().isValid():
            open_img_tab = menu.addAction("Open image in new tab")
            open_img_tab.triggered.connect(lambda: self._open_tab(data.mediaUrl(), tab))
        elif data.linkUrl().isValid():
            open_link_tab = menu.addAction("Open link in new tab")
            open_link_tab.triggered.connect(lambda: self._open_tab(data.linkUrl(), tab))

        menu.exec_(tab.view.mapToGlobal(pos))

    def _open_tab(self, url, tab):
        win = tab.window()
        if hasattr(win, "add_tab"):
            win.add_tab(url.toString())
            c = win.tabs.count()
            win.move_tab(c - 1, win.tabs.indexOf(tab) + 1)