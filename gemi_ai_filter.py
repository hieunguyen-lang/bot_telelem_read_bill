import os
import json
import re
from google import genai
from google.genai import types
from google.auth import default
from google.auth.credentials import Credentials
from google.auth import load_credentials_from_file


class GeminiBill_Analyzer:
    def __init__(self):
        # Lấy thông tin xác thực mặc định từ môi trường (ADC - Application Default Credentials)
        credentials, _ = load_credentials_from_file(
            "gemini-creds.json",
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        self.client = genai.Client(
            vertexai=True,
            project="e-caldron-463814-p7",
            location="global",
            credentials=credentials  
        )
        #gemini-2.5-pro
        #gemini-2.5-flash
        self.model = "gemini-2.5-pro"

    