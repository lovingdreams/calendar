SHELL := /bin/bash

env-local-setup:
	rm -rf venv
	python3 -m venv venv; \
	source venv/bin/activate; \
	pip install -r requirements.txt

run-dev:
	conda deactivate; \
	conda activate calendar; \
	pip install -r requirements.txt; \
	pip install wheel; \
	pip install git+https://workemasteradmin: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@github.com/worketeam/BaseWorke; \
	export CONFIG_PATH=common/configs/dev.cfg; \
	python manage.py makemigrations; \
	python manage.py migrate; \
	rm -rf src/static; \
	python manage.py collectstatic --noinput; \
	sudo systemctl restart calendar; \
	sudo systemctl enable workingHour_consumer; \
	sudo systemctl restart workingHour_consumer


run-local:
	source venv/bin/activate; \
	export CONFIG_PATH=common/configs/local.cfg; \
	pip install wheel; \
	pip install git+https://workemasteradmin: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@github.com/worketeam/BaseWorke; \
	python3 manage.py makemigrations; \
	python3 manage.py migrate --database=default; \
	black .; \
	python3 manage.py runserver 8000

run-stage:
	conda deactivate; \
	conda activate calendar; \
	pip install -r requirements.txt; \
	export CONFIG_PATH=common/configs/stage.cfg; \
	pip install wheel; \
	pip install git+https://workemasteradmin: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@github.com/worketeam/BaseWorke; \
	python manage.py makemigrations calendars; \
	python manage.py makemigrations; \
	python manage.py migrate; \
	rm -rf src/static; \
	python manage.py collectstatic --noinput; \
	sudo systemctl restart calendar; \
	sudo systemctl enable workingHour_consumer; \
	sudo systemctl restart workingHour_consumer

run-demo:
	conda deactivate; \
	conda activate calendar; \
	pip install -r requirements.txt; \
	export CONFIG_PATH=common/configs/demo.cfg; \
	pip install wheel; \
	pip install git+https://workemasteradmin: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@github.com/worketeam/BaseWorke; \
	python manage.py makemigrations; \
	python manage.py migrate; \
	rm -rf src/static; \
	python manage.py collectstatic --noinput; \
	sudo systemctl restart calendar; \
	sudo systemctl enable workingHour_consumer; \
	sudo systemctl restart workingHour_consumer
