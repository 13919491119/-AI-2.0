bind = '0.0.0.0:8000'
workers = 2
worker_class = 'uvicorn.workers.UvicornWorker'
preload_app = False
accesslog = '-'
errorlog = '-'
loglevel = 'info'
timeout = 60
