
install:
	pip install -r requirements/dev.txt

serve:
	gulp

SCOPE=user_accounts intake
test:
	./manage.py test $(SCOPE) \
		--verbosity 2

test.unit:
	python -m unittest $(SCOPE) \
		-v

test.coverage:
	coverage run \
		./manage.py test $(SCOPE) \
		--verbosity 2
	coverage report -m

test.acceptance:
	python ./manage.py test tests.acceptance

test.screenshots:
	python ./manage.py test \
		tests.acceptance.test_screenshots \
		--verbosity 2

deploy.demo:
	git push -f demo HEAD:master
	heroku run --app cmr-demo python manage.py migrate

deploy.prod:
	git push prod master
	heroku run --app cmr-prod python manage.py migrate