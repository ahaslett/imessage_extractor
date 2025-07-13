# iMessage Recovery Script

## Overview

The `recover_imessages.py` script extracts iMessages from the macOS Messages database (`chat.db`), including deleted messages if recovered, and organizes them into a structured format. It creates folders for each phone number or email, saves images as PNG and videos as MP4, and exports conversations as text files with timestamps and sender details. This script is designed for macOS users who want to recover and organize iMessages, especially after data loss.

## Features

- **Extracts Messages**: Retrieves all messages, including text and rich content (e.g., iMessage effects) from `chat.db`.
- **Organizes by Contact**: Creates a folder for each phone number or email (e.g., `1234567890`, `john_doe_gmail_com`).
- **Handles Orphaned Messages**: Processes messages not linked to chats, saving them in an `orphaned_messages` folder with unique files per message.
- **Saves Media**: Copies images as PNG and videos as MP4, referencing them in text files.
- **Text Export**: Saves conversations in `conversation.txt` (or `conversation_{message_id}.txt` for orphaned messages) with timestamps and sender info.
- **Debugging**: Logs issues (e.g., missing data, parsing errors) to `debug_log.txt`.

## Prerequisites

- **macOS**: Tested on macOS Ventura and later. Older versions may require schema adjustments.
- **Python 3**: Included with macOS, or install via:
  ```bash
  brew install python
  ```
- **Pillow**: For image conversion (optional, for media handling):
  ```bash
  pip3 install Pillow
  ```
- **plistlib**: Included in Python’s standard library. Install if missing:
  ```bash
  pip3 install plistlib
  ```
- **Messages Database**: Ensure `~/Library/Messages/chat.db` exists and contains data (current or recovered).
- **Permissions**: Grant read/write access to `~/Library/Messages/`:
  ```bash
  chmod -R u+rw ~/Library/Messages
  ```

## Installation

1. **Save the Script**:
   - Copy `recover_imessages.py` to your Desktop (e.g., `/Users/0x90/Desktop/recover_imessages.py`).

2. **Install Dependencies**:
   - Install Pillow:
     ```bash
     pip3 install Pillow
     ```
   - Verify `plistlib` (should be included with Python).

3. **Verify Database**:
   - Ensure `chat.db` exists:
     ```bash
     ls ~/Library/Messages/chat.db
     ```
   - Check for messages:
     ```bash
     sqlite3 ~/Library/Messages/chat.db "SELECT COUNT(*) FROM message"
     ```
   - Check for images:
     ```bash
     sqlite3 ~/Library/Messages/chat.db "SELECT COUNT(*) FROM attachment WHERE mime_type LIKE 'image/%'"
     ```

## Usage

1. **Run the Script**:
   - Open Terminal and navigate to the Desktop:
     ```bash
     cd ~/Desktop
     ```
   - Execute:
     ```bash
     python3 recover_imessages.py
     ```

2. **Output**:
   - Files are saved in `~/Desktop/iMessages_Export/`:
     - **Folders**: One per phone number/email (e.g., `1234567890`) or `orphaned_messages` for unlinked messages.
     - **Text Files**: `conversation.txt` (or `conversation_{message_id}.txt` for orphaned messages) with format:
       ```
       [2025-07-12 11:16:00] Me: Hello, this is a test
       [2025-07-12 11:16:05] 1234567890: Cool! [Media saved as media_1.png]
       ```
     - **Media Files**: Images as `media_X.png`, videos as `media_X.mp4`.
     - **Debug Log**: `debug_log.txt` with errors (e.g., skipped messages, parsing issues).

3. **Example Output Structure**:
   ```
   ~/Desktop/iMessages_Export/
   ├── 1234567890/
   │   ├── conversation.txt
   │   ├── media_1.png
   │   ├── media_2.mp4
   ├── orphaned_messages/
   │   ├── conversation_24890.txt
   │   ├── conversation_24893.txt
   ├── debug_log.txt
   ```

## Recovering Deleted Messages

If you’re recovering deleted iMessages:
- **Recently Deleted** (macOS Ventura+):
  - Open Messages, go to `View > Recently Deleted`, and recover messages.
- **Time Machine**:
  - Restore `chat.db` from `~/Library/Messages/`:
    ```bash
    cp ~/Library/Messages/chat.db ~/Library/Messages/chat.db.backup
    ```
    - Use Time Machine to restore an older `chat.db`.
- **iCloud**:
  - Ensure Messages in iCloud is enabled (`System Settings > Apple ID > iCloud > Messages`).
  - Sign out/in of Messages to sync.
- **Third-Party Tools**:
  - Use Disk Drill or similar to recover `chat.db` or `Attachments/`:
    - Scan `~/Library/Messages/` on an external drive.
    - Restore `chat.db` to `~/Library/Messages/` and attachments to `~/Library/Messages/Attachments/`.

## Troubleshooting

1. **No Messages Exported**:
   - Check `chat.db` content:
     ```bash
     sqlite3 ~/Library/Messages/chat.db "SELECT COUNT(*) FROM message WHERE text IS NOT NULL OR attributedBody IS NOT NULL"
     ```
   - If low, recover a different `chat.db`.

2. **Skipped Messages**:
   - Check `debug_log.txt` for reasons (e.g., “Invalid date”, “Plist parsing failed”).
   - Inspect orphaned messages:
     ```bash
     sqlite3 ~/Library/Messages/chat.db "SELECT m.ROWID, m.text, m.attributedBody, c.chat_identifier FROM message m LEFT JOIN chat_message_join cmj ON m.ROWID = cmj.message_id LEFT JOIN chat c ON cmj.chat_id = c.ROWID WHERE c.chat_identifier IS NULL LIMIT 10"
     ```

3. **No Text in Messages**:
   - If `conversation.txt` shows “[No text]” or “[Rich content not decoded]”, `attributedBody` may need custom parsing. Share `debug_log.txt` entries.

4. **Missing Media**:
   - Verify attachments:
     ```bash
     ls -R ~/Library/Messages/Attachments/
     ```
   - Recover with Disk Drill if empty.

5. **Permissions Issues**:
   - Ensure access:
     ```bash
     chmod -R u+rw ~/Library/Messages
     ```

6. **Schema Mismatch**:
   - Check schema:
     ```bash
     sqlite3 ~/Library/Messages/chat.db ".schema message"
     sqlite3 ~/Library/Messages/chat.db ".schema attachment"
     ```

## Limitations

- **Rich Content**: Some `attributedBody` data (e.g., iMessage effects) may not parse fully, resulting in “[Rich content not decoded]”.
- **Orphaned Messages**: Messages without a `chat_identifier` are saved in `orphaned_messages` with unique files.
- **Media Conversion**: Images/videos are copied as PNG/MP4. Non-standard formats may require additional tools (e.g., `ffmpeg` for videos).
- **Recovery Dependency**: Deleted messages require a recovered `chat.db` or attachments.

## Contributing

For issues or enhancements (e.g., group chat support, advanced plist parsing), contact the script author or submit a pull request with detailed comments.

## License

This script is provided as-is under the MIT License. Use at your own risk, and back up `chat.db` before running.
