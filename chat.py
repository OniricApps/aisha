import json
import logging
import markdown
import amazon_api
import random
import caches
from datetime import datetime
import time
import dspy
from pydantic import BaseModel, Field
from typing import List, Optional

# logfile.txt
logger = logging.getLogger(__name__)
logging.basicConfig(filename='logs/chatbot.txt', level=logging.INFO)

# Set your Gemini API key here
GEMINI_API_KEY = 'YOUR_GEMINI_API_KEY_HERE'

# Configure DSPy with Gemini
#genai.configure(api_key=GEMINI_API_KEY)
lm = dspy.LM('gemini/gemini-2.5-flash-lite', api_key=GEMINI_API_KEY)
dspy.configure(lm=lm)

# Prompts are in Spanish. Feel free to translate them to your audience language.
PROMPT_GENERAL = '''Te llamas Aisha. Eres un asistente de compras personal.
Ayudas a encontrar los productos descritos por el usuario en Amazon y otras
tiendas online. También das ideas de regalos, buscas productos que satisfagan
las necesidades del usuario y, en general, tratas de resolver las consultas del
usuario ofreciendo productos para comprar.
'''

PROMPT_STORES = '''<stores>
Amazon: Genérico. Todo tipo de productos que se puedan comprar online.
</stores>'''
#Aliexpress: Genérico. Todo tipo de productos que se puedan comprar online.
#Carrefour: Alimentación, productos de hogar, tecnología y electrónica.
#MediaMarkt: Tecnología y electrónica.
#PCComponentes: Tecnología, informática y electrónica.
#</stores>'''



state_description = {
    "Hello": "Saludo",

    "Product": '''La consulta es del tipo Product si:
  * Es una consulta directa sobre un producto.
  * Es una confirmación de una de las opciones ofrecidas en una la lista de ideas.''',

    "Ideas": '''Petición de ideas de productos:
  * Regalos
  * Resolver situaciones
  * Cubrir una necesidad
  * Solucionar un problema''',

    "NoProduct": 'Todas las órdenes o peticiones que no son consultas sobre productos o ideas de productos. Por ejemplo, generar textos, canciones, imágenes, etc.',

    "Complaint": "Queja",

    "System": "Consulta sobre tí, aisha, o el sistema con el que habla, cambiar configuración, aspectos de su cuenta de usuario, etc.",

    "Other": "Otro tipo de mensaje que no coincide con ninguna de las anteriores."}

