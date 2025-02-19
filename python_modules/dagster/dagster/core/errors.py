from contextlib import contextmanager
from enum import Enum
import sys
import traceback
from future.utils import raise_from


from dagster import check


class DagsterExecutionFailureReason(Enum):
    USER_CODE_ERROR = 'USER_CODE_ERROR'
    FRAMEWORK_ERROR = 'FRAMEWORK_ERROR'
    EXPECTATION_FAILURE = 'EXPECATION_FAILURE'


class DagsterError(Exception):
    @property
    def is_user_code_error(self):
        return False


class DagsterUserError(DagsterError):
    pass


class DagsterRuntimeCoercionError(DagsterError):
    '''Runtime checked faild'''


class DagsterInvalidDefinitionError(DagsterUserError):
    '''Indicates that some violation of the definition rules has been violated by the user'''


class DagsterInvariantViolationError(DagsterUserError):
    '''Indicates the user has violated a well-defined invariant that can only be deteremined
    at runtime.
    '''


class DagsterTypeError(DagsterUserError):
    '''Indicates an error in the solid type system (e.g. mismatched arguments)'''


class DagsterUserCodeExecutionError(DagsterUserError):
    '''
    This is base class for any exception that is meant to wrap an Exception
    thrown by user code. It wraps that existing user code. The original_exc_info
    argument to the ctor is meant to be a sys.exc_info at the site of constructor.
    '''

    def __init__(self, *args, **kwargs):
        # original_exc_info should be gotten from a sys.exc_info() call at the
        # callsite inside of the exception handler. this will allow consuming
        # code to *re-raise* the user error in it's original format
        # for cleaner error reporting that does not have framework code in it
        user_exception = check.inst_param(kwargs.pop('user_exception'), 'user_exception', Exception)
        original_exc_info = check.opt_tuple_param(
            kwargs.pop('original_exc_info', None), 'original_exc_info'
        )

        msg = _add_inner_exception_for_py2(args[0], original_exc_info)

        super(DagsterUserCodeExecutionError, self).__init__(msg, *args[1:], **kwargs)

        self.user_exception = check.opt_inst_param(user_exception, 'user_exception', Exception)
        self.original_exc_info = original_exc_info

    @property
    def is_user_code_error(self):
        return True


class DagsterExecutionStepNotFoundError(DagsterUserError):
    '''
    Generic exception used whenever a user an execution step is specified in an
    api that is consumed by higher level infrastructure (e.g. airflow integration)
    or that needs to be translated into a specific in the GraphQL domain.
    '''

    def __init__(self, *args, **kwargs):
        self.step_key = check.str_param(kwargs.pop('step_key'), 'step_key')
        super(DagsterExecutionStepNotFoundError, self).__init__(*args, **kwargs)


class DagsterExecutionStepExecutionError(DagsterUserCodeExecutionError):
    '''Indicates an error occured during the body of execution step execution'''

    def __init__(self, *args, **kwargs):
        self.step_key = check.str_param(kwargs.pop('step_key'), 'step_key')
        self.solid_name = check.str_param(kwargs.pop('solid_name'), 'solid_name')
        self.solid_def_name = check.str_param(kwargs.pop('solid_def_name'), 'solid_def_name')
        super(DagsterExecutionStepExecutionError, self).__init__(*args, **kwargs)


class DagsterResourceFunctionError(DagsterUserCodeExecutionError):
    '''Indicates an error occured during the body of resource_fn in a ResourceDefinition'''


class DagsterExpectationFailedError(DagsterError):
    '''Thrown with pipeline configured to throw on expectation failure'''

    def __init__(self, expectation_context, value, *args, **kwargs):
        super(DagsterExpectationFailedError, self).__init__(*args, **kwargs)
        self.expectation_context = expectation_context
        self.value = value

    def __repr__(self):
        inout_def = self.expectation_context.inout_def
        return (
            'DagsterExpectationFailedError(solid={solid_name}, {key}={inout_name}, '
            'expectation={e_name}, value={value})'
        ).format(
            solid_name=self.expectation_context.solid.name,
            key=inout_def.descriptive_key,
            inout_name=inout_def.name,
            e_name=self.expectation_context.expectation_def.name,
            value=repr(self.value),
        )

    def __str__(self):
        return self.__repr__()


