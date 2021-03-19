#flowers.py

import os
import json
import asyncio
import random
import requests

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TREFLE_TOKEN')

response = requests.get(f'https://trefle.io/api/v1/plants?token={TOKEN}&filter[scientific_name]=anemone')
print(response.json())