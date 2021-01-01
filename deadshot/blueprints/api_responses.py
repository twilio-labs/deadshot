from flask import make_response, jsonify, request

# This file defines a standard format for Flask API responses


def get_json_response(dict_object, code=200):
    return make_response(dict_object, code)


def get_object(object_name, properties, code=200):
    return make_response(jsonify({
        "code": code,
        object_name: properties
    }), code)


def create_object(object_name, properties):
    return get_object(object_name, properties, code=201)


def list_objects(page, page_size, items, total):
    count = len(items)

    base_url = request.base_url
    next_page = None
    if (page * page_size) < total:
        next_page = "{}?page={}&page_size={}".format(
            base_url,
            page + 1,
            page_size
        )

    previous_page = None
    if page > 1:
        previous_page = "{}?page={}&page_size={}".format(
            base_url,
            page - 1,
            page_size
        )

    return make_response(jsonify({
        "code": 200,
        "items": items,
        "meta": {
            "key": "items",
            "count": count,
            "total": total,
            "next": next_page,
            "previous": previous_page
        }
    }), 200)
