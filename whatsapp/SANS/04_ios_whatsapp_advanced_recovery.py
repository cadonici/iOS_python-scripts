import re
import sqlite3
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

# Connecting to Photos.sqlite database
conn_photos = sqlite3.connect('Photos.sqlite')
cursor_photos = conn_photos.cursor()

# Execute the query on Photos.sqlite database to retrieve ZORIGINALFILENAME and ZEXIFTIMESTAMPSTRING from ZADDITIONALASSETATTRIBUTES, ZFILENAME, ZADDEDDATE, and ZDATECREATED from ZASSET
query_photos = """
    SELECT a.ZORIGINALFILENAME, a.ZEXIFTIMESTAMPSTRING, b.ZFILENAME,
           datetime('2001-01-01', "ZADDEDDATE" || ' seconds', 'utc') AS "Added time",
           datetime('2001-01-01', "ZDATECREATED" || ' seconds', 'utc') AS "Creation time"
    FROM ZADDITIONALASSETATTRIBUTES AS a
    INNER JOIN ZASSET AS b ON a.Z_PK = b.ZADDITIONALATTRIBUTES
"""
cursor_photos.execute(query_photos)

# Retrieve results from Photos.sqlite
results_photos = cursor_photos.fetchall()

# Close Photos.sqlite database connection
cursor_photos.close()
conn_photos.close()

# Extract the values from the results_photos and store them in separate lists
values_photos = []
exif_timestamps = []
filenames = []
added_dates = []
created_dates = []

for row in results_photos:
    values_photos.append(row[0])
    exif_timestamps.append(row[1])
    filenames.append(row[2])
    added_dates.append(row[3])
    created_dates.append(row[4])

# Find the values that coincide between cloudkit_cache.db and Photos.sqlite
gallery_values = set(values_cloudkit) & set(values_photos)

# Convert the results to sets for comparison
set_chatstorage = set([row[0] for row in results_chatstorage])
set_cloudkit = set([row[0] for row in results_cloudkit])
set_new = set([row[0] for row in results_new])






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

# Define a dictionary to store the count of files by extension for each phone number
file_count_by_extension = defaultdict(lambda: defaultdict(int))

for number in number_count:
    for value in values_not_in_chatstorage:
        if number in value:
            extension = value.split(".")[-1]  # Extract the file extension
            file_count_by_extension[number][extension] += 1

sorted_numbers = sorted(number_count.items(), key=lambda x: (-x[1], str(x[0])))

for number, count in sorted_numbers:
    print("Phone number: +", number, sep="")
    print("Number of deleted messages:", count)

    # Print the number and type of files based on their extensions for the current phone number
    print("Files by extension:")
    file_counts = file_count_by_extension[number]
    for extension, file_count in file_counts.items():
        print(f"Number of {extension.upper()} files:", file_count)
    print()


while True:
    # Prompt the user to enter a phone number
    phone_number = input("Enter a phone number (or 'q' to quit): ")

    # Check if the user wants to quit
    if phone_number.lower() == 'q':
        break

    # Remove any leading and trailing whitespace
    phone_number = phone_number.strip()
    phone_number = phone_number.replace(" ", "")

    # Remove the leading "+" if present
    if phone_number.startswith("+"):
        phone_number = phone_number[1:]

    # Find the values that include the entered phone number
    matching_values = []
    for value in sorted(values_not_in_chatstorage):
        if phone_number in value:
            matching_values.append(value)

    # Print the values that include the entered phone number
    if matching_values:
        print("Matching values:")
        for value in matching_values:
            print(value)
        print()
        # Prompt the user to choose whether to compare the file names with `gallery_values`
        print("Do you want to compare the file names with gallery_values?")
        compare_choice = input("Enter 'y' for yes, or any other key for no: ")

        if compare_choice.lower() == 'y':
            # Compare file names with gallery_values
            matching_gallery_values = set([value.split('/')[-1] for value in matching_values]) & set(gallery_values)
            print("Matching values in gallery:")
            print()

            if len(matching_gallery_values) > 0:
                for value in sorted(matching_gallery_values):
                    index = values_photos.index(value)
                    print("Original File name:", value)
                    print("Exif Timestamp:", exif_timestamps[index])
                    print("File name:", filenames[index])
                    print("Added Date (UTC):", added_dates[index])
                    print("Created Date (UTC):", created_dates[index])
                    print()
            else:
                print("No matching values in the gallery.")
                print()
        else:
            # No comparison needed
            print("No comparison with gallery_values requested.")
            print()

    else:
        print("No entries found for the entered phone number.")
        print("Please enter a different phone number.")
        print()
