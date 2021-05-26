# postgresql/psycopg2.py
# Copyright (C) 2005-2021 the SQLAlchemy authors and contributors
# <see AUTHORS file>
#
# This module is part of SQLAlchemy and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php
r"""
.. dialect:: postgresql+psycopg2
    :name: psycopg2
    :dbapi: psycopg2
    :connectstring: postgresql+psycopg2://user:password@host:port/dbname[?key=value&key=value...]
    :url: http://pypi.python.org/pypi/psycopg2/

psycopg2 Connect Arguments
-----------------------------------

psycopg2-specific keyword arguments which are accepted by
:func:`_sa.create_engine()` are:


* ``isolation_level``: This option, available for all PostgreSQL dialects,
  includes the ``AUTOCOMMIT`` isolation level when using the psycopg2
  dialect.

  .. seealso::

    :ref:`psycopg2_isolation_level`

* ``client_encoding``: sets the client encoding in a libpq-agnostic way,
  using psycopg2's ``set_client_encoding()`` method.

  .. seealso::

    :ref:`psycopg2_unicode`

* ``use_native_unicode``: Under Python 2 only, this can be set to False to
  disable the use of psycopg2's native Unicode support.

  .. seealso::

    :ref:`psycopg2_disable_native_unicode`


* ``executemany_mode``, ``executemany_batch_page_size``,
  ``executemany_values_page_size``: Allows use of psycopg2
  extensions for optimizing "executemany"-stye queries.  See the referenced
  section below for details.

  .. seealso::

    :ref:`psycopg2_executemany_mode`


Unix Domain Connections
------------------------

psycopg2 supports connecting via Unix domain connections.   When the ``host``
portion of the URL is omitted, SQLAlchemy passes ``None`` to psycopg2,
which specifies Unix-domain communication rather than TCP/IP communication::

    create_engine("postgresql+psycopg2://user:password@/dbname")

By default, the socket file used is to connect to a Unix-domain socket
in ``/tmp``, or whatever socket directory was specified when PostgreSQL
was built.  This value can be overridden by passing a pathname to psycopg2,
using ``host`` as an additional keyword argument::

    create_engine("postgresql+psycopg2://user:password@/dbname?host=/var/lib/postgresql")

.. seealso::

    `PQconnectdbParams \
    <http://www.postgresql.org/docs/9.1/static/libpq-connect.html#LIBPQ-PQCONNECTDBPARAMS>`_

.. _psycopg2_multi_host:

Specifiying multiple fallback hosts
-----------------------------------

psycopg2 supports multiple connection points in the connection string.
When the ``host`` parameter is used multiple times in the query section of
the URL, SQLAlchemy will create a single string of the host and port
information provided to make the connections::

    create_engine(
        "postgresql+psycopg2://user:password@/dbname?host=HostA:port1&host=HostB&host=HostC"
    )

A connection to each host is then attempted until either a connection is successful
or all connections are unsuccessful in which case an error is raised.

.. versionadded:: 1.3.20 Support for multiple hosts in PostgreSQL connection
   string.

.. seealso::

    `PQConnString \
    <https://www.postgresql.org/docs/10/libpq-connect.html#LIBPQ-CONNSTRING>`_

Empty DSN Connections / Environment Variable Connections
---------------------------------------------------------

The psycopg2 DBAPI can connect to PostgreSQL by passing an empty DSN to the
libpq client library, which by default indicates to connect to a localhost
PostgreSQL database that is open for "trust" connections.  This behavior can be
further tailored using a particular set of environment variables which are
prefixed with ``PG_...``, which are  consumed by ``libpq`` to take the place of
any or all elements of the connection string.

For this form, the URL can be passed without any elements other than the
initial scheme::

    engine = create_engine('postgresql+psycopg2://')

In the above form, a blank "dsn" string is passed to the ``psycopg2.connect()``
function which in turn represents an empty DSN passed to libpq.

.. versionadded:: 1.3.2 support for parameter-less connections with psycopg2.

.. seealso::

    `Environment Variables\
    <https://www.postgresql.org/docs/current/libpq-envars.html>`_ -
    PostgreSQL documentation on how to use ``PG_...``
    environment variables for connections.

.. _psycopg2_execution_options:

Per-Statement/Connection Execution Options
-------------------------------------------

The following DBAPI-specific options are respected when used with
:meth:`_engine.Connection.execution_options`,
:meth:`.Executable.execution_options`,
:meth:`_query.Query.execution_options`,
in addition to those not specific to DBAPIs:

* ``isolation_level`` - Set the transaction isolation level for the lifespan
  of a :class:`_engine.Connection` (can only be set on a connection,
  not a statement
  or query).   See :ref:`psycopg2_isolation_level`.

* ``stream_results`` - Enable or disable usage of psycopg2 server side
  cursors - this feature makes use of "named" cursors in combination with
  special result handling methods so that result rows are not fully buffered.
  Defaults to False, meaning cursors are buffered by default.

* ``max_row_buffer`` - when using ``stream_results``, an integer value that
  specifies the maximum number of rows to buffer at a time.  This is
  interpreted by the :class:`.BufferedRowCursorResult`, and if omitted the
  buffer will grow to ultimately store 1000 rows at a time.

  .. versionchanged:: 1.4  The ``max_row_buffer`` size can now be greater than
     1000, and the buffer will grow to that size.

.. _psycopg2_batch_mode:

.. _psycopg2_executemany_mode:

Psycopg2 Fast Execution Helpers
-------------------------------

Modern versions of psycopg2 include a feature known as
`Fast Execution Helpers \
<http://initd.org/psycopg/docs/extras.html#fast-execution-helpers>`_, which
have been shown in benchmarking to improve psycopg2's executemany()
performance, primarily with INSERT statements, by multiple orders of magnitude.
SQLAlchemy internally makes use of these extensions for ``executemany()`` style
calls, which correspond to lists of parameters being passed to
:meth:`_engine.Connection.execute` as detailed in :ref:`multiple parameter
sets <execute_multiple>`.   The ORM also uses this mode internally whenever
possible.

The two available extensions on the psycopg2 side are the ``execute_values()``
and ``execute_batch()`` functions.  The psycopg2 dialect defaults to using the
``execute_values()`` extension for all qualifying INSERT statements.

.. versionchanged:: 1.4  The psycopg2 dialect now defaults to a new mode
   ``"values_only"`` for ``executemany_mode``, which allows an order of
   magnitude performance improvement for INSERT statements, but does not
   include "batch" mode for UPDATE and DELETE statements which removes the
   ability of ``cursor.rowcount`` to function correctly.

The use of these extensions is controlled by the ``executemany_mode`` flag
which may be passed to :func:`_sa.create_engine`::

    engine = create_engine(
        "postgresql+psycopg2://scott:tiger@host/dbname",
        executemany_mode='values_plus_batch')


Possible options for ``executemany_mode`` include:

* ``values_only`` - this is the default value.  the psycopg2 execute_values()
  extension is used for qualifying INSERT statements, which rewrites the INSERT
  to include multiple VALUES clauses so that many parameter sets can be
  inserted with one statement.

  .. versionadded:: 1.4 Added ``"values_only"`` setting for ``executemany_mode``
     which is also now the default.

* ``None`` - No psycopg2 extensions are not used, and the usual
  ``cursor.executemany()`` method is used when invoking statements with
  multiple parameter sets.

* ``'batch'`` - Uses ``psycopg2.extras.execute_batch`` for all qualifying
  INSERT, UPDATE and DELETE statements, so that multiple copies
  of a SQL query, each one corresponding to a parameter set passed to
  ``executemany()``, are joined into a single SQL string separated by a
  semicolon.  When using this mode, the :attr:`_engine.CursorResult.rowcount`
  attribute will not contain a value for executemany-style executions.

* ``'values_plus_batch'``- ``execute_values`` is used for qualifying INSERT
  statements, ``execute_batch`` is used for UPDATE and DELETE.
  When using this mode, the :attr:`_engine.CursorResult.rowcount`
  attribute will not contain a value for executemany-style executions against
  UPDATE and DELETE statements.

By "qualifying statements", we mean that the statement being executed
must be a Core :func:`_expression.insert`, :func:`_expression.update`
or :func:`_expression.delete` construct, and not a plain textual SQL
string or one constructed using :func:`_expression.text`.  When using the
ORM, all insert/update/delete statements used by the ORM flush process
are qualifying.

The "page size" for the "values" and "batch" strategies can be affected
by using the ``executemany_batch_page_size`` and
``executemany_values_page_size`` engine parameters.  These
control how many parameter sets
should be represented in each execution.    The "values" page size defaults
to 1000, which is different that psycopg2's default.  The "batch" page
size defaults to 100.  These can be affected by passing new values to
:func:`_engine.create_engine`::

    engine = create_engine(
        "postgresql+psycopg2://scott:tiger@host/dbname",
        executemany_mode='values',
        executemany_values_page_size=10000, executemany_batch_page_size=500)

.. versionchanged:: 1.4

    The default for ``executemany_values_page_size`` is now 1000, up from
    100.

.. seealso::

    :ref:`execute_multiple` - General information on using the
    :class:`_engine.Connection`
    object to execute statements in such a way as to make
    use of the DBAPI ``.executemany()`` method.


.. _psycopg2_unicode:

Unicode with Psycopg2
----------------------

The psycopg2 DBAPI driver supports Unicode data transparently.   Under Python 2
only, the SQLAlchemy psycopg2 dialect will enable the
``psycopg2.extensions.UNICODE`` extension by default to ensure Unicode is
handled properly; under Python 3, this is psycopg2's default behavior.

The client character encoding can be controlled for the psycopg2 dialect
in the following ways:

* For PostgreSQL 9.1 and above, the ``client_encoding`` parameter may be
  passed in the database URL; this parameter is consumed by the underlying
  ``libpq`` PostgreSQL client library::

    engine = create_engine("postgresql+psycopg2://user:pass@host/dbname?client_encoding=utf8")

  Alternatively, the above ``client_encoding`` value may be passed using
  :paramref:`_sa.create_engine.connect_args` for programmatic establishment with
  ``libpq``::

    engine = create_engine(
        "postgresql+psycopg2://user:pass@host/dbname",
        connect_args={'client_encoding': 'utf8'}
    )

* For all PostgreSQL versions, psycopg2 supports a client-side encoding
  value that will be passed to database connections when they are first
  established.  The SQLAlchemy psycopg2 dialect supports this using the
  ``client_encoding`` parameter passed to :func:`_sa.create_engine`::

      engine = create_engine(
          "postgresql+psycopg2://user:pass@host/dbname",
          client_encoding="utf8"
      )

  .. tip:: The above ``client_encoding`` parameter admittedly is very similar
      in appearance to usage of the parameter within the
      :paramref:`_sa.create_engine.connect_args` dictionary; the difference
      above is that the parameter is consumed by psycopg2 and is
      passed to the database connection using ``SET client_encoding TO
      'utf8'``; in the previously mentioned style, the parameter is instead
      passed through psycopg2 and consumed by the ``libpq`` library.

* A common way to set up client encoding with PostgreSQL databases is to
  ensure it is configured within the server-side postgresql.conf file;
  this is the recommended way to set encoding for a server that is
  consistently of one encoding in all databases::

    # postgresql.conf file

    # client_encoding = sql_ascii # actually, defaults to database
                                 # encoding
    client_encoding = utf8

.. _psycopg2_disable_native_unicode:

Disabling Native Unicode
^^^^^^^^^^^^^^^^^^^^^^^^

Under Python 2 only, SQLAlchemy can also be instructed to skip the usage of the
psycopg2 ``UNICODE`` extension and to instead utilize its own unicode
encode/decode services, which are normally reserved only for those DBAPIs that
don't fully support unicode directly.  Passing ``use_native_unicode=False`` to
:func:`_sa.create_engine` will disable usage of ``psycopg2.extensions.
UNICODE``. SQLAlchemy will instead encode data itself into Python bytestrings
on the way in and coerce from bytes on the way back, using the value of the
:func:`_sa.create_engine` ``encoding`` parameter, which defaults to ``utf-8``.
SQLAlchemy's own unicode encode/decode functionality is steadily becoming
obsolete as most DBAPIs now support unicode fully.


Transactions
------------

The psycopg2 dialect fully supports SAVEPOINT and two-phase commit operations.

.. _psycopg2_isolation_level:

Psycopg2 Transaction Isolation Level
-------------------------------------

As discussed in :ref:`postgresql_isolation_level`,
all PostgreSQL dialects support setting of transaction isolation level
both via the ``isolation_level`` parameter passed to :func:`_sa.create_engine`
,
as well as the ``isolation_level`` argument used by
:meth:`_engine.Connection.execution_options`.  When using the psycopg2 dialect
, these
options make use of psycopg2's ``set_isolation_level()`` connection method,
rather than emitting a PostgreSQL directive; this is because psycopg2's
API-level setting is always emitted at the start of each transaction in any
case.

The psycopg2 dialect supports these constants for isolation level:

* ``READ COMMITTED``
* ``READ UNCOMMITTED``
* ``REPEATABLE READ``
* ``SERIALIZABLE``
* ``AUTOCOMMIT``

.. seealso::

    :ref:`postgresql_isolation_level`

    :ref:`pg8000_isolation_level`


NOTICE logging
---------------

The psycopg2 dialect will log PostgreSQL NOTICE messages
via the ``sqlalchemy.dialects.postgresql`` logger.  When this logger
is set to the ``logging.INFO`` level, notice messages will be logged::

    import logging

    logging.getLogger('sqlalchemy.dialects.postgresql').setLevel(logging.INFO)

Above, it is assumed that logging is configured externally.  If this is not
the case, configuration such as ``logging.basicConfig()`` must be utilized::

    import logging

    logging.basicConfig()   # log messages to stdout
    logging.getLogger('sqlalchemy.dialects.postgresql').setLevel(logging.INFO)

.. seealso::

    `Logging HOWTO <https://docs.python.org/3/howto/logging.html>`_ - on the python.org website

.. _psycopg2_hstore:

HSTORE type
------------

The ``psycopg2`` DBAPI includes an extension to natively handle marshalling of
the HSTORE type.   The SQLAlchemy psycopg2 dialect will enable this extension
by default when psycopg2 version 2.4 or greater is used, and
it is detected that the target database has the HSTORE type set up for use.
In other words, when the dialect makes the first
connection, a sequence like the following is performed:

1. Request the available HSTORE oids using
   ``psycopg2.extras.HstoreAdapter.get_oids()``.
   If this function returns a list of HSTORE identifiers, we then determine
   that the ``HSTORE`` extension is present.
   This function is **skipped** if the version of psycopg2 installed is
   less than version 2.4.

2. If the ``use_native_hstore`` flag is at its default of ``True``, and
   we've detected that ``HSTORE`` oids are available, the
   ``psycopg2.extensions.register_hstore()`` extension is invoked for all
   connections.

The ``register_hstore()`` extension has the effect of **all Python
dictionaries being accepted as parameters regardless of the type of target
column in SQL**. The dictionaries are converted by this extension into a
textual HSTORE expression.  If this behavior is not desired, disable the
use of the hstore extension by setting ``use_native_hstore`` to ``False`` as
follows::

    engine = create_engine("postgresql+psycopg2://scott:tiger@localhost/test",
                use_native_hstore=False)

The ``HSTORE`` type is **still supported** when the
``psycopg2.extensions.register_hstore()`` extension is not used.  It merely
means that the coercion between Python dictionaries and the HSTORE
string format, on both the parameter side and the result side, will take
place within SQLAlchemy's own marshalling logic, and not that of ``psycopg2``
which may be more performant.

"""  # noqa
from __future__ import absolute_import

