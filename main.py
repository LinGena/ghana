import pyautogui
from facebook.content_from_har import AddLinks
from postgres_db.core import PostgreSQLTable
from dotenv import load_dotenv

load_dotenv(override=True)

class Facebook():
    def __init__(self) -> None:
        pyautogui.PAUSE = 1
        self.page_scroll = [350,350,200]
        self.count_try_reload = 0
        self.errors = 0
        self.count_scroll = len(self.page_scroll)
        

    def run(self):
        self.fill_filter_devtools()
        while True:
            try:
                self.get_url()
                self.press_clear_btn()
                self.errors = self.count_scroll
                for self.i in range(self.count_scroll):
                    self.run_scan() 
            except Exception as ex:
                self.exception_while(ex)
            if self.errors >= self.count_scroll - 1:
                self.count_try_reload = 0
                PostgreSQLTable('ghana_names').update_row('name', self.q, {'status':1})

    def exception_while(self, ex):
        if 'critical' in str(ex):
            btn = self.is_image_on_screen('img/reload.png')
            if not btn:
                raise Exception(ex)
            self._click(btn.x, btn.y)
            self.count_try_reload += 1
            if self.count_try_reload >= 2:
                raise Exception(f'[count_try_reload = 2] {ex}')
        else:
            raise Exception(ex)


    def run_scan(self):
        try:
            pyautogui.sleep(2)
            self.press_clear_btn()
            pyautogui.sleep(5)
            pyautogui.moveTo(x=660, y=485, duration=2)
            for i in range(self.page_scroll[self.i]):
                pyautogui.hscroll(-1000)
            self.get_har_file()
            AddLinks().run()
        except Exception as ex:
            self.errors = self.errors - 1
            print(ex)
            if 'critical' in str(ex):
                raise Exception(ex)
                
    def _click(self, x, y):
        pyautogui.moveTo(x, y, duration=2)
        pyautogui.leftClick()

    def is_image_on_screen(self, img_name) -> bool:
        try:
            return pyautogui.locateCenterOnScreen(img_name)
        except pyautogui.ImageNotFoundException:
            return False  
        
    def is_reconnect_devtools(self) -> bool:
        btn = self.is_image_on_screen('img/reconnect.png')
        if btn:
            self._click(btn.x, btn.y)
            return True
        return False
        
    def is_btn_appeared(self, img_filename: str, btn_name: str, retries: int = 10, wait_time: int = 5):
        for attempt in range(retries):
            btn = self.is_image_on_screen(img_filename)
            if not btn:
                if attempt < retries - 1:
                    pyautogui.sleep(wait_time)
                else:
                    print(f'Кнопка {btn_name} не появилась.')
                    raise Exception('critical')
            else:
                return btn
            
    def press_clear_btn(self, count_try: int = 1):
        btn = self.is_image_on_screen('img/clear.png')
        if not btn:
            if self.is_reconnect_devtools() and count_try<2:
                return self.press_clear_btn(2)
            else:
                print('Я не попадаю в блок is_reconnect_devtools')
            print('Не вижу кнопку очистки! Откройте Dev Tools на вкладке Networks')
            raise Exception('critical')
        self._click(btn.x, btn.y)
        pyautogui.moveTo(btn.x - 20, btn.y, duration=1)


    def get_har_file(self):
        pyautogui.sleep(5)
        # кнопка Export har
        btn = self.is_image_on_screen('img/download_har.png')
        if not btn:
            print('Откройте Dev Tools на вкладке Networks')
            raise Exception('critical')
        self._click(btn.x, btn.y)
        # кнопка сохранить
        btn = self.is_btn_appeared('img/save.png', 'Save')
        self._click(btn.x, btn.y)
        # заменить har файл 
        btn = self.is_btn_appeared('img/yes.png', 'Yes', 5, 2)
        self._click(btn.x, btn.y)
        # сбросить предыдущую запись в har
        self.press_clear_btn()

    def get_url(self):
        pyautogui.sleep(5)
        pyautogui.moveTo(x=628, y=79, duration=2)
        pyautogui.click()
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('del')
        self.q = PostgreSQLTable('ghana_names').get_row('status', 0).get('name')
        self.filters = PostgreSQLTable('ghana_cities').get_row('status', 0).get('filter_hash')
        url = f'https://www.facebook.com/search/people?q={self.q}&filters={self.filters}'
        pyautogui.typewrite(url, interval=0.1)
        pyautogui.press('enter')

    def fill_filter_devtools(self):
        pyautogui.sleep(5)
        if not self.is_image_on_screen('img/fetch_on.png'):
            btn = self.is_image_on_screen('img/fetch_off.png')
            if not btn:
                print('Откройте страницу facebook и DevTools на вкладке Networks')
                raise Exception('critical')
            self._click(btn.x, btn.y)
        btn = self.is_image_on_screen('img/filter_off.png')
        if btn:
            self._click(btn.x, btn.y)
            pyautogui.typewrite('graphql/', interval=0.1)


if __name__ == '__main__':
    Facebook().run()

    # pyautogui.sleep(5)
    # print(pyautogui.position())






