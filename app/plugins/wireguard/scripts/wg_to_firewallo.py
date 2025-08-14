import sqlite3
import re
import logging

# Configure logging
logger = logging.getLogger('wg_to_fw')
logger.setLevel(logging.WARN)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARN)

# Define log message format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(stream_handler)

DB_FILE_PATH="/var/home/pbroccolo/Codici/firewallo-ui-main/app/wg_config.db"
OUT_FILE_PATH="/var/home/pbroccolo/Codici/firewallo-ui-main/script/firewallo.txt"

try:
    logger.info("Connection to DB")
    # Connect to the SQLite database
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()

    logger.info("Start query")
    # Retrieve the ips_str and allowed_ips_str from the peers table
    cursor.execute("SELECT * FROM peers")
    users_settings = cursor.fetchall()
except sqlite3.Error as e:
    logger.error(f"Failed to connect to database: {e}")
    conn.close() if conn else None
    exit(1)
finally:
    logger.info("Connection close")
# Close the database connection
conn.close()
logger.info("Connection close")


# Generate new rules
new_rules = []
identifier_count = {}

try:
    logger.info("users iteration")
    for user_setting in users_settings:
        identity = user_setting[0]
        
        if identity not in identifier_count:
            identifier_count[identity] = 1

        for ip_range in re.split(r',\s*', user_setting[5]):

            # Increment the counter for each identifier
            current_count = identifier_count[identity]

            rule = f'#COMMENT:{identity}_{current_count}\n'
            rule += f'nft "add rule ip filter vpns2lan ip saddr {user_setting[2]} ip daddr {ip_range} tcp sport 1-65535 tcp dport 1-65535 log prefix \\"vpns2lan: {identity} \\" counter accept"\n'
            new_rules.append(rule)
            logger.info(f"adding {identity} rule")

            # Update the count for this identifier
            identifier_count[identity] += 1
except Exception as e:
    logger.error(f"Failed to process user settings: {e}")
    exit(1)


try:
    with open(OUT_FILE_PATH, 'r') as file:
        lines = file.readlines()

except IOError as e:
    logger.error(f"Failed to read from output file: {e}")
    exit(1)

# Replace the section between '# autowg start' and '# autowg stop'
continue_append = True
updated_lines = []

try:
    logger.info("Replace the section between autowg start and autowg stop")
    for line in lines:
        if continue_append:
            updated_lines.append(line)
        if line.strip() == '# autowg start':
            continue_append = False
        if line.strip() == '# autowg stop':
            continue_append = True
            updated_lines.extend(new_rules + [line])
except Exception as e:
    logger.error(f"Failed to update content: {e}")
    exit(1)


logger.info("Write the updated content back to the output file")
try:
    with open(OUT_FILE_PATH, 'w') as file:
        file.writelines(updated_lines)

except IOError as e:
    logger.error(f"Failed to write to output file: {e}")
    exit(1)

exit(0)
