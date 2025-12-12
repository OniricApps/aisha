import pandas as pd
import json
import os
import random
from datetime import datetime

# TODO
# Add a .lock file to avoid 2 different processes to write to the same cache file

# check folder structure exists and if not, create it
CACHE_FOLDERS = ['cache', 'cache/api_queries', 'cache/bot_queries', 'cache/chat', 'cache/out_links']
for folder in CACHE_FOLDERS:
    if not os.path.exists(folder):
        print(f'Creating folder {folder}')
        os.makedirs(folder)


def gen_id(length=16):
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return ''.join(random.choices(chars, k=length))


def _get_products_list(dataset_id, folder):
    file = f'{folder}/{dataset_id}.json'
    if os.path.exists(file):
        with open(file, 'r', encoding='utf8') as f:
            products = json.load(f)
        return products
    else:
        return None


def _cache_products_list(products, dataset_id, folder):
    # save products to file
    file = f'{folder}/{dataset_id}.json'
    with open(file, 'w', encoding='utf8') as f:
        json.dump(products, f)


def cache_html_by_dataset_id(dataset_id, html):
    file = f'cache/html/{dataset_id}.html'
    with open(file, 'w', encoding='utf8') as f:
        f.write(html)


class CacheApi:
    def __init__(self):
        self.queries = None
        self.folder = 'cache/api_queries'
        self.index_file = f'{self.folder}/index.csv'
        # load cache
        self.load_cache()

    def load_cache(self):
        if os.path.exists(self.index_file):
            self.queries = pd.read_csv(self.index_file, quotechar="'")
            # TODO: eliminar queries amb status FAILED? Va bé al moment, però després guardar-ho com a  cache no te gaire sentit
        else:
            self.queries = pd.DataFrame(columns=['id', 'dataset_id', 'query', 'status'])
            #self.queries.to_csv(self.index_file, index=False)

    # TODO: do the save file as async process if the file increases in size
    # Add or update query to cache
    def cache_query(self, query):
        id = query['id']

        # check if query is already in cache
        r_query = self.queries[self.queries['id'] == id]
        if not r_query.empty:
            # remove row from dataframe
            self.queries = self.queries.drop(self.queries[self.queries['id'] == id].index)

        # add query to cache. Don't use append because it is deprecated
        self.queries = pd.concat([self.queries, pd.DataFrame([query])], ignore_index=True)

        # save to file
        self.queries.to_csv(self.index_file, index=False, quotechar="'")

    def get_query(self, query_id):
        query = self.queries[self.queries['id'] == query_id]
        if query.empty:
            return None
        return query.iloc[0].to_dict()

    def get_query_str(self, query_str):
        #query_str = query_str.lower()
        query = self.queries[self.queries['query'] == query_str]
        if query.empty:
            return None
        return query.iloc[0].to_dict()

    def cache_products(self, products, dataset_id):
        _cache_products_list(products, dataset_id, self.folder)

    def get_products(self, dataset_id):
        return _get_products_list(dataset_id, self.folder)


class CacheQueries:
    def __init__(self):
        self.queries = None
        self.folder = 'cache/bot_queries'
        self.index_file = f'{self.folder}/index.csv'
        self.columns = ['id', 'dataset_id', 'api_query_id', 'filter', 'summary', 'status']
        self.load_cache()

    def load_cache(self):
        if os.path.exists(self.index_file):
            self.queries = pd.read_csv(self.index_file, quotechar="'")
            # filter and summary are strings, son change any NaN by ''
            self.queries['filter'] = self.queries['filter'].fillna('')
            self.queries['summary'] = self.queries['summary'].fillna('')

            # v0.5 canviem nom columna query_id a api_query_id.
            # Ara pot haver-hi vàries ids a api_query_id separades per :
            # if exists column query_api_id, change it by api_query_id
            if 'query_api_id' in self.queries.columns:
                print('Renaming column query_api_id to api_query_id')
                self.queries.rename(columns={'query_api_id': 'api_query_id'}, inplace=True)
                # save to file
                self.queries.to_csv(self.index_file, index=False, quotechar="'")
        else:
            self.queries = pd.DataFrame(columns=self.columns)
            self.queries.to_csv(self.index_file, index=False, quotechar="'")

    def cache_query(self, query):
        if 'id' in query:
            id = query['id']

            # check if query is already in cache
            r_query = self.queries[self.queries['id'] == id]
            if not r_query.empty:
                # remove row from dataframe
                self.queries = self.queries.drop(self.queries[self.queries['id'] == id].index)
        else:
            id = gen_id()
            query['id'] = id

        df_query = pd.DataFrame([query])
        # keep just the columns we want
        df_query = df_query[self.columns]
        # add query to cache. Don't use append because it is deprecated
        self.queries = pd.concat([self.queries, df_query], ignore_index=True)

        # save to file
        self.queries.to_csv(self.index_file, index=False, quotechar="'")

    def get_query(self, query_id):
        query = self.queries[self.queries['id'] == query_id]
        if query.empty:
            return None
        return query.iloc[0].to_dict()

    def get_query_by_summary(self, summary):
        query = self.queries[self.queries['summary'] == summary]
        if query.empty:
            return None
        return query.iloc[0].to_dict()

    def search_query(self, summary=None):
        if summary:
            query = self.get_query_by_summary(summary)
            if query:
                return query
        return None

    def cache_products(self, products, dataset_id):
        _cache_products_list(products, dataset_id, self.folder)

    def get_products(self, dataset_id):
        return _get_products_list(dataset_id, self.folder)


