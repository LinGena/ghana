from datetime import datetime
from postgres_db.core import PostgreSQLTable

prefiks = 'ghana_'

def update_cookies(network: str, username: str, cookies_value: dict):
    spreadsh = PostgreSQLTable(table_name=f'{prefiks}cm_social_accounts_{network}')
    el = {"row": "cookies", "value": cookies_value}
    spreadsh.update_row("login", username, {el.get('row'): el.get('value')})


def db_get_cookies(network: str, username: str):
    spreadsh = PostgreSQLTable(table_name=f'{prefiks}cm_social_accounts_{network}')
    row = spreadsh.get_row('login', username)
    return row.get('cookies')


def status_to_blocked(login: str, network: str):
    spreadsh = PostgreSQLTable(table_name=f'{prefiks}cm_social_accounts_{network}')
    to_update = [
        {"login": login, "row": "status", "value": "blocked"},
        {"login": login, "row": "status_time", "value": datetime.now()}
    ]
    for el in to_update:
        spreadsh.update_row("login", el.get('login'), {el.get('row'): el.get('value')})