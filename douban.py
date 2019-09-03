import os
import requests
from example.commons import Faker
from jinja2 import FileSystemLoader, Environment
from pyecharts import options
from pyquery import PyQuery as pq

from utils import log

from pyecharts.charts import Bar, Scatter, Pie


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
        self.comment_num = 0
        self.director = ''
        self.lead = ''
        self.year = 0
        self.category = ''

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
    m.comment_num = int(e('.star').find('span').text().split(' ')[3].split('人')[0])

    director_lead, year_country_category = str(e('.bd').find('p').html()).split('<br/>')
    m.director = director_lead.split('导演: ')[1].split('主演')[0].split(' / ')[0]
    if '主演: ' in director_lead:
        m.lead = director_lead.split('主演: ')[1].split('...')[0].split('/')[0]

    raw_ycc = year_country_category.split('\xa0/\xa0')
    m.year = raw_ycc[0].split(' ')[-1]
    m.country = raw_ycc[1].split(' ')[0]
    m.category = raw_ycc[2].split('\n')[0]
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


def score_vs_comment_num(movies):
    scores = [m.score for m in movies[:10]]
    comment_nums = [m.comment_num for m in movies[:10]]
    c = (
        Scatter()
        .add_xaxis(scores)
        .add_yaxis("comment_nums", comment_nums)
        .set_global_opts(title_opts=options.TitleOpts(title="Score VS Comment num"))
    )
    c.render('charts/scatter.html')


def pop_best(map):
    best = ['', 0]
    for k, v in map.items():
        if v > best[1]:
            best = [k, v]
    map.pop(best[0])
    return best


def top_10_country(movies):
    map = dict()
    for m in movies:
        if m.country not in map:
            map[m.country] = 1
        else:
            map[m.country] += 1
    best_10 = dict()
    for i in range(10):
        best = pop_best(map)
        best_10[best[0]] = best[1]
    c = (
        Pie()
        .add("", [list(z) for z in zip(best_10.keys(), best_10.values())])
    )
    c.render('charts/best_country.html')


def top_10_directors(movies):
    map = dict()
    for m in movies:
        if m.director not in map:
            map[m.director] = 1
        else:
            map[m.director] += 1
    best_10 = dict()
    for i in range(10):
        best = pop_best(map)
        best_10[best[0]] = best[1]
    c = (
        Pie()
        .add("Top250 导演次数", [list(z) for z in zip(best_10.keys(), best_10.values())])
        .set_global_opts(legend_opts=options.LegendOpts(is_show=False))
        .set_series_opts(label_opts=options.LabelOpts(formatter="{b}: {c}"))
    )
    c.render('charts/best_director.html')


def top_10_leads(movies):
    map = dict()
    for m in movies:
        if m.lead not in map:
            if m.lead != '':
                map[m.lead] = 1
        else:
            if m.lead != '':
                map[m.lead] += 1
    best_10 = dict()
    for i in range(10):
        best = pop_best(map)
        best_10[best[0]] = best[1]
    c = (
        Pie()
        .add('Top250 主演次数', [list(z) for z in zip(best_10.keys(), best_10.values())])
        .set_global_opts(legend_opts=options.LegendOpts(is_show=False))
        .set_series_opts(label_opts=options.LabelOpts(formatter="{b}: {c}"))
    )
    c.render('charts/best_leads.html')


def analize(movies):
    score_vs_comment_num(movies)
    top_10_directors(movies)
    top_10_leads(movies)
    top_10_country(movies)


def main():
    top_250 = []
    for i in range(0, 250, 25):
        url = 'https://movie.douban.com/top250?start={}'.format(i)
        movies = movies_from_url(url)
        print('top250 movies', movies)
        top_250.extend(movies)
    log(len(top_250))
    visualize_movies(top_250)
    analize(top_250)


def test():
    bar = Bar()
    bar.add_xaxis(["衬衫", "羊毛衫", "雪纺衫", "裤子", "高跟鞋", "袜子"])
    bar.add_yaxis("商家A", [5, 20, 36, 10, 75, 90])
    # render 会生成本地 HTML 文件，默认会在当前目录生成 render.html 文件
    # 也可以传入路径参数，如 bar.render("mycharts.html")
    bar.render('charts/mycharts.html')


if __name__ == '__main__':
    main()
    # test()
    # scatter()