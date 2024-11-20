from datetime import datetime

import requests
import json
from groq import Groq
from utils.utils import get_properties


class LLMService:
    def __init__(self):

        self.configs = get_properties()
        self.model = self.configs.get('local_model').data
        #print(self.model)
        if self.configs.get('local_url'):
            self.url = self.configs.get('local_url').data
            #print(self.url)
        else:
            self.url = "http://localhost:11434/api/generate"
        self.client = Groq(api_key=self.configs.get('api_key').data, )

    def find_name_to_email(self, command):
        prompt = 'Given the command - ' + str(command) + ''', find the name whom to send the email to, just give the 
        name and no other explanation is reuqired'''

        #private_or_public = self.is_personal_or_private(command)

        return self._query_groq(prompt).lower()

    def find_required_service(self, command):
        prompt = 'Given the command - ' + str(command) + ''' , forget previous commands, which category of task would
         it belong to among the given ones - email_send, email_reply, search, meeting, pdf . just give me the category, no explanation required.'''

        response = self._query_groq(prompt)

        if 'pdf' in command and response != 'pdf':
            response = 'pdf'

        if 'email' in response and 'send' in response:
            return 'email_send'
        elif 'email' in response and 'reply' in response:
            return 'email_reply'
        elif 'search' in response:
            return 'search'
        elif 'meeting' in response:
            return 'meeting'
        elif 'pdf' in response:
            return 'pdf_service'

        return 'unidentified'

    def is_personal_or_private(self, query):
        # chat_completion = self.client.chat.completions.create(
        #     messages=[
        #         {"role": "system",
        #          "content": ('''you are a router, you have to identify if there's is a requirement of personal data
        #          in user query asked, reply with private if there is a requirement of personal data otherwise reply
        #          with public''')},
        #         {"role": "user", "content": query}
        #     ],
        #     model="llama3-8b-8192",
        # )

        prompt = '''you are a router, you have to identify if there\'s is a requirement of personal data in user 
        content presented, reply with private if there is a requirement of personal data otherwise reply with public, 
        user content as follows - '''
        prompt += query
        response = self.query_local(prompt)
        #response = chat_completion.choices[0].message.content
        return 'private' if 'private' in response.lower() else 'public'

    def is_meeting_required(self, body):
        current_time = datetime.now()

        # Format the date and time as a string
        formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')

        prompt = "Given the message -  " + body + " , current datetime is " + formatted_time + ''', extract time , proper 
        date with month and year if date has already passed for this month consider the next month and email, 
        if no  date and time could be extracted return no- just give me  the answer in single line in this format -> 
        Yes/No, day(just number), month (in number), year , Time (24hrs format no am or pm needed), subject line, name of person (blank if no name)'''
        response = self._query_groq(prompt)
        response = response.split(',')
        return response

    def query_local(self, prompt):

        try:
            data = {'model': self.model, 'prompt': prompt, 'stream': False}
            response = requests.post(self.url, json=data)
            #print(str(response))
            response = response.json()
            return response['response']
        except Exception as ex:
            print(str(ex))

        return ""

    def _query_groq(self, query):
        chat_completion = self.client.chat.completions.create(
            messages=[
                {"role": "user",
                 "content": query,
                 }
            ],
            model="llama3-8b-8192",
        )

        # print(chat_completion.choices[0].message.content)
        chat_result = chat_completion.choices[0].message.content
        return chat_result

    def summarize(self, content, query):
        try:
            query = 'Answer the question - ' + query + ', based on the below search results: \n'
            query += content
            return self._query_groq(query)

        except Exception as ex:
            print(str(ex))

    def form_search_query(self, user_query):
        chat_completion = self.client.chat.completions.create(
            messages=[
                {"role": "system",
                 "content": ("As a fact-checking assistant, help me convert the following user input into a prompt"
                             " for google search. Only reply with the best converted prompt."
                             "Do not add quotes around the generated prompt."
                             "Your input will be directly sent to google search.")},
                {"role": "user", "content": user_query}
            ],
            model="llama3-8b-8192",
        )

        # print(chat_completion.choices[0].message.content)
        transformed_query = chat_completion.choices[0].message.content
        return transformed_query
