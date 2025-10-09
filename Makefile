# Celestial Nexus AI Operations Makefile

PY?=python
SHELL:=/bin/bash

.PHONY: help install deps wechat api restart-wechat restart-api encrypt-test observe self-check freeze

help:
	@echo '常用目标:'
	@echo '  make install        安装依赖+冻结版本'
	@echo '  make wechat         前台启动微信服务'
	@echo '  make api            前台启动API服务'
	@echo '  make restart-wechat 重启微信Gunicorn'
	@echo '  make restart-api    重启API Gunicorn'
	@echo '  make encrypt-test   加密模拟发送 (使用 .env.wechat)'
	@echo '  make observe        启动 Prometheus+Grafana'
	@echo '  make self-check     运行系统自检'
	@echo '  make freeze         生成 requirements-lock.txt'

install: deps freeze

deps:
	$(PY) -m pip install --upgrade pip
	pip install -r requirements.txt

freeze:
	pip freeze > requirements-lock.txt

wechat:
	./start_wechat_gunicorn.sh

api:
	./start_api_gunicorn.sh

restart-wechat:
	pkill -f 'gunicorn_wechat' || true
	./start_wechat_gunicorn.sh &

restart-api:
	pkill -f 'celestial_nexus.api:app' || true
	./start_api_gunicorn.sh &

encrypt-test:
	python simulate_encrypted_message.py 'Makefile加密测试'

observe:
	docker compose -f docker-compose.observability.yml up -d

self-check:
	bash system_self_check.sh
