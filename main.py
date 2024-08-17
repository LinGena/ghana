from postgres_db.core import PostgreSQLTable
from facebook.find_people import FacebookFindPeople
from dotenv import load_dotenv

load_dotenv(override=True)

account = PostgreSQLTable('ghana_cm_social_accounts_facebook').get_row('login','322y1uuysr@txcct.com')

q = 'a'
city_filters = 'eyJjaXR5OjAiOiJ7XCJuYW1lXCI6XCJ1c2Vyc19sb2NhdGlvblwiLFwiYXJnc1wiOlwiMTEwNDUzOTc1NjQzNjM2XCJ9In0%3D'

try:
    FacebookFindPeople(account).parse(q, city_filters, False)
except Exception as ex:
    print(ex)