state_goals = {
    "Hello": "Devuelve el saludo. Aprovecha para presentarte si no lo has hecho ya.",

    "Product": PROMPT_STORES + '''
Paso 1. NLP_Query
  Describe de forma resumida y completa la búsqueda de producto que pide el usuario.
  No añadas texto redundante del estilo "El usuario busca..."
  Si la descripción es tan vaga que no permite generar una NLP_Query, explica en Chat porqué
  no has podido buscar todavía y salta al paso 5.
  
Paso 2. Seleccionar tiendas
  Dado NLP_Query, decide en qué tiendas online de la lista 'stores' buscar.
  Si no hay ninguna tienda en la que puedas buscar, explica en Chat porqué
  no has podido buscar todavía y salta al paso 5.
  Chat = Explica al usuario qué estás buscando y en qué tiendas.
  
Paso 3. API_Queries
  Para cada tienda seleccionada, genera una o varias queries para buscar en su API.
  Requerimientos de las queries de API:
   1. La query debe incluir las palabras clave que mejor definen el producto buscado.
   2. Todas las palabras clave incluídas en una query deben considerarse unidas por AND.
      Si hay palabras clave que no se pueden considerar unidas por AND, genera varias queries.
   3. No incluyas las características del producto que se quieren evitar.
   4. No incluyas datos numéricos comparativos (por ejemplo, mayor que, menor que).
   5. Incluye números sólo cuando sean exactos (por ejemplo, talla 42, 3GB de RAM o niño de 9 años).
  El formato JSON de 'queries' es el siguiente:
  queries: [ {store: Text, query: Text} ]

Paso 4. AI_Filter   
  AI_Filter = Las peticiones en NLP_Query que no se han podido incluir en API_Queries. Indica también si es necesario
  reordenar los resultados si has hecho más de una query de API o si el usuario lo ha pedido. Si no hay que hacer nada
  con los resultados de API_Queries, déjalo en blanco.

Paso 5. Details
  Details = Pide al usuario más detalles para refinar la búsqueda o para ampliarla.
    Cada pregunta debe tener un campo 'question' con el texto de la pregunta y más de una respuesta posible en 'options'.
       En el campo 'type' escribe el tipo de respuesta que esperas del usuario. Puede ser 'check', 'radio', 'range' o 'text'.
         El tipo 'check' se usa para preguntas con respuestas múltiples,
         'radio' para preguntas con una sola respuesta,
         'range' para preguntas con un rango de valores (por ejemplo, precio, tamaño, etc.) y
         'text' para preguntas abiertas.
       En el campo 'options' escribe una lista de opciones posibles para la respuesta del usuario.
         No añadas opciones que son conjuntos de opciones anteriores.
         No añadas opciones como Otros o Ninguna de las anteriores.
         En las respuestas tipo 'range', añade los valores mínimo y máximo siempre que sea posible y los valores más típicos.
  El formato JSON de 'details' es el siguiente:
  details = [ {
        question: Text,
        type: Text,
        options: [ { name: Text } ]
  } ]

Paso 6
  Genera la respuesta en formato JSON válido con la siguiente estructura:
{ chat: $Chat,
  summary: $NLP_Query,
  queries: $Queries,
  filter: $AI_Filter,
  details: $Details
}

''',

    "Ideas": '''
Tu objetivo es generar una lista de ideas de productos que puedan ayudar a resolver la
consulta del usuario. Pueden ser productos concretos, combinaciones de productos,
productos de diferentes categorías, etc.

1. Pide los detalles que creas necesarios para entender bien la consulta.
2. Ofrece productos o combinaciones de productos que pueden ayudar a resolver la consulta del usuario.
3. Sé creativa con las respuestas y da explicaciones cortas de porqué crees que los productos que recomiendas resuelven la consulta del usuario.
4. No escribas explicaciones demasiado largas, intenta ser concisa y clara.
5. No devuelvas el saludo, ya os habéis saludado antes.
''',

    "NoProduct": '''
Responde al usuario que no puedes ayudarle con eso porque eres una asistente de compras online y que si tiene alguna otra
consulta sobre productos que se pueden comprar online, estás aquí para ayudarle''',

    "Complaint": '''
Explica al usuario que has recibido su queja y que la vas a tratar con el equipo''',
    
    "System": '''
Explícale al usuario que no puedes ayudarle con eso y que si tiene alguna otra
consulta, estás aquí para ayudarle con lo que necesite.''',

    "Other": '''
Responde al usuario que no puedes ayudarle con eso porque eres una asistente de compras online y que si tiene alguna otra
consulta sobre productos que se pueden comprar online, estás aquí para ayudarle'''
}

PROMPT_SET_TITLE = '''Pon un título a la conversación de 'chat_history' sin nombrar a Aisha ni al usuario ni al bot.
Puedes utilizar emojis UTF-8 al final del título. Devuelve sólo el título en una sola línea.'''


JAVASCRIPT_GOOGLE_ADS = '''
<!-- Event snippet for Visualització de la pàgina conversion page -->
<script>
  gtag('event', 'conversion', {
      'send_to': 'AW-16939841099/fq9TCJbV8KwaEMvsxY0_',
      'value': 1.0,
      'currency': 'EUR'
  });
</script>
'''

JAVASCRIPT_GOOGLE_ADS_CLICK = '''
<!-- Event snippet for Click en producte conversion page
In your html page, add the snippet and call gtag_report_conversion when someone clicks on the chosen link or button. -->
<script>
function gtag_report_conversion(url) {
  var callback = function () {
    if (typeof(url) != 'undefined') {
      window.location = url;
    }
  };
  gtag('event', 'conversion', {
      'send_to': 'AW-16939841099/TMdGCNGQobYaEMvsxY0_',
      'value': 5.0,
      'currency': 'EUR',
      'event_callback': callback
  });
  return false;
}
</script>
'''


def set_titles():
    print("Setting titles...")
    # get all chats from cache
    chats = caches.CacheChat()
    all_chats = chats.get_all_chats()
    rpm = 0
    new_titles = []
    for chat in all_chats:
        if chat['state'] == 'CLOSED' and not isinstance(chat['title'], str):
            chatbot = Chatbot(chat_id=chat['id'])
            title = chatbot.set_title()
            if title:
                new_titles.append([chat['id'], title])
                print(f"{chat['id']} - Title: {title}")
                rpm += 1
                if rpm % 5 == 0:
                    time.sleep(5)

    return new_titles


def remove_not_interesting_chats():
    print("Removing not interesting chats...")
    # get all chats from cache
    chats = caches.CacheChat()
    all_chats = chats.get_all_chats()
    for chat in all_chats:
        if chat['state'] == 'CLOSED':
            chatbot = Chatbot(chat_id=chat['id'])
            if not chatbot.is_chat_interesting():
                print(f"Removing chat {chat['id']}")
                chats.remove_chat(chat['id'])


