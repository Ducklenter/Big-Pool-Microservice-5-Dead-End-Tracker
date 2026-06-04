import random
import uuid
from typing import Optional
from collections import defaultdict
from flask import Flask, jsonify, request

app = Flask(__name__)

class Exit:
    def __init__(self, target_page_id: Optional[str] = None):
        self.target_page_id = target_page_id

class Page:
    def __init__(self, id: str, name: str, exits: list[Exit] = None):
        self.id = id
        self.name = name
        self.exits = exits if exits is not None else []

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "exits": [{"target_page_id": e.target_page_id} for e in self.exits],
        }

WebSite: dict[str, Page] = {}

def _pages_with_exit_count(exit_count: int) -> list[Page]:
    return [page for page in WebSite.values() if len(page.exits) == exit_count]

def _link_source_to_page(source: Page, new_page: Page):
    unset = next((e for e in source.exits if e.target_page_id is None), None)
    if unset:
        unset.target_page_id = new_page.id
    else:
        source.exits.append(Exit(target_page_id=new_page.id))

    already_linked = any(e.target_page_id == source.id for e in new_page.exits)
    if not already_linked:
        unset_back = next((e for e in new_page.exits if e.target_page_id is None), None)
        if unset_back:
            unset_back.target_page_id = source.id
        else:
            new_page.exits.append(Exit(target_page_id=source.id))

# Flood fill to check for invalid map

def analyse_pages(page_ids: list[str]) -> dict:
    visit_count: dict[str, int] = defaultdict(int)
    visited_sources: set[str] = set()
    stack = list(page_ids)

    while stack:
        page_id = stack.pop()
        if page_id in visited_sources:
            continue
        visited_sources.add(page_id)

        page = WebSite.get(page_id)
        if page is None:
            continue

        for exit_obj in page.exits:
            target = exit_obj.target_page_id
            if target is None:
                continue
            visit_count[target] += 1
            if target not in visited_sources:
                stack.append(target)
    
    results = []
    for page_id in page_ids:
        if page_id not in WebSite:
            results.append({"id": page_id, "status": "unknown"})
            continue

        page = WebSite[page_id]
        exit_count = len(page.exits)
        visits = visit_count.get(page_id, 0)

        if visits == 0:
            status = "inaccessible"
        elif visits < exit_count:
            status = "one_way"
        else:
            status = "reachable"
        
        results.append({
            "id": page_id,
            "name": page.name,
            "exit_count": exit_count,
            "visit_count": visits,
            "status": status,
        })

    return {"WebSite": results}

"""
GET("/WebSite")

will respond with a json containing every page's info
{'exits': [{'target_page_id: id},], 'id': 'page id', 'name': 'page name'}
"""
@app.get("/WebSite")
def list_pages():
    return jsonify([m.to_dict() for m in WebSite.values()])

"""
GET('/Website/' + page id)

returns the same as above but just one instead of multiple
"""
@app.get("/WebSite/<page_id>")
def get_page(page_id: str):
    page = WebSite.get(page_id)
    if not page:
        return jsonify({"error":f"Page {page_id} not found"}), 404
    return jsonify(page.to_dict())

"""
POST("/WebSite", json={"name": "somename", "from_page_ids": [some id, some other id, any number of page ids]})

this creates a new page and links it to the id of whatever page you want, if there is no page id supplied then it will be linked to a random page
with only one exit.
"""
@app.post("/WebSite")
def add_page():
    """
    
    """
    body = request.get_json() or {}
    new_id = f"page-{uuid.uuid4().hex[:8]}"
    new_name = body.get("name") or f"Page {new_id}"


    from_page_ids = body.get("from_page_ids") or []
    if isinstance(from_page_ids, str):
        from_page_ids = [from_page_ids]

    new_page = Page(id=new_id, name=new_name, exits=[Exit()])

    WebSite[new_id] = new_page

    if not from_page_ids:
        candidates = _pages_with_exit_count(1)
        pool = candidates if candidates else list(WebSite.values())
        pool = [p for p in pool if p.id != new_id]
        if pool:
            from_page_ids = [random.choice(pool).id]
    source_pages = []
    for from_id in from_page_ids:
        if from_id not in WebSite:
            continue
        _link_source_to_page(WebSite[from_id], new_page)
        source_pages.append(WebSite[from_id])

    return jsonify({
        "new_page": new_page.to_dict(),
        "source_page": [s.to_dict() for s in source_pages],
    }), 201
"""
POST("/WebSite/analyse", json={any, number, of, page, ids})

this will evaluate the all page ids passed and detect if every page is reachable. the only truely important thing
is the json has "status": "reachable" inside
"""
@app.post("/WebSite/analyse")
def analyse():
    body = request.get_json() or {}
    page_ids = body.get("page_ids")

    if not page_ids or not isinstance(page_ids, list):
        return jsonify({"error": f"Provide a JSON body with 'page_ids'"}), 400
    
    return jsonify(analyse_pages(page_ids))

""""
get("/WebSite/exits/some int value")
This returns all pages with x exits
"""
@app.get("/WebSite/exits/<int:exit_count>")
def get_pages_by_exit_count(exit_count: int):
    pages = [
        page.to_dict()
        for page in WebSite.values()
        if len(page.exits) == exit_count
    ]

    return jsonify(pages)

if __name__ == "__main__":
    app.run(port=5000)