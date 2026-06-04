import requests

URL = 'http://127.0.0.1:5000'

def test_new_page():
    r = requests.post(URL + '/WebSite', json={"name": "first"})
    first_id = r.json()["new_page"]["id"]
    r = requests.post(URL + '/WebSite', json={"name": "second", "from_page_ids": [first_id]})
    r = requests.post(URL + '/WebSite', json={"name": "third"})
    return first_id

def list_all_pages():
    r = requests.get(URL + '/WebSite')
    pages = r.json()
    for p in pages: print(p["name"])

def test_reachability(page_ids):
    r = requests.post(URL + '/WebSite/analyse', json={"page_ids": page_ids})
    print(r.json())

def get_all_page_ids():
    r = requests.get(URL + '/WebSite')
    pages = r.json()
    return [page["id"] for page in pages]

def get_pages_with_one_exit():
    r = requests.get(URL + '/WebSite/exits/1')
    print(r.json())

def get_one_page_by_id(id):
    r = requests.get(URL + '/WebSite/' + id)
    print(r.json())

if __name__ == '__main__':
    first_id = test_new_page()
    list_all_pages()
    all_page_ids = get_all_page_ids()
    test_reachability(all_page_ids)
    get_pages_with_one_exit()
    get_one_page_by_id(first_id)