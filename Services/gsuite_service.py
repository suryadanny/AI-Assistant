import random
import string
from email.message import EmailMessage

import pytz
from google.auth.transport.requests import Request
from Services.llm_service import LLMService
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
import base64
import os

import datetime
import time

from utils.utils import get_properties
import re


def _get_email_data(message):
    #print(message)
    headers = message['payload']['headers']
    email_data = {}
    for header in headers:
        if header['name'] == 'From':
            match = re.search(r'<(.*?)>', header['value'])
            # Extracted text
            extracted_text = match.group(1) if match else None
            email_data['From'] = extracted_text if extracted_text else ''
        elif header['name'] == 'To':
            match = re.search(r'<(.*?)>', header['value'])
            # Extracted text
            extracted_text = match.group(1) if match else None
            email_data['To'] = extracted_text
        elif header['name'] == 'Subject':
            email_data['Subject'] = header['value']

    # Get the snippet (preview of the email)
    email_data['Snippet'] = message.get('snippet', 'No content')
    # Decode the email body
    body_data = ''
    if 'data' in message['payload']['body']:
        body_data = message['payload']['body']['data']
    elif 'data' in message['payload']['parts'][0]['body']:
        body_data = message['payload']['parts'][0]['body']['data']
    body = base64.urlsafe_b64decode(body_data).decode('utf-8')
    email_data['body'] = body
    return email_data


