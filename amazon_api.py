import requests
import json
import time
import caches
from amazon_paapi import AmazonApi

# add to any product URL your affiliate tag
AMAZON_AFFILIATE_TAG = 'oniricapps-21' # Your affiliate tag here

# Set API token for Apify
API_TOKEN = 'YOUR_APIFY_API_TOKEN_HERE'

# Amazona PA API credentials
ACCESS_KEY = 'YOUR_ACCESS_KEY_HERE'
SECRET_KEY = 'YOUR_SECRET_KEY_HERE'


def add_affiliate_tag(url, affiliate_tag=AMAZON_AFFILIATE_TAG):
    if "?" in url:
        return f"{url}&tag={affiliate_tag}"
    else:
        return f"{url}?tag={affiliate_tag}"



class AmazonAPI: #_PAAPI:
    def __init__(self):
        self.access_key = ACCESS_KEY
        self.secret_key = SECRET_KEY
        self.amazon_tag = AMAZON_AFFILIATE_TAG
        #self.verify_ssl = False  # A Onricbot es posa a true
        self.paapi = AmazonApi(ACCESS_KEY, SECRET_KEY, AMAZON_AFFILIATE_TAG, 'ES', throttling=3) #, verify=self.verify_ssl)
        self.cache = caches.CacheApi()

    def get_query(self, query_id):
        return self.cache.get_query(query_id)

    # TODO: do it async
    def async_search(self, query, pages=3):
        query_str = query['query']
        # check if query is already done
        if query['status'] == 'SUCCEEDED':
            print("Query already done")
            return

        # run the search
        query['status'] = 'RUNNING'
        self.cache.cache_query(query)
        products = []
        for page in range(pages):
            try:
                search_result = self.paapi.search_items(keywords=query_str, item_page=page+1)
                for item in search_result.items:
                    product = {
                        'id': item.asin,
                        'url': item.detail_page_url,
                        'name': item.item_info.title.display_value,
                        'image': item.images.primary.large.url,
                        'description': '',
                        'price': '',
                    }
                    try:
                        #if item.item_info.offers:
                        product['price'] = item.offers.listings[0].price.display_amount
                    except:
                        print("Error getting price")
                        print(item)
                        pass
                    try:
                        #if item.item_info.features.display_values:
                       product['description'] = ' '.join(item.item_info.features.display_values)
                    except:
                        pass
                    if product['price'] != '':
                        print(product)
                        products.append(product)
            except Exception as e:
                print(f"Error: {e}")
                # if error, break the loop
                break
            #if len(products) >= 10 * (pages+1):
            #    break

        if len(products) == 0:
            query['status'] = 'FAILED'
            self.cache.cache_query(query)
            return
        self.cache.cache_products(products, query['dataset_id'])
        query['status'] = 'SUCCEEDED'
        self.cache.cache_query(query)

    def search(self, query_str):
        # check if query is in cache
        query = self.cache.get_query_str(query_str)
        if query and query['status'] != 'FAILED':
            print("Query found in cache")
            print(query)
            return query

        # generate query
        query = {'id': caches.gen_id(), 'dataset_id': caches.gen_id(), 'query': query_str, 'status': 'READY'}
        self.cache.cache_query(query)

        # TODO: make this call really async
        #self.async_search(query)

        return query

    def get_product_list(self, dataset_id):
        products = self.cache.get_products(dataset_id)
        if products:
            return products
        return None
