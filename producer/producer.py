import os
import json
import spacy
from bs4 import BeautifulSoup
from kafka import KafkaProducer

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

# Kafka Producer setup
producer = KafkaProducer(
    bootstrap_servers=['kafka:9092'],  # Changed to localhost
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Directory and file path settings
articles_dir = './articles'
html_list_file = './html.lst.0'

# Function to process individual files
def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    soup = BeautifulSoup(content, 'html.parser')
    text = soup.get_text()

    doc = nlp(text)
    for ent in doc.ents:
        message = {
            'word': ent.text,
            'entity': ent.label_
        }
        producer.send('word-entity-topic', value=message)
        print(f"Produced: {message}")

# Function to process the list of files
def process_files():
    with open(html_list_file, 'r') as file:
        files = file.readlines()

    for file_name in files:
        file_name = file_name.strip()
        file_path = os.path.join(articles_dir, file_name)
        if os.path.isfile(file_path):
            process_file(file_path)
        else:
            print(f"File not found: {file_path}")

if __name__ == "__main__":
    process_files()
    producer.flush()
