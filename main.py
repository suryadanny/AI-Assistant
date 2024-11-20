from Services.llm_service import LLMService
from Services.pdf_service import PdfService
from Services.search_service import SearchService
from Services.gsuite_service import GSuiteService
from groq import Groq
from jproperties import Properties
import argparse

from utils.utils import get_properties


def main():
    parser = argparse.ArgumentParser(description="Your personal assistant")

    parser.add_argument("command", nargs='+', help="your command to the assistant")
    args = parser.parse_args()
    #print(args.command)
    command = ' '.join(args.command)

    name = get_properties().get('name').data
    print(f'hello {name}')

    print(f'your command to the assistant - {command}')

    router = LLMService()
    pdf_service = PdfService('llama3.2', None)
    search_service = SearchService()
    gsuite_service = GSuiteService()
    #service.get_recent_emails()

    required_service = router.find_required_service(command)
    if 'unidentified' in required_service:
        print('couldn\'t identify the command properly, please frame it properly')

    if required_service == 'email_send':
        gsuite_service.gmail_send_email(command)
    elif required_service == 'email_reply':
        gsuite_service.get_recent_emails()
    elif required_service == 'pdf_service':
        pdf_service.find_answer(command)
    elif required_service == 'meeting':
        gsuite_service.set_meeting_required(command)
    elif required_service == 'search':
        search_service.query(command)

    #response = email_service.create_google_meet_link()
    # llmService = LLMService()
    # type_of_data = llmService.is_personal_or_private("find out my financial data")
    #print('answer')


if __name__ == '__main__':
    main()