#        for page in range(3):
#            search_result = amazon.search_items(keywords=query_str, search_index='All', item_page=page + 1)
#            # print(search_result)
#            products = []
#            for item in search_result.items:
#                product = {
#                    'id': item.asin,
#                    'url': item.detail_page_url,
#                    'name': item.item_info.title.display_value,
#                    'img': item.images.primary.large.url,
#                    'description': ' '.join(item.item_info.features.display_values)
#                }
#                print(product)
#                products.append(product)
#        self.cache.cache_products(products, dataset_id)
#        return products

    def check_query_status(self, query_id):
        query = self.cache.get_query(query_id)
        return query['status'] if query else None

    def await_query_succeed(self, query_id):
        query = self.cache.get_query(query_id)
        if not query:
            return False
        self.async_search(query)
        if query['status'] == 'SUCCEEDED':
            self.cache.cache_query(query)
            return True
        return False
        #while query['status'] in ['READY', 'RUNNING']:
        #    time.sleep(1)
        #    query['status'] = self.check_query_status(query_id)
        #    print(query['status'])
        #    if query['status'] == 'SUCCEEDED':
        #        self.cache.cache_query(query)
        #        return True
        #    elif query['status'] == 'FAILED' or query['status'] not in ['READY', 'RUNNING']:
        #        self.cache.cache_query(query)
        #       return False

    def get_query_results(self, query_id):
        query = self.cache.get_query(query_id)
        if not query or 'status' not in query or query['status'] == 'FAILED':
            return None
        if query['status'] == 'SUCCEEDED':
            return self.get_product_list(query['dataset_id'])
        elif query['status'] in ['READY', 'RUNNING']:
            if self.await_query_succeed(query['id']):
                return self.get_product_list(query['dataset_id'])
            else:
                return None
        else:
            return None

# Rename this class to AmazonAPI if you want to use Apify instead of PAAPI
class AmazonAPI_Apify:
    def __init__(self, actor=None):
        self.actor = "igolaizola/amazon-search"
        self.url_actor = 'myKKbZPxScDexiGz7'
        self.api_token = API_TOKEN
        self.verify_ssl = False # False for testing purposes, set to True in production
        self.cache = caches.CacheApi()

    def get_query(self, query_id):
        return self.cache.get_query(query_id)

    def search(self, query_str):
        # check if query is in cache
        query = self.cache.get_query_str(query_str)
        if query and query['status'] != 'FAILED':
            print("Query found in cache")
            print(query)
            return query

        if self.actor == "igolaizola/amazon-search":
            query_url = query_str
            # change spaces to url encode the query
            query_url = query_url.replace(" ", "+")
            # change Spanish not valid characters to url encoding
            query_url = query_url.replace("á", "%C3%A1")
            query_url = query_url.replace("é", "%C3%A9")
            query_url = query_url.replace("í", "%C3%AD")
            query_url = query_url.replace("ó", "%C3%B3")
            query_url = query_url.replace("ú", "%C3%BA")
            query_url = query_url.replace("ü", "%C3%BC")
            query_url = query_url.replace("ñ", "%C3%B1")

            run_input = {
                "search": f"https://www.amazon.es/s?k={query_url}",
                "proxyConfiguration": {
                    "useApifyProxy": True,
                    "apifyProxyGroups": ["RESIDENTIAL"],
                    "apifyProxyCountry": "ES",
                },
                "pages": 1,
            }
            print(run_input)
        else:
            print("Actor not found")
            return None

        # Define the API endpoint. force build=0.0.11
        url = f"https://api.apify.com/v2/acts/{self.url_actor}/runs?token={self.api_token}&build=0.0.11"
        # latest
        # url = f"https://api.apify.com/v2/acts/{self.url_actor}/runs?token={self.api_token}"

        # Make the POST request
        response = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(run_input),
                                 verify=self.verify_ssl)

        if response.status_code == 201:
            print("Request was successful")
            print(response.json())
            dataset_id = response.json()["data"]["defaultDatasetId"]
            status = response.json()["data"]["status"]
            query_id = response.json()["data"]["id"]

            query = {'id': query_id, 'dataset_id': dataset_id, 'query': query_str, 'status': status}
            self.cache.cache_query(query)
            return query
        else:
            print("Request failed")
            print(response)
            return None

    def check_query_status(self, query_id):
        url = f"https://api.apify.com/v2/actor-runs/{query_id}?token={self.api_token}"
        response = requests.get(url, headers={'Content-Type': 'application/json'}, verify=self.verify_ssl)
        try:
            status = response.json()["data"]["status"]
        except:
            status = "FAILED"
        if status == "FAILED":
            print(response)
            print(response.json())
        return status

    def await_query_succeed(self, query_id):
        query = self.cache.get_query(query_id)
        if not query:
            return False

        while query['status'] in ['READY', 'RUNNING']:
            query['status'] = self.check_query_status(query_id)
            print(query['status'])
            if query['status'] == 'SUCCEEDED':
                self.cache.cache_query(query)
                return True
            elif query['status'] == 'FAILED' or query['status'] not in ['READY', 'RUNNING']:
                self.cache.cache_query(query)
                return False
            time.sleep(1)

    def get_product_list(self, dataset_id):
        products = self.cache.get_products(dataset_id)
        if products:
            return products

        url = f'https://api.apify.com/v2/datasets/{dataset_id}/items?token={self.api_token}'
        response = requests.get(url, headers={'Content-Type': 'application/json'}, verify=self.verify_ssl)
        if response.status_code == 200:
            products = response.json()
            remove_str = 'PatrocinadoPatrocinado PatrocinadoPatrocinadoPatrocinadoPatrocinadoPuedes ver este anuncio debido a la relevancia del producto con respecto a tu búsqueda.Más información sobre este anuncio  Más información sobre este anuncio'
            for product in products:
                product['url'] = add_affiliate_tag(product['url'])
                if product['name'].startswith(remove_str):
                    product['name'] = product['name'][len(remove_str):]
                # change \n by space
                product['name'] = product['name'].replace('\n', ' ')
            self.cache.cache_products(products, dataset_id)
            return products
        else:
            return None

    def get_query_results(self, query_id):
        query = self.cache.get_query(query_id)
        if not query or 'status' not in query or query['status'] == 'FAILED':
            return None
        if query['status'] == 'SUCCEEDED':
            return self.get_product_list(query['dataset_id'])
        elif query['status'] in ['READY', 'RUNNING']:
            if self.await_query_succeed(query['id']):
                return self.get_product_list(query['dataset_id'])
            else:
                return None
        else:
            return None


