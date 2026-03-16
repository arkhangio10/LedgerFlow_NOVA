import asyncio
import os
from dotenv import load_dotenv

load_dotenv('../.env')

from nova_act import NovaAct

def main():
    try:
        with NovaAct(starting_page='http://localhost:3001/invoices.html', ignore_https_errors=True) as nova:
            print('Nova Act started successfully on http://localhost:3001/invoices.html!')
            screenshot = nova.page.screenshot()
            print(f"Screenshot bytes: {len(screenshot)}")
            res = nova.act("What is the title of this page?")
            print(f"Act result: {res}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
