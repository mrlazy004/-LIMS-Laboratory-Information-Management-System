"""Shared response helpers and serialisers."""
from bson import ObjectId
from datetime import datetime
import json


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


def serialise(doc):
    """Convert a MongoDB document to a JSON-serialisable dict."""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialise(d) for d in doc]
    d = dict(doc)
    if "_id" in d:
        d["_id"] = str(d["_id"])
    for k, v in d.items():
        if isinstance(v, ObjectId):
            d[k] = str(v)
        elif isinstance(v, datetime):
            d[k] = v.isoformat()
    return d


def ok(data=None, message="Success", status=200):
    body = {"success": True, "message": message}
    if data is not None:
        body["data"] = data
    return body, status


def err(message="Error", status=400, detail=None):
    body = {"success": False, "error": message}
    if detail:
        body["detail"] = detail
    return body, status


def paginate(collection, query, page, per_page, sort=None):
    sort = sort or [("created_at", -1)]
    total = collection.count_documents(query)
    cursor = collection.find(query).sort(sort).skip((page - 1) * per_page).limit(per_page)
    items = serialise(list(cursor))
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    }