def get_interesting_chats(number=0, selection='LAST'):
    # get all chats from cache
    chats = caches.CacheChat()
    all_chats = chats.get_all_chats()
    if selection == 'LAST':
        random.shuffle(all_chats)
        # TODO: order chats by date instead of random
    elif selection == 'NEWEST':
        all_chats = sorted(all_chats, key=lambda x: x['date_last'], reverse=True)
    chat_list = []
    for chat in all_chats:
        if isinstance(chat['title'], str) and chat['title'] != '':
            print(f"Chat: {chat['id']} - {chat['title']}")
            chat_url = '/chat?chat_id=' + chat['id']
            chat_list.append({'title': chat['title'], 'url': chat_url})
        if number and len(chat_list) >= number:
            break
    return chat_list


def get_chat_state(chat_id):
    chat = caches.CacheChat()
    chat = chat.get_chat(chat_id)
    if chat:
        return chat['state']
    return None


# close chats that are in state ACTIVE and have not been active for more than 1 hour
def close_inactive_chats():
    print("Closing inactive chats...")
    # get all chats from cache
    chats = caches.CacheChat()
    all_chats = chats.get_all_chats()
    for chat in all_chats:
        if chat['state'] == 'ACTIVE' and 'date_last' in chat:
            # note date_last is a string ('%Y-%m-%d %H:%M:%S')
            last_active = chat['date_last']
            minutes = (datetime.now() - datetime.strptime(last_active, '%Y-%m-%d %H:%M:%S')).total_seconds() / 60
            if minutes > 60:
                print(f"Closing chat {chat['id']}")
                chat['state'] = 'CLOSED'
                chats.cache_chat(chat)


# generate the HTML code for the list of products.
def gen_html_product_list(products):
    cache_out_links = caches.CacheOutLinks()
    for product in products:
        if 'url' in product:
            link_id = 'AMZ' + product['id']
            cache_out_links.cache_out_link(product['url'], link_id=link_id)
            product['out_link'] = '/out/' + link_id
            product['link_id'] = link_id

    html = ''

    for product in products:
        #print(product)
        if 'price' not in product:
            product['price'] = ''
        if 'url' in product and 'name' in product and 'image' in product and 'price' in product:
            html += '            <li class="product">\n'
            html += '                <div class="header">\n'
            html += f'                    <a href="{product["url"]}" target="_blank" onclick="return OutLinkClick(\'{product["link_id"]}\');"><img class="product-img" src="{product["image"]}" alt="{product["name"]}" /></a>\n'
            html += '                </div>\n'
            html += '                <div class="product-footer">\n'
            title_str = product['name']
            if len(product['name']) > 50:
                title_str = product['name'][:50] + '...'

            html += f'                    <h3 class="product-name">\n'
            html += f'                        <a href="{product["url"]}" target="_blank" onclick="return OutLinkClick(\'{product["link_id"]}\');"  alt="{product["name"]}">{title_str}</a>\n'
            html += '                    </h3>\n'
            html += f'                    <p class="product-price">{product["price"]}</p>\n'
            if 'score' in product:
                html += f'                    <p class="product-comment">{int(product["score"]*10)}\n'
                if 'comment' in product:
                    html += f' - {product["comment"]}\n'
                html += '                    </p>\n'
                # html += '                    <p class="product-cat">\n'
                # html += '                        Sale!!\n'
                # html += '                    </p>\n'

            html += '                </div>\n'
            html += '            </li>\n'

    return html


def gen_html_from_markdown(markdown_text):
    html = markdown.markdown(markdown_text)
    return html


def filter_non_utf8_characters(text):
    return text.encode('utf-8', 'ignore').decode('utf-8')


def gen_html_from_json_details(details):
    html = ''
    print('Details:')
    print(details)
    if details:
        for detail in details:
            if 'question' in detail:
                question_id = detail['question_id']
                html += f'<div class="question" id="div-{question_id}">\n'
                html += f'<p>{detail["question"]}</p>\n'
                if 'type' in detail and 'options' in detail:
                    if detail['type'] == 'check':
                        for option in detail['options']:
                            option_name = option['name']
                            id_elem = caches.gen_id(4)
                            html += f'<input type="checkbox" id="{id_elem}" name="{option_name}" onclick="checkOption(\'{id_elem}\', \'{option_name}\', \'tag-{question_id}-{id_elem}\');">\n'
                            html += f'<label for="{id_elem}">{option["name"]}</label>\n'
                    elif detail['type'] == 'radio' or detail['type'] == 'range':
                        for option in detail['options']:
                            id_elem = caches.gen_id(4)
                            html += f'<input type="radio" id="{id_elem}" name="{question_id}" value="{option["name"]}">\n'
                            html += f'<label for="{id_elem}">{option["name"]}</label>\n'
                            html += f'<script>\n'
                            html += f'''    document.getElementById("{id_elem}").addEventListener("change", function() {{
                            var prev_tag = document.getElementById("tag-{question_id}");
                            if (prev_tag) {{
                                prev_tag.remove();
                            }} 
                            checkOption("{id_elem}", "{option["name"]}", "tag-{question_id}");
                            }});\n'''
                            html += f'</script>\n'
                    elif detail['type'] == 'text':
                        pass
                # on click, delete div-{question_id}
                html += f'<button class="delete-button" id="delete-{question_id}" onclick="document.getElementById(\'div-{question_id}\').remove();">X</button></div>\n'
    return html


