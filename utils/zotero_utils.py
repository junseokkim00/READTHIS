from pyzotero import zotero
import time
class Zotero:
    def __init__(self, library_id, library_type, api_key):
        self.zot = zotero.Zotero(library_id=library_id,
                                 library_type=library_type,
                                 api_key=api_key)
    def retrieve_collection(self):
        collection_dict={}
        time.sleep(2.05)
        collections = self.zot.collections()
        for idx in range(len(collections)):
            name, key = collections[idx]['data']['name'], collections[idx]['data']['key']
            collection_dict[name] = key
        return collection_dict
    
    def retrieve_collection_papers(self, key):
        collection_papers=[]
        items = self.zot.collection_items(key)
        for idx in range(len(items)):
            try:
                title, DOI = items[idx]['data']['title'], items[idx]['data']['DOI']
                collection_papers.append((title, DOI))
            except:
                pass
        return collection_papers