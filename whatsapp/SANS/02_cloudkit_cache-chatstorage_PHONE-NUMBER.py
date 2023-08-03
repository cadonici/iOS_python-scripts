import re
import sqlite3
import os
from collections import defaultdict

# Connecting to ChatStorage.sqlite database
conn_chatstorage = sqlite3.connect('ChatStorage.sqlite')
cursor_chatstorage = conn_chatstorage.cursor()

# Execute the query on ChatStorage.sqlite database
query_chatstorage = "SELECT ZMEDIALOCALPATH FROM ZWAMEDIAITEM WHERE ZMEDIALOCALPATH IS NOT NULL AND ZMEDIALOCALPATH NOT LIKE '%status%' ORDER BY ZMEDIALOCALPATH"
cursor_chatstorage.execute(query_chatstorage)

# Retrieve results from ChatStorage.sqlite
results_chatstorage = cursor_chatstorage.fetchall()

# Close ChatStorage.sqlite database connection
cursor_chatstorage.close()
conn_chatstorage.close()

# Connecting to cloudkit_cache.db database
conn_cloudkit = sqlite3.connect('cloudkit_cache.db')
cursor_cloudkit = conn_cloudkit.cursor()

# Execute the query on cloudkit_cache.db database and remove "Message/" from each value
query_cloudkit = "SELECT REPLACE(relativePath, 'Message/', '') FROM fileChanges WHERE relativePath LIKE '%whatsapp%' AND relativePath LIKE '%Message/Media%'  AND SIZE != 0 ORDER BY relativePath ASC"
cursor_cloudkit.execute(query_cloudkit)

# Retrieve results from cloudkit_cache.db
results_cloudkit = cursor_cloudkit.fetchall()

# Execute the new query on cloudkit_cache.db database
query_new = "SELECT REPLACE(relativePath, 'Message/', '') FROM Files WHERE relativePath LIKE '%/%/%/%.%' AND relativePath LIKE '%whatsapp%' AND deleted = 1"
cursor_cloudkit.execute(query_new)

# Retrieve results from cloudkit_cache.db for the new query
results_new = cursor_cloudkit.fetchall()

# Close cloudkit_cache.db database connection
cursor_cloudkit.close()
conn_cloudkit.close()

# Extract the values after the last '/' character and store them in a list
values_chatstorage = [row[0].split('/')[-1] for row in results_chatstorage]
values_cloudkit = [row[0].split('/')[-1] for row in results_cloudkit]
values_new = [row[0].split('/')[-1] for row in results_new]

# Convert the results to sets for comparison
set_chatstorage = set([row[0] for row in results_chatstorage])
set_cloudkit = set([row[0] for row in results_cloudkit])
set_new = set([row[0] for row in results_new])

# Find files that are present in cloudkit_cache.db or new query but not in ChatStorage.sqlite
values_not_in_chatstorage = (set_cloudkit | set_new) - set_chatstorage

# Connecting to ChatStorage.sqlite database for ZXMPPTHUMBPATH
conn_chatstorage_thumbpath = sqlite3.connect('ChatStorage.sqlite')
cursor_chatstorage_thumbpath = conn_chatstorage_thumbpath.cursor()

# Execute the query on ChatStorage.sqlite database to retrieve ZXMPPTHUMBPATH
query_thumbpath = "SELECT ZXMPPTHUMBPATH FROM ZWAMEDIAITEM WHERE ZXMPPTHUMBPATH IS NOT NULL AND ZXMPPTHUMBPATH NOT LIKE '%status%' ORDER BY ZXMPPTHUMBPATH"
cursor_chatstorage_thumbpath.execute(query_thumbpath)

# Retrieve results from ChatStorage.sqlite for ZXMPPTHUMBPATH
results_thumbpath = cursor_chatstorage_thumbpath.fetchall()

# Close ChatStorage.sqlite database connection for ZXMPPTHUMBPATH
cursor_chatstorage_thumbpath.close()
conn_chatstorage_thumbpath.close()

# Extract the values after the last '/' character and store them in a list
values_thumbpath = [row[0].split('/')[-1] for row in results_thumbpath]

# Find the values present in cloudkit_cache.db but not in ChatStorage.sqlite
values_not_in_chatstorage = (set_cloudkit | set_new) - set_chatstorage

# Filter values to exclude those with duplicates and different extensions
filtered_values = []
for value in values_not_in_chatstorage:
    if value.endswith(".thumb"):
        base_value = value[:-6]
        has_duplicate_with_different_extension = any(v != value and v.startswith(base_value) and not v.endswith(".thumb") for v in values_not_in_chatstorage if not v.endswith(".thumb"))
        if not has_duplicate_with_different_extension:
            filtered_values.append(value)
    else:
        has_duplicate_with_different_extension = any(v != value and v.startswith(value) and not v.endswith(".thumb") for v in values_not_in_chatstorage if not v.endswith(".thumb"))
        if not has_duplicate_with_different_extension:
            filtered_values.append(value)

# Connecting to ChatStorage.sqlite database for the thumbpath check
conn_chatstorage = sqlite3.connect('ChatStorage.sqlite')
cursor_chatstorage = conn_chatstorage.cursor()

# Query to fetch ZXMPPTHUMBPATH values from ZWAMEDIAITEM
query_thumbpath = "SELECT ZXMPPTHUMBPATH FROM ZWAMEDIAITEM"
cursor_chatstorage.execute(query_thumbpath)

# Retrieve ZXMPPTHUMBPATH results from ChatStorage.sqlite
results_thumbpath = cursor_chatstorage.fetchall()

# Close ChatStorage.sqlite database connection
cursor_chatstorage.close()
conn_chatstorage.close()

thumbpath_set = set(row[0] for row in results_thumbpath)

# Remove the values that have a match in the thumbpath_set
final_filtered_values = [value for value in filtered_values if value not in thumbpath_set]


# Replace values_not_in_chatstorage with the new filtered values
values_not_in_chatstorage = final_filtered_values

# Define a regular expression pattern to match 12-13 digit numbers
number_pattern = r"\b\d{12,13}\b"

# Count the occurrences of each number in cloudkit_cache.db
number_count = {}
for value in values_not_in_chatstorage:
    match = re.search(number_pattern, value)
    if match:
        number = match.group()
        number_count[number] = number_count.get(number, 0) + 1

# Sort the numbers by occurrence count in descending order
sorted_numbers = sorted(number_count.items(), key=lambda x: (-x[1], str(x[0])))

# Print the sorted numbers and their occurrence count
for number, count in sorted_numbers:
    print("Phone number: +", number, sep="")
    print("Number of deleted messages:", count)
    print()