import decimal
import logging
import re
from uuid import UUID as _python_UUID

from .base import _DECIMAL_TYPES
from .base import _FLOAT_TYPES
from .base import _INT_TYPES
from .base import ENUM
from .base import PGCompiler
from .base import PGDialect
from .base import PGExecutionContext
from .base import PGIdentifierPreparer
from .base import UUID
from .hstore import HSTORE
from .json import JSON
from .json import JSONB
from ... import exc
from ... import processors
from ... import types as sqltypes
from ... import util
from ...engine import cursor as _cursor
from ...sql import elements
from ...util import collections_abc


logger = logging.getLogger("sqlalchemy.dialects.postgresql")


class _PGNumeric(sqltypes.Numeric):
    def bind_processor(self, dialect):
        return None

    def result_processor(self, dialect, coltype):
        if self.asdecimal:
            if coltype in _FLOAT_TYPES:
                return processors.to_decimal_processor_factory(
                    decimal.Decimal, self._effective_decimal_return_scale
                )
            elif coltype in _DECIMAL_TYPES or coltype in _INT_TYPES:
                # pg8000 returns Decimal natively for 1700
                return None
            else:
                raise exc.InvalidRequestError(
                    "Unknown PG numeric type: %d" % coltype
                )
        else:
            if coltype in _FLOAT_TYPES:
                # pg8000 returns float natively for 701
                return None
            elif coltype in _DECIMAL_TYPES or coltype in _INT_TYPES:
                return processors.to_float
            else:
                raise exc.InvalidRequestError(
                    "Unknown PG numeric type: %d" % coltype
                )


