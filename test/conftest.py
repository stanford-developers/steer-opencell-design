# SPDX-FileCopyrightText: 2024-2026 Stanford University
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Session-scoped cache for from_database() calls.

Patches SerializerMixin.from_database so each unique (class, name) pair
is fetched from the database only once per test session.  Every caller
gets a deepcopy, preserving full test isolation.

Tests run in development mode (local SQLite via ``steer-opencell-data``)
so the suite works offline with no API credentials.
"""
import os
from copy import deepcopy
from steer_core.Mixins.Serializer import SerializerMixin

os.environ.setdefault("OPENCELL_ENV", "development")

_original_from_database = SerializerMixin.from_database
_cache: dict[tuple, object] = {}


@classmethod
def _cached_from_database(cls, name: str, table_name: str = None):
    key = (cls, name, table_name)
    if key not in _cache:
        _cache[key] = _original_from_database.__func__(cls, name, table_name=table_name)
    return deepcopy(_cache[key])


SerializerMixin.from_database = _cached_from_database
