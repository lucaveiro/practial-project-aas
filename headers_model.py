import re
import pandas as pd
from email import policy
from email.parser import BytesParser
from sklearn.preprocessing import OneHotEncoder


def extract_content(msg):
    content = ""
    if msg.is_multipart():
        # Recursively process all parts
        for part in msg.iter_parts():
            content += extract_content(part)
    else:
        # Process non-multipart content
        content_type = msg.get_content_type()
        if content_type in ["text/plain", "text/html"]:
            try:
                return msg.get_payload(decode=True).decode(msg.get_content_charset(), errors="replace") + "\n"
            except Exception as e:
                print(f"Error decoding payload: {e}")
    return content

def extract_server_names(received_headers):
    server_names = []
    for header in received_headers:
        # Regex to match domain or server names in "by" or "from" fields
        match = re.search(r'\bby\s+([\w.-]+)|\bfrom\s+([\w.-]+)', header, re.IGNORECASE)
        if match:
            # Take the first non-empty group (by or from)
            server_name = match.group(1) or match.group(2)
            server_names.append(server_name)
    return server_names

def extract_certifying_authorities(auth_results):
    authorities = []
    for result in auth_results:
        # Regex to capture authority names from authentication results (e.g., "spf=pass (domain.com)")
        match = re.search(r'(\w+)=\w+', result)
        if match:
            authority = match.group(1)  # Capture the authentication method (e.g., spf, dkim, dmarc)
            authorities.append(authority)
    return authorities

def clean_duplicates_in_cell(value):
    if pd.isnull(value):  # Handle NaN values
        return value
    # Split the content by ';', strip whitespace, deduplicate, and recombine
    items = [item.strip() for item in value.split(';')]  # Split and clean each item
    unique_items = list(dict.fromkeys(items))  # Maintain order and remove duplicates
    return ';'.join(unique_items)

def cleaning(headers_dataset):
    headers_dataset['certifying_authorities'] = headers_dataset['certifying_authorities'].apply(clean_duplicates_in_cell)

    # Replace missing values with "unknown"
    headers_dataset['reply_to_header'].fillna('unknown', inplace=True)

    # Replace missing values with False
    headers_dataset['reply_is_same_as_from'].fillna(False, inplace=True)

    # Replace missing values with "missing"
    headers_dataset['certifying_authorities'].fillna('missing', inplace=True)

    # Strip leading/trailing spaces and lowercase all object columns
    headers_dataset = headers_dataset.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    headers_dataset = headers_dataset.applymap(lambda x: x.lower() if isinstance(x, str) else x)

    return headers_dataset  # Ensure the cleaned dataset is returned


def encoding(headers_dataset):
    fields_to_encode = ["ham or spam","from_header","reply_to_header","is_no_reply", "reply_is_same_as_from", "content_type_header", "certifying_authorities"]
    encoder = OneHotEncoder(handle_unknown="ignore", max_categories=30, sparse=False)

    #Apply encoding to the selected fields
    encoded_recommended_headers = encoder.fit_transform(headers_dataset[fields_to_encode])

    #Create a DataFrame with the encoded values
    encoded_columns = encoder.get_feature_names_out(fields_to_encode)
    encoded_df = pd.DataFrame(encoded_recommended_headers, columns=encoded_columns)

    #Combine the encoded columns with the rest of the dataset (dropping original encoded fields)
    processed_headers = pd.concat(
        [
            headers_dataset.drop(columns=fields_to_encode).reset_index(drop=True),
            encoded_df.reset_index(drop=True),
        ],
        axis=1,
    )

    return processed_headers


def build_object(eml_file):
    if eml_file.endswith('.eml'):
        data = []
        try:
            # Open and parse the .eml file
            with open(eml_file, 'rb') as fp:
                msg = BytesParser(policy=policy.default).parse(fp)

            # Access headers
            from_header = msg['from']
            reply_to_header = msg['reply-to']
            content_type_header = msg['content-type']

            # Extract only the type without additional parameters
            content_type_header = content_type_header.split(";")[0]

            authenticated_results_header = msg.get_all('authentication-results', [])

            # Calculate additional columns
            reply_is_same_as_from = (
                (from_header and reply_to_header) and 
                (from_header.strip().lower() == reply_to_header.strip().lower())
            )

            certifying_authorities = "; ".join(extract_certifying_authorities(authenticated_results_header))

            is_no_reply = any(substring in from_header.lower() for substring in ["noreply", "no-reply"]) if from_header else False

            # Append the data as a row
            data.append([
                'ham',
                from_header,
                is_no_reply,
                reply_to_header,
                reply_is_same_as_from,
                content_type_header,
                certifying_authorities
            ])

        except Exception as e:
            print(f"An error occurred while processing {eml_file}: {e}")

        # Convert the list to a DataFrame
        df = pd.DataFrame(data, columns=[
            'ham or spam',
            'from_header',
            'is_no_reply',
            'reply_to_header',
            'reply_is_same_as_from',
            'content_type_header',
            'certifying_authorities'
        ])

        # Clean the data
        df = cleaning(df)

        return encoding(df)

    else:
        return "Not a valid file extension, please try an .eml file"
