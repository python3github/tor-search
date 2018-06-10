#!/usr/bin/env python3
"""
Краулер (паук) для сети tor. Собирает на страницах ссылки (внешние и внутринние),
 а так же html-теги (title, h1, h2, h3, h4, h5, h6, lang)
"""

from multiprocessing.dummy import Pool as ThreadPool
import urllib.request
from urllib.request import urlopen
from urllib.parse import urlparse
from urllib.parse import urlunparse
import time
import csv
import sys
import gc
from bs4 import BeautifulSoup
import re
from user_agent import generate_user_agent
import resource
import socket
import socks


TIME_START = time.time()
REGEX_FOR_ONION = '(?:(?:http|https|HTTP|HTTPS)\:\/\/)?(?:\/\/)?[a-zA-Z0-9\.\-\_\:\@\%]{16,}\.onion\/?[a-zA-Zа-яА-ЯёЁ0-9\№\{\}\.\?\/\-\_\=\#\&\%\:\~\+\@\(\)\;\,\'\"\!\$]*'  # регулярное выражение для поиска ссылок на домен .onion в тексте страниц (не среди html-тегов)
PATTERN = re.compile(REGEX_FOR_ONION)        # компилируем регулярное выражение
NUMBER_OF_THREADS = 50 # количество потоков (количество ссылок для запроса) можно увеличить до 50, больше могут быть ошибки
# файлы, указанные ниже, будут созданы в папке откда запускается программа
FILE_ALL_LINKS = 'all_links.csv'             # сюда сохраняются все ссылки найденные среди html-тегов, отсюда же берутся ссылки для дальнейшей работы программы
FILE_VISITED_LINKS = 'visited_links.csv'     # сюда сохраняются собранные html-теги со страниц которые посетили
FILE_INDEX_START = 'index_start.txt'         # сюда сохраняется индекс на ссылки с которого начнет работу программа при следующем старте
FILE_ERROR = 'error.csv'                     # сохраняются ошибки возникшие во время работы
FILE_DOMAINS = 'domains_counter.csv'         # сюда сохраняются доменны, а также счетчик сколько ссылок принадлежат этому доменну
FILE_LINKS_FROM_TEXT = 'links_from_text.txt' # сюда сохраняются ссылки найденные в тексте страниц, а не среди html-тегов. После проверки на правильность ссылки из этого файла можно добавить в файл all_links.csv


def csv_max_size():
    """
    Это код нужен чтобы при чтении .csv файла большого размера не возникало ошибки по причине лимита размера файла.
    """
    SYS_MAX_SYZE = sys.maxsize
    DECREMENT = True
    # decrease the SYS_MAX_SYZE value by factor 10 as long as the OverflowError occurs.
    while DECREMENT:
        DECREMENT = False
        try:
            csv.field_size_limit(SYS_MAX_SYZE)
        except OverflowError:
            SYS_MAX_SYZE = int(SYS_MAX_SYZE/10)
            DECREMENT = True


def set_open_file_limit_up_to():
    """
    Эта функция увеличивает лимит дескрипторов открытых файлов,
    чтобы избежать ошибки: OSError: [Errno 24] Too many open files:
    """
    limit=65536
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    limit = max(soft, limit)
    limit = min(limit, hard)
    while limit > soft:
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (limit, hard))
            break
        except ValueError:
            limit -= 256


def create_connection(address, timeout=None, source_address=None):
    """
    Этот код нужен для подключения к сети tor
    """
    sock = socks.socksocket()
    sock.connect(address)
    return sock


def connection_tor():
    """
    Этот код нужен для подключения к сети tor
    """
    socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
    # patch the socket module
    socket.socket = socks.socksocket
    socket.create_connection = create_connection


