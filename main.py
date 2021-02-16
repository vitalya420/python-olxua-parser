from OLXParser.utils import read_proxy_from_file
from OLXParser import Parser, CSVWriterThreaded

proxies = None  # read_proxy_from_file("proxylist.txt", "socks4")

parser = Parser(proxy_queue=proxies)
writer = CSVWriterThreaded("results.csv")
writer.start()


@parser.on("new")
def new_phone(phone):
    print("A new fucking phone: ", phone)
    writer.append(phone)


@parser.on("finish")
def on_finish(phone_list):
    print("Finished: ", phone_list)


urls = parser.grab_urls("https://www.olx.ua/transport/avtobusy/", 1)
print(parser.parse(urls))
