import logging
import time
import traceback
import random
from bs4 import BeautifulSoup
from postgres_db.core import PostgreSQLTable
from .get_links import GetLinksFromMbasicFacebook
from utils.func import write_to_file, load_file
from driver.dynamic import UndetectedDriver
from postgres_db.accounts import update_cookies, db_get_cookies, status_to_blocked
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


class FacebookFindPeople():
    def __init__(self, account: dict) -> None:        
        self.count_try = 0
        self.db_table_liks = 'ghana_links'
        self.account = account
        self.driver = UndetectedDriver(self.account).get_driver()
        self.wait = lambda time_w, criteria: WebDriverWait(self.driver, time_w).until(
            EC.presence_of_element_located(criteria))


    def parse(self, q: str, city_filters: str, link_next_file:bool = False):
        try:
            self._login()

            if not link_next_file:
                link = f'https://mbasic.facebook.com/search/people/?q={q}&filters={city_filters}'
            else:
                link = load_file('next_link.txt')
            self.driver.get(link)
            while True:
                try:
                    xpath = '//*[@id="see_more_pager"]/a'
                    self.wait(10, (By.XPATH, xpath))
                except TimeoutException:
                    raise Exception('Нет следующей страницы') 
                src = self.driver.page_source
                write_to_file('response.html', src)
                link = self.get_next_page_and_update_links_db(src)
                write_to_file('next_link.txt', link)
                
                next = self.driver.find_element(By.XPATH, xpath)
                self.driver.execute_script("arguments[0].scrollIntoView(true);", next)
                next.click()


        except Exception as e:
            self.register_error(e)

        



    def _login(self):
        cookies = db_get_cookies('facebook', self.account['login'])
        if cookies:
            self.driver.get("https://mbasic.facebook.com")
            for name, value in cookies.items():
                self.driver.add_cookie({'name': name, 'value': value})
            return True

        
        # //*[@id="m_login_email"]
        # //*[@id="password_input_with_placeholder"]/input

        time.sleep(1000)

        
    def get_next_page_and_update_links_db(self, src: str) -> str:
        client = GetLinksFromMbasicFacebook(src)
        datas = client.get_links()
        if not datas:
            write_to_file('error_page_links.html', src)
            raise Exception('Нет информации на странице (error_page_links.html)')
        self.update_db_with_links(datas)
        next_page = client.get_next_page()
        if not next_page:
            write_to_file('error_next_page.html', src)
            raise Exception('Нет ссылки на следующую страницу (error_next_page.html)')
        return next_page
    
    def update_db_with_links(self, datas: list) -> None:
        total_user = 0
        add_count = 0
        client = PostgreSQLTable(self.db_table_liks)
        for data in datas:
            total_user += 1
            row = client.get_row('id',data['id'])
            if not row:
                add_count += 1
                client.insert_row(data)
        print(f'Добавлено {add_count} юзеров из {total_user}')

    
    
    def register_error(self, e: Exception):
        logging.info(e)
        print(traceback.format_exc())