class _PGEnum(ENUM):
    def result_processor(self, dialect, coltype):
        if util.py2k and self._expect_unicode is True:
            # for py2k, if the enum type needs unicode data (which is set up as
            # part of the Enum() constructor based on values passed as py2k
            # unicode objects) we have to use our own converters since
            # psycopg2's don't work, a rare exception to the "modern DBAPIs
            # support unicode everywhere" theme of deprecating
            # convert_unicode=True. Use the special "force_nocheck" directive
            # which forces unicode conversion to happen on the Python side
            # without an isinstance() check.   in py3k psycopg2 does the right
            # thing automatically.
            self._expect_unicode = "force_nocheck"
        return super(_PGEnum, self).result_processor(dialect, coltype)


class _PGHStore(HSTORE):
    def bind_processor(self, dialect):
        if dialect._has_native_hstore:
            return None
        else:
            return super(_PGHStore, self).bind_processor(dialect)

    def result_processor(self, dialect, coltype):
        if dialect._has_native_hstore:
            return None
        else:
            return super(_PGHStore, self).result_processor(dialect, coltype)


class _PGJSON(JSON):
    def result_processor(self, dialect, coltype):
        return None


class _PGJSONB(JSONB):
    def result_processor(self, dialect, coltype):
        return None


class _PGUUID(UUID):
    def bind_processor(self, dialect):
        if not self.as_uuid and dialect.use_native_uuid:

            def process(value):
                if value is not None:
                    value = _python_UUID(value)
                return value

            return process

    def result_processor(self, dialect, coltype):
        if not self.as_uuid and dialect.use_native_uuid:

            def process(value):
                if value is not None:
                    value = str(value)
                return value

            return process


