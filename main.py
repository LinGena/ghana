import pyautogui
from facebook.content_from_har import AddLinks
from postgres_db.core import PostgreSQLTable
from dotenv import load_dotenv
import os
from utils.func import write_to_file, load_file, _get_filename

load_dotenv(override=True)

class Facebook():
    def __init__(self) -> None:
        pyautogui.PAUSE = 1
        self.page_scroll = [350,300,100]
        self.queries = ['a', 'b', 'c', 'd', 'e', 'i', 'o', 'u']
        self.count_try_reload = 0
        self.errors = 0
        self.count_scroll = len(self.page_scroll)
        self.number_file_path = 'number_q.txt'
        self.filtres_number_file_path = 'number_filter.txt'
        self.number = self.get_number(self.number_file_path)
        self.city_id = self.get_number(self.filtres_number_file_path)


    def run(self):
        self.fill_filter_devtools()
        while True:
            try:
                self.get_url()
                self.press_clear_btn()
                self.errors = self.count_scroll
                self.end_page = False
                for self.i in range(self.count_scroll):
                    self.run_scan() 
                    if self.end_page:
                        break
            except Exception as ex:
                self.exception_while(ex)
            if self.errors >= self.count_scroll - 1:
                self.count_try_reload = 0
                self.number += 1
                write_to_file(self.number_file_path,str(self.number))
            

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
            count_end = 0
            for i in range(self.page_scroll[self.i]):
                previous_screenshot = pyautogui.screenshot()
                pyautogui.hscroll(-1000)
                current_screenshot = pyautogui.screenshot()
                if current_screenshot == previous_screenshot:
                    count_end += 1
                    if count_end > 4:
                        self.end_page = True
                        break
                else:
                    count_end = 0
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
        count_try += 1
        btn = self.is_image_on_screen('img/clear.png')
        if btn:
            self._click(btn.x, btn.y)
            pyautogui.moveTo(btn.x - 20, btn.y, duration=1)
            return
        if not self.is_reconnect_devtools():
            if count_try > 3:
                print('Не вижу кнопку очистки! Откройте Dev Tools на вкладке Networks')
                raise Exception('Something wrong with DevTools')
            return self.press_clear_btn(count_try)
        if count_try > 3:
            raise Exception('Here and what ?')
        return self.press_clear_btn(count_try)
        


    def get_har_file(self):
        pyautogui.sleep(5)
        btn = self.is_image_on_screen('img/download_har.png')
        if not btn:
            print('Откройте Dev Tools на вкладке Networks')
            raise Exception('critical')
        self._click(btn.x, btn.y)

        # pyautogui.sleep(10)
        # pyautogui.press('enter')
        btn = self.is_btn_appeared('img/save.png', 'Save')
        self._click(btn.x, btn.y)

        btn = self.is_btn_appeared('img/yes.png', 'Yes', 5, 2)
        self._click(btn.x, btn.y)
        self.press_clear_btn()

    def get_url(self):
        pyautogui.sleep(5)
        pyautogui.moveTo(x=628, y=79, duration=2)
        pyautogui.click()
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('del')
        
        self.q = self.get_q(self.number)
        if not self.q:
            write_to_file(self.number_file_path,'0')
            write_to_file(self.filtres_number_file_path,'0')
            self.city_id = 0
            self.number = 0
            self.q = self.get_q(self.number)
        
        if self.city_id == 0:
            city = PostgreSQLTable('ghana_cities').get_row('status', 0)
            self.filters = city.get('filter_hash')
            self.city_id = city.get('id')
            write_to_file(self.filtres_number_file_path,str(self.city_id))
            PostgreSQLTable('ghana_cities').update_row('id', self.city_id, {'status':1})
            
        self.filters = PostgreSQLTable('ghana_cities').get_row('id', self.city_id).get('filter_hash')
        url = f'https://www.facebook.com/search/people?q={self.q}&filters={self.filters}'
        pyautogui.typewrite(url, interval=0.1)
        pyautogui.press('enter')


    def get_number(self, filename):
        is_filename = _get_filename(filename)
        if not os.path.exists(is_filename):
            write_to_file(filename,'0')
            return 0
        else:
            src = load_file(filename)
            return int(src)

    def get_q(self, number) -> str:
        if number == len(self.queries):
            return None
        return self.queries[number]

    def fill_filter_devtools(self):
        pyautogui.sleep(5)
        if not self.is_image_on_screen('img/fetch_on.png'):
            btn = self.is_image_on_screen('img/fetch_off.png')
            if not btn:
                self.press_clear_btn()
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






