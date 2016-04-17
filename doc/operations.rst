##########
Operations
##########

There are several kinds of operations:

* Metadata operations – modify object's metadata or perform metadata related
  adjustments on the object
* Row operations – Operations on whole rows such as filtering
* Field Operations – Derive fields, change fields, create fields,....
* Compositions – compose multiple objects into one
* Auditing – determine object properties of object's content
* Assertions – check whether object properties match certain conditions
* Conversions - convert objects to other types
* Output – generate output from objects

Currently implemented operations can be found at
http://www.scribd.com/doc/147247069/Bubbles-Brewery2-Operations.

Metadata
========

.. function:: field_filter(object[, keep][, drop][, rename][, filter])

    Filters fields of an object. `keep` – keep only listed fields, `drop` –
    keep all except fields in the `drop` list, `rename` – new field names.

    `filter` is a `FieldFilter` object. Use either the filter object or the
    first three filtering arguments.


    Signatures: ``rows``, ``sql``

.. function:: rename_fields(object, rename)

    Rename the fields according to a dictionary `rename`. Keys are original
    field names, values are the new field names.

.. function:: drop_fields(object, drop)

    Drop or ignore fields in the list `drop`. This is a convenience operation
    for `field_filter()`

.. function:: keep_fields(object, keep)

    Keep only the fields in the list `keep`. This is a convenience operation
    for `field_filter()`


Record Filters
==============

.. function:: filter_by_value(object, key, value[, discard])

    Resulting object will represent only those records where field `key` is
    equal to `value`. If `discard` is `True` then the result will be inverted
    – matching objects will be discarded.

    Signatures: ``rows``, ``sql``

.. function:: filter_by_set(object, key, values[, discard])

    Resulting object will represent only those records where field `key` is
    is one of values of the `values` set. If `discard` is `True` then the
    result will be inverted – matching objects will be discarded.

    Signatures: ``rows``, ``sql``

.. function:: filter_by_range(object, key, low, high[, discard])

    Resulting object will represent only those records where field `key` is in
    the range `low` < `key` < `high`. If `discard` is `True` then the result
    will be inverted – matching objects will be discarded.

    Signatures: ``rows``, ``sql``

.. function:: filter_not_empty(object, field)

    Resulting object will represent only those records where field `key` is in
    not empty.

    Signatures: ``rows``, ``sql``

.. function:: filter_empty(object, field)

    Resulting object will represent only those records where field `key` is in
    empty.

    Signatures: ``rows``, ``sql``

.. function:: filter_predicate(object, predicate, fields[, discard], **kwargs)

    Resulting object will represent only those records which match predicate
    function `predicate`. `fields` is a list of fields that are passed to the
    `predicate` as arguments. `kwargs` are passed as the keyword arguments.

    Signatures: ``rows``

    .. note::

        This operation is available only within Python.

Record Operations
=================


.. function:: distinct(object,[ key][, is_sorted=False])

    Resulting object will represent distinct values of `key` of the `object`.
    If no `key` is specified, then all fields are considered. `is_sorted` is a
    hint for some backends that the `object` is already sorted according to
    the `key`. Some backends might ignore the option if it is not relevant to
    them.

    Signatures: ``rows``, ``sql``

.. function:: distinct_rows(object,[ key][, is_sorted=False])

    Resulting object will represent whole first rows with distinct values of
    `key` of the `object`.  If no `key` is specified, then all fields are
    considered. `is_sorted` is a hint for some backends that the `object` is
    already sorted according to the `key`. Some backends might ignore the
    option if it is not relevant to them.

    Signatures: ``rows``, ``sql``

.. function:: first_unique(object[, keys][, discard])

    Resulting object will represent rows that are unique if the original
    object is ordered (in its natural order), every other row is discarded. If
    `discard` is `True` then the unique rows are discarded and the duplicates
    are kept.

    Signatures: ``rows``, ``sql``

.. function:: sample(object, value[, discard][, mode='first'])

    Resulting object will represent a sample of the `object`. The sample type
    is determined by `mode` which can be ``first``, ``nth`` or ``random``.

    Signatures: ``rows``, ``sql``

    .. note::

        The ``sql`` version of this operation can operate only in the
        ``first`` mode.

.. function:: discard_nth(object, step):

    Resulting object will represent rows where every `step` row is discarded.

Ordering
========

.. function:: sort(object, ordeby)

    Returns an object that represents `object` sorted according to the
    `orderby`. The `orderby` is a list of keys to order by or list of tuples
    (`key`, `direction`) where `direction` can be ``asc`` or ``desc``.

    Signatures: ``rows``, ``sql``

    .. note::

        This might be renamed in the future to `order()`

Aggregation
===========

.. function:: aggregate(object, key[, measures])

    Returns an aggregated representation of `object` by `key`. All fields of
    analytical type `measure` are aggregated if no `measures` is specified.
    `measures` can be a list of fields or list of tuples (`field`,
    `function`). `function` is an aggregation function: ``sum``, ``avg``,
    ``min``, ``max``

    Signatures: ``rows``, ``sql``

Field Operations
================

