# -*- coding: utf-8 -*-
import itertools
from collections import defaultdict
from ..errors import *
from ..dev import is_experimental
from ..operation import Operation, OperationList, extract_signatures
from ..common import get_logger
from ..threadlocal import LocalProxy

__all__ = (
            "OperationContext",
            "default_context",
            "LoggingContextObserver",
            "CollectingContextObserver",
        )

"""List of modules with operations to be loaded for the default contex."""

# FIXME: make this more intelligent and lazy
_default_op_modules = (
            "bubbles.backends.sql.ops",
            "bubbles.backends.mongo.ops",
            "bubbles.ops.rows",
            "bubbles.ops.generic",
        )


class _OperationReference(object):
    def __init__(self, context, name):
        """Creates a reference to an operation within a context"""
        self.context = context
        self.name = name

    def __call__(self, *args, **kwargs):
        return self.context.call(self.name, *args, **kwargs)


class OperationContext(object):
    # TODO: add parent_context
    def __init__(self, retry_count=10):
        """Creates an operation context. Default `retry_count` is 10.

        Use:

        .. code-block:: python

            c = Context()
            duplicate_records = c.op.duplicates(table)

        Context uses multiple dispatch based on operation arguments. The
        `k.duplicates()` operation might be different, based on available
        representations of `table` object.
        """

        super().__init__()
        self.operations = defaultdict(OperationList)
        self.operation_retry_count = retry_count
        self.op = _OperationGetter(self)
        # TODO: depreciate
        self.o = self.op

        self.logger = get_logger()
        self.observer = LoggingContextObserver(self.logger)
        self.retry_count = retry_count

        self.retry_allow = []
        self.retry_deny = []

    def operation_list(self, name):
        """Get list of operation variants for an operation with `name`."""

        if name not in self.operations:
            self.operation_not_found(name)

        try:
            ops = self.operations[name]
        except KeyError:
            raise OperationError("Unable to find operation %s" % name)

        return ops

    def operation_prototype(self, name):
        """Returns a prototype signature for operation `name`"""
        oplist = self.operation_list(name)
        return oplist.prototype

    def add_operations_from(self, obj):
        """Import operations from `obj`. All attributes of `obj` are
        inspected. If they are instances of Operation, then the operation is
        imported."""

        for name in dir(obj):
            op = getattr(obj, name)
            if isinstance(op, Operation):
                self.add_operation(op)

    def add_operation(self, op):
        """Registers a decorated operation.  operation is considered to be a
        context's method and would receive the context as first argument."""

        if op.name not in self.operations:
            self.operations[op.name] = OperationList()

        if any(c.signature == op.signature for c in self.operations[op.name]):
            raise ArgumentError("Operation %s with signature %s already "
                                "registered" % (op.name, op.signature))

        self.operations[op.name].append(op)

    def remove_operation(self, name, signature=None):
        """Removes all operations with `name` and `signature`. If no
        `signature` is specified, then all operations with given name are
        removed, regardles of the signature."""

        operations = self.operations.get(name)
        if not operations:
            return
        elif not signature:
            del self.operations[name]
            return

        newops = [op for op in operations if op.signature != signature]
        self.operations[name] = newops

    def operation_list(self, name):
        """Return a list of operations with `name`. If no list is found, then
        `operation_not_found(name)` is called. See `operation_not_found` for
        more information"""
        # Get all signatures registered for the operation
        operations = self.operations[name]
        if not operations:
            self.operation_not_found(name)
            operations = self.operations[name]
            if not operations:
                raise OperationError("Unable to find operation %s" % name)

        return operations

    def operation_not_found(self, name):
        """Subclasses might override this method to load necessary modules and
        register operations using `register_operation()`. Default
        implementation raises an exception."""
        raise OperationError("Operation '%s' not found" % name)

    def get_operation(self, name, signature):
        """Returns an operation with given name and signature. Requires exact
        signature match."""
        # Get all signatures registered for the operation
        operations = self.operation_list(name)

        for op in operations:
            if op.signature == signature:
                return op
        raise OperationError("No operation '%s' with signature '%s'" %
                                                        (name, signature))

    def operation(self, name):
        """Returns a bound operation with `name`"""

        return _OperationReference(self, name)

    def debug_print_catalogue(self):
        """Pretty prints the operation catalogue – all operations, their
        signatures and function references. Used for debugging purposes."""

        print("== OPERATIONS ==")
        keys = list(self.operations.keys())
        keys.sort()
        for name in keys:
            ops = self.operations[name]
            print("* %s:" % name)

            for op in ops:
                print("    - %s:%s" % \
                            (op.signature.signature, op.function) )

    def can_retry(self, opname):
        """Returns `True` if an operation can be retried. By default, all
        operations can be retried. `Context.retry_allow` contains list of
        allowed operations, `Context.retry_deny` contains list of denied
        operations. When the allow list is set, then only operations from the
        list are allowed. When the deny list is set, the operations in the
        deny list are not allowed."""

        if self.retry_deny and opname in self.retry_deny:
            return False

        if self.retry_allow and opname not in self.retry_allow:
            return False

        return True

    def call(self, op_name, *args, **kwargs):
        """Call operation with `name`. Arguments are passed to the
        operation"""

        oplist = self.operation_list(op_name)
        argc = oplist.prototype.operand_count
        match_objects = args[0:argc]

        # Find best signature match for the operation based on object
        # arguments
        op = self.lookup_operation(op_name, *match_objects)

        if self.observer:
            self.observer.will_call_operation(self, op)

        result = None
        retries = 0

        # We try to perform requested operation. If the operation raises
        # RetryOperation exception, then we use signature from the exception
        # for another operation. Operation can be retried retry_count number
        # of times.
        # Observer is notified about each retry.

        # TODO: allow retry without a signature
        # This will require to have a prepared list of matching operations and
        # number of retries will be number of operations in the list.

        try:
            if is_experimental(op.function):
                self.logger.warn("operation %s is experimental" % \
                                    op_name)
            result = op.function(self, *args, **kwargs)
        except RetryOperation as e:
            if not self.can_retry(op_name):
                raise RetryError("Retry of operation '%s' is not allowed")

            signature = e.signature
            reason = e.reason
            success = False

            for i in range(0, self.retry_count):
                op = self.get_operation(op_name, signature)
                retries += 1

                if self.observer:
                    self.observer.will_retry_operation(self, op, reason)

                try:
                    result = op.function(self, *args, **kwargs)
                except RetryOperation as e:
                    signature = e.signature
                    reason = e.reason
                else:
                    success = True
                    break

            if not success:
                raise RetryError("Operation retry limit reached "
                                     "(allowed: %d)" % self.retry_count)

        # Let the observer know which operation was called at last and
        # completed sucessfully

        if self.observer:
            self.observer.did_call_operation(self, op, retries)

        return result

    def lookup_operation(self, name, *objlist):
        """Returns a matching operation for given data objects as arguments.
        This is the main lookup method of the operation context.

        Lookup is performed for all representations of objects, the first
        matching signature is accepted. Order of representations returned by
        object's `representations()` matters here.

        Returned object is a OpFunction tuple with attributes: `name`, `func`,
        `signature`.

        Note: If the match does not fit your expectations, it is recommended
        to pefrom explicit object conversion to an object with desired
        representation.
        """

        operations = self.operation_list(name)
        if not operations:
            # TODO: check parent context
            raise OperationError("No known signatures for operation '%s'" %
                                    name)

        # TODO: add some fall-back mechanism when no operation signature is
        # found
        # Extract signatures from arguments

        arg_signatures = extract_signatures(*objlist)
        match = None
        for arguments in itertools.product(*arg_signatures):
            for op in operations:
                if op.signature.matches(*arguments):
                    match = op
                    break
            if match:
                break

        if match:
            return match

        raise OperationError("No matching signature found for operation '%s' "
                             " (args: %s)" %
                                (name, arg_signatures))

