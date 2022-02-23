dev:
	git submodule init
	git submodule update
	pip3 install -U pipenv
	pipenv install

update-requirements:
	pipenv lock -r > src/requirements.txt

invoke:
	sam local invoke -e events/buildEvent.json

start-api:
	sam local start-api