def func_links_for_thread_pool(i_stop, all_links_list, list_links_for_thread_pool, domain_count):
    """
    Готовим список новых ссылок для функции thread_pool()
    """
    i_start = i_stop
    bad_site = ['btctic74pykkotsy.onion', 'archivecrfip2lpi.onion'] # список плохих сайтов (утечка памяти)
    # страницы которые не будем открывать
    not_url3 = [".rm", ".gz", ".7z", ".xz", ".bz"]
    not_url4 = [".avi", ".mp3", ".mp4", ".flv", ".mpg", ".swf", ".svg", ".bmp", ".jpg", ".fb2",
                ".pdf", ".mkv", ".ogv", ".odt", ".doc", ".dll", ".png", ".wmv", ".wav", ".mov",
                ".3gp", ".ogg", ".mid", ".tgz", ".jar", ".tar", ".bz2", ".zip", ".gif", ".rar",
                ".exe", ".bin", ".apk", ".csv", ".msi", ".xls", ".ppt", ".ape", ".ac3", ".waw",
                ".wma", ".m4a", ".aac", ".ico", ".raw", ".wmw", ".mts", ".vob", ".ini", ".bat",
                ".iso", ".mds", ".mdf", ".vdf", ".img", ".daa", ".vcd", ".nrg", ".isz", ".cr2",
                ".eps", ".shs", ".xps", ".all", ".azw", ".cbz", ".cbr"]
    not_url5 = [".epub", ".jpeg", ".webm", ".opus", ".djvu", ".docx", ".mobi", ".xlsx", ".pptx",
                ".flac", ".ttif", ".mpeg", ".gzip", ".azw3"]
    not_url6 = [".accdb"]
    # страницы которые будем открывать
    in_url4 = ['.htm', '.xht', '.wml', '.sht', '.php', '.txt']
    in_url5 = ['.html', '.xhtm', '.stml', '.shtm', '.phtm', '.php5', '.php4', '.php3', '.mspx', '.fcgi']
    in_url6 = ['.xhtml', '.shtml', '.rhtml', '.phtml', '.jhtml', '.dhtml']
    while len(list_links_for_thread_pool) < NUMBER_OF_THREADS:
        if i_stop < len(all_links_list):
            url = all_links_list[i_stop]
            i_stop += 1
            url_parse = urlparse(url)
            if url_parse.scheme == 'http' or url_parse.scheme == 'https':
                if url_parse.path == '' or url_parse.path == '/' or (url_parse.path[-4:] in in_url4) or (url_parse.path[-5:] in in_url5) or (url_parse.path[-6:] in in_url6):
                    if (url_parse.query[-3:].lower() not in not_url3) and (url_parse.query[-4:].lower() not in not_url4) and (url_parse.query[-5:].lower() not in not_url5) and (url_parse.query[-6:].lower() not in not_url6):
                        if (url_parse.netloc not in bad_site) and (domain_count.get(url_parse.netloc, 0) < 2000): # сравниваем счетчик сохраненных ссылок на доменн
                            link = urlunparse((url_parse.scheme, url_parse.netloc, url_parse.path, url_parse.params, url_parse.query, url_parse.fragment))     # создаем полную ссылку
                            if link not in list_links_for_thread_pool:
                                list_links_for_thread_pool.append(link)
        else:
            i_start = 0
            i_stop = 0
            break
    return i_start, i_stop, list_links_for_thread_pool


def thread_pool(list_links_for_thread_pool):
    """
    Функция получает ссылки и обробатывает их в многопоточном режиме. 
    """ 
    results = []
    error = None
    pool = ThreadPool(len(list_links_for_thread_pool))           
    results = pool.map(get_html, list_links_for_thread_pool)
    pool.close()
    pool.join()
    return results


def get_html(url):
    """
    Функция получает url, а возвращает содержимое веб-страницы либо сообщение об ошибке.
    """
    error = None
    html = None
    try:        
        headers = {"User-Agent": generate_user_agent()}
        req = urllib.request.Request(url, None, headers)
        with urlopen(req) as fio:
            html = fio.read()
    except Exception as err:
        html = None
        error = (time.ctime(), 'get_html', err, url)
    return url, html, error


def results_work(results, visited_url, all_links_list, write_links_list, error, all_links_from_text):
    """
    обрабатываем результат многопоточного запуска функции thread_pool()
    """
    for line in results:
        if line[3] != None and line[1] is None:        # если есть ссылки и нет ошибок
            tag = line[2]                              # помещаем в список ссылку и соответствующие ей теги(title, h1, h2, ...)
            visited_url.append([line[0], tag.get('lang', 'None'), tag.get('title', 'None'), tag.get('h1', 'None'), tag.get('h2', 'None'), tag.get('h3', 'None'), tag.get('h4', 'None'), tag.get('h5', 'None'), tag.get('h6', 'None')])   # переносим теги из словаря
            for url in line[3]:
                if str(url) not in all_links_list:     # если ссылку не сохранили ранее, то
                    all_links_list.append(str(url))    # сохраняем найденные на странице, среди html-тегов, ссылки
                    write_links_list.append(str(url))  # создаем список ссылок для записи в файл
        if line[4] != None and len(line[4]) > 0:       # проверяем есть ли ссылки найденные в тексте (не из html-тегов) 
            for link in line[4]:
                if link not in all_links_from_text:
                    all_links_from_text.append(link)   # сохраняем найденные в тексте ссылки (не из html-тегов)
        else:       # если работа завершилась ошибкой, то сохраняем информацию об ошибке
            if line[1] != None:
                error.append(line[1])
    return visited_url, all_links_list, write_links_list, error, all_links_from_text