def gen_html_tabs(ids, titles, list_id=1, loading=True):
    html = '<div class="tabrow-stores">\n'
    buttons_ids = []
    aisha_button_id = None
    for i in range(len(ids)):
        button_id = f'tab-stores-{ids[i]}-{list_id}'
        if titles[i] == 'Aisha' or titles[i] == 'aisha':
            aisha_button_id = button_id
        html += f'    <button class="tab-stores" id="{button_id}"'
        if (loading and i == 0) or (not loading and i == 1):
            if aisha_button_id and aisha_button_id == button_id:
                html += ' style="background-color:rgb(175, 238, 238)"'
            else:
                html += ' style="background-color:#FFF"'
        html += f' onclick="openTab_{list_id}(\'{button_id}\', \'products-container-{ids[i]}-{list_id}\')">{titles[i]}'
        if loading:
            html += f'&nbsp;<div class="lds-dual-ring" id="loading-{ids[i]}-{list_id}"></div>'
        html += '</button>\n'
        buttons_ids.append(button_id)
    html += '</div>\n'

    # script openTab
    html_script = '<script>\n'
    html_script += f'function openTab_{list_id}(button_id, product_container_id) {{\n'
    container_str = '"' + '", "'.join([f'products-container-{ids[i]}-{list_id}' for i in range(len(ids))]) + '"'
    html_script += f'    var i;\n'
    html_script += f'    const container_ids = [{container_str}];\n'
    html_script += f'    for (i = 0; i < container_ids.length; i++) {{\n'
    html_script += f'        document.getElementById(container_ids[i]).style.display = "none";\n'
    html_script += f'    }}\n'
    html_script += f'    document.getElementById(product_container_id).style.display = "block";\n'

    buttons_str = '"' + '", "'.join(buttons_ids) + '"'
    html_script += f'    const tab_ids = [{buttons_str}];\n'
    html_script += '''
        for (i = 0; i < tab_ids.length; i++) {
            document.getElementById(tab_ids[i]).style.background = "#f1f1f1";
        }
        document.getElementById(button_id).style.background = "#FFF";'''
    if aisha_button_id:
        html_script += f'''
        if (button_id == "{aisha_button_id}") {{
            document.getElementById(button_id).style.background = "rgb(175, 238, 238)";
        }}
'''
    html_script += '''
    }
    </script>'''

    return html_script + html


def gen_html_products_loading_script(query_id, list_id=1):
    html = f'''
    <script>
        $(document).ready(function() {{
            $.get("/product-list?query_id={query_id}", function(data) {{
                $("#product-list-{query_id}-{list_id}").html(data);
                document.getElementById("loading-{query_id}-{list_id}").style.display = "none";
                openTab_{list_id}("tab-stores-{query_id}-{list_id}", "products-container-{query_id}-{list_id}");
            }});
        }});
    </script>
    '''
    return html

def gen_html_products_container(query_id, list_id=1, head=True, display=True):
    if head:
        display_str = '' if display else ' style="display:none"'
        html = f'''
        <div class="container" id="products-container-{query_id}-{list_id}"{display_str}> 
            <div class="sub-container">
                <ul class="product-container" id="product-list-{query_id}-{list_id}">
        '''
    else:
        html = '</ul></div></div>'

    return html


def first_time_tag(tag, chat_history):
    # check if tag is in chat history
    for msg in chat_history:
        if msg['role'] == 'aisha' and 'tag' in msg['message']:
            if msg['message']['tag'] == tag:
                return False
    return True


# Pydantic Output Models
class ClassifyOutput(BaseModel):
    tag: str = Field(description="The classification tag for the user query")


class DetailOption(BaseModel):
    name: str = Field(description="The name of the option")


class DetailQuestion(BaseModel):
    question: str = Field(description="The question to ask the user")
    type: str = Field(description="Type of response: 'check', 'radio', 'range', or 'text'")
    options: List[DetailOption] = Field(description="List of possible options for the answer")


