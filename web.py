# all the imports
import sqlite3, json, jinja2, os, html
import datetime
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, send_from_directory
from flask_cors import CORS, cross_origin # http://flask-cors.readthedocs.io/en/latest/
from flask_restful import reqparse, abort, Resource, Api
from contextlib import closing
from flaskext.mysql import MySQL

from myTextRank import *
import asyncio
import jpype
p = textRank()

'''
# for mongoDB
import pymongo
client = pymongo.MongoClient('mongodb://lsw:0000@ds241578.mlab.com:41578/pyeongchang')
db = client.pyeongchang
collection = db.survey  # survey backup
print('mongoDB connected...')

#-------sqlite3---------
# 라우팅 함수 내에서 선언

#-------mysql---------
mysql = MySQL()
# sungwoo local
# app.config['MYSQL_DATABASE_USER'] = 'guest'
# app.config['MYSQL_DATABASE_PASSWORD'] = '0000'
# app.config['MYSQL_DATABASE_DB'] = 'robot'
# app.config['MYSQL_DATABASE_HOST'] = 'localhost'

# real db
app.config['MYSQL_DATABASE_USER'] = 'lsw'
app.config['MYSQL_DATABASE_PASSWORD'] = 'lsw0504'
app.config['MYSQL_DATABASE_DB'] = 'olympic'
app.config['MYSQL_DATABASE_HOST'] = '10.0.1.163'
mysql.init_app(app)

# 이건 파이썬 템플릿 렌더링 위치만 변경. 지금은 앵귤러에서 다 하므로 렌더링 불필요 
# my_loader = jinja2.ChoiceLoader([
#     app.jinja_loader,
#     jinja2.FileSystemLoader('front/dist'),
# ])
# app.jinja_loader = my_loader
'''

# ANGULAR SPA쓰므로 아래 설정 반드시 필요 
app = Flask(__name__, static_url_path='',
            static_folder='front',)
            # template_folder='templates')
CORS(app, support_credentials=True)
api = Api(app)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path), 'favicon.png')

@app.route("/")
# @app.route("/dashboard")
# @app.route("/textNews")
# @app.route("/cardNews")
# @app.route("/movieNews")
def home():
    return send_from_directory(os.path.join(app.root_path, 'front'), 'index.html')    

# 뉴스주소 받기
@app.route("/news", methods=['POST'])
def news():
  # 다른 스레드 사용시엔 반드시 필요
    jpype.attachThreadToJVM()
    
    body = json.loads(request.data)
    news_url = body['news_url']
    news_doc = body['news_doc']

    # 네이버 뉴스 제외하고 url대신 본문으로 보낸경우
    if news_url is '':
      print(news_doc)
      p.article_parsed = news_doc.split('. ')
      p.title = 'have no title'
    else:
      # # 비동기로 불러오기
      # # loop = asyncio.get_event_loop()
      # # loop.run_until_complete(p.getNews(news_url))
      # # 주피터에서 사용
      # article = p.getNews(news_url)
      article = requests.get(news_url)
      p.parse(article)
    # textrank
    p.setGraph()
    p.getSummary()
    news_summ = p.getSummary()
    keywords = p.getKeyword(5)

    return json.dumps({
        'url': news_url,
        'news_title': p.title,
        'news_origin': p.article_parsed,
        'news_summ': news_summ,
        'keywords': keywords
      })
    # print(body['news_url'], p.title, '\n', p.article_parsed)
    # return json.dumps(body)

# question answring
@app.route("/query", methods=['POST'])
def query():
    body = json.loads(request.data)
    query = body['query']
    # 뉴스요약 먼저 하고 질문해야함
    try:
      res = {
        'answers': p.getAnswer(query)
      }
    except:
      res = {
        'answers': 'get news first!!'
      }

    return json.dumps(res)

'''
flask-restful api
'''
TODOS = {
    'todo1': {'task': 'build an API'},
    'todo2': {'task': '?????'},
    'todo3': {'task': 'profit!'},
}


def abort_if_todo_doesnt_exist(todo_id):
    if todo_id not in TODOS:
        abort(404, message="Todo {} doesn't exist".format(todo_id))

parser = reqparse.RequestParser()
parser.add_argument('task')


# Todo
# shows a single todo item and lets you delete a todo item
class Todo(Resource):
    def get(self, todo_id):
        abort_if_todo_doesnt_exist(todo_id)
        return TODOS[todo_id]

    def delete(self, todo_id):
        abort_if_todo_doesnt_exist(todo_id)
        del TODOS[todo_id]
        return '', 204

    def put(self, todo_id):
        args = parser.parse_args()
        task = {'task': args['task']}
        TODOS[todo_id] = task
        return task, 201


# TodoList
# shows a list of all todos, and lets you POST to add new tasks
class TodoList(Resource):
    def get(self):
        return TODOS

    def post(self):
        args = parser.parse_args()
        todo_id = int(max(TODOS.keys()).lstrip('todo')) + 1
        todo_id = 'todo%i' % todo_id
        TODOS[todo_id] = {'task': args['task']}
        return TODOS[todo_id], 201

# url here!!
api.add_resource(TodoList, '/todos')
api.add_resource(Todo, '/todos/<todo_id>')

# ---------------가상주소 리다이렉션용
# @app.route("/contents/<style>")
# def contents_style(style):
#     print('contents loaded:', style)
#     return send_from_directory(os.path.join(app.root_path, 'front/dist2'), 'news.html')    


# SPA prge refresh문제 해결용
@app.errorhandler(404)
def page_not_found(e):
    # return send_from_directory(os.path.join(app.root_path, 'front/dist'), 'index.html')    
    return "죄송합니다. 요청하신 페이지를 찾을수 없습니다.(Error: 404)"



if __name__ == '__main__':
    # print(os.path.join(app.root_path)) # C:\Users\LSW\Desktop\myTextRank
    app.run(debug=True, host='0.0.0.0', port=5000) # 이건 내부, 외부 한번에
    # app.run(debug=True, host='10.0.1.21', port=5000)
    # app.run(debug=True, host='127.0.0.1', port=5000)
    # app.run(debug=True)
