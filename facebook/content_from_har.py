from utils.func import *
from postgres_db.core import PostgreSQLTable
import json
from dotenv import load_dotenv
from threading import Thread

load_dotenv(override=True)


class AddLinks():
    def __init__(self) -> None:
        self.filename = '2.har'
        

    def get_links(self, data: json):
        result = []
        if 'serpResponse' in data['data']:
            edges = data['data']['serpResponse']['results']['edges']
            for edge in edges:
                try:
                    profile = edge['relay_rendering_strategy']['view_model']['profile']
                    res = {
                        'id': int(profile['id']),
                        'name': profile['name'],
                        'profile_url': profile['profile_url']
                    }
                    result.append(res)
                except Exception as ex:
                    print(ex)
        return result


    def insert_to_db(self, links):
        threads_count = 5
        countThread = round(len(links) / int(threads_count)) + 1
        for i in func_chunk_array (links, countThread):
            Thread(target=AddDataThread().insert_data, args=(i,)).start()


    def run(self):
        try:
            scr = load_file(self.filename, in_dir=False)
            data = json.loads(scr)
            res = []
            for entries in data['log']['entries']:
                for i,n in entries.items():
                    if i == 'response':
                        if 'content' in n and 'text' in n['content']:
                            is_profile = n['content']['text']
                            if 'profile_url' in str(is_profile):
                                datas = []
                                if is_profile and is_profile.startswith("{") and is_profile.endswith("}"):
                                    try:
                                        deserialized_data = json.loads(is_profile)
                                        datas = self.get_links(deserialized_data)
                                    except Exception as e:
                                        print(e) 
                                else:
                                    print("Значение 'text' не содержит валидный JSON")
                                if datas:
                                    # res += datas
                                    self.insert_to_db(datas)
        except Exception as ex:
            print(ex)
        

class AddDataThread():
    def __init__(self) -> None:
        self.db_table_liks = 'ghana_links'

    def insert_data(self, datas):
        for data in datas:
            try:
                row = PostgreSQLTable(self.db_table_liks).get_row('id',data['id'])
                if not row:
                    print(f'Добавлен: {data}')
                    PostgreSQLTable(self.db_table_liks).insert_row(data)
                else:
                    print(f"Есть в базе: {data['id']}")
            except Exception as ex:
                print(ex)
    


if __name__ == '__main__':
    AddLinks().run()