def url_domain_count(domain_count, links_list):
    """
    Счетчик ссылок для каждого доменна.
    """
    for line in links_list:
        url_parse = urlparse(line)        
        domain_count[url_parse.netloc] = domain_count.get(url_parse.netloc, 0) + 1  # сохряняем счетчик доменов
    return domain_count


def get_soup_links(soup, url):
    """
    Функция получает содержимое страницы, а возвращает список найденых ссылок, либо сообщение об ошибке.
    """
    links = []
    error = None
    try:
        for link in soup.findAll("a"):
            if "href" not in link.attrs:
                continue
            elif link.attrs['href'] is not None:
                href_url_parse = urlparse(link.attrs['href'])  #разбиваем url-ссылку на состовляющие
                if href_url_parse.netloc == "" and href_url_parse.path != "":  # если ссылка внутрення
                    url_parse = urlparse(url)
                    url_un_parse = urlunparse((url_parse.scheme, url_parse.netloc, href_url_parse.path, href_url_parse.params, href_url_parse.query, href_url_parse.fragment))     #создаем полную ссылку
                    links.append(url_un_parse.replace(chr(173), ''))#удаляем символ "Место возможного переноса" (или "Мягкий дефис")
                elif href_url_parse.netloc[-6:] == ".onion":
                    url_un_parse = link.attrs['href']
                    links.append(url_un_parse.replace(chr(173), ''))#удаляем символ "Место возможного переноса" (или "Мягкий дефис")
    except Exception as err:
        links = None
        error = (time.ctime(), 'get_soup_links', err, url)
    return links, error


def search_links_text(url, soup):
    """
    Функция ищет ссылки в тексте страницы, а не среди тегов. Файл с найденными ссылками (links_from_text.txt)
    необходимо обработать в ручном режиме и добавить правильные ссылки в файл all_links.csv
    """
    links_from_text = []
    error = None
    try:
        text = soup.find("body").get_text()    
        res = [link.strip() for link in PATTERN.findall(text)]
        for line in res:
            if line not in links_from_text:
                links_from_text.append(line)
    except Exception as err:
        links_from_text = None
        error = (time.ctime(), 'search_links_text', err, url)
    return links_from_text, error


def tag_dict(soup, url):
    """
    Функция получает содержимое страницы, а возвращает теги (title, h1, h2, h3, h4, h5, h6, lang)
    """
    dict_tag = dict()
    error_tag = None
    lang_site = 'None'
    try:
        for tag in ["title", "h1", "h2", "h3", "h4", "h5", "h6"]:
            tag_val_dict = []
            for line in soup.find_all(tag):
                html_text = line.get_text()
                tag_val_dict.append(html_text.strip())
            if tag_val_dict:
                dict_tag[tag] = tag_val_dict
        lang_site = soup.html.get("lang") if soup.html.get("lang") else soup.html.get("xml:lang") # получаем язык сайта
        if lang_site == '':
            lang_site = 'None'
        dict_tag["lang"] = lang_site 
    except Exception as err:
        dict_tag = {"title": "None", "h1": "None", "h2": "None", "h3": "None", "h4": "None", "h5": "None", "h6": "None", "lang": "None"}
        error_tag = (time.ctime(), 'tag_dict', err, url)
    return dict_tag, error_tag


def get_links(url, html, error_get_html):
    """
    Функция получает url-ссылку, а возвращает список ссылок найденых по этому url,
    сообщение об ошибке, заголовок страницы, и сам этот url.
    """
    result_get_links = []
    links = None
    links_from_text = None
    error = error_get_html
    dict_tag = None
    error_tag_dict = None
    error_search_links_text = None
    soup = None
    try:
        if html:
            soup = BeautifulSoup(html, "lxml")
            if soup:
                links, error = get_soup_links(soup, url)
                dict_tag, error_tag_dict = tag_dict(soup, url)
                links_from_text, error_search_links_text = search_links_text(url, soup)
    except Exception as err:
        error = (time.ctime(), 'get_links', err, url)
    if error is None:
        error = error_tag_dict
    if error is None:
        error = error_search_links_text    
    result_get_links.append(url)
    result_get_links.append(error)
    result_get_links.append(dict_tag)
    result_get_links.append(links)
    result_get_links.append(links_from_text)
    return result_get_links


