import json
import logging
import mysql.connector
import os
from kafka import KafkaConsumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mysql_config = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', 'root'),
    'database': os.getenv('MYSQL_DB_NAME', 'KA'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'autocommit': True
}

try:
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()

    create_table_query = '''
        CREATE TABLE IF NOT EXISTS word_frequency (
            word VARCHAR(255),
            entity VARCHAR(255),
            frequency INTEGER,
            PRIMARY KEY (word, entity)
        )
    '''
    cursor.execute(create_table_query)
    logger.info("Connected to MySQL database.")
except mysql.connector.Error as e:
    logger.error(f"Error connecting to MySQL database: {e}")
    exit(1)


def update_word_frequency(word, entity):
    try:
        insert_query = '''
            INSERT INTO word_frequency (word, entity, frequency)
            VALUES (%s, %s, 1)
            ON DUPLICATE KEY UPDATE frequency = frequency + 1
        '''
        cursor.execute(insert_query, (word, entity))
        logger.info(f"Updated frequency for word '{word}' and entity '{entity}'")
    except mysql.connector.Error as e:
        logger.error(f"MySQL error: {e}")


def consume_messages():
    try:
        consumer = KafkaConsumer(
            'wordentity',
            bootstrap_servers=[os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')],
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='my-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )

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