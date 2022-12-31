rootdir = $(realpath .)

export PROXYX_ROUTING_CONFIG_PATH=$(rootdir)/proxyx.yaml
export PROXYX_APP_CONFIG_PATH=$(rootdir)/.env

local-up:
	./entrypoint.sh

local-install:
	python -m pip install --no-cache-dir -U -e ..

local-uninstall:
	pip uninstall -y proxyx

local-reinstall: local-uninstall local-install

docker-build:
	docker build -t proxyx .

docker-up:
	docker run --rm -p 8000:8000 proxyx
