from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs


class GetLinksFromMbasicFacebook():
    def __init__(self, page_source: str) -> None:
        self.soup = BeautifulSoup(page_source, 'html.parser')

    def get_links(self) -> list:
        result = []
        block_result = self.soup.find('div', id='BrowseResultsContainer')
        blocks = block_result.find_all('tr')
        for block in blocks:
            tds = block.find_all('td')
            content = tds[1].find('a')
            next_block = tds[2]
            if content:
                profile_url = self.get_href_from_content(content)
                if profile_url:
                    res = {
                        'name':self.get_name_from_content(content),
                        'profile_url':profile_url
                    }
                    id = self.get_id_from_content(next_block, profile_url)
                    if id:
                        res.update({'id':id})
                        result.append(res)
        return result
    
    def get_next_page(self) -> str:
        block = self.soup.find('div',id='see_more_pager')
        if block:
            link = block.find('a')
            if link:
                href = link.get('href')
                if href:
                    return href
        print('There is not next page')
        return None
    
    def get_id_from_content(self, content: BeautifulSoup, profile_url: str) -> int:
        try:
            if 'id=' in profile_url:
                return int(profile_url.split('id=')[1])
            else:
                block = content.find('a')
                if block:
                    href = block.get('href')
                    parsed_url = urlparse(href)
                    params = parse_qs(parsed_url.query)
                    id = params.get('subject_id', None)
                    if not id:
                        id = params.get('id', None)
                    if not id:
                        return None
                    return int(id[0])
        except Exception as ex:
            print(f'[get_id_from_content] - {profile_url} - {ex}')
        return None

       
    def get_name_from_content(self, content: BeautifulSoup) -> str:
        try:
            blocks = content.find_all('div')
            name = blocks[0].text.strip()
            name = name.replace('\n',' ').replace('  ','')
            return name
        except Exception as ex:
            print(f"[get_name_from_content] {ex}")
        return ''

    def get_href_from_content(self, content: BeautifulSoup) -> str:
        try:
            url = content.get('href')
            profile_url = url.split('eav=')[0]
            result = 'https://www.facebook.com' + profile_url[:-1]
            return result
        except Exception as ex:
            print(f"[get_href_from_content] {ex}")
        return None
    