from gevent import monkey
monkey.patch_all()
import multiprocessing

#debug = True
loglevel = 'debug'
bind = '0.0.0.0:8050' #绑定与Nginx通信的端口
pidfile = 'log/gunicorn.pid'
accesslog = 'log/access.log'
errorlog = 'log/debug.log'
#daemon = True
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'gevent' #默认为阻塞模式，最好选择gevent模式
threads = 2