_server_side_id = util.counter()


class PGExecutionContext_psycopg2(PGExecutionContext):
    _psycopg2_fetched_rows = None

    def create_server_side_cursor(self):
        # use server-side cursors:
        # http://lists.initd.org/pipermail/psycopg/2007-January/005251.html
        ident = "c_%s_%s" % (hex(id(self))[2:], hex(_server_side_id())[2:])
        return self._dbapi_connection.cursor(ident)

    def post_exec(self):
        if (
            self._psycopg2_fetched_rows
            and self.compiled
            and self.compiled.returning
        ):
            # psycopg2 execute_values will provide for a real cursor where
            # cursor.description works correctly. however, it executes the
            # INSERT statement multiple times for multiple pages of rows, so
            # while this cursor also supports calling .fetchall() directly, in
            # order to get the list of all rows inserted across multiple pages,
            # we have to retrieve the aggregated list from the execute_values()
            # function directly.
            strat_cls = _cursor.FullyBufferedCursorFetchStrategy
            self.cursor_fetch_strategy = strat_cls(
                self.cursor, initial_buffer=self._psycopg2_fetched_rows
            )
        self._log_notices(self.cursor)

    def _log_notices(self, cursor):
        # check also that notices is an iterable, after it's already
        # established that we will be iterating through it.  This is to get
        # around test suites such as SQLAlchemy's using a Mock object for
        # cursor
        if not cursor.connection.notices or not isinstance(
            cursor.connection.notices, collections_abc.Iterable
        ):
            return

        for notice in cursor.connection.notices:
            # NOTICE messages have a
            # newline character at the end
            logger.info(notice.rstrip())

        cursor.connection.notices[:] = []


