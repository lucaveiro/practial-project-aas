import os
import chardet
import unicodedata
import pandas as pd
from email import policy
from bs4 import BeautifulSoup
from email.parser import BytesParser


def clean_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text()

def fix_misencoded_text(text):
    try:
        # Detect encoding
        detected = chardet.detect(text.encode('utf-8', errors='ignore'))
        encoding = detected['encoding'] if detected['confidence'] > 0.7 else 'utf-8'
        # Decode and re-encode properly
        fixed_text = text.encode('latin1').decode('utf-8')  # Adjust encodings as needed
        return unicodedata.normalize('NFKD', fixed_text)
    except Exception:
        # If decoding fails, return the original text
        return text

def extract_content_from_multipart(msg):
    content = ''
    if msg.is_multipart():
        html_part = None
        text_part = None

        for part in msg.iter_parts():
            content_type = part.get_content_type().lower()
            charset = 'utf-8'

            if 'html' in content_type:
                html_part = part
            elif 'plain' in content_type:
                text_part = part

        if html_part:
            try:
                content = clean_html(html_part.get_payload(decode=True).decode(charset, errors='replace'))
            except Exception as e:
                print(f"Error decoding HTML part: {e}")
        elif text_part:
            try:
                content = text_part.get_payload(decode=True).decode(charset, errors='replace')
            except Exception as e:
                print(f"Error decoding text part: {e}")
    else:
        try:
            charset = msg.get_content_charset() or 'utf-8'
            content = msg.get_payload(decode=True).decode(charset, errors='ignore')
            content = fix_misencoded_text(content)  # Fix misencoded text
        except Exception as e:
            print(f"Error decoding simple payload: {e}")

    return content

def build_object(eml_file):
    if eml_file.endswith('.eml'):
        data = []
        print(f"Processing file: {eml_file}")
        try:
            with open(eml_file, 'rb') as fp:
                msg = BytesParser(policy=policy.default).parse(fp)

            content = fix_misencoded_text(extract_content_from_multipart(msg))

            if content:
                data.append(['ham', content])
        except Exception as e:
            print(f"An error occurred while processing {eml_file}: {e}")

        # Convert the list to a DataFrame
        df = pd.DataFrame(data, columns=['ham or spam', 'content'])
        return df
    else:
        return "Not a valid file extension, please try an .eml file"
