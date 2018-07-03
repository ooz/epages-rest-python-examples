# Cleanup
clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +
	rm -rf .cache

clean_vscode:
	rm -rf .vscode

clean_pypi:
	rm -rf dist
	rm -rf epages_rest_python.egg-info

clean_all: clean clean_vscode clean_pypi

# Setup / dependencies
install_pipenv:
	pip install pipenv

install_dependencies:
	pipenv install requests
	pipenv install six
	pipenv install --dev pytest

init: install_pipenv
	pipenv --three
	make install_dependencies

init2: install_pipenv
	pipenv --two
	make install_dependencies

# Docker
docker_build:
	docker build -t oozz/beautiful-order-documents:latest .

docker_run:
	docker run --env-file ./env.list -p 8080:80 -it oozz/beautiful-order-documents:latest

docker_run_beyond:
	docker run --env-file ./env-beyond.list -p 8080:80 -it oozz/beautiful-order-documents:latest

docker_buildrun: docker_build docker_run

docker_buildrun_beyond: docker_build docker_run_beyond

docker_clean:
	docker ps -q -f status=exited | xargs --no-run-if-empty docker rm
	docker images -q -f dangling=true | xargs --no-run-if-empty docker rmi

docker_push:
	docker push oozz/beautiful-order-documents

docker_init_env:
	cp env.list.template env.list
	cp env-beyond.list.template env-beyond.list



.PHONY: clean clean_vscode clean_pypi clean_all \
install_pipenv install_dependencies init init2 \
test \
publish \
docker_build docker_run docker_run_beyond \
docker_buildrun docker_buildrun_beyond \
docker_clean docker_push docker_init_env
