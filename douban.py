import os
import requests
from jinja2 import FileSystemLoader, Environment
from pyquery import PyQuery as pq

from utils import log


def _initialized_environment():
    # 创建一个加载器, jinja2 会从这个目录中加载模板
    loader = FileSystemLoader('templates')
    # 用加载器创建一个环境, 有了它才能读取模板文件
    e = Environment(loader=loader)
    return e


class MyTemplate:
    env = _initialized_environment()

    @classmethod
    def render(cls, filename, **kwargs):
        t = cls.env.get_template(filename)
        return t.render(**kwargs)


class Model():
    def __repr__(self):
        name = self.__class__.__name__
        properties = ('{}=({})'.format(k, v) for k, v in self.__dict__.items())
        s = '\n<{} \n  {}>'.format(name, '\n  '.join(properties))
        return s


class Movie(Model):
    def __init__(self):
        self.name = ''
        self.other = ''
        self.score = 0
        self.quote = ''
        self.cover_url = ''
        self.ranking = 0


def get(url, filename):
    """
    缓存, 避免重复下载网页浪费时间
    """
    folder = 'cached'
    # 建立 cached 文件夹
    if not os.path.exists(folder):
        os.makedirs(folder)

    path = os.path.join(folder, filename)
    if os.path.exists(path):
        with open(path, 'rb') as f:
            s = f.read()
            return s
    else:
        # 发送网络请求, 把结果写入到文件夹中
        r = requests.get(url)
        with open(path, 'wb') as f:
            f.write(r.content)
            return r.content


def movie_from_div(div):
    e = pq(div)

    m = Movie()
    m.name = e('.title').text()
    m.other = e('.other').text()
    m.score = e('.rating_num').text()
    m.quote = e('.inq').text()
    m.cover_url = e('img').attr('src')
    m.ranking = e('.pic').find('em').text()
    return m


def save_cover(movies):
    for m in movies:
        filename = '{}.jpg'.format(m.ranking)
        get(m.cover_url, filename)


def cached_page(url):
    filename = '{}.html'.format(url.split('=', 1)[-1])
    page = get(url, filename)
    return page


def movies_from_url(url):
    page = cached_page(url)
    # html 流实例化为 Pyquery 对象
    e = pq(page)
    items = e('.item')
    movies = [movie_from_div(i) for i in items]
    save_cover(movies)
    return movies


def save_html_str(html_str):
    """
    缓存, 避免重复下载网页浪费时间
    """
    folder = 'visualising'
    # 建立 cached 文件夹
    if not os.path.exists(folder):
        os.makedirs(folder)

    bytes = html_str.encode()
    path = os.path.join(folder, 'visualising.html')
    with open(path, 'wb') as f:
        f.write(bytes)
        return html_str


def visualize_movies(movies):
    html = MyTemplate.render('index.html', movies=movies)
    save_html_str(html)


def main():
    top_250 = []
    for i in range(0, 250, 25):
        url = 'https://movie.douban.com/top250?start={}'.format(i)
        movies = movies_from_url(url)
        print('top250 movies', movies)
        top_250.extend(movies)
    log(len(top_250))
    visualize_movies(top_250)

if __name__ == '__main__':
    main()