class StoreQuery(BaseModel):
    store: str = Field(description="The store name (e.g., Amazon)")
    query: str = Field(description="The search query for the store API")


class ManageMessagesOutput(BaseModel):
    chat: str = Field(description="The response message to the user")
    summary: Optional[str] = Field(default=None, description="NLP query describing the product search")
    queries: Optional[List[StoreQuery]] = Field(default=None, description="List of store queries")
    filter: Optional[str] = Field(default=None, description="AI filter for refining results")
    details: Optional[List[DetailQuestion]] = Field(default=None, description="Questions to ask user for refinement")
    action: Optional[str] = Field(default=None, description="Any action to perform")


class TitleOutput(BaseModel):
    title: str = Field(description="The title for the conversation")


class ProductScore(BaseModel):
    id: str = Field(description="Product ID")
    score: float = Field(description="Score between 0 and 1")
    comment: str = Field(description="Brief explanation (max 5 words)")


class FilterProductsOutput(BaseModel):
    products: List[ProductScore] = Field(description="List of products with scores")


# DSPy Signatures
class ClassifySignature(dspy.Signature):
    """Classify user query into predefined categories."""
    prompt: str = dspy.InputField()
    output: ClassifyOutput = dspy.OutputField()


class ManageMessagesSignature(dspy.Signature):
    """Process user messages and generate appropriate responses with structured output."""
    prompt: str = dspy.InputField()
    output: ManageMessagesOutput = dspy.OutputField()


class SetTitleSignature(dspy.Signature):
    """Generate a title for the conversation."""
    prompt: str = dspy.InputField()
    output: TitleOutput = dspy.OutputField()


class FilterProductsSignature(dspy.Signature):
    """Filter and score products based on requirements."""
    prompt: str = dspy.InputField()
    output: FilterProductsOutput = dspy.OutputField()


