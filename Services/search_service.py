import threading
from utils.utils import retrieve_url_data, get_properties
from Services.llm_service import LLMService
from brave import Brave


class SearchService(LLMService):

    def __init__(self, model=None, url=None):
        super().__init__()
        self.configs = get_properties()
        self.brave = Brave(api_key=self.configs.get('BRAVE_API_KEY').data)

    def summarize_web_results(self, url, content, query):
        text = []
        retrieve_url_data(url, text)
        response = self.summarize(text[0][:29000], query)
        content.append(response)

    def query(self, query):
        search_response = ''
        try:
            search_query = self.form_search_query(query)
            print(search_query)
            num_results = 6
            search_results = self.brave.search(q=search_query, count=num_results,
                                               # result_filter='news',
                                               freshness='py',
                                               spellcheck=True,
                                               raw=True)  #

            news_results = search_results["web"]["results"]
            doc_urls = [doc["url"] for doc in news_results]
            content = []
            threads = []
            for i, url in enumerate(doc_urls):
                execThread = threading.Thread(target=retrieve_url_data, args=(url, content))
                threads.append(execThread)
                execThread.start()

            for exec_thread in threads:
                exec_thread.join()
            print('')
            print('final summary \n')
            joined_content = '\n'.join(content)
            #print(joined_content)
            search_response = self.summarize(joined_content[:29000], query)
            print(search_response)

        except Exception as ex:
            print(str(ex))
            return search_response
