dev:
	git submodule init
	git submodule update
	pip3 install -U pipenv
	pipenv install

update-requirements:
	pipenv lock -r > src/requirements.txt

invoke:
	sam local invoke BuildTemplateFunction -e events/buildEvent.json

invoke-sam:
	sam local invoke SamBuildTemplateFunction -e events/buildSamEvent.json

invoke-sam-bad:
	sam local invoke SamBuildTemplateFunction -e events/buildSamEventBadActor.json

invoke-powertools:
	sam local invoke BuildTemplateFunction -e events/buildPowerToolsEvent.json

start-api:
	sam local start-api

deploy:
	sam validate
	sam build
	sam deploy
