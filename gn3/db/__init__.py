# pylint: disable=[R0902, R0903]
"""Module that exposes common db operations"""
from dataclasses import asdict, astuple
from typing import Any, Dict, List, Optional, Generator, Tuple, Union
from typing_extensions import Protocol

from gn3.db.metadata_audit import MetadataAudit
from gn3.db.phenotypes import Phenotype
from gn3.db.phenotypes import Probeset
from gn3.db.phenotypes import Publication
from gn3.db.phenotypes import PublishXRef


from gn3.db.metadata_audit import metadata_audit_mapping
from gn3.db.phenotypes import phenotype_mapping
from gn3.db.phenotypes import probeset_mapping
from gn3.db.phenotypes import publication_mapping
from gn3.db.phenotypes import publish_x_ref_mapping


TABLEMAP = {
    "Phenotype": phenotype_mapping,
    "ProbeSet": probeset_mapping,
    "Publication": publication_mapping,
    "PublishXRef": publish_x_ref_mapping,
    "metadata_audit": metadata_audit_mapping,
}

DATACLASSMAP = {
    "Phenotype": Phenotype,
    "ProbeSet": Probeset,
    "Publication": Publication,
    "PublishXRef": PublishXRef,
    "metadata_audit": MetadataAudit,
}


class Dataclass(Protocol):
    """Type Definition for a Dataclass"""
    __dataclass_fields__: Dict


def update(conn: Any,
           table: str,
           data: Dataclass,
           where: Dataclass) -> Optional[int]:
    """Run an UPDATE on a table"""
    if not (any(astuple(data)) and any(astuple(where))):
        return None
    data_ = {k: v for k, v in asdict(data).items()
             if v is not None and k in TABLEMAP[table]}
    where_ = {k: v for k, v in asdict(where).items()
              if v is not None and k in TABLEMAP[table]}
    sql = f"UPDATE {table} SET "
    sql += ", ".join(f"{TABLEMAP[table].get(k)} "
                     "= %s" for k in data_.keys())
    sql += " WHERE "
    sql += " AND ".join(f"{TABLEMAP[table].get(k)} = "
                        "%s" for k in where_.keys())
    with conn.cursor() as cursor:
        cursor.execute(sql,
                       tuple(data_.values()) + tuple(where_.values()))
        return cursor.rowcount


def fetchone(conn: Any,
             table: str,
             where: Optional[Dataclass],
             columns: Union[str, List[str]] = "*") -> Optional[Dataclass]:
    """Run a SELECT on a table. Returns only one result!"""
    if not any(astuple(where)):
        return None
    where_ = {TABLEMAP[table].get(k): v for k, v in asdict(where).items()
              if v is not None and k in TABLEMAP[table]}
    sql = ""
    if columns != "*":
        sql = f"SELECT {', '.join(columns)} FROM {table} "
    else:
        sql = f"SELECT * FROM {table} "
    if where:
        sql += "WHERE "
        sql += " AND ".join(f"{k} = "
                            "%s" for k in where_.keys())
    with conn.cursor() as cursor:
        cursor.execute(sql, tuple(where_.values()))
        return DATACLASSMAP[table](*cursor.fetchone())


def fetchall(conn: Any,
             table: str,
             where: Optional[Dataclass],
             columns: Union[str, List[str]] = "*") -> Optional[Generator]:
    """Run a SELECT on a table. Returns all the results as a tuple!"""
    if not any(astuple(where)):
        return None
    where_ = {TABLEMAP[table].get(k): v for k, v in asdict(where).items()
              if v is not None and k in TABLEMAP[table]}
    sql = ""
    if columns != "*":
        sql = f"SELECT {', '.join(columns)} FROM {table} "
    else:
        sql = f"SELECT * FROM {table} "
    if where:
        sql += "WHERE "
        sql += " AND ".join(f"{k} = "
                            "%s" for k in where_.keys())
    with conn.cursor() as cursor:
        cursor.execute(sql, tuple(where_.values()))
        return (DATACLASSMAP[table](*record) for record in cursor.fetchall())


def insert(conn: Any,
           table: str,
           data: Dataclass) -> Optional[int]:
    """Run an INSERT into a table"""
    dict_ = {TABLEMAP[table].get(k): v for k, v in asdict(data).items()
             if v is not None and k in TABLEMAP[table]}
    sql = f"INSERT INTO {table} ("
    sql += ", ".join(f"{k}" for k in dict_.keys())
    sql += ") VALUES ("
    sql += ", ".join("%s" for _ in dict_.keys())
    sql += ")"
    with conn.cursor() as cursor:
        cursor.execute(sql, tuple(dict_.values()))
        return cursor.rowcount


def diff_from_dict(old: Dict, new: Dict) -> Dict:
    """Construct a new dict with a specific structure that contains the difference
between the 2 dicts in the structure:

diff_from_dict({"id": 1, "data": "a"}, {"id": 2, "data": "b"})

Should return:

{"id": {"old": 1, "new": 2}, "data": {"old": "a", "new": "b"}}
    """
    dict_ = {}
    for key in old.keys():
        dict_[key] = {"old": old[key], "new": new[key]}
    return dict_
