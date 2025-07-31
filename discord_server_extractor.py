import requests
import json
import csv
import datetime
import os
import argparse
import pandas as pd
import time
from collections import defaultdict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def extract_messages_with_content(channel_id, user_token, channel_name="Unknown", limit=100, before=None, max_messages=None):
    """
    Extract complete message data from a channel including full content.
    
    Args:
        channel_id: The Discord channel ID to extract messages from
        user_token: Discord user token for authentication
        channel_name: The name of the channel (for display only)
        limit: Number of messages to request per API call (max 100)
        before: Message ID to fetch messages before
        max_messages: Maximum number of messages to extract (None for all)
    
    Returns:
        List of complete message data including content, attachments, embeds, etc.
    """
    messages = []
    base_url = f'https://discord.com/api/v9/channels/{channel_id}/messages'
    
    # Headers for API requests
    headers = {
        'Authorization': user_token,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print(f"Extracting complete message content from channel: {channel_name} (ID: {channel_id})...")
    
    total_messages = 0
    has_more = True
    
    while has_more and (max_messages is None or total_messages < max_messages):
        # Determine batch size
        batch_limit = limit
        if max_messages is not None:
            batch_limit = min(limit, max_messages - total_messages)
            
        # Prepare query parameters
        params = {'limit': batch_limit}
        if before:
            params['before'] = before
            
        # Make API request
        response = requests.get(base_url, headers=headers, params=params)
        
        if response.status_code == 200:
            batch = response.json()
            
            if not batch:
                has_more = False
                continue
                
            # Process each message in detail
            for msg in batch:
                # Convert timestamp
                created_at = datetime.datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                timestamp = created_at.strftime("%Y-%m-%d %H:%M:%S")
                
                # Extract author information
                author_info = {
                    'id': msg['author']['id'],
                    'username': msg['author']['username'],
                    'discriminator': msg['author'].get('discriminator', '0'),
                    'display_name': msg['author'].get('global_name') or msg['author']['username'],
                    'bot': msg['author'].get('bot', False),
                    'avatar': msg['author'].get('avatar')
                }
                
                # Create full username
                if author_info['discriminator'] != '0':
                    full_username = f"{author_info['username']}#{author_info['discriminator']}"
                else:
                    full_username = author_info['username']
                
                # Extract attachments
                attachments = []
                for attachment in msg.get('attachments', []):
                    attachments.append({
                        'id': attachment['id'],
                        'filename': attachment['filename'],
                        'size': attachment['size'],
                        'url': attachment['url'],
                        'content_type': attachment.get('content_type'),
                        'width': attachment.get('width'),
                        'height': attachment.get('height')
                    })
                
                # Extract embeds
                embeds = []
                for embed in msg.get('embeds', []):
                    embed_data = {
                        'type': embed.get('type'),
                        'title': embed.get('title'),
                        'description': embed.get('description'),
                        'url': embed.get('url'),
                        'color': embed.get('color'),
                        'timestamp': embed.get('timestamp')
                    }
                    
                    # Add embed fields if present
                    if 'fields' in embed:
                        embed_data['fields'] = embed['fields']
                    
                    # Add embed author/footer if present
                    if 'author' in embed:
                        embed_data['author'] = embed['author']
                    if 'footer' in embed:
                        embed_data['footer'] = embed['footer']
                    if 'image' in embed:
                        embed_data['image'] = embed['image']
                    if 'thumbnail' in embed:
                        embed_data['thumbnail'] = embed['thumbnail']
                    
                    embeds.append(embed_data)
                
                # Extract reactions
                reactions = []
                for reaction in msg.get('reactions', []):
                    reactions.append({
                        'emoji': reaction['emoji'],
                        'count': reaction['count'],
                        'me': reaction.get('me', False)
                    })
                
                # Extract mentions
                mentions = []
                for mention in msg.get('mentions', []):
                    mentions.append({
                        'id': mention['id'],
                        'username': mention['username'],
                        'discriminator': mention.get('discriminator', '0'),
                        'display_name': mention.get('global_name') or mention['username']
                    })
                
                # Extract role mentions
                role_mentions = msg.get('mention_roles', [])
                
                # Extract channel mentions
                channel_mentions = []
                if 'content' in msg and msg['content']:
                    import re
                    channel_mention_pattern = r'<#(\d+)>'
                    channel_mentions = re.findall(channel_mention_pattern, msg['content'])
                
                # Check if message is a reply
                reply_info = None
                if msg.get('message_reference'):
                    reply_info = {
                        'message_id': msg['message_reference'].get('message_id'),
                        'channel_id': msg['message_reference'].get('channel_id'),
                        'guild_id': msg['message_reference'].get('guild_id')
                    }
                
                # Create complete message object
                message_data = {
                    'message_id': msg['id'],
                    'channel_id': channel_id,
                    'channel_name': channel_name,
                    'timestamp': timestamp,
                    'timestamp_iso': msg['timestamp'],
                    'author': author_info,
                    'full_username': full_username,
                    'content': msg.get('content', ''),
                    'attachments': attachments,
                    'embeds': embeds,
                    'reactions': reactions,
                    'mentions': mentions,
                    'role_mentions': role_mentions,
                    'channel_mentions': channel_mentions,
                    'reply_to': reply_info,
                    'pinned': msg.get('pinned', False),
                    'edited_timestamp': msg.get('edited_timestamp'),
                    'message_type': msg.get('type', 0),
                    'flags': msg.get('flags', 0)
                }
                
                messages.append(message_data)
            
            # Update pagination
            before = batch[-1]['id']
            total_messages += len(batch)
            print(f"  Extracted {total_messages} messages so far...")
            
            if len(batch) < batch_limit:
                has_more = False
                
        elif response.status_code == 429:  # Rate limited
            retry_after = response.json().get('retry_after', 5)
            print(f"  Rate limited. Waiting for {retry_after} seconds...")
            time.sleep(retry_after + 0.5)
        else:
            print(f"  Error: {response.status_code} - {response.text}")
            has_more = False
    
    print(f"  Finished extracting {len(messages)} messages with full content")
    return messages

def organize_messages_by_user(messages):
    """
    Organize messages by user for easier analysis.
    
    Args:
        messages: List of message dictionaries
        
    Returns:
        Dictionary with user IDs as keys and their message data as values
    """
    user_data = defaultdict(lambda: {
        'user_info': None,
        'messages': [],
        'stats': {
            'total_messages': 0,
            'total_characters': 0,
            'total_words': 0,
            'channels_used': set(),
            'attachments_sent': 0,
            'embeds_sent': 0,
            'reactions_received': 0,
            'mentions_made': 0,
            'first_message': None,
            'last_message': None
        }
    })
    
    for msg in messages:
        user_id = msg['author']['id']
        
        # Store user info (will be the same for all messages from this user)
        if user_data[user_id]['user_info'] is None:
            user_data[user_id]['user_info'] = msg['author'].copy()
            user_data[user_id]['user_info']['full_username'] = msg['full_username']
        
        # Add message to user's list
        user_data[user_id]['messages'].append(msg)
        
        # Update statistics
        stats = user_data[user_id]['stats']
        stats['total_messages'] += 1
        stats['total_characters'] += len(msg['content'])
        stats['total_words'] += len(msg['content'].split()) if msg['content'] else 0
        stats['channels_used'].add(msg['channel_id'])
        stats['attachments_sent'] += len(msg['attachments'])
        stats['embeds_sent'] += len(msg['embeds'])
        stats['reactions_received'] += sum(reaction['count'] for reaction in msg['reactions'])
        stats['mentions_made'] += len(msg['mentions'])
        
        # Track first and last message timestamps
        msg_time = datetime.datetime.fromisoformat(msg['timestamp_iso'].replace('Z', '+00:00'))
        if stats['first_message'] is None or msg_time < stats['first_message']:
            stats['first_message'] = msg_time
        if stats['last_message'] is None or msg_time > stats['last_message']:
            stats['last_message'] = msg_time
    
    # Convert sets to lists for JSON serialization and datetime to strings
    for user_id in user_data:
        stats = user_data[user_id]['stats']
        stats['channels_used'] = list(stats['channels_used'])
        stats['unique_channels'] = len(stats['channels_used'])
        
        if stats['first_message']:
            stats['first_message'] = stats['first_message'].isoformat()
        if stats['last_message']:
            stats['last_message'] = stats['last_message'].isoformat()
        
        # Calculate average message length
        if stats['total_messages'] > 0:
            stats['avg_message_length'] = stats['total_characters'] / stats['total_messages']
            stats['avg_words_per_message'] = stats['total_words'] / stats['total_messages']
        else:
            stats['avg_message_length'] = 0
            stats['avg_words_per_message'] = 0
        
        # Sort messages by timestamp (oldest first)
        user_data[user_id]['messages'].sort(key=lambda x: x['timestamp_iso'])
    
    return dict(user_data)

def save_user_data(user_data, output_dir, server_id, server_name=None):
    """
    Save user message data in various formats.
    
    Args:
        user_data: Dictionary of user data organized by user ID
        output_dir: Directory to save files
        server_id: Discord server ID
        server_name: Discord server name (optional)
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    server_prefix = f"{server_name}_{server_id}" if server_name else f"server_{server_id}"
    
    # Create subdirectory for this extraction
    extraction_dir = os.path.join(output_dir, f"{server_prefix}_{timestamp}")
    os.makedirs(extraction_dir, exist_ok=True)
    
    # 1. Save complete data as one large JSON file
    complete_file = os.path.join(extraction_dir, "complete_user_data.json")
    with open(complete_file, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, indent=2, ensure_ascii=False)
    print(f"Complete user data saved to: {complete_file}")
    
    # 2. Save individual JSON files for each user
    users_dir = os.path.join(extraction_dir, "individual_users")
    os.makedirs(users_dir, exist_ok=True)
    
    for user_id, data in user_data.items():
        # Create safe filename from username
        username = data['user_info']['username']
        safe_username = "".join(c for c in username if c.isalnum() or c in "._-")
        
        user_file = os.path.join(users_dir, f"{safe_username}_{user_id}.json")
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Individual user files saved to: {users_dir}")
    
    # 3. Save user statistics summary
    stats_summary = {}
    for user_id, data in user_data.items():
        stats_summary[user_id] = {
            'user_info': data['user_info'],
            'stats': data['stats']
        }
    
    stats_file = os.path.join(extraction_dir, "user_statistics.json")
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats_summary, f, indent=2, ensure_ascii=False)
    print(f"User statistics saved to: {stats_file}")
    
    # 4. Save a CSV summary for quick analysis
    csv_data = []
    for user_id, data in user_data.items():
        user_info = data['user_info']
        stats = data['stats']
        
        csv_data.append({
            'user_id': user_id,
            'username': user_info['username'],
            'display_name': user_info['display_name'],
            'full_username': user_info['full_username'],
            'is_bot': user_info['bot'],
            'total_messages': stats['total_messages'],
            'total_characters': stats['total_characters'],
            'total_words': stats['total_words'],
            'avg_message_length': round(stats['avg_message_length'], 2),
            'avg_words_per_message': round(stats['avg_words_per_message'], 2),
            'unique_channels': stats['unique_channels'],
            'attachments_sent': stats['attachments_sent'],
            'embeds_sent': stats['embeds_sent'],
            'reactions_received': stats['reactions_received'],
            'mentions_made': stats['mentions_made'],
            'first_message': stats['first_message'],
            'last_message': stats['last_message']
        })
    
    # Sort by message count (most active first)
    csv_data.sort(key=lambda x: x['total_messages'], reverse=True)
    
    csv_file = os.path.join(extraction_dir, "user_summary.csv")
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if csv_data:
            fieldnames = csv_data[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
    
    print(f"User summary CSV saved to: {csv_file}")
    
    # 5. Create a README file explaining the data structure
    readme_file = os.path.join(extraction_dir, "README.md")
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(f"""# Discord Message Extraction Results

## Extraction Details
- **Server ID:** {server_id}
- **Server Name:** {server_name or 'Unknown'}
- **Extraction Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Total Users:** {len(user_data)}
- **Total Messages:** {sum(data['stats']['total_messages'] for data in user_data.values())}

## File Structure

### `complete_user_data.json`
Complete dataset with all users and their messages in one file.

### `individual_users/`
Directory containing individual JSON files for each user:
- Filename format: `username_userid.json`
- Each file contains all messages and statistics for that user

### `user_statistics.json`
Summary statistics for all users without the full message content.

### `user_summary.csv`
Spreadsheet-friendly summary of user activity statistics.

## Data Structure

Each user's data contains:
- **user_info**: Basic user information (ID, username, display name, etc.)
- **messages**: Array of all messages with complete content
- **stats**: Calculated statistics (message counts, character counts, etc.)

### Message Object Structure
Each message includes:
- Basic info: ID, timestamp, content, channel
- Author information
- Attachments (files, images, etc.)
- Embeds (rich content)
- Reactions
- Mentions (@user, @role, #channel)
- Reply information
- Edit history

## Usage Examples

```python
import json

# Load all user data
with open('complete_user_data.json', 'r') as f:
    users = json.load(f)

# Get messages from specific user
user_messages = users['USER_ID']['messages']

# Get user statistics
user_stats = users['USER_ID']['stats']
```
""")
    
    print(f"README with data structure info saved to: {readme_file}")
    print(f"\nExtraction complete! All files saved to: {extraction_dir}")
    
    return extraction_dir

def enumerate_channels(server_id, user_token):
    """
    Enumerate all channels in a Discord server (kept from original)
    """
    headers = {
        'Authorization': user_token,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        server_response = requests.get(
            f'https://discord.com/api/v9/guilds/{server_id}',
            headers=headers
        )
        
        if server_response.status_code == 200:
            server_data = server_response.json()
            print(f"Successfully connected to server: {server_data.get('name')}")
        else:
            print(f"Error accessing server: {server_response.status_code} - {server_response.text}")
            return None
    except Exception as e:
        print(f"Error connecting to Discord API: {e}")
        return None
    
    try:
        channel_response = requests.get(
            f'https://discord.com/api/v9/guilds/{server_id}/channels',
            headers=headers
        )
        
        if channel_response.status_code == 200:
            channels = channel_response.json()
            print(f"Successfully retrieved {len(channels)} channels from server")
        else:
            print(f"Error getting channels: {channel_response.status_code} - {channel_response.text}")
            return None
    except Exception as e:
        print(f"Error retrieving channels: {e}")
        return None
    
    channel_info = {}
    text_channels = []
    
    # Build category map
    categories = {}
    for channel in channels:
        if channel['type'] == 4:  # Category
            categories[channel['id']] = channel['name']
    
    # Process channels
    for channel in channels:
        if channel['type'] == 4:
            continue
            
        channel_type = "Unknown"
        if channel['type'] == 0:
            channel_type = "Text"
            text_channels.append({
                'id': channel['id'],
                'name': channel['name'],
                'parent': categories.get(channel.get('parent_id', ''), 'Uncategorized')
            })
        elif channel['type'] == 2:
            channel_type = "Voice"
        elif channel['type'] == 5:
            channel_type = "Announcement"
            text_channels.append({
                'id': channel['id'],
                'name': channel['name'],
                'parent': categories.get(channel.get('parent_id', ''), 'Uncategorized')
            })
        elif channel['type'] == 13:
            channel_type = "Stage"
        elif channel['type'] == 15:
            channel_type = "Forum"
        elif channel['type'] == 16:
            channel_type = "MediaChannel"
        
        channel_info[channel['id']] = {
            'name': channel['name'],
            'type': channel_type,
            'category': categories.get(channel.get('parent_id', ''), 'Uncategorized')
        }
    
    print("\nAvailable text channels:")
    print("------------------------")
    
    by_category = {}
    for channel in text_channels:
        if channel['parent'] not in by_category:
            by_category[channel['parent']] = []
        by_category[channel['parent']].append(channel)
    
    sorted_categories = sorted(by_category.keys())
    
    for category in sorted_categories:
        print(f"\n{category.upper()}:")
        for channel in sorted(by_category[category], key=lambda x: x['name']):
            print(f"  - {channel['name']} (ID: {channel['id']})")
    
    return channel_info

def extract_server_content(server_id, user_token, channel_ids=None, max_messages=None, output_dir="output"):
    """
    Extract complete message content from all channels in a server.
    
    Args:
        server_id: Discord server ID
        user_token: Discord user token
        channel_ids: List of specific channel IDs (None for all text channels)
        max_messages: Maximum messages per channel (None for all)
        output_dir: Directory to save output files
        
    Returns:
        Path to the extraction directory
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Get server info
    server_name = None
    try:
        headers = {
            'Authorization': user_token,
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        server_response = requests.get(f'https://discord.com/api/v9/guilds/{server_id}', headers=headers)
        if server_response.status_code == 200:
            server_name = server_response.json().get('name')
    except Exception as e:
        print(f"Could not fetch server name: {e}")
    
    # Get all channels if not specified
    if channel_ids is None:
        all_channels = enumerate_channels(server_id, user_token)
        if not all_channels:
            print("Failed to retrieve channels from server.")
            return None
        
        # Filter for text channels
        text_channels = {
            id: info for id, info in all_channels.items() 
            if info['type'] in ['Text', 'Announcement']
        }
        channel_ids = list(text_channels.keys())
    else:
        # If specific channel IDs provided, get their info
        all_channels = enumerate_channels(server_id, user_token)
        text_channels = {
            id: info for id, info in all_channels.items() 
            if id in channel_ids and info['type'] in ['Text', 'Announcement']
        }
    
    if not channel_ids:
        print("No text channels found to process.")
        return None
    
    print(f"\nExtracting complete message content from {len(channel_ids)} channels...")
    
    # Collect all messages from all channels
    all_messages = []
    
    for i, channel_id in enumerate(channel_ids):
        channel_name = "Unknown"
        if channel_id in text_channels:
            channel_name = text_channels[channel_id]['name']
        
        print(f"\nProcessing channel {i+1}/{len(channel_ids)}: {channel_name}")
        
        # Extract complete messages for this channel
        channel_messages = extract_messages_with_content(
            channel_id=channel_id,
            user_token=user_token,
            channel_name=channel_name,
            max_messages=max_messages
        )
        
        if channel_messages:
            all_messages.extend(channel_messages)
    
    if not all_messages:
        print("No messages were extracted.")
        return None
    
    print(f"\nTotal messages extracted: {len(all_messages)}")
    print("Organizing messages by user...")
    
    # Organize messages by user
    user_data = organize_messages_by_user(all_messages)
    
    print(f"Messages organized for {len(user_data)} users")
    
    # Save all the data
    extraction_dir = save_user_data(user_data, output_dir, server_id, server_name)
    
    return extraction_dir

def main():
    parser = argparse.ArgumentParser(description='Discord Complete Message Content Extractor')
    
    # Discord API parameters
    parser.add_argument('--token', help='Discord user token (or set DISCORD_USER_TOKEN env var)')
    parser.add_argument('--server', help='Discord server ID (or set SERVER_ID env var)')
    parser.add_argument('--channels', nargs='+', help='Specific channel IDs to extract (default: all text channels)')
    parser.add_argument('--max-messages', type=int, default=None, 
                      help='Maximum number of messages to extract per channel (default: all)')
    parser.add_argument('--output-dir', default='output',
                      help='Directory to save output files (default: output)')
    
    args = parser.parse_args()
    
    # Get credentials
    user_token = args.token or os.getenv('DISCORD_USER_TOKEN')
    server_id = args.server or os.getenv('SERVER_ID')
    
    if not user_token or not server_id:
        print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                          MISSING REQUIRED PARAMETERS                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

Discord token and Server ID are required.

You can provide these values in one of two ways:

1. Command-line arguments:
   python discord_content_extractor.py --token YOUR_TOKEN --server SERVER_ID

2. Environment variables in a .env file:
   DISCORD_USER_TOKEN=your_token_here
   SERVER_ID=your_server_id_here

How to find these values:
• Token: Discord web → F12 → Application → Local Storage → discord.com → token
• Server ID: Right-click server → Copy ID (Developer Mode required)
        """)
        return
    
    try:
        # Extract complete content
        extraction_dir = extract_server_content(
            server_id=server_id,
            user_token=user_token,
            channel_ids=args.channels,
            max_messages=args.max_messages,
            output_dir=args.output_dir
        )
        
        if extraction_dir:
            print(f"\n✅ Extraction completed successfully!")
            print(f"📁 All files saved to: {extraction_dir}")
            print(f"\n📊 Ready for analysis! Check the individual_users/ folder for per-user JSON files.")
        else:
            print("❌ Extraction failed.")
            
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
