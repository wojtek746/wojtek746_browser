from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QMenu, QFileDialog, QApplication
import requests

class CustomContextMenu:
    def _context_menu(self, tab, pos):
        x = int(pos.x())
        y = int(pos.y())
        js = f"""
        (function(){{
          try {{
            var el = document.elementFromPoint({x},{y});
            if (!el) return {{link:'', img:''}};
            var a = el.closest ? el.closest('a') : (function(){{
                var p=el; while(p && p.tagName!=='A') p=p.parentElement; return p;
            }})();
            var link = (a && a.href) ? a.href : '';
            var img = '';
            if (el.tagName === 'IMG') img = el.src || '';
            else {{
              var inside = el.querySelector && el.querySelector('img');
              if (inside) img = inside.src || '';
            }}
            return {{link: link, img: img}};
          }} catch(e) {{ return {{link:'', img:''}}; }}
        }})();
        """

        def cb(res):
            link = ""
            img = ""
            try:
                if isinstance(res, dict):
                    link = res.get("link", "") or ""
                    img = res.get("img", "") or ""
            except Exception:
                pass

            menu = QMenu(tab)
            if img:
                menu.addAction("Open image in new tab", lambda: self._open_tab(img, tab))
                menu.addAction("Save image as...", lambda: self._save_image(img, tab))
            if link:
                menu.addAction("Open link in new tab", lambda: self._open_tab(link, tab))
                menu.addAction("Copy link address", lambda: QApplication.clipboard().setText(link))
            menu.exec(tab.view.mapToGlobal(pos))

        tab.view.page().runJavaScript(js, cb)

    def _open_tab(self, url, tab):
        win = tab.window()
        if hasattr(win, "add_tab"):
            prev_index = win.tabs.currentIndex()
            win.add_tab(url, True)
            c = win.tabs.count()
            win.move_tab(c - 1, win.tabs.indexOf(tab) + 1)
            if win.tabs.currentIndex() != prev_index:
                win.tabs.setCurrentIndex(prev_index)
                win.custom_tab_bar.setCurrentIndex(prev_index)

    def _save_image(self, url, tab):
        QFileDialog.getSaveFileName()
        path, _ = QFileDialog.getSaveFileName(tab, "Save image as", "", "Images (*.png *.jpg *.jpeg *.webp *.gif)")
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            with open(path, "wb") as f:
                f.write(r.content)