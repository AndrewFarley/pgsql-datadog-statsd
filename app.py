#!/usr/bin/env python

# Imports
from datadog import initialize, statsd
import yaml
import sys
import datetime
import os
import glob
import traceback
import time
import urlparse
import psycopg2

# Print on startup
print("Starting up...")
separator = "=========================="
print(separator)

# Current folder
dir_path = os.path.dirname(os.path.realpath(__file__))

# Initialize datadog
STATSD_HOST=os.environ.get('STATSD_HOST', 'localhost')
print("Using STATSD_HOST: {}".format(STATSD_HOST))
STATSD_PORT=os.environ.get('STATSD_PORT', '8125')
print("Using STATSD_PORT: {}".format(STATSD_PORT))
initialize(
    statsd_host=STATSD_HOST,
    statsd_port=STATSD_PORT,
)

# Time increment (in seconds)
TIME_BETWEEN_REQUESTS = int(os.environ.get('TIME_BETWEEN_REQUESTS', 60))
print("Using TIME_BETWEEN_REQUESTS: {}".format(TIME_BETWEEN_REQUESTS))

# Initialize database configuration from Connection URL String
DB_URI = os.environ.get('DATABASE_URI', 'postgres://test:test@localhost/test')
result = urlparse.urlparse(DB_URI)
username = result.username
password = result.password
hostname = result.hostname
port     = result.port if result.port else 5432
database = result.path[1:]
print("Using DB_URI: postgres://{}:<omitted>@{}:{}/{}".format(username, hostname, port, database))

# Re-usable connection global
connection = False

# Simple exponential backoff function
def backoff(attempt):
    waittime = min(60, 2 ** attempt)
    print("after waiting {} seconds...".format(waittime))
    time.sleep(waittime)

# Simple merge dicts with overriding
def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        if isinstance(dictionary, dict):
            result.update(dictionary)
    return result

# Connect to database, with exponential backoff
def getPGSQLConnection(retries=0):
    global connection
    if connection:
        try:
            # print("returning existing cursor connection")
            connection.cursor().execute('select 1') # make sure its alive
            return connection
        except:
            # print("Connection must be dead...")
            connection = False

    if retries >= 5:
        raise Exception("Unable to connect to database {}".format(DB_URI))
        exit(1)

    print("Trying to connect to database {}".format(DB_URI))

    try:
        connection = psycopg2.connect( 
            database = database,
            user = username,
            password = password,
            host = hostname,
            port = port
        )
        return connection
    except:
        print("Exception while trying to connect to database, retrying...")
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        backoff(retries)
        return getPGSQLConnection(retries + 1)

def fetchOne(cur, query):
    cur.execute(query)
    return cur.fetchone()[0]

# First, load our queries from any .yaml files within this folder or any subfolders of /app
queries = {}
for file in glob.glob("{}/**/*.yaml".format(dir_path)):
    with open(file) as f:
        new_queries = yaml.safe_load(f)
        queries = merge_dicts(queries, new_queries)

print("Found queries:")
if not queries or len(queries) < 1:
    print("  ERROR: NONE FOUND, please mount some into a subfolder of /app")
    time.sleep(60)
    exit(1)
for key, value in queries.items():
    print("  Key: {}".format(key))
    print("    Value: {}".format(value))
    
# Then connect to our database and/or make sure the DB connection is functional
current_conn = getPGSQLConnection()
current_cursor = current_conn.cursor()

# And fetch our queries
while True:
    print(separator)
    print("Starting loop at: {}".format(datetime.datetime.now()))
    start = time.time()
    
    for key, query in queries.items():
        # Fetch the value
        try:
            print("Fetching {} - {}".format(key, query))
            result = fetchOne(current_cursor, query)
        except psycopg2.ProgrammingError as e:
            print("Error, skipping key: {}".format(key))
            current_conn.rollback()
            continue
        except:
            print("Unknown exception while fetching key")
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            current_conn.rollback()
            continue

        try:
            # Grab the right helper name based on the last octet from the key
            func_name = key.split('.')[-1]
            func = getattr(statsd, func_name)
            if not callable(func):
                print("ERROR: function {} is not valid on the dogstatsd object.\n  Please see: http://datadogpy.readthedocs.io/en/latest/#datadog.dogstatsd.base.DogStatsd".format(func_name))
            # Get the key (without the func name)
            key = key.rsplit('.', 1)[0]
            # Ship to statsd and print it with our desired function
            print("  Result: {}".format(result))
            func(key, result)
        except Exception as e:
            print("Exception while trying to call statsd: {}".format(e))

    # If we have taken too little time, wait until the next recurrance time
    time_remaining = TIME_BETWEEN_REQUESTS - (time.time() - start)
    if time_remaining > 0:
        print('Waiting for: {} seconds'.format(time_remaining))
        time.sleep(time_remaining)
