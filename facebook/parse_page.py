from postgres_db.core import PostgreSQLTable
from utils.func import *
from bs4 import BeautifulSoup
import json


class ParsePage():
    def __init__(self) -> None:
        self.db_table = 'ghana_links'
        self.result = {
            'id': None,
            'profile_url': None,
            'profile_photo': None,
            'cover_photo': None,
            'gender': None,
            'is_verified': None,
            'intro': None,
            'posts': None,
            'overview': None,
            'friends': None,
            'groups': None,
            'likes': None,
        }

    def run(self, page_html_content: str):
        self.get_result(page_html_content)
        self.result = {k: v for k, v in self.result.items() if v is not None}
        if 'id' in self.result:
            self.result['status'] = 2
            if 'groups' in self.result:
                self.result['groups'] = json.dumps(self.result['groups'])
            if 'likes' in self.result:
                self.result['likes'] = json.dumps(self.result['likes'])
            print('UPDATE',self.result['id'])
            PostgreSQLTable(self.db_table).update_row('id', self.result['id'], self.result)

    def get_result(self, page_html_content) -> dict:
        soup = BeautifulSoup(page_html_content,'lxml')
        scripts = soup.find_all('script', {"type":"application/json"})
        for script in scripts:
            script_text = script.text.strip()
            try:
                data = json.loads(script_text)
            except json.JSONDecodeError as e:
                print(f"Ошибка декодирования JSON: {e}")
                continue
    
            if 'profile_header_renderer":' in script_text:
                result = self.find_key(data, 'profile_header_renderer')
                if result:
                    self.get_user_info(result)

            if 'profile_tile_sections":' in script_text:
                result = self.find_key(data, 'profile_tile_sections')
                if result:
                    self.get_intro(result)
            
            if '"__typename":"CometStorySections"' in script_text:
                result = self.find_key(data, 'comet_sections')
                if result:
                    comet_sections = self.find_key(result, 'comet_sections')
                    if comet_sections and 'message' in comet_sections and comet_sections['message'] and 'story' in comet_sections['message']:
                        if comet_sections['message']['story']:
                            self.get_posts(comet_sections['message']['story'])
                    attached_story_layout = self.find_key(result, 'attached_story_layout')
                    if attached_story_layout and 'story' in attached_story_layout and attached_story_layout['story']:
                        self.get_posts(attached_story_layout['story'])

            if 'about_app_sections":' in script_text:
                result = self.find_key(data, 'about_app_sections')
                if result:
                    self.get_about(result)

            if '"__typename":"Group"' in script_text:
                result = self.find_key(data, 'all_collections')
                if result:
                    self.get_groups(result)
            
            if '"name":"All Likes"' in script_text:
                result = self.find_key(data, 'all_collections')
                if result:
                    self.get_likes(result)

    def get_likes(self, result):
        if 'nodes' in result and result['nodes']:
            for node in result['nodes']:
                edges = self.find_key(node, 'edges')
                if edges:
                    for edge in edges:
                        if 'node' in edge and edge['node']:
                            data = edge['node']
                            res = {}
                            if 'title' in data and data['title'] and 'text' in data['title']:
                                res['title'] = data['title']['text']
                            if 'url' in data and data['url']:
                                res['url'] = data['url']
                            if not self.result['likes']:
                                self.result['likes'] = []
                            self.result['likes'].append(res)

    def get_groups(self, result):
        if 'nodes' in result and result['nodes']:
            for node in result['nodes']:
                edges = self.find_key(node, 'edges')
                if edges:
                    for edge in edges:
                        if 'node' in edge and edge['node']:
                            data = edge['node']
                            res = {}
                            if 'title' in data and data['title'] and 'text' in data['title']:
                                res['title'] = data['title']['text']
                            if 'subtitle_text' in data and data['subtitle_text'] and 'text' in data['subtitle_text']:
                                res['subtitle_text'] = data['subtitle_text']['text']
                            if 'url' in data and data['url']:
                                res['url'] = data['url']
                            if 'node' in data and data['node']:
                                if 'privacy_info' in data['node'] and data['node']['privacy_info']:
                                    if 'title' in data['node']['privacy_info'] and data['node']['privacy_info']['title']:
                                        if 'text' in data['node']['privacy_info']['title']:
                                            res['privacy_info'] = data['node']['privacy_info']['title']['text']
                                if 'group_member_profiles' in data['node'] and data['node']['group_member_profiles']:
                                    if 'formatted_count_text' in data['node']['group_member_profiles']:
                                        res['formatted_count'] = data['node']['group_member_profiles']['formatted_count_text']
                            if not self.result['groups']:
                                self.result['groups'] = []
                            self.result['groups'].append(res)

    def get_posts(self, result):
        if 'message' in result and result['message'] and 'text' in result['message']:
            post = self.get_value(result['message'], 'text')
            if post:
                post = post.replace('\n','')
                if not self.result['posts']:
                    self.result['posts'] = [] 
                self.result['posts'].append(post)
                        
    def get_about(self, result):
        profile_field_sections = self.find_key(result, 'profile_field_sections')
        if profile_field_sections:
            for profile_field_section in profile_field_sections:
                profile_fields = self.find_key(profile_field_section, 'profile_fields')
                if profile_fields:
                    if 'nodes' in profile_fields:
                        for node in profile_fields['nodes']:
                            title = ''
                            text_content = ''
                            if 'title' in node and 'text' in node['title']:
                                title = node['title']['text']
                            if 'renderer' in node and node['renderer'] and 'field' in node['renderer'] and node['renderer']['field']:
                                if 'text_content' in node['renderer']['field'] and node['renderer']['field']['text_content'] and 'text' in node['renderer']['field']['text_content']:
                                    text_content = node['renderer']['field']['text_content']['text']
                            if title or text_content:
                                if not self.result['overview']: 
                                    self.result['overview'] = []
                                self.result['overview'].append(title + ' ' + text_content)

    def get_user_info(self, result):
        if 'user' in result:
            user = result['user']
            id = self.get_value(user, 'id')
            if id:
                self.result['id'] = int(id)
            self.result['gender'] = self.get_value(user, 'gender')
            self.result['profile_url'] = self.get_value(user, 'url')
            self.result['is_verified'] = self.get_value(user, 'is_verified')
            self.get_profile_photo(user)
            self.get_cover_photo(user)
            self.get_friends(user)
            
    def get_profile_photo(self, user):
        if 'profilePicLarge' and user and user['profilePicLarge'] and 'uri' in user['profilePicLarge'] and user['profilePicLarge']['uri']:
            self.result['profile_photo'] = user['profilePicLarge']['uri']
        else:
            if 'profilePicMedium' and user and user['profilePicMedium'] and 'uri' in user['profilePicMedium'] and user['profilePicMedium']['uri']:
                self.result['profile_photo'] = user['profilePicMedium']['uri']
            else:
                if 'profilePicSmall' and user and user['profilePicSmall'] and 'uri' in user['profilePicSmall'] and user['profilePicSmall']['uri']:
                    self.result['profile_photo'] = user['profilePicSmall']['uri']

    def get_cover_photo(self, user):
        cover_photo = self.get_value(user, 'cover_photo')
        if cover_photo and 'photo' in cover_photo and cover_photo['photo']:
            if 'image' in cover_photo['photo'] and cover_photo['photo']['image']:
                if 'uri' in cover_photo['photo']['image'] and cover_photo['photo']['image']['uri']:
                    self.result['cover_photo'] = cover_photo['photo']['image']['uri']

    def get_friends(self, user):
        if 'profile_social_context' in user and user['profile_social_context']:
            if 'content' in user['profile_social_context'] and user['profile_social_context']['content']:
                for content in user['profile_social_context']['content']:
                    if 'text' in content and 'text' in content['text']:
                        if not self.result['friends']:
                            self.result['friends'] = []
                        self.result['friends'].append(content['text']['text'])
    
    def get_intro(self, result):
        profile_tile_views = self.find_key(result, 'profile_tile_views')
        if 'nodes' in profile_tile_views:
            for nodes in profile_tile_views['nodes']:
                profile_tile_items = self.find_key(nodes, 'profile_tile_items')
                if profile_tile_items:
                    if 'nodes' in profile_tile_items:
                        for node in profile_tile_items['nodes']:
                            if 'node' in node:
                                section = node['node']
                                text = self.find_key(section, 'text')
                                if text:
                                    if not self.result['intro']:
                                        self.result['intro'] = [] 
                                    self.result['intro'].append(text.strip())
        
    def get_value(self, data, key):
        if key in data:
            return data[key] 
        return None
        
    def find_key(self, data, target_key):
        if isinstance(data, dict):
            if target_key in data:
                return data[target_key]
            for key, value in data.items():
                result = self.find_key(value, target_key)
                if result is not None:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = self.find_key(item, target_key)
                if result is not None:
                    return result
        return None

            

# if __name__ == "__main__":
#     page_html_content = load_file('page.html')
#     ParsePage().run(page_html_content)