class LoggingContextObserver(object):
    def __init__(self, logger=None):
        self.logger = logger

    def will_call_operation(self, ctx, op):
        logger = self.logger or ctx.logger
        logger.info("calling %s(%s)" % (op, op.signature))

    def did_call_operation(self, ctx, op, retries):
        logger = self.logger or ctx.logger

        if not retries:
            logger.debug("called %s(%s)" % (op, op.signature))
        else:
            logger.debug("called %s(%s) wth %s retries" % \
                                (op, op.signature, retries))

    def will_retry_operation(self, ctx, op, reason):
        logger = self.logger or ctx.logger
        logger.info("retry %s(%s), reason: %s" %
                                        (op, op.signature, reason))

class CollectingContextObserver(object):
    def __init__(self):
        self.history = []
        self.current = None
        self.tried = []

    def will_call_operation(self, ctx, op):
        self.current = op
        self.tried = []

    def will_retry_operation(self, ctx, op, reason):
        self.tried.append( (self.current, reason) )
        self.current = op

    def did_call_operation(self, ctx, op, retries):
        line = (op, retries, self.tried)
        self.history.append(line)


class _OperationGetter(object):
    def __init__(self, context):
        self.context = context

    def __getattr__(self, name):
        return self.context.operation(name)

    def __getitem__(self, name):
        return self.context.operation(name)

def create_default_context():
    """Creates a ExecutionContext with default operations."""
    context = OperationContext()

    for modname in _default_op_modules:
        mod = _load_module(modname)
        context.add_operations_from(mod)

    return context

def _load_module(modulepath):
    mod = __import__(modulepath)
    path = []
    for token in modulepath.split(".")[1:]:
       path.append(token)
       try:
           mod = getattr(mod, token)
       except AttributeError:
           raise BubblesError("Unable to get %s" % (path, ))
    return mod


default_context = LocalProxy("default_context",
                             factory=create_default_context)

# FIXME: k is for backward prototype compatibility reasons and means 'kernel'
k = default_context
