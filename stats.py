import pandas as pd
import os


def clean_url(url, n_params=1):
    """
    Clean URL by removing parameters
    """
    ads = '&gclid' in url
    if '//' in url:
        url = url.split('//')[1]
    domain = url.split('/')[0]
    has_params = '?' in url
    clean_url_no_params = url
    clean_url_params = url
    if has_params:
        parts = url.split('?')
        clean_url_no_params = parts[0]
        if len(parts) > 1:
            clean_url_params = parts[0] + '?' + '&'.join(parts[1].split('&')[:n_params])


    return domain, clean_url_no_params, clean_url_params, ads


def gen_extended_log():
    """
    Generate correct log file extending columns doing some pre processing
    """
    with open('logs/requests-log.csv', 'r', encoding="utf-8") as f:
        lines = f.readlines()

    with open('logs/requests-log-correct.csv', 'w', encoding='utf-8') as f:
        f.write('Date,IP,Session,URL_base,URL_param,ADS,Ref_domain,Ref_clean_url,Ref_url\n')
        for line in lines[1:]:
            parts = line.strip().split(',')
            # some URLs may have , in the URL. if the text after coma is not None or http, it is part of the URL
            url_n_col = 3
            ref_n_col = 4

            while len(parts) > 5:
                #URL contains coma
                if parts[url_n_col+1] != 'None' and not parts[url_n_col+1].startswith('http'):
                    parts[url_n_col] += ',' + parts[url_n_col+1]
                    parts = parts[:url_n_col+1] + parts[url_n_col+2:]
                # Referer contains coma
                else:
                    parts[ref_n_col] += ','.join(parts[ref_n_col+1:])
                    break
            if len(parts) > 5:
                print(parts)
                print('A comma added somewhere?')
                continue

            if parts[3] == 'None':
                domain, clean_url_no_params, clean_url_params, ads = '', '', '', False
            else:
                domain, clean_url_no_params, clean_url_params, ads = clean_url(parts[3], n_params=1)
            if parts[4] == 'None':
                ref_domain, clean_ref_no_params, clean_ref_params, ads__ = '', '', '', False
            else:
                #print(parts[4])
                ref_domain, clean_ref_no_params, clean_ref_params, ads__ = clean_url(parts[4])

            f.write(f"{parts[0]},{parts[1]},{parts[2]},'{clean_url_no_params}','{clean_url_params}',{ads},'{ref_domain}','{clean_ref_no_params}','{parts[4]}'\n")


def filter_useless_data(logs):
    # Not interested in crawler robots. Ignore them
    # Ignore Visits from IPs that never has Session nor referer. Also, These IPs don't get css or images
    IP_list = logs['IP'].unique()
    for ip in IP_list:
        ip_logs = logs[logs['IP'] == ip]
        # no cookie and no referer means robot
        if ip_logs['Session'].isnull().all() and ip_logs['Ref_domain'].isnull().all():
            # remove this IP from logs
            logs = logs[logs['IP'] != ip]
            print(f'IP {ip} removed from logs')
        # I use to visit stats. No one else do it. remove my visits
        if ip_logs['URL_base'].str.contains('/stats').any():
            logs = logs[logs['IP'] != ip]
            print(f'IP {ip} removed from logs. Because visit /stats')

    # drop out rows that column URL_base includes "/static/"
    logs = logs[~logs['URL_base'].str.contains('/static/')]
    # remove rows when URL_base ends with '.css', '.ico', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'
    logs = logs[~logs['URL_base'].str.endswith(('.css', '.ico', '.js', '.png', '.jpg', '.jpeg', '.gif'))]

    # remove my visits from windows
    logs = logs[~logs['IP'].str.startswith('200.234.239.77')]

    return logs


def gen_filtered_log():
    gen_extended_log()
    logs = pd.read_csv('logs/requests-log-correct.csv', sep=',', quotechar="'")
    columns = ['Date', 'IP', 'Session', 'URL_base', 'URL_param', 'ADS', 'Ref_domain', 'Ref_clean_url', 'Ref_url']

    filtered_file = 'logs/requests-log-filtered.csv'
    if os.path.exists(filtered_file):
        # starts from last date of filtered_file (last value of first column)
        filtered = pd.read_csv(filtered_file, sep=',', quotechar="'")
        # sort by date
        filtered = filtered.sort_values(by='Date', ascending=False)
        last_date = pd.to_datetime(filtered.iloc[0]['Date'])
        print(f'Last date: {last_date}')
        logs = logs[logs['Date'] > last_date.strftime('%Y-%m-%d %H:%M:%S')]
        logs = filter_useless_data(logs)
        # concatenate filtered and logs
        filtered = pd.concat([filtered, logs], ignore_index=True)
        filtered.to_csv(filtered_file, sep=',', quotechar="'", index=False)
    else:
        filtered = filter_useless_data(logs)
        filtered.to_csv(filtered_file, sep=',', quotechar="'", index=False)

