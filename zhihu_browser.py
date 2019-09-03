import time
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options

import secret
import platform
import os

from utils import log


def add_chrome_webdriver():
    log(platform.system())
    working_path = os.getcwd()
    library = 'library'
    path = os.path.join(working_path, library)
    os.environ['PATH'] += '{}{}{}'.format(os.pathsep, path, os.pathsep)
    log(os.environ['PATH'])


def reset_cookie(browser, domain):
    browser.delete_all_cookies()
    log('before', browser.get_cookies())
    for part in secret.cookie.split('; '):
        kv = part.split('=', 1)
        d = dict(
            name=kv[0],
            value=kv[1],
            path='/',
            domain=domain,
            secure=True
        )
        log('cookie', d)
        browser.add_cookie(d)
    log('after', browser.get_cookies())


def scroll_to_end(browser):
    browser.execute_script('window.scrollTo(0, document.body.scrollHeight);')


def start_crawler(browser):
    url = "https://www.zhihu.com"
    # 先访问一个 url，之后才能设置这个域名 对应的 cookie
    browser.get('https://www.zhihu.com/404')
    reset_cookie(browser, '.zhihu.com')

    # 访问目的 URL, 有 cookie 就可以伪装登录了
    browser.get(url)
    # 滚 7 次
    count = 7
    res = set()
    while True:
        count -= 1
        if count < 0:
            break

        try:
            cards = browser.find_elements_by_css_selector('.Card.TopstoryItem')
            for card in cards:
                title = card.find_elements_by_css_selector('.ContentItem-title')
                # 这里实际上只有一个, 不过 title 默认是数组
                for i in title:
                    res.add(i.text)
        except NoSuchElementException:
            pass
        scroll_to_end(browser)

    for text in res:
        log(text)


def main():
    add_chrome_webdriver()

    o = Options()
    # o.add_argument("--headless")
    browser = webdriver.Chrome(chrome_options=o)
    try:
        start_crawler(browser)
    finally:
        browser.quit()


if __name__ == '__main__':
    main()
