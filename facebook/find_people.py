import logging
import time
import traceback
import random
from bs4 import BeautifulSoup
from postgres_db.accounts import update_cookies
from postgres_db.core import PostgreSQLTable
from .fb_login import FacebookLogin
from .get_links import GetLinksFromMbasicFacebook
from utils.func import write_to_file, load_file


class FacebookFindPeople(FacebookLogin):
    def __init__(self, account: dict) -> None:        
        super().__init__(account)
        self.login()
        self.count_try = 0
        self.db_table_liks = 'ghana_links'

    def parse(self, q: str, city_filters: str, link_next_file:bool = False):
        try:
            if not link_next_file:
                link = f'https://mbasic.facebook.com/search/people/?q={q}&filters={city_filters}'
            else:
                link = load_file('next_link.txt')
            while True:
                src = self.get_page_content(link)
                link = self.get_next_page_and_update_links_db(src)
                write_to_file('next_link.txt', link)
                time.sleep(random.randint(1,10))
        except Exception as e:
            self.register_error(e)

        update_cookies('facebook', self.account['login'], self.session.cookies.get_dict())
        
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

    def get_page_content(self, link: str) -> str:
        response = self.session.get(link)
        status = response.status_code
        if status == 200:
            write_to_file('response.html', response.text)
            soup = BeautifulSoup(response.text, 'html.parser')
            block_result = soup.find('div', id='BrowseResultsContainer')
            if not block_result:
                time.sleep(3)
                self.count_try += 1
                if self.count_try > 3:
                    raise Exception('На странице нет блока div с id=BrowseResultsContainer')
                return self.get_page_content(link)
            self.count_try = 0
            return response.text
        else:
            raise Exception(f'Status_code: {status}. Link: {link}')
    
    def register_error(self, e: Exception):
        logging.info(e)
        print(traceback.format_exc())