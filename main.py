import sqlite3
import os
import shutil
from datetime import datetime
import re
import mimetypes
import unicodedata
import plistlib

# Define output directory
output_dir = os.path.expanduser("~/Desktop/iMessages_Export")
os.makedirs(output_dir, exist_ok=True)

# Debug log file
debug_log_path = os.path.join(output_dir, "debug_log.txt")
debug_log = open(debug_log_path, 'w', encoding='utf-8')

# Connect to the Messages database
db_path = os.path.expanduser("~/Library/Messages/chat.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all messages with their chats and attachments
cursor.execute("""
    SELECT c.chat_identifier, m.text, m.is_from_me, m.date, a.ROWID, a.filename, a.mime_type, m.attributedBody, m.ROWID
    FROM message m
    LEFT JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
    LEFT JOIN chat c ON cmj.chat_id = c.ROWID
    LEFT JOIN message_attachment_join maj ON m.ROWID = maj.message_id
    LEFT JOIN attachment a ON maj.attachment_id = a.ROWID
    ORDER BY m.date
""")
messages = cursor.fetchall()

# Normalize phone numbers/emails to create safe folder names
def normalize_identifier(identifier):
    if not identifier:
        return "orphaned_messages"
    identifier = re.sub(r'^\+1', '', identifier)  # Remove +1 for US numbers
    identifier = re.sub(r'[^a-zA-Z0-9]', '_', identifier)
    return unicodedata.normalize('NFKD', identifier).encode('ASCII', 'ignore').decode('ASCII')

# Extract text from attributedBody
def extract_attributed_body(attributed_body, message_id):
    if not attributed_body:
        return None
    try:
        # Try decoding as plist
        plist_data = plistlib.loads(attributed_body)
        # Handle common plist structures
        if isinstance(plist_data, dict):
            # Look for NS.string or similar keys
            for key, value in plist_data.items():
                if key.startswith('NS.') or key in ('string', 'text'):
                    if isinstance(value, bytes):
                        return value.decode('utf-8', errors='ignore')
                    elif isinstance(value, str):
                        return value
            # Extract from NS.data or similar
            if 'NS.data' in plist_data:
                return plist_data['NS.data'].decode('utf-8', errors='ignore')
        elif isinstance(plist_data, (str, bytes)):
            return plist_data.decode('utf-8', errors='ignore') if isinstance(plist_data, bytes) else plist_data
        debug_log.write(f"Message ID {message_id}: Unparsed plist structure: {plist_data}\n")
        return "[Complex plist content]"
    except (plistlib.InvalidFileException, ValueError, AttributeError) as e:
        debug_log.write(f"Message ID {message_id}: Plist parsing failed: {e}\n")
        # Fallback to raw decoding
        try:
            return attributed_body.decode('utf-8', errors='ignore')
        except (AttributeError, UnicodeDecodeError):
            return "[Rich content not decoded]"

# Process messages
current_chat = None
text_file = None
chat_folder = None
media_count = 0
skipped_messages = 0
processed_messages = 0

for message in messages:
    chat_identifier, text, is_from_me, date, attachment_id, filename, mime_type, attributed_body, message_id = message
    
    # Convert date (macOS epoch: seconds since 2001-01-01)
    try:
        date = datetime.fromtimestamp(date / 1_000_000_000 + 978_307_200).strftime('%Y-%m-%d %H:%M:%S')
    except (TypeError, ValueError):
        debug_log.write(f"Skipped message ID {message_id}: Invalid date\n")
        skipped_messages += 1
        continue
    
    # Normalize chat identifier
    safe_identifier = normalize_identifier(chat_identifier)
    
    # New chat detected
    if chat_identifier != current_chat or safe_identifier == "orphaned_messages":
        if text_file:
            text_file.close()
            text_file = None
        
        # Create folder for this chat
        chat_folder = os.path.join(output_dir, safe_identifier)
        os.makedirs(chat_folder, exist_ok=True)
        
        # Open new text file for conversation
        text_file_path = os.path.join(chat_folder, f"conversation_{message_id if safe_identifier == 'orphaned_messages' else safe_identifier}.txt")
        try:
            text_file = open(text_file_path, 'a', encoding='utf-8')
        except OSError as e:
            debug_log.write(f"Failed to open file for {safe_identifier}, message ID {message_id}: {e}\n")
            skipped_messages += 1
            continue
        
        current_chat = chat_identifier
    
    # Ensure text_file is open
    if text_file is None:
        debug_log.write(f"Error: text_file is None for chat {safe_identifier}, message ID {message_id}\n")
        skipped_messages += 1
        continue
    
    # Determine message content
    message_content = text
    if not message_content and attributed_body:
        message_content = extract_attributed_body(attributed_body, message_id)
    
    # Write message to text file
    sender = "Me" if is_from_me else chat_identifier or f"Unknown_{message_id}"
    message_line = f"[{date}] {sender}: {message_content or '[No text]'}\n"
    text_file.write(message_line)
    processed_messages += 1
    
    # Handle attachments
    if attachment_id and filename and mime_type:
        media_count += 1
        # Determine file extension
        if 'image' in mime_type:
            ext = '.png'
        elif 'video' in mime_type:
            ext = '.mp4'
        else:
            ext = mimetypes.guess_extension(mime_type) or '.bin'
        
        # Save attachment
        attachment_path = os.path.expanduser(filename) if filename else None
        if attachment_path and os.path.exists(attachment_path):
            dest_path = os.path.join(chat_folder, f"media_{media_count}{ext}")
            try:
                shutil.copy(attachment_path, dest_path)
                text_file.write(f"[{date}] {sender}: [Media saved as media_{media_count}{ext}]\n")
            except (OSError, shutil.Error) as e:
                text_file.write(f"[{date}] {sender}: [Media copy failed: {e}]\n")
        else:
            text_file.write(f"[{date}] {sender}: [Media not found for attachment]\n")

# Clean up
if text_file:
    text_file.close()
debug_log.write(f"Processed {processed_messages} messages, skipped {skipped_messages} messages\n")
debug_log.close()
conn.close()

print(f"Export complete. Files saved in {output_dir}")
print(f"Processed {processed_messages} messages, skipped {skipped_messages} messages")
print(f"Check {debug_log_path} for details on skipped messages")
