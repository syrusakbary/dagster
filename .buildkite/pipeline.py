import os
import yaml

DOCKER_PLUGIN = "docker#v3.2.0"

TIMEOUT_IN_MIN = 15

# This should be an enum once we make our own buildkite AMI with py3
class SupportedPython:
    V3_7 = "3.7"
    V3_6 = "3.6"
    V3_5 = "3.5"
    V2_7 = "2.7"


SupportedPythons = [
    SupportedPython.V3_7,
    SupportedPython.V3_6,
    SupportedPython.V3_5,
    SupportedPython.V2_7,
]

PY_IMAGE_MAP = {
    SupportedPython.V3_7: "python:3.7.3-stretch",
    SupportedPython.V3_6: "python:3.6.8-stretch",
    SupportedPython.V3_5: "python:3.5.7-stretch",
    SupportedPython.V2_7: "python:2.7.16-stretch",
}

IMAGE_VERSION_MAP = {
    SupportedPython.V3_7: "3.7.3",
    SupportedPython.V3_6: "3.6.8",
    SupportedPython.V3_5: "3.5.7",
    SupportedPython.V2_7: "2.7.16",
}

TOX_MAP = {
    SupportedPython.V3_7: "py37",
    SupportedPython.V3_6: "py36",
    SupportedPython.V3_5: "py35",
    SupportedPython.V2_7: "py27",
}

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
LIBRARY_PATH = os.path.join(SCRIPT_PATH, '..', 'python_modules/libraries/')
LIBRARY_MODULES = set(os.listdir(LIBRARY_PATH))

# Skip these two. dagster-gcp is handled separately by gcp_tests() below, dagster-pyspark does not
# have tests
LIBRARY_MODULES -= {'dagster-gcp', 'dagster-pyspark'}


class StepBuilder:
    def __init__(self, label):
        self._step = {"label": label, "timeout_in_minutes": TIMEOUT_IN_MIN}

    def run(self, *argc):
        self._step["commands"] = map(lambda cmd: "time " + cmd, argc)
        return self

    def base_docker_settings(self):
        return {"shell": ["/bin/bash", "-xeuc"], "always-pull": True}

    def on_python_image(self, ver, env=None):
        settings = self.base_docker_settings()
        settings["image"] = PY_IMAGE_MAP[ver]
        if env:
            settings['environment'] = env

        self._step["plugins"] = [{DOCKER_PLUGIN: settings}]

        return self

    def on_integration_image(self, ver, env=None):
        settings = self.base_docker_settings()
        # version like dagster/buildkite-integration:py3.7.3
        settings["image"] = "dagster/buildkite-integration:py" + IMAGE_VERSION_MAP[ver]
        # map the docker socket to enable docker to be run from inside docker
        settings["volumes"] = ["/var/run/docker.sock:/var/run/docker.sock"]

        if env:
            settings['environment'] = env

        self._step["plugins"] = [{DOCKER_PLUGIN: settings}]
        return self

    def with_timeout(self, num_minutes):
        self._step["timeout_in_minutes"] = num_minutes
        return self

    def with_retry(self, num_retries):
        self._step["retry"] = {'automatic': {'limit': num_retries}}
        return self

    def build(self):
        return self._step


def wait_step():
    return "wait"


def python_modules_tox_tests(directory, prereqs=None, env=None):
    label = directory.replace("/", "-")
    tests = []
    for version in SupportedPythons:
        coverage = ".coverage.{label}.{version}.$BUILDKITE_BUILD_ID".format(
            label=label, version=version
        )
        tox_command = []
        if prereqs:
            tox_command += prereqs
        tox_command += [
            "pip install tox;",
            "cd python_modules/{directory}".format(directory=directory),
            "tox -e {ver}".format(ver=TOX_MAP[version]),
            "mv .coverage {file}".format(file=coverage),
            "buildkite-agent artifact upload {file}".format(file=coverage),
        ]

        env_vars = ['AWS_DEFAULT_REGION'] + (env or [])

        builder = (
            StepBuilder("{label} tests ({ver})".format(label=label, ver=TOX_MAP[version]))
            .run(*tox_command)
            .on_python_image(version, env_vars)
        )
        tests.append(builder.build())

    return tests