class DagsterSubprocessExecutionError(DagsterError):
    '''Indicates that an error was encountered when executing part or all of an execution plan
    in a subprocess.

    Although this may be a user error, it is intended to be raised in circumstances where we don't
    have access to the sys.exc_info generated by the error (or where the error is raised by a
    non-Python process).
    '''


class DagsterRunNotFoundError(DagsterError):
    def __init__(self, *args, **kwargs):
        self.invalid_run_id = check.str_param(kwargs.pop('invalid_run_id'), 'invalid_run_id')
        super(DagsterRunNotFoundError, self).__init__(*args, **kwargs)


class DagsterStepOutputNotFoundError(DagsterError):
    def __init__(self, *args, **kwargs):
        self.step_key = check.str_param(kwargs.pop('step_key'), 'step_key')
        self.output_name = check.str_param(kwargs.pop('output_name'), 'output_name')
        super(DagsterStepOutputNotFoundError, self).__init__(*args, **kwargs)


class InvalidRepositoryLoadingComboError(Exception):
    pass


class InvalidPipelineLoadingComboError(Exception):
    pass


def _add_inner_exception_for_py2(msg, exc_info):
    if sys.version_info[0] == 2:
        return (
            msg
            + '\n\nThe above exception was the direct cause of the following exception:\n\n'
            + ''.join(traceback.format_exception(*exc_info))
        )

    return msg


@contextmanager
def user_code_error_boundary(error_cls, msg, **kwargs):
    '''
    Wraps the execution of user-space code in an error boundary. This places a uniform
    policy around an user code invoked by the framework. This ensures that all user
    errors are wrapped in the DagsterUserCodeExecutionError, and that the original stack
    trace of the user error is preserved, so that it can be reported without confusing
    framework code in the stack trace, if a tool author wishes to do so. This has
    been especially help in a notebooking context.
    '''
    check.str_param(msg, 'msg')
    check.subclass_param(error_cls, 'error_cls', DagsterUserCodeExecutionError)

    try:
        yield
    except Exception as e:  # pylint: disable=W0703
        if isinstance(e, DagsterError):
            # The system has thrown an error that is part of the user-framework contract
            raise e
        else:
            # An exception has been thrown by user code and computation should cease
            # with the error reported further up the stack
            raise_from(
                error_cls(msg, user_exception=e, original_exc_info=sys.exc_info(), **kwargs), e
            )


class DagsterPY4JTribalKnowledgeException(Exception):
    '''
    The sole purpose of this class is to catalog and note the strange conditions
    under which py4j exceptions are raised. This is just a place to encode
    insitutional knowledge.

    Note: We no longer throw this for now because it is masking errors
    '''


# HAS_P4J = True
# try:
#     import py4j
# except ImportError:
#     HAS_P4J = False

TRIBAL_KNOWLEDGE_ERROR_MESSAGE = '''
Congratulations, you have managed to encountered an error out of Py4J. These
error messages are often quite inscrutable and nearly impossible to act upon
in a meaningful way without serious investigation. As a result, we have
created this generic wrapper exceptions whose sole purpose in life is to document
all the different error conditions that have been reported as py4j errors
in the hopes that others can benefit from these joyous explorations.

Note: The original exception is reraised along with DagsterPY4JTribalKnowledgeException
in python 3.

Case 1:

An error of the form:
---------
py4j.protocol.Py4JError: An error occurred while calling o44.__getstate__. Trace:
py4j.Py4JException: Method __getstate__([]) does not exist
        at py4j.reflection.ReflectionEngine.getMethod(ReflectionEngine.java:318)
        at py4j.reflection.ReflectionEngine.getMethod(ReflectionEngine.java:326)
        at py4j.Gateway.invoke(Gateway.java:274)
        at py4j.commands.AbstractCommand.invokeMethod(AbstractCommand.java:132)
        at py4j.commands.CallCommand.execute(CallCommand.java:79)
        at py4j.GatewayConnection.run(GatewayConnection.java:238)
        at java.lang.Thread.run(Thread.java:748)
---------

We have encountered this while attempting to pickle an unpickable object that proxies
into the JVM (such as a spark dataframe).


Original Error Text:
{original_error_text}
'''
