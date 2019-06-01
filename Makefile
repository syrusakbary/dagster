pylint:
	pylint -j 0 `git ls-files '*.py'` --rcfile=.pylintrc

update_doc_snapshot:
	pytest docs --snapshot-update

black:
	black examples python_modules --line-length 100 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/" -N

check_black:
	black examples python_modules --check --line-length 100 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/" -N

install_dev_python_modules:
	# NOTE: previously, we did a pip install --upgrade pip here. We have removed that and instead
	# depend on the user to ensure an up-to-date pip is installed and available. For context, there
	# is a lengthy discussion here:
	# https://github.com/pypa/pip/issues/5599

	# On machines with less memory, pyspark install will fail... see:
	# https://stackoverflow.com/a/31526029/11295366
	pip --no-cache-dir install pyspark==2.4.0

	pip install -r python_modules/dagster/dev-requirements.txt
	pip install -e python_modules/dagster
	pip install -e python_modules/dagster-graphql
	pip install -e python_modules/dagit
	pip install -r python_modules/dagit/dev-requirements.txt
	pip install -e python_modules/dagstermill
	SLUGIFY_USES_TEXT_UNIDECODE=yes pip install -e python_modules/dagster-airflow
	pip install -e python_modules/dagster-dask
	pip install -e python_modules/libraries/dagster-aws
	pip install -r python_modules/libraries/dagster-aws/dev-requirements.txt
	pip install -e python_modules/libraries/dagster-datadog
	pip install -e python_modules/libraries/dagster-gcp
	pip install -e python_modules/libraries/dagster-ge
	pip install -e python_modules/libraries/dagster-pandas
	pip install -e python_modules/libraries/dagster-slack
	pip install -e python_modules/libraries/dagster-snowflake
	pip install -e python_modules/libraries/dagster-spark
	pip install -e python_modules/libraries/dagster-pyspark
	pip install -e python_modules/libraries/dagster-pagerduty
	pip install -e python_modules/libraries/dagster-slack
	pip install -e python_modules/libraries/dagster-datadog
	pip install -e python_modules/automation
	pip install -e examples[full]
	pip install -r bin/requirements.txt

graphql:
	cd js_modules/dagit/; make generate-types

rebuild_dagit:
	cd js_modules/dagit/; yarn install && yarn build-for-python

dev_install: install_dev_python_modules rebuild_dagit

graphql_tests:
	pytest examples/dagster_examples_tests/graphql_tests/ python_modules/dagster-graphql/dagster_graphql_tests/graphql/ -s -vv
