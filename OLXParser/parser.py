import re
from queue import Queue

import lxml.html
import requests
import typing
from bs4 import BeautifulSoup


class Parser:
    def __init__(self, urls: typing.Iterable = None,
                 proxy_queue: Queue = None):
        if urls is None:
            urls = []
        self.urls = urls
        self.proxy_queue = proxy_queue
        self.session = requests.Session()
        self.handlers = {}

    def on(self, event, handler=None):
        def set_handler(handler_):
            if callable(handler_):
                self.handlers[event] = handler_
            return handler_

        if handler is None:
            return set_handler
        set_handler(handler)

    @staticmethod
    def get_id(url):
        id_ = re.search(r"-ID[a-zA-Z0-9]+", url).group(0)[3:]
        return id_

    def get_data(self, url, **extra):
        try:
            html = self.session.get(url, **extra)
            id_ = self.get_id(url)
            token = self.grab_phone_token(html.text)
            return html, id_, token if id_ and token else None
        except requests.exceptions.ConnectionError:
            print(f"Bad proxy: {extra}")
            return None, None, None

    @staticmethod
    def grab_users_data(html):
        tree = lxml.html.fromstring(html.text)
        title = tree.xpath('//*[@id="offerdescription"]/div[1]/h1/text()')[0].strip()
        try:
            price = tree.xpath('//*[@id="offerdescription"]/div[1]/div[2]/div/strong/text()')[0].strip()
        except Exception as e:
            price = "unknown"
        try:
            name = tree.xpath('//*[@id="offeractions"]/div[3]/div[2]/div[2]/h4/a/text()')[0].strip().capitalize()
        except IndexError:
            name = ""
        address = tree.xpath('//*[@id="offeractions"]/div[4]/div[2]/div[1]/address/p/text()')[0].strip()
        return {'title': title, 'price': price, 'name': name, 'address': address}

    def grab_phone(self, id_, token, url, **extra):
        res = self.session.get(
            f"https://www.olx.ua/uk/ajax/misc/contact/phone/{id_}/?pt={token}",
            headers={'User-Agent': 'bot228', 'Referer': url},
            **extra
        )
        phone = res.json()["value"].replace(" ", '')
        for symbol in '-()':
            if symbol in phone:
                phone = phone.replace(symbol, "")
        phones = re.findall(r'[0-9]+', phone)
        formatted = self._format_phones(phones)
        return ", ".join(formatted)

    @staticmethod
    def grab_phone_token(html):
        try:
            phone_token = re.search(r"var phoneToken = '[a-zA-Z0-9]+", html).group(0)[18:]
        except AttributeError:
            return
        return phone_token

    @staticmethod
    def grab_urls(start_url, page_limit=10):
        urls = []
        for i in range(page_limit):
            current_url = start_url + f'?page={i}'
            html = requests.get(current_url).text
            soup = BeautifulSoup(html, parser='lxml', features="lxml")
            raw_urls = soup.find_all('a', class_='marginright5 link linkWithHash detailsLink')
            urls += [url["href"] for url in raw_urls]
        return urls

    def parse(self, urls=None):
        parsed = []
        urls = urls or self.urls

        if not urls or not isinstance(urls, list):
            return

        for url in urls:
            extra = self._get_extra()
            html, id_, token = self.get_data(url, **extra)
            while not id_ and token:
                extra = self._get_extra()
                data = self.get_data(url, **extra)

            user_data = self.grab_users_data(html)
            user_data["url"] = url
            user_data["phone"] = self.grab_phone(id_, token, url, **extra)
            self._handle("new", user_data)
            parsed.append(user_data)

        self._handle("finish", parsed)
        return parsed

    @staticmethod
    def _format_phones(phones):
        formatted = []
        for phone in phones:
            if phone.startswith('0'):
                phone = "38" + phone
            if phone.startswith('8'):
                phone = "3" + phone
            elif phone.startswith('+'):
                phone = phone[1:]
            formatted.append(phone)
        return formatted

    def _get_extra(self) -> dict:
        extra = {}
        if proxy := self._next_proxy():
            extra["proxies"] = proxy
        return extra

    def _handle(self, event, *args, **kwargs):
        if func := self.handlers.get(event):
            func(*args, **kwargs)

    def _next_proxy(self):
        if self.proxy_queue and not self.proxy_queue.empty():
            proxy = self.proxy_queue.get()
            return proxy
