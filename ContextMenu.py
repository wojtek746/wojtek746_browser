from PyQt6.QtWidgets import QMenu, QFileDialog
import requests

class CustomContextMenu:
    def _context_menu(self, tab, pos):
        data = tab.view.page().contextMenuData()
        menu = QMenu(tab)

        #dodać więcej opcji (kopiuj link)
        if data.mediaType() == data.MediaTypeImage and data.mediaUrl().isValid():
            open_img_tab = menu.addAction("Open image in new tab")
            open_img_tab.triggered.connect(lambda: self._open_tab(data.mediaUrl(), tab))
            save_img_as = menu.addAction("Save image as...")
            save_img_as.triggered.connect(lambda: self._save_image(data.mediaUrl(), tab))
        if data.linkUrl().isValid():
            open_link_tab = menu.addAction("Open link in new tab")
            open_link_tab.triggered.connect(lambda: self._open_tab(data.linkUrl(), tab))

        menu.exec_(tab.view.mapToGlobal(pos))

    def _open_tab(self, url, tab):
        win = tab.window()
        if hasattr(win, "add_tab"):
            prev_index = win.tabs.currentIndex()
            win.add_tab(url.toString(), True)
            c = win.tabs.count()
            win.move_tab(c - 1, win.tabs.indexOf(tab) + 1)
            if win.tabs.currentIndex() != prev_index:
                win.tabs.setCurrentIndex(prev_index)
                win.custom_tab_bar.setCurrentIndex(prev_index)

    def _save_image(self, url, tab):
        QFileDialog.getSaveFileName()
        path, _ = QFileDialog.getSaveFileName(tab, "Save image as", "", "Images (*.png *.jpg *.jpeg *.webp *.gif)")
        r = requests.get(url.toString(), timeout=10)
        if r.status_code == 200:
            with open(path, "wb") as f:
                f.write(r.content)