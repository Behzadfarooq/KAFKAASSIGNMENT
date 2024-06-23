import json
from kafka import KafkaConsumer
import mysql.connector
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kafka Consumer setup
consumer = KafkaConsumer(
    'word-entity-topic',
    bootstrap_servers=['kafka:9092'],  
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='my-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# MySQL Database configuration
mysql_config = {
    'host': 'localhost',  # Assuming MySQL is running on localhost
    'user': 'root',  # Assuming MySQL user is root
    'password': 'root',  # Assuming MySQL password is root
    'database': 'kafka',  # Your database name
    'port': 3306  # MySQL default port
}

# Connect to MySQL database
try:
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()

    # Create table if not exists
    create_table_query = '''
        CREATE TABLE IF NOT EXISTS word_frequency (
            word VARCHAR(255),
            entity VARCHAR(255),
            frequency INTEGER,
            PRIMARY KEY (word, entity)
        )
    '''
    cursor.execute(create_table_query)
    conn.commit()
    logger.info("Connected to MySQL database.")
except mysql.connector.Error as e:
    logger.error(f"Error connecting to MySQL database: {e}")
    exit(1)

# Function to update word frequency in the database
def update_word_frequency(word, entity):
    try:
        insert_query = '''
            INSERT INTO word_frequency (word, entity, frequency)
            VALUES (%s, %s, 1)
            ON DUPLICATE KEY UPDATE frequency = frequency + 1
        '''
        cursor.execute(insert_query, (word, entity))
        conn.commit()
        logger.info(f"Updated frequency for word '{word}' and entity '{entity}'")
    except mysql.connector.Error as e:
        conn.rollback()
        logger.error(f"MySQL error: {e}")

# Main consumer loop
def consume_messages():
    try:
        for message in consumer:
            try:
                word = message.value['word']
                entity = message.value['entity']
                logger.info(f"Consumed: {message.value}")
                update_word_frequency(word, entity)
            except KeyError as ke:
                logger.error(f"KeyError: {ke}. Message: {message}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    except KeyboardInterrupt:
        logger.info("Consumer stopped by keyboard interrupt.")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    logger.info("Starting consumer...")
    consume_messages()