class PGCompiler_psycopg2(PGCompiler):
    def visit_bindparam(self, bindparam, skip_bind_expression=False, **kw):

        text = super(PGCompiler_psycopg2, self).visit_bindparam(
            bindparam, skip_bind_expression=skip_bind_expression, **kw
        )
        # note that if the type has a bind_expression(), we will get a
        # double compile here
        if not skip_bind_expression and (
            bindparam.type._is_array or bindparam.type._is_type_decorator
        ):
            typ = bindparam.type._unwrapped_dialect_impl(self.dialect)

            if typ._is_array:
                text += "::%s" % (
                    elements.TypeClause(typ)._compiler_dispatch(
                        self, skip_bind_expression=skip_bind_expression, **kw
                    ),
                )
        return text


class PGIdentifierPreparer_psycopg2(PGIdentifierPreparer):
    pass


EXECUTEMANY_PLAIN = util.symbol("executemany_plain", canonical=0)
EXECUTEMANY_BATCH = util.symbol("executemany_batch", canonical=1)
EXECUTEMANY_VALUES = util.symbol("executemany_values", canonical=2)
EXECUTEMANY_VALUES_PLUS_BATCH = util.symbol(
    "executemany_values_plus_batch",
    canonical=EXECUTEMANY_BATCH | EXECUTEMANY_VALUES,
)