class CacheChat:
    def __init__(self):
        self.chats = None
        self.folder = 'cache/chat'
        self.index_file = f'{self.folder}/index.csv'
        # load cache
        self.load_cache()

    def load_cache(self):
        if os.path.exists(self.index_file):
            self.chats = pd.read_csv(self.index_file, quotechar="'")
        else:
            self.chats = pd.DataFrame(columns=['id', 'user_id', 'title', 'permission', 'date_start', 'date_last',
                                               'state'])

    def get_all_chats(self):
        return self.chats.to_dict(orient='records')

    def cache_chat(self, chat):
        id = chat['id']
        chat['date_last'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # check if chat is already in cache
        r_chat = self.chats[self.chats['id'] == id]
        if not r_chat.empty:
            # remove row from dataframe
            self.chats = self.chats.drop(self.chats[self.chats['id'] == id].index)

        # add chat to cache. Don't use append because it is deprecated
        self.chats = pd.concat([self.chats, pd.DataFrame([chat])], ignore_index=True)

        # save to file
        self.chats.to_csv(self.index_file, index=False, quotechar="'")

    def new_chat(self, user_id=1, permission='PUBLIC'):
        chat = CacheChatHistory()
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        chat_q = {'id': chat.id, 'user_id': user_id, 'title': '', 'permission': permission,
                  'date_start': now_str, 'date_last': now_str, 'state': 'ACTIVE'}
        self.cache_chat(chat_q)
        return chat.id

    def get_chat(self, chat_id):
        chat = self.chats[self.chats['id'] == chat_id]
        if chat.empty:
            return None
        return chat.iloc[0].to_dict()

    def get_chat_history(self, chat_id):
        chat = self.get_chat(chat_id)
        if chat:
            return CacheChatHistory(chat_id)
        else:
            return CacheChatHistory()

    def remove_chat(self, chat_id):
        # remove chat history
        chat = CacheChatHistory(chat_id)
        chat.remove_history()
        # remove chat from cache
        self.chats = self.chats.drop(self.chats[self.chats['id'] == chat_id].index)
        self.chats.to_csv(self.index_file, index=False, quotechar="'")


class CacheChatHistory:
    def __init__(self, id=None):
        self.history = []
        self.folder = 'cache/chat'
        if id:
            self.id = id
            self.load_cache()
        else:
            self.id = gen_id()

    def load_cache(self):
        file = f'{self.folder}/{self.id}.json'
        if os.path.exists(file):
            with open(file, 'r', encoding='utf8') as f:
                self.history = json.load(f)

    def append_history(self, role, message):
        message = {'role': role, 'message': message}
        self.history.append(message)
        file = f'{self.folder}/{self.id}.json'
        with open(file, 'w', encoding='utf8') as f:
            json.dump(self.history, f)

    def get_history(self):
        return self.history

    def remove_history(self):
        file = f'{self.folder}/{self.id}.json'
        if os.path.exists(file):
            os.remove(file)
        self.history = []



class CacheOutLinks:
    def __init__(self):
        self.out_links = None
        self.folder = 'cache/out_links'
        self.index_file = f'{self.folder}/index.csv'
        self.columns = ['id', 'url', 'status']
        self.load_cache()

    def load_cache(self):
        if os.path.exists(self.index_file):
            self.out_links = pd.read_csv(self.index_file, quotechar="'")
        else:
            self.out_links = pd.DataFrame(columns=self.columns)
            self.out_links.to_csv(self.index_file, index=False, quotechar="'")

    def cache_out_link(self, url, link_id=None, status='ACTIVE'):
        out_link = {'url': url, 'id': link_id, 'status': status}
        if link_id:
            # check if link_id is already in cache
            r = self.out_links[self.out_links['id'] == link_id]
            if not r.empty:
                if r['url'].values[0] == url and r['status'].values[0] == status:
                    print(f'Link {link_id} already exists')
                    return
                # remove row from dataframe to update the values
                self.out_links = self.out_links.drop(self.out_links[self.out_links['id'] == link_id].index)
        else:
            link_id = gen_id()
            out_link['id'] = link_id

        df_out_link = pd.DataFrame([out_link])
        # add link to cache. Don't use append because it is deprecated
        self.out_links = pd.concat([self.out_links, df_out_link], ignore_index=True)

        # save to file
        self.out_links.to_csv(self.index_file, index=False, quotechar="'")

    def get_out_link(self, link_id):
        r = self.out_links[self.out_links['id'] == link_id]
        if r.empty:
            return None
        return r.iloc[0].to_dict()


if __name__ == '__main__':
    # open cachechat index
    cache_chat = CacheChat()
    # drop columns has_products and has_ideas
    # cache_chat.chats = cache_chat.chats.drop(columns=['has_products', 'has_ideas', 'last_date'])
    cache_chat.chats = cache_chat.chats.drop(columns=['last_date'])
    # create column 'state' with value 'CLOSED'
    # cache_chat.chats['state'] = 'CLOSED'
    # for rows without value in date_start, set a random date of february 2025
    # cache_chat.chats['date_start'] = cache_chat.chats['date_start'].fillna('2025-02-01 00:00:00')
    # same for date_last
    # cache_chat.chats['date_last'] = cache_chat.chats['date_last'].fillna('2025-02-01 00:01:00')
    # save to file
    cache_chat.chats.to_csv(cache_chat.index_file, index=False, quotechar="'")