def write_file(file_name, write_data):
    """
    Функция получает имя файла и данные которые надо в него записать.
    """
    if file_name == FILE_ALL_LINKS:
        with open(FILE_ALL_LINKS, "r") as fio:
            read_urls = [row[1] for row in csv.reader(fio)]
        with open(FILE_ALL_LINKS, "at") as fio:
            writer = csv.writer(fio)
            for link in write_data:
                if link not in read_urls:
                    writer.writerow((time.ctime(), link))

    if file_name == FILE_ERROR:
        if write_data:
            with open(FILE_ERROR, "r") as fio:
                read_errors = [row[1:] for row in csv.reader(fio)]
            with open(FILE_ERROR, "at") as fio:
                writer = csv.writer(fio)
                for line in write_data:
                    if line[1:] not in read_errors:
                        writer.writerow(line)

    if file_name == FILE_VISITED_LINKS:
        with open(FILE_VISITED_LINKS, "r") as fio:
            read_visited_urls = [row[1] for row in csv.reader(fio)]
        with open(FILE_VISITED_LINKS, "at") as fio:
            writer = csv.writer(fio)
            for line in write_data:
                if line[0] not in read_visited_urls:
                    writer.writerow((time.ctime(), line[0], line[1], line[2], line[3], line[4], line[5], line[6], line[7], line[8]))

    if file_name == FILE_INDEX_START:
        with open(FILE_INDEX_START, "w") as fio:
            fio.write(write_data)

    if file_name == FILE_DOMAINS:
        with open(FILE_DOMAINS, "w") as fio:
            writer = csv.writer(fio)
            for key, val in sorted(write_data.items(), key=lambda x: x[1], reverse=True):
                writer.writerow((key, val))

    if file_name == FILE_LINKS_FROM_TEXT:
        with open(FILE_LINKS_FROM_TEXT, "r") as fio:
            read_urls = [line[:-1] for line in fio]
        with open(FILE_LINKS_FROM_TEXT, "a") as fio:
            for link in write_data:
                if link not in read_urls:
                    fio.write(link + '\n')