class PGDialect_psycopg2(PGDialect):
    driver = "psycopg2"

    supports_statement_cache = True

    if util.py2k:
        # turn off supports_unicode_statements for Python 2. psycopg2 supports
        # unicode statements in Py2K. But!  it does not support unicode *bound
        # parameter names* because it uses the Python "%" operator to
        # interpolate these into the string, and this fails.   So for Py2K, we
        # have to use full-on encoding for statements and parameters before
        # passing to cursor.execute().
        supports_unicode_statements = False

    supports_server_side_cursors = True

    default_paramstyle = "pyformat"
    # set to true based on psycopg2 version
    supports_sane_multi_rowcount = False
    execution_ctx_cls = PGExecutionContext_psycopg2
    statement_compiler = PGCompiler_psycopg2
    preparer = PGIdentifierPreparer_psycopg2
    psycopg2_version = (0, 0)

    _has_native_hstore = True

    engine_config_types = PGDialect.engine_config_types.union(
        {"use_native_unicode": util.asbool}
    )

    colspecs = util.update_copy(
        PGDialect.colspecs,
        {
            sqltypes.Numeric: _PGNumeric,
            ENUM: _PGEnum,  # needs force_unicode
            sqltypes.Enum: _PGEnum,  # needs force_unicode
            HSTORE: _PGHStore,
            JSON: _PGJSON,
            sqltypes.JSON: _PGJSON,
            JSONB: _PGJSONB,
            UUID: _PGUUID,
        },
    )

    def __init__(
        self,
        use_native_unicode=True,
        client_encoding=None,
        use_native_hstore=True,
        use_native_uuid=True,
        executemany_mode="values_only",
        executemany_batch_page_size=100,
        executemany_values_page_size=1000,
        **kwargs
    ):
        PGDialect.__init__(self, **kwargs)
        self.use_native_unicode = use_native_unicode
        if not use_native_unicode and not util.py2k:
            raise exc.ArgumentError(
                "psycopg2 native_unicode mode is required under Python 3"
            )
        if not use_native_hstore:
            self._has_native_hstore = False
        self.use_native_hstore = use_native_hstore
        self.use_native_uuid = use_native_uuid
        self.supports_unicode_binds = use_native_unicode
        self.client_encoding = client_encoding

        # Parse executemany_mode argument, allowing it to be only one of the
        # symbol names
        self.executemany_mode = util.symbol.parse_user_argument(
            executemany_mode,
            {
                EXECUTEMANY_PLAIN: [None],
                EXECUTEMANY_BATCH: ["batch"],
                EXECUTEMANY_VALUES: ["values_only"],
                EXECUTEMANY_VALUES_PLUS_BATCH: ["values_plus_batch", "values"],
            },
            "executemany_mode",
        )

        if self.executemany_mode & EXECUTEMANY_VALUES:
            self.insert_executemany_returning = True

        self.executemany_batch_page_size = executemany_batch_page_size
        self.executemany_values_page_size = executemany_values_page_size

        if self.dbapi and hasattr(self.dbapi, "__version__"):
            m = re.match(r"(\d+)\.(\d+)(?:\.(\d+))?", self.dbapi.__version__)
            if m:
                self.psycopg2_version = tuple(
                    int(x) for x in m.group(1, 2, 3) if x is not None
                )

            if self.psycopg2_version < (2, 7):
                raise ImportError(
                    "psycopg2 version 2.7 or higher is required."
                )

    def initialize(self, connection):
        super(PGDialect_psycopg2, self).initialize(connection)
        self._has_native_hstore = (
            self.use_native_hstore
            and self._hstore_oids(connection.connection) is not None
        )

        # PGDialect.initialize() checks server version for <= 8.2 and sets
        # this flag to False if so
        if not self.full_returning:
            self.insert_executemany_returning = False
            self.executemany_mode = EXECUTEMANY_PLAIN

        self.supports_sane_multi_rowcount = not (
            self.executemany_mode & EXECUTEMANY_BATCH
        )

    @classmethod
    def dbapi(cls):
        import psycopg2

        return psycopg2

    @classmethod
    def _psycopg2_extensions(cls):
        from psycopg2 import extensions

        return extensions

    @classmethod
    def _psycopg2_extras(cls):
        from psycopg2 import extras

        return extras

    @util.memoized_property
    def _isolation_lookup(self):
        extensions = self._psycopg2_extensions()
        return {
            "AUTOCOMMIT": extensions.ISOLATION_LEVEL_AUTOCOMMIT,
            "READ COMMITTED": extensions.ISOLATION_LEVEL_READ_COMMITTED,
            "READ UNCOMMITTED": extensions.ISOLATION_LEVEL_READ_UNCOMMITTED,
            "REPEATABLE READ": extensions.ISOLATION_LEVEL_REPEATABLE_READ,
            "SERIALIZABLE": extensions.ISOLATION_LEVEL_SERIALIZABLE,
        }

    def set_isolation_level(self, connection, level):
        try:
            level = self._isolation_lookup[level.replace("_", " ")]
        except KeyError as err:
            util.raise_(
                exc.ArgumentError(
                    "Invalid value '%s' for isolation_level. "
                    "Valid isolation levels for %s are %s"
                    % (level, self.name, ", ".join(self._isolation_lookup))
                ),
                replace_context=err,
            )

        connection.set_isolation_level(level)

    def set_readonly(self, connection, value):
        connection.readonly = value

    def get_readonly(self, connection):
        return connection.readonly

    def set_deferrable(self, connection, value):
        connection.deferrable = value

    def get_deferrable(self, connection):
        return connection.deferrable

    def on_connect(self):
        extras = self._psycopg2_extras()
        extensions = self._psycopg2_extensions()

        fns = []
        if self.client_encoding is not None:

            def on_connect(conn):
                conn.set_client_encoding(self.client_encoding)

            fns.append(on_connect)

        if self.isolation_level is not None:

            def on_connect(conn):
                self.set_isolation_level(conn, self.isolation_level)

            fns.append(on_connect)

        if self.dbapi and self.use_native_uuid:

            def on_connect(conn):
                extras.register_uuid(None, conn)

            fns.append(on_connect)

        if util.py2k and self.dbapi and self.use_native_unicode:

            def on_connect(conn):
                extensions.register_type(extensions.UNICODE, conn)
                extensions.register_type(extensions.UNICODEARRAY, conn)

            fns.append(on_connect)

        if self.dbapi and self.use_native_hstore:

            def on_connect(conn):
                hstore_oids = self._hstore_oids(conn)
                if hstore_oids is not None:
                    oid, array_oid = hstore_oids
                    kw = {"oid": oid}
                    if util.py2k:
                        kw["unicode"] = True
                    kw["array_oid"] = array_oid
                    extras.register_hstore(conn, **kw)

            fns.append(on_connect)

        if self.dbapi and self._json_deserializer:

            def on_connect(conn):
                extras.register_default_json(
                    conn, loads=self._json_deserializer
                )
                extras.register_default_jsonb(
                    conn, loads=self._json_deserializer
                )

            fns.append(on_connect)

        if fns:

            def on_connect(conn):
                for fn in fns:
                    fn(conn)

            return on_connect
        else:
            return None

    def do_executemany(self, cursor, statement, parameters, context=None):
        if (
            self.executemany_mode & EXECUTEMANY_VALUES
            and context
            and context.isinsert
            and context.compiled.insert_single_values_expr
        ):
            executemany_values = (
                "(%s)" % context.compiled.insert_single_values_expr
            )
            if not self.supports_unicode_statements:
                executemany_values = executemany_values.encode(self.encoding)

            # guard for statement that was altered via event hook or similar
            if executemany_values not in statement:
                executemany_values = None
        else:
            executemany_values = None

        if executemany_values:
            statement = statement.replace(executemany_values, "%s")
            if self.executemany_values_page_size:
                kwargs = {"page_size": self.executemany_values_page_size}
            else:
                kwargs = {}
            xtras = self._psycopg2_extras()
            context._psycopg2_fetched_rows = xtras.execute_values(
                cursor,
                statement,
                parameters,
                template=executemany_values,
                fetch=bool(context.compiled.returning),
                **kwargs
            )

        elif self.executemany_mode & EXECUTEMANY_BATCH:
            if self.executemany_batch_page_size:
                kwargs = {"page_size": self.executemany_batch_page_size}
            else:
                kwargs = {}
            self._psycopg2_extras().execute_batch(
                cursor, statement, parameters, **kwargs
            )
        else:
            cursor.executemany(statement, parameters)

    @util.memoized_instancemethod
    def _hstore_oids(self, conn):
        extras = self._psycopg2_extras()
        if hasattr(conn, "connection"):
            conn = conn.connection
        oids = extras.HstoreAdapter.get_oids(conn)
        if oids is not None and oids[0]:
            return oids[0:2]
        else:
            return None

    def create_connect_args(self, url):
        opts = url.translate_connect_args(username="user")

        is_multihost = False
        if "host" in url.query:
            is_multihost = isinstance(url.query["host"], (list, tuple))

        if opts:
            if "port" in opts:
                opts["port"] = int(opts["port"])
            opts.update(url.query)
            if is_multihost:
                opts["host"] = ",".join(url.query["host"])
            # send individual dbname, user, password, host, port
            # parameters to psycopg2.connect()
            return ([], opts)
        elif url.query:
            # any other connection arguments, pass directly
            opts.update(url.query)
            if is_multihost:
                opts["host"] = ",".join(url.query["host"])
            return ([], opts)
        else:
            # no connection arguments whatsoever; psycopg2.connect()
            # requires that "dsn" be present as a blank string.
            return ([""], opts)

    def is_disconnect(self, e, connection, cursor):
        if isinstance(e, self.dbapi.Error):
            # check the "closed" flag.  this might not be
            # present on old psycopg2 versions.   Also,
            # this flag doesn't actually help in a lot of disconnect
            # situations, so don't rely on it.
            if getattr(connection, "closed", False):
                return True

            # checks based on strings.  in the case that .closed
            # didn't cut it, fall back onto these.
            str_e = str(e).partition("\n")[0]
            for msg in [
                # these error messages from libpq: interfaces/libpq/fe-misc.c
                # and interfaces/libpq/fe-secure.c.
                "terminating connection",
                "closed the connection",
                "connection not open",
                "could not receive data from server",
                "could not send data to server",
                # psycopg2 client errors, psycopg2/conenction.h,
                # psycopg2/cursor.h
                "connection already closed",
                "cursor already closed",
                # not sure where this path is originally from, it may
                # be obsolete.   It really says "losed", not "closed".
                "losed the connection unexpectedly",
                # these can occur in newer SSL
                "connection has been closed unexpectedly",
                "SSL SYSCALL error: Bad file descriptor",
                "SSL SYSCALL error: EOF detected",
                "SSL error: decryption failed or bad record mac",
                "SSL SYSCALL error: Operation timed out",
            ]:
                idx = str_e.find(msg)
                if idx >= 0 and '"' not in str_e[:idx]:
                    return True
        return False


dialect = PGDialect_psycopg2
