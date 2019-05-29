Resources
=========

We've already learned about logging through the context object. We can also use the context object
to manage pipelines' access to resources like the file system, databases, or cloud services.
In general, interactions with features of the external environment like these should be modeled
as resources.

Let's imagine that we are using a key value store offered by a cloud service that has a python API.
We are going to record the results of computations in that key value store.

We are going to model this key value store as a resource.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/resources.py
   :lines: 1
   :dedent: 2

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/resources.py
   :lines: 30-38, 56-66

The core of a resource are the definition of its configuration (the ``config_field``)
and then the function that can actually construct the resource. Notice that all of the
configuration specified for a given resource is passed to its constructor under the
``resource_config`` key of the ``init_context`` parameter.

Let's now attach this resource to a pipeline and use it in a solid.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/resources.py
   :lines: 68-75, 77-84, 86-87

Modes
=====

Resources are attached to a set of :py:class:`ModeDefinition <dagster.ModeDefinition>` defined on the pipeline.
A :py:class:`ModeDefinition <dagster.ModeDefinition>` is the way that a pipeline can declare the different
"modes" it can operate in. For example, you may have "unittest", "local",
or "production" modes that allow you to swap out implementations of
resources by altering configuration, while not changing your code.

In order to invoke this pipeline, we invoke it in this way:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/resources.py
   :lines: 91-100
   :dedent: 4
   :emphasize-lines: 3, 5-7

Note how we are selecting the "cloud" mode via the :py:class:`RunConfig <dagster.RunConfig>` and then parameterizing
the store resource with the appropriate config for cloud mode. As a config,
any user-provided configuration for an artifact (in this case the ``store`` resource)
is placed under the ``config`` key.

So this works, but imagine we wanted to have a local mode, where we interacted
with an in memory version of that key value store and not develop against the live
public cloud version.

First, we need a version of the store that implements the same interface as the production key-value
store; this version can be used in testing contexts without touching the public cloud:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/resources.py
   :lines: 40-46

Next we package this up as a resource.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/resources.py
   :lines: 49-54

And lastly add a new :py:class:`ModeDefinition <dagster.ModeDefinition>` to represent this:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/resources.py
   :lines: 79-87
   :emphasize-lines: 7

Now we can simply change the mode via :py:class:`RunConfig <dagster.RunConfig>` and the "in-memory" version of the
resource will be used instead of the cloud version:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/resources.py
   :lines: 102-108
   :emphasize-lines: 3
   :dedent: 4

In the next section, we'll see how to declaratively specify :doc:`Repositories <repos>` to
manage collections of multiple dagster pipelines.