def gen_daily_stats():
    """
    Generate daily stats for the past 30 days
    """
    # open logs/requests.csv as dataframe
    logs = pd.read_csv('logs/requests-log-filtered.csv', sep=',', quotechar="'")
    columns = ['Date', 'IP', 'Session', 'URL_base', 'URL_param', 'ADS', 'Ref_domain', 'Ref_clean_url', 'Ref_url']
    #logs = filter_useless_data(logs)

    # for each day in the past 30 days, calculate metrics
    daily_array = []
    for i in range(30):
        date = pd.Timestamp.now().date() - pd.Timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        date_logs = logs[logs['Date'].str.startswith(date_str)]
        # remove rows when URL_base ends with '.css', '.ico', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'
        #date_logs = date_logs[~date_logs['URL_base'].str.endswith(('.css', '.ico', '.js', '.png', '.jpg', '.jpeg', '.gif'))]
        #date_logs = date_logs[~date_logs['URL_base'].str.endswith('.css')]

        page_views = date_logs.shape[0]
        unique_visitors = date_logs['IP'].nunique()
        new_chats = date_logs[date_logs['URL_base'].str.contains('/new-chat')].shape[0]
        ads = date_logs[date_logs['ADS'] == True].shape[0]
        print(f'{date_str}: {unique_visitors} unique visitors, {page_views} page views, new chats: {new_chats}, ads: {ads}')
        daily_reg = {'date': date_str, 'unique_visitors': unique_visitors, 'page_views': page_views, 'new_chats': new_chats, 'ads': ads}
        daily_array.append(daily_reg)

    # top 10 pages by page views
    page_views = {}
    page_views_array = []
    urls = logs['URL_param'].unique().tolist() + logs['URL_base'].unique().tolist()
    for url in urls:
        if '?' in url:
            page_views[url] = logs[logs['URL_param'] == url].shape[0]
        else:
            page_views[url] = logs[logs['URL_base'] == url].shape[0]
    page_views = dict(sorted(page_views.items(), key=lambda x: x[1], reverse=True))
    print('Top 10 pages:')
    for url, views in list(page_views.items())[:50]:
        print(f'{url}: {views} views')
        page_views_array.append({'url': url, 'views': views})

    # top 10 referrers by domain
    referrers = {}
    referrers_array = []
    domains = logs['Ref_domain'].unique()
    for domain in domains:
        logs_ref = logs[logs['Ref_domain'] == domain]
        #print(f"logs_ref: {logs_ref['ADS']}") # AQUI!!!!!
        # sum of rows with ADS == true
        ads = logs_ref[logs_ref['ADS'] == True].shape[0]
        views = logs_ref.shape[0]
        referrers[domain] = {'views': views, 'ads': ads}
    # sort by views
    referrers = dict(sorted(referrers.items(), key=lambda x: x[1]['views'], reverse=True))
    print('Top 20 referrers by domain')
    for referer in list(referrers.items())[:20]:
        domain = referer[0]
        views = referer[1]['views']
        ads = referer[1]['ads']
        print(f'{domain}: {views} views, {ads} ads')
        referrers_array.append({'domain': domain, 'views': views, 'ads': ads})

    print('Ratios:')
    ratios = calc_ratios(logs)

    return daily_array, page_views_array, referrers_array, ratios

def calc_ratios(logs):

    # percentage of unique visitors that start a new chat
    new_chats = 0
    with_messages = 0
    product_lists = 0
    outs_after_chat = 0
    outs_without_chat = 0
    IP_list = logs['IP'].unique()
    for ip in IP_list:
        ip_logs = logs[logs['IP'] == ip]
        if ip_logs['URL_base'].str.contains('/new-chat').any():
            new_chats += 1
            if ip_logs['URL_base'].str.contains('/get').any():
                with_messages += 1
                if ip_logs['URL_base'].str.contains('/product-list').any():
                    product_lists += 1
                    if ip_logs['URL_base'].str.contains('/out').any():
                        outs_after_chat += 1
        elif ip_logs['URL_base'].str.contains('/out').any():
            outs_without_chat += 1
    new_chat_ratio = new_chats / len(IP_list)
    with_messages_ratio = with_messages / new_chats
    get_products_ratio = product_lists / with_messages
    outs_after_chat_ratio = outs_after_chat / product_lists
    outs_without_chat_ratio = outs_without_chat / len(IP_list)
    print(f'Visitors: {len(IP_list)}, New chats: {new_chats}, With messages: {with_messages}, Product lists: {product_lists}, Outs after chat: {outs_after_chat}, Outs without chat: {outs_without_chat}')
    print(f'New chat ratio: {new_chat_ratio:.2%}')
    print(f'With messages ratio: {with_messages_ratio:.2%}')
    print(f'Get products ratio: {get_products_ratio:.2%}')
    print(f'Outs after chat ratio: {outs_after_chat_ratio:.2%}')
    print(f'Outs without chat ratio: {outs_without_chat_ratio:.2%}')

    ratios = {
            'visitors': {'total': len(IP_list), 'ratio': 1},
            'new_chats': {'total': new_chats, 'ratio': new_chat_ratio},
            'with_messages': {'total': with_messages, 'ratio': with_messages_ratio},
            'product_lists': {'total': product_lists, 'ratio': get_products_ratio},
            'outs_after_chat': {'total': outs_after_chat, 'ratio': outs_after_chat_ratio},
            'outs_without_chat': {'total': outs_without_chat, 'ratio': outs_without_chat_ratio}
    }
    # save ratios in logs/ratios.csv
    with open('logs/ratios.csv', 'w', encoding='utf-8') as f:
        f.write('Metric,Total,Ratio\n')
        for key in ratios.keys():
            f.write(f"{key},{ratios[key]['total']},{ratios[key]['ratio']:.2%}\n")

    return ratios


if __name__ == "__main__":
    gen_filtered_log()
    gen_daily_stats()
    #calc_ratios()
    #gen_monthly_stats()