if __name__ == '__main__':
    amz = AmazonAPI()
    # amz.search('nintendo')
    query = amz.search("bicicleta tres ruedas")

    print(query)
    #exit()
    print(f"Query ID: {query['id']}")
    products = amz.get_query_results(query['id'])
    if products:
        # write a file
        with open('products-test.json', 'w') as f:
            json.dump(products, f)
        for product in products[:3]:
            print(product)
    else:
        print("No products found")
    exit()
    #amazon = AmazonAPI_PAAPI()
    amazon = AmazonApi(ACCESS_KEY, SECRET_KEY, AMAZON_AFFILIATE_TAG, 'ES', throttling=1)
    #search_result = amazon.search_items(keywords="brújula barómetro termómetro verde")
    for page in range(3):
        search_result = amazon.search_items(keywords="bicicleta", search_index='All', item_page=page+1)
        #print(search_result)
        products = []
        for item in search_result.items:
            product = {
                'id': item.asin,
                'url': item.detail_page_url,
                'name': item.item_info.title.display_value,
                'img': item.images.primary.large.url,
                'description': ' '.join(item.item_info.features.display_values)
            }
            print(product)
            products.append(product)
        #    print(item.item_info.title.display_value)  # Item title
        #    print(item.item_info.product_info.color)  # Item color
        #    print(item.customer_reviews)  # Item reviews
    exit()
    item = amazon.get_items('B0DTTNM7RC')[0]
    print(item.item_info.title.display_value)  # Item title
    print(item.customer_reviews)
    print(item)
    # save search_result in a json file
    with open('search_result_item.json', 'w', encoding="UTF-8") as f:
        json.dump(item.to_dict(), f)

    exit()

    amz = AmazonAPI()
    #amz.search('nintendo')
    query = amz.search("brújula barómetro termómetro verde")

    print(query)
    exit()
    print(f"Query ID: {query['id']}")
    products = amz.get_query_results(query['id'])
    if products:
        # write a file
        with open('products-test.json', 'w') as f:
            json.dump(products, f)
        for product in products[:3]:
            print(product)
    else:
        print("No products found")
