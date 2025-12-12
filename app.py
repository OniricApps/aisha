import os.path
from flask import Flask, render_template, request, session
import random
import caches
import chat
import json
import cron
import stats
from datetime import datetime

VERSION = '0.7.0' # using DSPy, gemini-2.5

app = Flask(__name__)
app.secret_key = 'AISHA_ONIRICAPPS_0723'  # Replace with a secure key in production

# Save PID in logs/pid.txt
pid = os.getpid()
with open('logs/pid.txt', 'w') as f:
    f.write(str(pid))
print(f'PID: {pid}')


# To remove any cache data on reload.
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

# To log any request
@app.before_request
def log_request():
    referer = request.headers.get('Referer')
    ip_address = request.remote_addr
    if ip_address == '127.0.0.1':
        ip_address =request.headers.get('X-Forwarded-For',  request.headers.get('Client-Ip', request.remote_addr))
    session_id = session.get('ID')
    url = request.url
    date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'ip: {ip_address}, session: {session_id}, url: {url}, referer: {referer}')
    log_file = 'logs/requests-log.csv'
    if not os.path.exists(log_file):
        with open(log_file, 'w') as f:
            f.write('Date,IP,Session,URL,Referer\n')
    with open(log_file, 'a') as f:
        f.write(f'{date_str},{ip_address},{session_id},{url},{referer}\n')


@app.route('/')
def home():
    if not session.get('ID'):
        session['ID'] = str(random.randint(10000, 99999))
    chat_list = chat.get_interesting_chats(5, 'LAST')
    return render_template('index.html', last_chats=chat_list)
    #return app.redirect("/new-chat", code=302)


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')


def filter_html(text):
    return text.replace('<', '&lt;').replace('>', '&gt;')

@app.route('/new-chat')
def new_chat():
    session['ChatID'] = None
    chatbot = chat.Chatbot(session)
    chat_id = chatbot.get_chat_id()
    session['ChatID'] = chat_id
    # first message?
    first_msg = request.args.get('msg')
    if first_msg:
        first_msg = filter_html(first_msg)
        print(f'First message: {first_msg}')
        chatbot.chatbot_response(first_msg)
    # redirect to chat?chat_id=chat_id
    return app.redirect(f"/chat?chat_id={chat_id}", code=302)


@app.route('/chat')
def chat_by_id():
    chat_id = request.args.get('chat_id')
    if chat_id:
        session['ChatID'] = chat_id
    else:
        session['ChatID'] = None
        return app.redirect("/new-chat", code=302)
    chat_state = chat.get_chat_state(chat_id)
    chatbot = chat.Chatbot(chat_id=chat_id)
    if not chatbot:
        return 'Disculpa, ha habido algun error, por favor <a href="/new-chat">abre un nuevo chat</a>.'
    chat_history = []
    next = 1
    while next:
        r = chatbot.get_chat_history(next)
        next = r['next']
        if r['has_content']:
            chat_history.append(r)
    chat_title = chatbot.get_title()
    if not chat_title:
        chat_title = 'Chat'
    #if chat_state == 'CLOSED':
    #    return render_template('chat-closed.html', chat_id=chat_id, chat_state=chat_state,
    #                           chat_history=chat_history, chat_title=chat_title)
    return render_template('chat.html', chat_id=chat_id, chat_state=chat_state,
                           chat_history=chat_history, chat_title=chat_title)


# TODO: cridar al metode get en mode POST. Sino, preguntes massa llargues seran un problema
@app.route('/get')
def get_bot_response():
    userText = request.args.get('msg')
    userText = filter_html(userText)
    chat_id = request.args.get('chat_id')
    print(userText)
    # TODO: Check logging by validating Token in cookies

    # Chat ID
    if not chat_id:
        return 'Disculpa, ha habido algun error, por favor <a href="/new-chat">abre un nuevo chat</a>.'
        #if not session.get("ChatID"):
        #    chatbot = chat.Chatbot(session)
        #    chat_id = chatbot.get_chat_id()
        #else:
        #    chat_id = session["ChatID"]

    chatbot = chat.Chatbot(chat_id=chat_id)
    if not chatbot:
        chatbot = chat.Chatbot(session)
        #chats[session["ChatID"]] = chatbot
    return chatbot.chatbot_response(str(userText))


@app.route('/get-history')
def get_chat_history():
    chat_id = request.args.get('chat_id')
    index = request.args.get('index')
    chatbot = chat.Chatbot(chat_id=chat_id)
    print(f'Get history for chat_id: {chat_id}, index: {index}')
    if chatbot:
        response = chatbot.get_chat_history(index)
    else:
        response = {'next': 0, 'role': 'bot', 'msg': 'No chatbot found', 'has_content': False}
    response_json = json.dumps(response)
    print(response_json)
    return response_json


@app.route('/product-list')
def product_list():
    query_id = request.args.get('query_id')
    if query_id:
        chat_id = session["ChatID"]
        chatbot = chat.Chatbot(chat_id=chat_id)
        if not chatbot:
            return render_template('empty-product-list.html')
        return chatbot.get_product_list(query_id)
    else:
        return render_template('empty-product-list.html')


@app.route('/chats-list')
def get_chats_list():
    chats_list = chat.get_interesting_chats(0, 'NEWEST')
    return render_template('chats-list.html', chats_list=chats_list)


@app.route('/cron')
def cron_jobs():
    cron.chats_maintenance()
    return 'Cron jobs executed'

@app.route('/stats')
def stats_report():
    stats.gen_filtered_log()
    daily_array, page_views_array, referrers_array, ratios = stats.gen_daily_stats()
    max_daily = max([d['page_views'] for d in daily_array])
    max_page_views = max([d['views'] for d in page_views_array])
    max_referrer = max([d['views'] for d in referrers_array])
    max_chats = max([d['new_chats'] for d in daily_array])
    return render_template('stats.html', daily=daily_array, page_views=page_views_array,
                           referrers=referrers_array, max_daily=max_daily, max_page=max_page_views, max_chats=max_chats,
                           max_referrer=max_referrer, ratios=ratios)

@app.route('/out')
def out():
    link_id = request.args.get('link_id')
    chat_id = request.args.get('chat_id')
    cache_out_links = caches.CacheOutLinks()
    out_link = cache_out_links.get_out_link(link_id)
    if not out_link:
        print(f'Link id {link_id} not found')
        #return app.redirect("/", code=302)
        return 'Link not found'
    #return app.redirect(out_link['url'], code=302)
    print(f'{link_id} Out link: {out_link}')
    return out_link


if __name__ == '__main__':
    # Cron jobs. First call at start
    cron.chats_maintenance()

    app.run(debug=True, host='0.0.0.0', threaded=False, port=5009)
    #app.run(debug=False, host='0.0.0.0', threaded=False)