class GSuiteService(LLMService):

    def __init__(self):
        super().__init__()
        self.scopes = ['https://www.googleapis.com/auth/gmail.readonly',
                       'https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/calendar.events']
        self.configs = get_properties()
        self.primary = self.configs.get('primary').data
        self.name = self.configs.get('name').data
        self.allowed_recipients = set(self.configs.get('reply_to').data.split(','))
        self.creds = self._authenticate()
        self.email_service = build('gmail', 'v1', credentials=self.creds)
        self.calender_service = build('calendar', 'v3', credentials=self.creds)
        self.contacts = {'surya': 'suryadhaneshwarlingam@gmail.com', 'lingam': 'sdlingam@tamu.edu'}

    def _authenticate(self):
        creds = None
        # Check if token.json exists, which stores the user's access and refresh tokens
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.scopes)
        # If no token.json, request user to log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secret.json', self.scopes)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return creds

    def _reply_required(self, snippet):
        prompt = "Given the email message - \"" + snippet + "\", do i have to reply back or not, consider being polite ? just yes or no"
        response = self.query_local(prompt)
        return True if 'yes' in response.lower() else False

    def gmail_send_email(self, command):
        recipient = self.find_name_to_email(command).lower()
        if recipient not in self.contacts:
            print('Email to this contact can\'t be automated')
            return

        print(f'Sending email to {recipient} - {self.contacts[recipient]}')
        privacy_level = self.is_personal_or_private(command)

        subject_prompt = 'write a subject line for an email from '+ str(self.name) + ' , just give me the subject line no other explanation, addressing the given context - ' + command

        body_prompt = 'Write an email body from '+ str(self.name) +', just give me the direct body with no other explanation so that i can directly add it in the email, addressing the given the context - ' + command

        if privacy_level == 'private':
            email_body = self.query_local(body_prompt)
            subject_line = self.query_local(subject_prompt)
        else:
            email_body = self._query_groq(body_prompt)
            subject_line = self._query_groq(subject_prompt)
        send_message = {'data': 'HI'}

        try:
            # create gmail api client

            message = EmailMessage()

            message.set_content(email_body)

            message["To"] = self.contacts[recipient]
            message["From"] = self.primary
            message["Subject"] = subject_line

            # encoded message
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            create_message = {"raw": encoded_message}
            # pylint: disable=E1101
            send_message = (
                self.email_service.users()
                .messages()
                .send(userId="me", body=create_message)
                .execute()
            )

            print(f'email sent successfully - id: {send_message["id"]}\n')

        except HttpError as error:
            print(f"An error occurred: {error}")
            draft = None

        return send_message

    def get_recent_emails(self, num_emails=10):
        try:
            # Get current time and one hour ago in RFC 3339 format (required by Gmail API)
            current_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
            cdt_timezone = pytz.timezone("America/Chicago")
            current_time_cdt = current_time.astimezone(cdt_timezone)
            # current_time = datetime.datetime.utcnow()
            print(current_time_cdt)
            one_hour_ago = current_time_cdt - datetime.timedelta(hours=4)
            one_hour_ago_unix = int(time.mktime(current_time_cdt.timetuple()))
            email_id = self.primary
            after_date_str = current_time_cdt.strftime('%Y/%m/%d')
            # Define the Gmail search query for messages in the last hour
            query = f'after:{after_date_str} category:primary label:inbox'
            print(query)

            # List messages based on the query and limit to the most recent emails
            results = self.email_service.users().messages().list(userId=email_id, q=query,
                                                                 maxResults=num_emails).execute()
            messages = results.get('messages', [])
            print(len(messages))
            # Retrieve details for each message
            for msg in messages:
                msg_data = (self.email_service.users().messages()
                            .get(userId=email_id, id=msg['id'], format='full').execute())
                print(msg)
                #print(str(msg.data))
                snippet = msg_data.get('snippet', 'No content')

                received_time = msg_data['internalDate']
                print(f"Time: {received_time}, Snippet: {snippet}")
                email_data = _get_email_data(msg_data)
                print(f"sender : {email_data['From']}")
                if email_data['From'] in self.allowed_recipients and self._reply_required(snippet):
                    msg_id = msg['id']
                    thread_id = msg['threadId']
                    print(f'sending back a reply to email with msg id - {msg_id}, thread Id  - {thread_id}')
                    self.reply_to_message(msg_id, thread_id, email_data)

                #self.is_meeting_required(msg)


        except HttpError as error:
            print(f'An error occurred: {error}')

    def set_meeting_required(self, prompt):
        response = self.is_meeting_required(prompt)
        print(response)
        attendees = []
        attendees.append(self.primary)
        if len(response) >= 7 and response[6].strip().lower() in self.contacts:
            #print(response[6].strip().lower())
            attendees.append(self.contacts[response[6].strip().lower()])

        data = {}
        data['attendees'] = attendees
        data['calendar_id'] = self.primary
        data['year'] = int(response[3].strip())
        data['day'] = int(response[1].strip())
        data['month'] = int(response[2].strip())
        data['time'] = response[4]
        data['subject'] = response[5]
        print(data)
        self.create_google_meet_link(data)

    def _build_reply_for_email(self, msg):
        prompt = 'Build a reply to the message, just give me the body of the constructed message - ' + msg
        if self.is_personal_or_private(msg) == 'private':
            print('private')
            return self.query_local(prompt)
        else:
            print('public')
            return self._query_groq(prompt)

    def reply_to_message(self, msg_id, thread_id, email_data):

        body = email_data['body']

        reply_body = self._build_reply_for_email(body)

        reply_message = EmailMessage()

        reply_message.set_content(reply_body)

        reply_message["To"] = email_data['From']
        reply_message["From"] = email_data['To']
        reply_message["Subject"] = email_data['Subject']
        reply_message['In-Reply-To'] = msg_id  # Link to the original message
        reply_message['References'] = msg_id
        # encoded message
        encoded_message = base64.urlsafe_b64encode(reply_message.as_bytes()).decode('utf-8')

        create_message = {"raw": encoded_message, "threadId": thread_id}
        # pylint: disable=E1101
        send_message = (
            self.email_service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )

        print(f'mail id: {send_message["id"]}\n')

    def create_google_meet_link(self, meet_data):
        calendar_id = meet_data['calendar_id']

        # Define the event details with minimal information for Google Meet link creation
        characters = string.ascii_letters + string.digits
        unique_meet_id = ''.join(random.choice(characters) for _ in range(10))
        print(unique_meet_id)
        attendees_emails = meet_data['attendees']
        times = meet_data['time'].split(':')

        event = {
            'summary': meet_data['subject'],
            'description': meet_data['subject'],
            'start': {
                'dateTime': datetime.datetime(year=meet_data['year'], month=meet_data['month'], day=meet_data['day'],
                                              hour=int(times[0].strip()), minute=int(times[1].strip()), second=0).isoformat() ,
                'timeZone': 'America/Chicago',
            },
            'end': {
                'dateTime': (datetime.datetime(year=meet_data['year'], month=meet_data['month'], day=meet_data['day'],
                                               hour=int(times[0].strip()), minute=int(times[1].strip()), second=0) + datetime.timedelta(
                    minutes=30)).isoformat() ,
                'timeZone': 'America/Chicago',
            },
            'attendees': [{'email': email} for email in attendees_emails],
            'conferenceData': {
                'createRequest': {
                    'requestId': unique_meet_id  # Unique request ID to prevent duplicate creation
                }
            },
        }

        try:
            # Insert the event with conference data to generate Google Meet link
            created_event = self.calender_service.events().insert(calendarId=calendar_id, body=event,
                                                                  conferenceDataVersion=1).execute()

            # Extract the Google Meet link
            meet_link = created_event.get('conferenceData', {}).get('entryPoints', [])[0].get('uri')

            if meet_link:
                print(f"Google Meet link: {meet_link}")
                return meet_link
            else:
                print("Failed to create Google Meet link.")
                return None

        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