class Chatbot:
    def __init__(self, session=None, chat_id=None, user_id=1):
        self.session = session
        self.amz = amazon_api.AmazonAPI()
        self.bot_queries = caches.CacheQueries()
        self.cache = caches.CacheChat()
        
       
        # Initialize DSPy modules
        self.classify_module = dspy.Predict(ClassifySignature)
        self.manage_messages_module = dspy.Predict(ManageMessagesSignature)
        self.set_title_module = dspy.Predict(SetTitleSignature)
        self.filter_products_module = dspy.Predict(FilterProductsSignature)
        
        not_found = False
        if chat_id:
            self.chat_id = chat_id
            chat = self.cache.get_chat(chat_id)
            if chat and (chat['user_id'] == user_id or chat['permission'] == 'PUBLIC'):
                self.chat_history = self.cache.get_chat_history(chat_id)
            else:
                print("Chat not found or not allowed")
                # TODO: gestionar aquest error. per ara en creo un de nou com si no hagues dit chat_id
                not_found = True
        if not chat_id or not_found:
            self.chat_id = self.cache.new_chat(user_id=user_id, permission='PUBLIC')
            self.chat_history = self.cache.get_chat_history(self.chat_id)

    def get_chat_id(self):
        return self.chat_id

    def is_chat_interesting(self):
        chat_history = self.chat_history.get_history()
        # at least one message should be tag as Product or Ideas
        interesting = False
        for msg in chat_history:
            if msg['role'] == 'aisha' and 'tag' in msg['message']:
                if msg['message']['tag'] in ['Product', 'Ideas']:
                    interesting = True
                    break
        return interesting

    def set_title(self):
        chat = self.cache.get_chat(self.chat_id)
        if 'title' in chat and isinstance(chat['title'], str) and chat['title'] != '':
            return False

        if not self.is_chat_interesting():
            return False

        chat_context_history = self.get_context_history()
        prompt = PROMPT_SET_TITLE
        chat_history_str = '\n'.join(chat_context_history)
        prompt += f'<chat_history>\n{chat_history_str}\n</chat_history>\n'
        logger.log(logging.INFO, '<system>\n' + prompt + '\n</system>')
        
        # Use DSPy
        response = self.set_title_module(prompt=prompt)
        title = response.output.title
        
        logger.log(logging.INFO, '<bot>\n' + title + '\n</bot>')
        # take out any \n in title
        title = title.replace('\n', '')
        chat['title'] = title
        self.cache.cache_chat(chat)
        return title

    def get_title(self):
        chat = self.cache.get_chat(self.chat_id)
        if 'title' in chat and isinstance(chat['title'], str) and chat['title'] != '':
            return chat['title']
        return None

    def generate_prompt_head(self, user_input, chat_history):
        prompt = PROMPT_GENERAL
        chat_history_str = '\n'.join(chat_history)
        prompt += f'<chat_history>\n{chat_history_str}\n</chat_history>\n'
        prompt += f'<user_input>\n{user_input}\n</user_input>\n'
        return prompt

    def generate_prompt_classify(self, user_input, chat_history):
        prompt = self.generate_prompt_head(user_input, chat_history)
        prompt += 'Clasifica la consulta del usuario en "user_input" en una de las siguientes categorías:\n'
        # for state in state_outputs[chat_state] + ['Other']:
        for state in state_description.keys():
            #prompt += f'* {state_description[state]}. TAG: {state}\n'
            prompt += f'# TAG: {state}\n* {state_description[state]}\n\n'

        prompt += "\nResponde con una sola palabra con el tag correspondiente.\n"

        return prompt

    def generate_prompt(self, chat_state, user_input, chat_history):
        prompt = self.generate_prompt_head(user_input, chat_history)
        # prompt += f'<chat_state>\n{chat_state}\n</chat_state>\n'
        prompt += f'<goals>\n{state_goals[chat_state]}</goals>\n'
        prompt += 'Sigue las instrucciones de "goals" utilizando la información de "chat_history" y "user_input".\n'
        return prompt

    def classify_query(self, user_input, chat_history):
        prompt = self.generate_prompt_classify(user_input, chat_history)

        logger.log(logging.INFO, '<system>\n' + prompt + '\n</system>')
        
        # Use DSPy
        response = self.classify_module(prompt=prompt)
        tag = response.output.tag
        
        logger.log(logging.INFO, '<bot>\n' + tag + '\n</bot>')

        # remove \n from the response
        tag = tag.replace('\n', '')
        if 'TAG: ' in tag:
            tag = tag.split('TAG: ')[1]

        return tag

    def manage_messages(self, chat_state, user_input, chat_history):
        prompt = self.generate_prompt(chat_state, user_input, chat_history)

        logger.log(logging.INFO, '<system>\n' + prompt + '\n</system>')
        
        # Use DSPy
        response = self.manage_messages_module(prompt=prompt)
        output = response.output
        
        # Convert Pydantic model to dict
        r = output.model_dump()
        
        logger.log(logging.INFO, '<bot>\n' + json.dumps(r, ensure_ascii=False) + '\n</bot>')

        return r

    def filter_products(self, products, filter, summary):
        simplified = []
        product_by_ID = {}
        for product in products:
            simple = {}
            simple['id'] = product['id']
            for tag in ['name', 'description', 'price']:
                if tag in product:
                    simple[tag] = product[tag]
            simplified.append(simple)
            product_by_ID[product['id']] = product

        #p_str = json.dumps(simplified, indent=2, ensure_ascii=False).encode('utf-8')
        p_str = f'{simplified}'
        prompt = '''Dada la lista de productos en 'products', comprueba si cumplen los requerimientos de 'filter' y 'summary'.
        Devuelve una lista en JSON con la 'id' del producto evaluado y una puntuación en el campo 'score'. Añade un
        campo 'comment' con una breve explicación de la puntuación máximo 5 palabras.
        La puntuación calculala de la siguiente manera:
        * Los productos que puedes asegurar que cumplen con todos los requerimientos, tienen puntuación de 1
        * Los productos que puedes asegurar que no cumplen alguno de los requerimientos, puntualos con un 0.
        * El resto de productos, puntualos entre 0.1 y 0.9 en función de lo bien que cumplen los requerimientos.
        La respuesta debe ser sólo un JSON, sin ningún otro texto.
        '''
        prompt += f"\n<products>\n{p_str}\n</products>\n"
        prompt += f"\n<summary>\n{summary}\n</summary>\n"
        prompt += f"\n<filter>\n{filter}\n</filter>\n"
        logger.log(logging.INFO, '<system>\n' + prompt + '\n</system>')
        
        # Use DSPy
        response = self.filter_products_module(prompt=prompt)
        response_json = [p.model_dump() for p in response.output.products]
        
        logger.log(logging.INFO, '<bot>\n' + json.dumps(response_json, ensure_ascii=False) + '\n</bot>')
        print(json.dumps(response_json, ensure_ascii=False))

        for p in response_json:
            if p['id'] in product_by_ID:
                product_by_ID[p['id']]['score'] = p['score']
                product_by_ID[p['id']]['comment'] = p['comment']

        for p in products:
            if 'score' not in p:
                p['score'] = 0

        # Remove products with Score 0
        products = [p for p in products if p['score'] > 0.0]

        # Order products by 'Score'
        products = sorted(products, key=lambda x: x['score'], reverse=True)

        return products

    def get_context_history(self):
        chat_history = self.chat_history.get_history()
        context_history = []
        for msg in chat_history:
            context_history.append(f"{msg['role']}: {msg['message']['chat']}")
            if 'details' in msg['message']:
                details = msg['message']['details']
                if isinstance(details, list):
                    for detail in details:
                        context_history.append(f"{detail['question']}")
                        if 'options' in detail:
                            for option in detail['options']:
                                context_history.append(f"* {option['name']}")
                else:
                    context_history.append(f"{details}")
        return context_history

    def chatbot_response(self, user_input):
        chat_history = self.get_context_history()
        self.chat_history.append_history('user', {'chat': user_input})

        tag = self.classify_query(user_input, chat_history)

        if tag in ["Hello", "Product", "Ideas", "NoProduct", "Complaint", "System"]:
            chat_state = tag
            self.chat_state = chat_state
            r = self.manage_messages(chat_state, user_input, chat_history)
            r['tag'] = tag

            response = gen_html_from_markdown(r["chat"])

            if 'queries' in r and r['queries'] and len(r['queries']):
                print(r)
                api_queries = []
                for query in r['queries']:
                    if 'store' in query and query['store'] == 'Amazon':
                        api_query = self.amz.search(query['query'])
                        api_queries.append(api_query['id'])
                        query['id'] = api_query['id']

                list_id = caches.gen_id(length=3)
                bot_query = self.bot_queries.search_query(summary=r['summary'])
                if not bot_query:
                    bot_query = {'id': caches.gen_id(), 'dataset_id': caches.gen_id(), 'api_query_id': ':'.join(api_queries),
                                 'filter': r['filter'] if 'filter' in r else '', 'summary': r['summary'], 'status': 'RUNNING'}
                    self.bot_queries.cache_query(bot_query)
                print(f"Bot Query: {bot_query}")
                print(f"API Queries: {':'.join(api_queries)}")
                print(f"Filter: {bot_query['filter']}")
                print(f"Summary: {bot_query['summary']}")

                loading = True if bot_query['status'] != 'SUCCEEDED' else False

                html_bot_results = self.gen_html_loading_search(bot_query['id'], list_id=list_id, loading=loading,
                                                                display=True)  # bot
                r['bot_query_id'] = bot_query['id']
                r['list_id'] = list_id
                r['api_query_id'] = ':'.join(api_queries)

                response += html_bot_results
                # TODO: Arreglar aixo, ho he tret perque peta
                #if first_time_tag(tag, self.chat_history.get_history() and self.chat_state == 'ACTIVE'):
                #    response += JAVASCRIPT_GOOGLE_ADS

            if 'details' in r and r['details']:
                if isinstance(r['details'], dict) or isinstance(r['details'], list):
                    for detail in r['details']:
                        detail['question_id'] = caches.gen_id(4)
                    details_html = gen_html_from_json_details(r['details'])
                else:
                    details_html = gen_html_from_markdown(r['details'])
            else:
                details_html = ''


            response += details_html

            self.chat_history.append_history('aisha', r)
            return response

        else:
            answer = "Lo siento pero no entiendo tu pregunta. Soy una asistente de compras online ¿Puedo ayudarte en algo?"
            r = {'chat': answer, 'action': 'Goodbye', 'tag': tag}
            self.chat_history.append_history('aisha', r)
            chat_state = "Goodbye"
            #session['chat_state'] = chat_state
            #session['chat_history'] = []
            return answer

    def get_product_list(self, query_id):
        print(f'Getting product list for query {query_id}')
        query = self.amz.get_query(query_id)
        html = '<p>Algo ha salido mal haciendo la búsqueda, disculpa las molestias</p>'
        if query:
            # Es query de API
            products = self.amz.get_query_results(query_id)
            if products and len(products) > 0:
                html = gen_html_product_list(products)
                print(f'Returning results for API query {query_id} ({len(products)} products)')
            else:
                html = '<p>No se han encontrado productos para la búsqueda</p>'
        else:
            # Es query de bot
            query = self.bot_queries.get_query(query_id)
            if query:
                if query['status'] == 'SUCCEEDED':
                    products = self.bot_queries.get_products(query['dataset_id'])
                    if products:
                        html = gen_html_product_list(products)
                        print(f'Returning results for BOT query {query_id} ({len(products)} products)')
                        #print(html)

                elif query['status'] in ['READY', 'RUNNING']:
                    if ':' in query['api_query_id']:
                        api_ids = query['api_query_id'].split(':')
                    else:
                        api_ids = [query['api_query_id']]
                    products = []
                    for api_id in api_ids:
                        ret = self.amz.get_query_results(api_id)
                        if ret:
                            products += ret
                    if products and len(products) > 0:
                        print(products)
                        # AI filter if needed
                        if 'filter' in query: # and query['filter'] != '':
                            filtered_products = self.filter_products(products, query['filter'], query['summary'])
                            if len(filtered_products) > 0:
                                self.bot_queries.cache_products(filtered_products, query['dataset_id'])
                                query['status'] = 'SUCCEEDED'
                                html = gen_html_product_list(filtered_products)
                                print(f'Returning results for BOT query {query_id} ({len(products)} products)')
                            else:
                                print("fail 1")
                                query['status'] = 'FAILED'
                                # return just APIs products
                                html = gen_html_product_list(products)
                        else:
                            print("No filter")
                            html = gen_html_product_list(products)
                            self.bot_queries.cache_products(products, query['dataset_id'])
                            query['status'] = 'SUCCEEDED'
                            #caches.cache_html_by_dataset_id(query['dataset_id'], html)
                            print(f'Returning results for BOT query {query_id}')
                    else:
                        print("fail 2")
                        # TODO: gestionar error. No hi ha productes d'Amazon.
                        query['status'] = 'FAILED'
                        html = '<p>No se han encontrado productos para la búsqueda</p>'
                    self.bot_queries.cache_query(query)

        return html

    # return HTML with javascript to show a loading message while the search is being done.
    # Includes a jQuery get of /get-product-list with query_id
    def gen_html_loading_search(self, query_id, list_id=1, display=True, loading=True):
        html = ''
        if loading:
            html += gen_html_products_loading_script(query_id, list_id)

        html += gen_html_products_container(query_id, list_id, head=True, display=display)

        if loading:
            html += '<li class="product"><div class="loading-products">Loading&#8230;</div></li>'
            html += '<li class="product"><div class="loading-products">Loading&#8230;</div></li>'
            html += '<li class="product"><div class="loading-products">Loading&#8230;</div></li>'
            html += '<li class="product"><div class="loading-products">Loading&#8230;</div></li>'
        else:
            html += self.get_product_list(query_id)

        html += gen_html_products_container(query_id, list_id, head=False)

        return html

    def get_chat_history(self, index):
        chat_history = self.chat_history.get_history()
        if not index or int(index) <= 0 or int(index) > len(chat_history):
            return {'next': 0, 'role': 'aisha', 'msg': 'No chatbot found', 'has_content': False}
        index = int(index)
        message = chat_history[index-1]
        role = message['role']
        if role == 'aisha':
            answer = message['message']
            response = gen_html_from_markdown(answer['chat'])
            html_lists = ''
            #if 'queries' in answer and len(answer['queries']):
            #    print("Has queries")
            if 'bot_query_id' in answer:
                list_id = answer['list_id']
                bot_loading = True
                print(f"Bot query ID: {answer['bot_query_id']}")
                # check if query status is SUCCEEDED
                query = self.bot_queries.get_query(answer['bot_query_id'])
                if query and 'status' in query and query['status'] == 'SUCCEEDED':
                    bot_loading = False

                html_lists = self.gen_html_loading_search(answer['bot_query_id'], list_id=list_id,
                                                           loading=bot_loading,  display=True)
            details = ''
            if 'details' in answer and answer['details']:
                if isinstance(answer['details'], dict) or isinstance(answer['details'], list):
                    for detail in answer['details']:
                        if 'question_id' not in detail:
                            detail['question_id'] = caches.gen_id(4)
                    details += gen_html_from_json_details(answer['details'])
                else:
                    details += gen_html_from_markdown(answer['details'])
            response += html_lists + details
        else:
            response = message['message']['chat']

        next = index + 1
        if next > len(chat_history):
            next = 0

        return {'next': next, 'role': role, 'msg': response, 'has_content': True}



if __name__ == "__main__":
    #chat_id = "v878n92xq4pwgj0w"
    #chatbot = Chatbot(chat_id=chat_id)
    #title = chatbot.set_title()
    #print(title)
    remove_not_interesting_chats()
    #set_titles()
    exit(0)
    #main_loop()
    #prova_analitza_html()
    #create_templates()

    query = "reloj digital de pulsera con brújula, barómetro y termómetro"
    summary = "El usuario busca un reloj digital de pulsera con brújula, barómetro y termómetro. Que sea pequeño."
    #products = amazon_search(query)
    #products = filter_products(products, {'Summary': summary})
    products = json.loads(open("products.json", "r").read())
    print(f'{len(products)} productos encontrados para la búsqueda "{query}":')
    print(products)
    html = gen_html_product_list(products)
    # save the html to a file
    with open("products.html", "w") as f:
        f.write(html)
    