.. function:: append_costant_fields(object, fields, value)

    Resulting object will have `fields` appended and their value will be
    `value`.

    Signatures: ``rows``, ``sql``


.. function:: dates_to_dimension(object[, fields][, unknown_date])

    Resulting object will have all `fields` converted into simple date
    dimension key `YYYYMMDD`. If no `fields` are specified then all fields of
    type `date` or `datetime` are considered.

    Signatures: ``rows``, ``sql``


.. function:: string_to_date(object, fields[, fmt])

    Resulting object will have `fields`, which are expected to be of type
    `string`, converted to date according to `fmt`. Default is ISO date
    format.

    Signatures: ``rows``, ``sql``


.. function:: split_date(object, fields[, parts])

    Resulting object will have additional columns derived from date fields in
    `fields` as date units specified in `parts`. Default parts are ``year``,
    ``month``, ``day``.

    For example field `start_date` will yield new fields `start_date_year`,
    `start_date_month` and `start_date_day`.

    Signatures: ``rows``, ``sql``


.. function:: text_substitute(object, field, substitutions)

    Regular expression `substitutions` are applied to `field`

    Signatures: ``rows``

.. function:: empty_to_missing(object[, fields][, strict])

    Empty values in `fields` or all fields, if not specified, will be replaced
    with the respective field's `missing value` value.

    Signatures: ``rows``

.. function:: string_strip(object[, fields][, chars])

    Strip `chars` or spaces from the `fields` or all string fields.

    Signatures: ``rows``

.. function::  transpose_by(object, key, new_field)

    Resulting object will be transposed representation of `object`. `key` is a
    field which will be used for transposition.

    Signatures: ``rows``


Composition
===========

.. function:: append(objects)

    Resulting object will represent sequentially chained `objects`. The
    `objects` are expected to have the same field structure.

    Signatures: ``rows``, ``sql``

    .. note::

        ``rows`` version of the operation chains the iterators.

        ``sql`` version of the operation for objects from the same store uses
        ``UNION``.

        The ``sql`` version also expects all of the objects to be composable
        within the same connection, otherwise the ``rows`` version is retried.


.. function:: join_details(master, detail, master_key, detail_key):

    Resulting object is a representation of simple master-detail join of
    `detail` to `master` where `master_key` == `detail_key`.

    ``rows`` version of the operation consumes whole `detail` and returns an
    iterator over `master`

    ``sql`` version of the operation yields a ``JOIN`` statement.


Output
======

.. function:: pretty_print(objects[, target])

    Object rows are formatted to a textual table and printed to the standard
    output or `target` stream if specified.

Conversions
===========

.. note::

    These operations are meant to be used in Python only.

.. function:: fetch_all(object)

    Retrieves all the data and puts them into an object wrapping a python
    list. Useful for smaller datasets, not recommended for bigger data.

.. function:: as_dict(object[, key][, value])

    Returns dictionary constructed from the iterator.  `key` is name of a
    field or list of fields that will be used as a simple key or composite
    key. `value` is a field or list of fields that will be used as values.

    If no `key` is provided, then the first field is used as key. If no
    `value` is provided, then whole rows are used as values.

    Keys are supposed to be unique. If they are not, result might be
    unpredictable.

    .. warning::

        This method consumes whole iterator. Might be very costly on large
        datasets.



.. seealso::

    :doc:`context`


Adding Custom Operations
========================

Example of `append` operation - append contents of objects sequentially.


.. note:: The `name` argument is not necessary if the functions are in
   different modules. In this case we have to name them differently, but
   provide equal operation name.

Version of the operation for list of iterators:

.. code-block:: python

    @operation("rows[]", name="append")
    def append_rows(ctx, objects):

        iterators = [iter(obj) for obj in objects]
        iterator = itertools.chain(*iterators)

        return IterableDataSource(iterator, objects[0].fields)

Version for list of SQL objects:

.. code-block:: python

    @operation("sql[]", name="append")
    def append_sql(ctx, objects):

        first = objects[0]

        statements = [o.sql_statement() for o in objects]
        statement = sqlalchemy.sql.expression.union(*statements)

        return first.clone_statement(statement=statement)

When we call `context.o.append(objects)` then appropriate version will be
chosen based on the objects and their representations. In this case all
objects have to have `sql` representation for the SQL version to be used.

Retry
-----

Sometimes it is not possible to preform composition, because the objects might
be from different databases. Or there might be some other reason why
operation might not be able to be performed on provided objects.

In this case the operation might give up, but still not fail – it might assume
that there might be some other operation that might be able to complete desired
task. In our case, the SQL objects might not be composable:

.. code-block:: python

    @operation("sql[]", name="append")
    def append_sql(ctx, objects):
        first = objects[0]

        # Fail and use iterator version instead
        if not all(first.can_compose(o) for o in objects[1:]):
            raise RetryOperation(["rows", "rows[]"],
                                 reason="Can not compose")

        statements = [o.sql_statement() for o in objects]
        statement = sqlalchemy.sql.expression.union(*statements)

        return first.clone_statement(statement=statement)