def airline_demo_tests():
    tests = []
    for version in SupportedPythons:
        coverage = ".coverage.airline-demo.{version}.$BUILDKITE_BUILD_ID".format(version=version)
        tests.append(
            StepBuilder('airline-demo tests ({version})'.format(version=TOX_MAP[version]))
            .run(
                "cd examples",
                # Build the image we use for airflow in the demo tests
                "./build_airline_demo_image.sh",
                "mkdir -p /home/circleci/airflow",
                # Run the postgres db. We are in docker running docker
                # so this will be a sibling container.
                "docker-compose stop",
                "docker-compose rm -f",
                "docker-compose up -d",
                # Can't use host networking on buildkite and communicate via localhost
                # between these sibling containers, so pass along the ip.
                "export DAGSTER_AIRLINE_DEMO_DB_HOST=`docker inspect --format '{{ .NetworkSettings.IPAddress }}' airline-demo-db`",
                "pip install tox",
                "apt-get update",
                "apt-get -y install libpq-dev",
                "tox -c airline.tox -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
            )
            .on_integration_image(version)
            .build()
        )
    return tests


def events_demo_tests():
    tests = []
    for version in SupportedPythons:
        coverage = ".coverage.events-demo.{version}.$BUILDKITE_BUILD_ID".format(version=version)
        tests.append(
            StepBuilder('events-demo tests ({version})'.format(version=TOX_MAP[version]))
            .run(
                "mkdir -p /tmp/dagster/events",
                "pushd scala_modules",
                "sbt events/assembly",
                "cp ./events/target/scala-2.11/events-assembly-0.1.0-SNAPSHOT.jar /tmp/dagster/events/",
                "popd",
                "pushd examples",
                "pip install tox",
                "tox -c event.tox -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
            )
            .on_integration_image(
                version, ['AWS_SECRET_ACCESS_KEY', 'AWS_ACCESS_KEY_ID', 'AWS_DEFAULT_REGION']
            )
            .build()
        )
    return tests


def airflow_tests():
    tests = []
    for version in SupportedPythons:
        coverage = ".coverage.dagster-airflow.{version}.$BUILDKITE_BUILD_ID".format(version=version)
        tests.append(
            StepBuilder("dagster-airflow tests ({ver})".format(ver=TOX_MAP[version]))
            .run(
                "cd python_modules/dagster-airflow/dagster_airflow_tests/test_project",
                "./build.sh",
                "mkdir -p /airflow",
                "export AIRFLOW_HOME=/airflow",
                "cd ../../",
                "pip install tox",
                "tox -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
            )
            .on_integration_image(version, ['AIRFLOW_HOME'])
            .build()
        )
    return tests


def examples_tests():
    tests = []
    for version in SupportedPythons:
        coverage = ".coverage.examples.{version}.$BUILDKITE_BUILD_ID".format(version=version)
        tests.append(
            StepBuilder("examples tests ({ver})".format(ver=TOX_MAP[version]))
            .run(
                "pushd examples",
                "pip install tox",
                "tox -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
            )
            .on_integration_image(version)
            .build()
        )
    return tests


def gcp_tests():
    # GCP tests need appropriate credentials
    creds_local_file = "/tmp/gcp-key-elementl-dev.json"

    return python_modules_tox_tests(
        "libraries/dagster-gcp",
        prereqs=[
            "pip install awscli",
            "aws s3 cp s3://${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json "
            + creds_local_file,
            "export GOOGLE_APPLICATION_CREDENTIALS=" + creds_local_file,
        ],
        env=['BUILDKITE_SECRETS_BUCKET', 'GCP_PROJECT_ID'],
    )


def dask_tests():
    tests = []
    for version in SupportedPythons:
        coverage = ".coverage.dagster-dask.{version}.$BUILDKITE_BUILD_ID".format(version=version)
        tests.append(
            StepBuilder("dagster-dask tests ({ver})".format(ver=TOX_MAP[version]))
            .run(
                "pushd python_modules/dagster-dask/dagster_dask_tests/dask-docker",
                "./build.sh " + IMAGE_VERSION_MAP[version],
                # Run the docker-compose dask cluster
                "export PYTHON_VERSION=\"{ver}\"".format(ver=IMAGE_VERSION_MAP[version]),
                "docker-compose up -d --remove-orphans",
                # hold onto your hats, this is docker networking at its best. First, we figure out
                # the name of the currently running container...
                "export CONTAINER_ID=`cut -c9- < /proc/1/cpuset`",
                r'export CONTAINER_NAME=`docker ps --filter "id=\${CONTAINER_ID}" --format "{{.Names}}"`',
                # then, we dynamically bind this container into the dask user-defined bridge
                # network to make the dask containers visible...
                r"docker network connect dask \${CONTAINER_NAME}",
                # Now, we grab the IP address of the dask-scheduler container from within the dask
                # bridge network and export it; this will let the tox tests talk to the scheduler.
                "export DASK_ADDRESS=`docker inspect --format '{{ .NetworkSettings.Networks.dask.IPAddress }}' dask-scheduler`",
                "popd",
                "pushd python_modules/dagster-dask/",
                "pip install tox",
                "tox -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
            )
            .on_integration_image(
                version, ['AWS_SECRET_ACCESS_KEY', 'AWS_ACCESS_KEY_ID', 'AWS_DEFAULT_REGION']
            )
            .with_timeout(5)
            .with_retry(3)
            .build()
        )
    return tests


