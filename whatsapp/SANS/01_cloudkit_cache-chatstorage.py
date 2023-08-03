import sqlite3

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

# Execute the query on FileChanges in cloudkit_cache.db database and remove "Message/" from each value
query_cloudkit = "SELECT REPLACE(relativePath, 'Message/', '') FROM FileChanges WHERE relativePath LIKE '%whatsapp%' AND relativePath LIKE '%Message/Media%' AND SIZE != 0 ORDER BY relativePath ASC"
cursor_cloudkit.execute(query_cloudkit)

# Retrieve results from cloudkit_cache.db
results_cloudkit = cursor_cloudkit.fetchall()

# Connecting to cloudkit_cache.db database again for the new query
conn_cloudkit = sqlite3.connect('cloudkit_cache.db')
cursor_cloudkit = conn_cloudkit.cursor()

# Execute the new query on Files in cloudkit_cache.db database
query_new = "SELECT REPLACE(relativePath, 'Message/', '') FROM Files WHERE relativePath LIKE '%/%/%/%.%' AND relativePath LIKE '%whatsapp%' AND deleted = 1"
cursor_cloudkit.execute(query_new)

# Retrieve results from cloudkit_cache.db for the new query
results_new = cursor_cloudkit.fetchall()

# Close cloudkit_cache.db database connection
cursor_cloudkit.close()
conn_cloudkit.close()

# Extract the values after the last '/' character and store them in a list
#values_chatstorage = [row[0].split('/')[-1] for row in results_chatstorage]
#values_cloudkit = [row[0].split('/')[-1] for row in results_cloudkit]
#values_new = [row[0].split('/')[-1] for row in results_new]

# Convert the results to sets for comparison
set_chatstorage = set([row[0] for row in results_chatstorage])
set_cloudkit = set([row[0] for row in results_cloudkit])
set_new = set([row[0] for row in results_new])

# Find the values present in cloudkit_cache.db and the new query but not in ChatStorage.sqlite
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
query_thumbpath = "SELECT ZXMPPTHUMBPATH FROM ZWAMEDIAITEM WHERE ZXMPPTHUMBPATH IS NOT NULL AND ZXMPPTHUMBPATH NOT LIKE '%status%' ORDER BY ZXMPPTHUMBPATH"
cursor_chatstorage.execute(query_thumbpath)

# Retrieve ZXMPPTHUMBPATH results from ChatStorage.sqlite
results_thumbpath = cursor_chatstorage.fetchall()

# Close ChatStorage.sqlite database connection
cursor_chatstorage.close()
conn_chatstorage.close()

thumbpath_set = set(row[0] for row in results_thumbpath)

# Remove the values that have a match in the thumbpath_set
final_filtered_values = [value for value in filtered_values if value not in thumbpath_set]

# Print the filtered values not present in ChatStorage.sqlite
for value in sorted(final_filtered_values):
    print(value)
