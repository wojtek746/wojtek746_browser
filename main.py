import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineScript

from AdBlock import AdBlockInterceptor
from session import load_session
from BrowserWindow import BrowserWindow

import os

sys.argv += [
    "--force-dark-mode",
    "--enable-features=WebContentsForceDark",
    "--disable-features=WebAuthnAPI",
    "--disable-features=WebAuthentication",
    "--disable-component-update",
    "--disable-background-networking"
]
sys.argv += ["--remote-debugging-port=9222"]

WHITELIST = [
    "vider.info", "aternos.org", "vider.pl", "openai.com"
]

flags = [
    "--disable-blink-features=AutomationControlled",
    "--exclude-switches=enable-automation",
    "--disable-dev-shm-usage",
    "--disable-features=WebAuth,WebAuthentication,WebAuthenticationCable,WebAuthenticationCableSecondFactor,WebAuthenticationConditionalUI,WebAuthnAPI,WebAuth,WebCredentials",
    "--disable-webauthn-api"
]
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = " ".join(flags)

def main():
    app = QApplication(sys.argv)

    profile = QWebEngineProfile("Wojtek746 Browser Profile", app)

    cache_path = os.path.join(os.getcwd(), "browser_cache")
    profile.setCachePath(cache_path)
    profile.setPersistentStoragePath(cache_path)
    profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
    profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)

    # interceptor = AdBlockInterceptor(whitelist=WHITELIST)
    # try:
    #     profile.setUrlRequestInterceptor(interceptor)
    # except AttributeError:
    #     try:
    #         profile.setRequestInterceptor(interceptor)
    #     except Exception:
    #         pass

    settings = profile.settings()

    anti_detection_script = QWebEngineScript()
    anti_detection_script.setSourceCode("""
        (function() {
            if (navigator.credentials) {
                Object.defineProperty(navigator, 'credentials', {
                    value: undefined,
                    writable: false,
                    configurable: false
                });
            }
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            Object.defineProperty(navigator, 'vendor', {
                get: () => 'Google Inc.'
            });
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32'
            });
            delete window.navigator.__proto__.webdriver;
        })();
    """)
    anti_detection_script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
    anti_detection_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
    anti_detection_script.setRunsOnSubFrames(True)
    profile.scripts().insert(anti_detection_script)

    sess = load_session()
    if sess:
        for win_tabs in sess:
            w = BrowserWindow(profile, tabs_urls=win_tabs)
            w.show()
    else:
        w = BrowserWindow(profile)
        w.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()