def main():
    """
    Главная функция, из неё постоянно в цикле запускаются все остальные функции.
    """
    list_links_for_thread_pool = ["http://dirnxxdraygbifgc.onion",
                     "http://wiki5kauuihowqi5.onion/",
                     "http://torlinkbgs6aabns.onion/",
                     "http://directoryvi6plzm.onion/",
                     "http://zqktlwi4fecvo6ri.onion/wiki/index.php/Main_Page" 
                    ]           # список ссылок для функции map()

    all_links_list = ["http://dirnxxdraygbifgc.onion",
                      "http://wiki5kauuihowqi5.onion/",
                      "http://torlinkbgs6aabns.onion/",
                      "http://directoryvi6plzm.onion/",
                      "http://zqktlwi4fecvo6ri.onion/wiki/index.php/Main_Page" 
                     ]          # список всех ссылок

    error = []                  # список для сообщений об ошибках
    write_links_list = []       # ссылки которые будут переданны для записи в файл
    i_start = 0                 # начальный индекс ссылок для запроса
    i_stop = 0                  # конечный индекс ссылок для запроса
    counter_for_write_file = 0  # данный счетчик используется при записи данных в файл
    visited_url = []            # список обработанных ссылок
    all_links_from_text = []    # ссылки найденные в тексте, а не среди html-тегов
    time_write = time.time()    # отсчёт времени для записи данных в файлы
    now_time = time.time()

    file_name_list=['all_links.csv', 'visited_links.csv', 'index_start.txt', 'domains_counter.csv', 'links_from_text.txt', 'error.csv']
    for file_name in file_name_list:
        open(file_name, 'a').close()    # создаем необходимые файлы, если их нету. 
  
    my_ip = urlopen("http://icanhazip.com/").read()
    print("ip до tor:    ", my_ip[: -1], "\n", "="*30) # ip до tor

    csv_max_size() # Эта функция нужна чтобы при чтении .csv файла большого размера не возникало ошибки по причине лимита размера файла.
    set_open_file_limit_up_to()  #увеличиваем лимит дескрипторов открытых файлов: URLError(OSError(24, 'Too many open files')
    connection_tor()    # функция осуществляет подключение к сети tor

    my_tor_ip = urlopen("http://httpbin.org/ip").read()
    print("ip после tor: ", my_tor_ip[11: -3], "\n", "="*30) # ip после tor

    with open(FILE_ALL_LINKS, "r") as fio:       # создаем список всех ссылок
        all_links_list = [row[1] for row in csv.reader(fio)]

    with open(FILE_DOMAINS, 'r') as fio:         # создаем словарь доменов и их счетчик
        domain_count = {row[0]: int(row[1]) for row in csv.reader(fio)}

    if len(all_links_list) > 1:
        with open(FILE_INDEX_START, "r") as fio: # при старте получаем сохраненный индекс на ссылки на которых закончили
            i_start = int(fio.read())
        i_stop = i_start + NUMBER_OF_THREADS
                                                 # формируем список ссылок для функции thread_pool
        i_start, i_stop, list_links_for_thread_pool = func_links_for_thread_pool(i_stop, all_links_list, list_links_for_thread_pool, domain_count)

    print("\nДля корректного завершения программы нажмите 'Ctrl+c' и дождитесь сохранения данных в файл!\n")

    while True:
        try:
            results = []
            time_loc_time = time.localtime()
            time_str = str(time_loc_time[3]) + ":" + str(time_loc_time[4]) + ":" + str(time_loc_time[5])
            print("%s || время работы: %s сек || общее количество ссылок: %s || доменнов: %s || обрабатываются ссылки с %s по %s" % (time_str, int(time.time() - TIME_START), len(all_links_list), len(domain_count), i_start, i_stop))

            gc.collect()                   # сборщик мусора (нужен для очистки памяти компьютера)
            
            results_thread_pool = thread_pool(list_links_for_thread_pool)

            gc.collect()
            
            results_get_links = []
            for row in results_thread_pool:                                                            
                results_get_links.append(get_links(row[0], row[1], row[2])) 

            gc.collect()

            visited_url, all_links_list, write_links_list, error, all_links_from_text = results_work(results_get_links, visited_url, all_links_list, write_links_list, error, all_links_from_text) # обрабатываем результаты работы               
            
            gc.collect()
            domain_count = url_domain_count(domain_count, write_links_list)  # счетчик ссылок для каждого доменна
                                             
            gc.collect()
                       
            list_links_for_thread_pool = []# формируем ссылки для thread_pool()
            i_start, i_stop, list_links_for_thread_pool = func_links_for_thread_pool(i_stop, all_links_list, list_links_for_thread_pool, domain_count)
            if i_start == 0:
                counter_for_write_file = 0

            gc.collect()

            old_time = now_time              # на случай если очень быстро будет открываться много соединений,
            now_time = time.time()        
            if (now_time - old_time) < 20:   # чтобы избежать: URLError(OSError(24, 'Too many open files'),)
                time.sleep(20)               # OSError: [Errno 24] Too many open files: 'all_links.csv'
                now_time = time.time()
            
            # чтобы не делать запись после каждой итерации (это может привести к преждевременному износу носителя данных), сохраняемся после определенного количества ссылок или через определенный интервал времени 
            links_count_for_write = 1000 
            # если количество новых ссылок больше 1000 или прошло указанное количество секунд, то сохраняем данные в файлы
            if (len(all_links_list) // links_count_for_write > counter_for_write_file) or ((time.time() - time_write) > 3600):
                counter_for_write_file = len(all_links_list) // links_count_for_write
                write_file(FILE_ALL_LINKS, write_links_list)
                write_file(FILE_ERROR, error)
                write_file(FILE_VISITED_LINKS, visited_url)                
                write_file(FILE_DOMAINS, domain_count)
                write_file(FILE_LINKS_FROM_TEXT, all_links_from_text)
                write_file(FILE_INDEX_START, str(i_start))
                visited_url = []
                write_links_list = []
                error = []
                all_links_from_text = []
                time_write = time.time()

        except KeyboardInterrupt:
            print("\n*********************\nПодождите, идет сохранение данных в файл!\n*********************\n")
            write_file(FILE_ALL_LINKS, write_links_list)
            write_file(FILE_ERROR, error)
            write_file(FILE_VISITED_LINKS, visited_url)            
            write_file(FILE_DOMAINS, domain_count)
            write_file(FILE_LINKS_FROM_TEXT, all_links_from_text)
            write_file(FILE_INDEX_START, str(i_start))
            break


if __name__ == "__main__": 
    main()
