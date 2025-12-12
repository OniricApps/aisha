import chat


def chats_maintenance():
    chat.close_inactive_chats()
    chat.remove_not_interesting_chats()
    new_titles = chat.set_titles()
    if len(new_titles):
        txt = 'Nous chats:\n'
        for chat_id, title in new_titles:
            txt += f'{title} - https://aisha-on.com/chat?chat_id={chat_id}\n'
        # save in logs new_chats.txt
        with open('logs/new_chats.txt', 'w', encoding='UTF-8') as f:
            f.write(txt)


if __name__ == '__main__':
    chats_maintenance()
