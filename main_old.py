from postgres_db.core import PostgreSQLTable
from facebook.find_people import FacebookFindPeople
# from facebook.find_people_driver import FacebookFindPeople
from driver.dynamic import UndetectedDriver
from dotenv import load_dotenv
import time

load_dotenv(override=True)

account = PostgreSQLTable('ghana_cm_social_accounts_facebook').get_row('login','tjbalfahty@txcct.com')

q = 'o'
city_filters = 'eyJjaXR5OjAiOiJ7XCJuYW1lXCI6XCJ1c2Vyc19sb2NhdGlvblwiLFwiYXJnc1wiOlwiMTEwNDUzOTc1NjQzNjM2XCJ9In0%3D'

try:
    FacebookFindPeople(account).parse(q, city_filters, False)
except Exception as ex:
    print(ex)