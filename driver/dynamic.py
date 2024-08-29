import undetected_chromedriver as uc_webdriver
import os
import zipfile
import requests


class UndetectedDriver:
    def __init__(self, account: dict):
        self.account = account
        self.__options = uc_webdriver.ChromeOptions()
        self._set_chromeoptions()
        self.__driver = self._create_driver()

    def get_driver(self):
        return self.__driver
    
    def set_timezone(self) -> str:
        ip = self.account['proxy_host']
        url = f"http://ipapi.co/{ip}/timezone/"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.text.strip()
            else:
                print(f'[set_timezone] status_code={response.status_code}')
        except Exception as ex:
            print(f'[set_timezone] {ex}')
        return None


    def _set_chromeoptions(self):
        extensions = []
        proxy_extension_path = self.load_proxy()
        extensions.append(proxy_extension_path)
       
        self.__options.add_argument(f"--load-extension={','.join(extensions)}")

        self.__options.add_argument('--ignore-ssl-errors=yes')
        self.__options.add_argument('--ignore-certificate-errors')
        self.__options.add_argument('--start-maximized')
        self.__options.add_argument('--no-sandbox')
        self.__options.add_argument('--disable-dev-shm-usage')
        self.__options.add_argument('--disable-setuid-sandbox')
        self.__options.add_argument('--disable-gpu')
        self.__options.add_argument('--disable-software-rasterizer')
        if self.proxy:
            self.__options.add_argument("--disable-features=WebRtcHideLocalIpsWithMdns")
            self.__options.add_experimental_option('prefs', {
                'enable_do_not_track': True
            })
            preferences = {
                "webrtc.ip_handling_policy": "disable_non_proxied_udp",
                "webrtc.multiple_routes_enabled": False,
                "webrtc.nonproxied_udp_enabled": False
            }
            self.__options.add_experimental_option("prefs", preferences)

    def _create_driver(self):       
        driver = uc_webdriver.Chrome(options=self.__options)

        timezone = self.set_timezone()
        if timezone:
            tz_params = {'timezoneId': timezone}
            driver.execute_cdp_cmd('Emulation.setTimezoneOverride', tz_params)

        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            'source': '''
                            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
                            delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
                            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy;
                    '''
        })
        print('return driver')
        return driver       

    def load_proxy(self):
        PROXY_USER = self.account['proxy_username']
        PROXY_PASS = self.account['proxy_password']
        PROXY_HOST = self.account['proxy_host']
        PROXY_PORT = self.account['proxy_port']

        self.proxy = f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'

        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """

        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                },
                bypassList: ["localhost"]
                }
            };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
    callbackFn,
        {urls: ["<all_urls>"]},
        ['blocking']
        );
        """ % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)

        pluginfile = 'proxy_auth_plugin_' + str(PROXY_HOST)
        base_path = 'driver/proxies/'
        os.makedirs(base_path, exist_ok=True)
        with zipfile.ZipFile(base_path + pluginfile + ".zip", 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        os.makedirs(base_path + pluginfile, exist_ok=True)
        with zipfile.ZipFile(base_path + pluginfile + ".zip") as zp:
            zp.extractall(base_path + pluginfile)
        return os.getenv('PRODUCTION_DIR') + base_path + pluginfile
