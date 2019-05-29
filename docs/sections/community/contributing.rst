Contributing
============

If you are planning to contribute to dagster, you will need to set up a local
development environment.

Local development setup
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Install Python. Python 3.6 or above recommended.

2. Create and activate a virtualenv.

.. code-block:: console

    $ python3 -m venv dagsterenv
    $ source dagsterenv/bin/activate

3. Install yarn. If you are on macOS, this should be:

.. code-block:: console

    $ brew install yarn

4. Run the `make dev_install` at repo root. This sets up a full
   dagster developer environment with all modules and runs tests that
   do not require heavy external dependencies such as docker. This will
   take a few minutes.

.. code-block:: console

    $ make dev_install

5. Run some tests manually to make sure things are working.

.. code-block:: console

    $ pytest python_modules/dagster/dagster_tests

Have fun coding!

6. Optional: Set up pre-commit hooks

We use black to enforce a consistent code style. We test this in our CI/CD pipeline.

To set up a pre-commit hook, just run:

.. code-block:: console

    $ pre-commit install

(The `pre-commit` package is installed in dagster's dev-requirements.)

Otherwise, we recommend setting up your development environment to format on save.

Lastly there is always the option to run `make black` from the `python_modules/` directory

Running dagit webapp in development
-------------------------------------
For development, run the dagit GraphQL server on a different port than the
webapp, from any directory that contains a repository.yaml file. For example:

.. code-block:: console

    $ cd dagster/python_modules/dagster/dagster/tutorials/intro_tutorial
    $ dagit -p 3333

Keep this running. Then, in another terminal, run the local development
(autoreloading, etc.) version of the webapp:

.. code-block:: console

    $ cd dagster/js_modules/dagit
    $ make dev_webapp

To run JavaScript tests for the dagit frontend, you can run:

.. code-block:: console

    $ cd dagster/js_modules/dagit
    $ yarn test

In webapp development it's handy to run ``yarn run jest --watch`` to have an
interactive test runner.

Some webapp tests use snapshots--auto-generated results to which the test
render tree is compared. Those tests are supposed to break when you change
something.

Check that the change is sensible and run ``yarn run jest -u`` to update the
snapshot to the new result. You can also update snapshots interactively
when you are in ``--watch`` mode.

Releasing
-----------
Projects are released using the Python script at ``dagster/bin/publish.py``.

Developing docs
---------------
Running a live html version of the docs can expedite documentation development.

.. code-block:: console

    $ cd docs
    $ make livehtml
