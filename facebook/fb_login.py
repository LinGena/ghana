import requests
import secmail
import time
from bs4 import BeautifulSoup
from postgres_db.accounts import update_cookies, db_get_cookies, status_to_blocked
from utils.func import write_to_file


class FacebookLogin():
    def __init__(self, account: dict) -> None:
        self.account = account
        self.domain = 'https://mbasic.facebook.com'

    def __del__(self):
        self.session.close()

    def login(self) -> requests.Session:
        """Возвращает requests.Session"""

        self.session = requests.Session()

        proxy = self.get_proxy() 
        self.session.proxies = {'http':proxy, 'https':proxy}

        if self.check_db_cookies():
            self.session.headers = self.get_headers()
            return self.session
               
        response = self.session.get("https://mbasic.facebook.com/login")

        soup = BeautifulSoup(response.text, 'html.parser')
        if 'Blocked' in response.text:
            status_to_blocked(self.account['login'], 'facebook')
            raise Exception("Title response message: You're Temporarily Blocked")
        
        value_lsd = soup.find('input', {'name': 'lsd'}).get('value')
        value_jazoest = soup.find('input', {'name': 'jazoest'}).get('value')
        value_li = soup.find('input', {'name': 'li'}).get('value')
        cookies_dict = self.session.cookies.get_dict()

        params={
            'refsrc': 'deprecated',
            'lwv': '100',
            'ref': 'dbl'
            }
        cookies={
            'datr': str(cookies_dict.get('datr', '')), 
            'sb': str(cookies_dict.get('sb', '')), 
            'ps_l': '0', 
            'ps_n': '0'
            }
        data={
            'lsd': str(value_lsd), 
            'jazoest': str(value_jazoest), 
            'm_ts': str(time.time()).split('.')[0], 
            'li': str(value_li), 
            'try_number': '0', 
            'unrecognized_tries': '0', 
            'email': str(self.account['login']), 
            'pass': str(self.account['password']), 
            'login': 'Войти', 
            'bi_xrwh': '0'
            }
        response = self.session.post(
            'https://mbasic.facebook.com/login/device-based/regular/login/', 
            params=params, 
            cookies=cookies, 
            headers=self.get_headers(), 
            data=data)
        
        update_cookies('facebook', self.account['login'], self.session.cookies.get_dict())

        if "c_user" in response.cookies.get_dict().keys() or 'm_page_voice' in str(response.cookies):
            return self.session

        elif "checkpoint" in response.cookies.get_dict().keys():
            if self.get_checkpoint(response.text):
                return self.session
            write_to_file('checkpoint.html', response.text)
            raise Exception('CheckPoint')
        else:
            write_to_file('wrong_login.html', response.text)
            raise Exception('Wrong login')
        
    def get_checkpoint(self, src: str) -> bool:
        soup = BeautifulSoup(src, 'html.parser')
        title = soup.find('title').text.strip()
        if title == 'Get a code sent to your email':
            if '@txcct.com' in self.account['login']:
                status = self.checkpoint_1secMail(soup)
                return status
        # if title == 'Log in on another device to continue':
            
        return False
    
    def checkpoint_1secMail(self, soup: BeautifulSoup) -> bool:
        response = self.click_recieve_code(soup)
        if not response: 
            print('не нажали кнопку')
            return False        
        code = self.gettind_code()
        response = self.enter_recieved_code(response, code)
        if not response: return False
        write_to_file('result.html', response)
        return True
       
    def gettind_code(self):
        print('Получаем код')
        client = secmail.Client()
        new_message = client.await_new_message(self.account['login'])
        message = client.get_message(address=self.account['login'], message_id=new_message.id)
        text_body = message.text_body
        code = str(text_body).split('security code is: ')[1].split(' ')[0].strip()
        print('CODE =',code)
        return code

    def enter_recieved_code(self, response, code):
        soup = BeautifulSoup(response, 'html.parser')
        form = soup.find('form', class_='l')
        if not form: return None
        link = self.domain + form.get('action')
        data = {
            'fb_dtsg': self.get_value(soup, 'fb_dtsg'),
            'jazoest': self.get_value(soup, 'jazoest'),
            'checkpoint_data': self.get_value(soup, 'checkpoint_data'),
            'captcha_response': code,
            'submit[Continue]': 'Continue',
            'nh': self.get_value(soup, 'nh')
        }
        response = self.session.post(link, data=data)
        return response.text
    
    def click_recieve_code(self, soup: BeautifulSoup) -> bool:
        form = soup.find('form', class_='m')
        if not form: return None
        link = self.domain + form.get('action')
        data = {
            'fb_dtsg': self.get_value(soup, 'fb_dtsg'),
            'jazoest': self.get_value(soup, 'jazoest'),
            'checkpoint_data': self.get_value(soup, 'checkpoint_data'),
            'send_code': self.get_value(soup, 'send_code'),
            'eindex': self.get_eindex(soup),
            'submit[Continue]': 'Continue',
            'nh': self.get_value(soup, 'nh')
        }
        response = self.session.post(link, data=data)
        return response.text
    
    def get_eindex(self, soup: BeautifulSoup) -> str:
        select = soup.find('select', {'name':'eindex'})
        options = select.find_next('option')
        return options.get('value')


    def get_value(self, soup: BeautifulSoup, name: str) -> str:
        value = soup.find('input', {'name': name})
        return value.get('value','')
        
    def check_db_cookies(self) -> bool:
        cookies = db_get_cookies('facebook', self.account['login'])
        if cookies:
            if 'c_user' in cookies.keys():
                self.session.cookies.update(cookies)
                return True
            # if 'checkpoint' in cookies.keys():
                # raise Exception('CheckPoint')
        return False

    def get_proxy(self):
        PROXY_USER = self.account['proxy_username']
        PROXY_PASS = self.account['proxy_password']
        PROXY_HOST = self.account['proxy_host']
        PROXY_PORT = self.account['proxy_port']
        return f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'
    
    def get_headers(self):
        return {
            'authority': 'mbasic.facebook.com', 
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,uk;q=0.6',
            'cache-control': 'max-age=0', 
            'content-type': 'application/x-www-form-urlencoded', 
            'dpr': '2', 
            'origin': 'https://mbasic.facebook.com', 
            'referer': 'https://mbasic.facebook.com/login/?next&ref=dbl&fl&login_from_aymh=1&refid=8', 
            'sec-ch-prefers-color-scheme': 'dark', 
            'sec-ch-ua': '"Not)A;Brand";v="24", "Chromium";v="116"', 
            'sec-ch-ua-full-version-list': '"Not)A;Brand";v="24.0.0.0", "Chromium";v="116.0.5845.72"', 
            'sec-ch-ua-mobile': '?0', 
            'sec-ch-ua-model': '""', 
            'sec-ch-ua-platform': '"Linux"', 
            'sec-ch-ua-platform-version': '""', 
            'sec-fetch-dest': 'document', 
            'sec-fetch-mode': 'navigate', 
            'sec-fetch-site': 'same-origin', 
            'sec-fetch-user': '?1', 
            'upgrade-insecure-requests': '1', 
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36', 
            'viewport-width': '980'
            } 
        