if __name__ == "__main__":
    steps = [
        StepBuilder("pylint")
        .run("make install_dev_python_modules", "make pylint")
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        StepBuilder("black")
        # black 18.9b0 doesn't support py27-compatible formatting of the below invocation (omitting
        # the trailing comma after **check.opt_dict_param...) -- black 19.3b0 supports multiple
        # python versions, but currently doesn't know what to do with from __future__ import
        # print_function -- see https://github.com/ambv/black/issues/768
        .run("pip install black==18.9b0", "make check_black")
        .on_python_image(SupportedPython.V3_7)
        .build(),
        StepBuilder("docs snapshot test")
        .run(
            "pip install -r python_modules/dagster/dev-requirements.txt -qqq",
            "pip install -e python_modules/dagster -qqq",
            "pytest -vv docs",
        )
        .on_python_image(SupportedPython.V3_7)
        .build(),
        StepBuilder("dagit webapp tests")
        .run(
            "pip install -r python_modules/dagster/dev-requirements.txt -qqq",
            "pip install -e python_modules/dagster -qqq",
            "pip install -e python_modules/dagster-graphql -qqq",
            "pip install -e python_modules/dagit -qqq",
            "pip install -r python_modules/dagit/dev-requirements.txt -qqq",
            "pip install -e examples -qqq",
            "cd js_modules/dagit",
            "yarn install --offline",
            "yarn run ts",
            "yarn run jest",
            "yarn run check-prettier",
            "yarn run download-schema",
            "yarn run generate-types",
            "git diff --exit-code",
            "mv coverage/lcov.info lcov.dagit.$BUILDKITE_BUILD_ID.info",
            "buildkite-agent artifact upload lcov.dagit.$BUILDKITE_BUILD_ID.info",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
    ]
    steps += airline_demo_tests()
    steps += events_demo_tests()
    steps += airflow_tests()
    steps += dask_tests()

    steps += python_modules_tox_tests("dagster")
    steps += python_modules_tox_tests("dagit", ["apt-get update", "apt-get install -y xdg-utils"])
    steps += python_modules_tox_tests("dagster-graphql")
    steps += python_modules_tox_tests("dagstermill")

    for library in LIBRARY_MODULES:
        steps += python_modules_tox_tests("libraries/{library}".format(library=library))

    steps += gcp_tests()
    steps += examples_tests()
    steps += [
        wait_step(),  # wait for all previous steps to finish
        StepBuilder("coverage")
        .run(
            "apt-get update",
            "apt-get -qq -y install lcov ruby-full",
            "pip install coverage coveralls coveralls-merge",
            "gem install coveralls-lcov",
            "mkdir -p tmp",
            'buildkite-agent artifact download ".coverage*" tmp/',
            'buildkite-agent artifact download "lcov.*" tmp/',
            "cd tmp",
            "coverage combine",
            "coveralls-lcov -v -n lcov.* > coverage.js.json",
            "coveralls --merge=coverage.js.json",
        )
        .on_python_image(
            SupportedPython.V3_7,
            [
                'COVERALLS_REPO_TOKEN',  # exported by /env in ManagedSecretsBucket
                'CI_NAME',
                'CI_BUILD_NUMBER',
                'CI_BUILD_URL',
                'CI_BRANCH',
                'CI_PULL_REQUEST',
            ],
        )
        .build(),
    ]

    print(
        yaml.dump(
            {
                "env": {
                    "CI_NAME": "buildkite",
                    "CI_BUILD_NUMBER": "$BUILDKITE_BUILD_NUMBER",
                    "CI_BUILD_URL": "$BUILDKITE_BUILD_URL",
                    "CI_BRANCH": "$BUILDKITE_BRANCH",
                    "CI_PULL_REQUEST": "$BUILDKITE_PULL_REQUEST",
                },
                "steps": steps,
            },
            default_flow_style=False,
        )
    )
