import os
from dotenv import load_dotenv
import googleapiclient.discovery
import re
import json

# Load environment variables
load_dotenv()

def extract_specialized_seed_phrase(text):
    """
    Extract cryptocurrency seed phrases from text using various pattern matching techniques.
    Args:
        text (str): Input text potentially containing a seed phrase
    Returns:
        list: Extracted seed phrase words, or empty list if no valid seed phrase found
    """
    # Patterns to capture seed phrases with various delimiters
    patterns = [
        # Hyphen-delimited pattern with optional backup phrase indication
        r'(?:backup\s*phrase\s*:?\s*)?(-?[a-z]+-\s*-?[a-z]+-\s*-?[a-z]+-\s*-?[a-z]+-\s*-?[a-z]+-\s*-?[a-z]+-\s*-?[a-z]+-\s*-?[a-z]+-\s*-?[a-z]+-\s*-?[a-z]+-\s*-?[a-z]+-\s*-?[a-z]+)',
        # Bracket patterns
        r'(?:recovery\s*phrase:?\s*)?((?:<[a-z]+>-){11}<[a-z]+>)',
        r'(?:recovery\s*phrase:?\s*)?((?:《[a-z]+》-){11}《[a-z]+》)',
        r'(?:recovery\s*phrase:?\s*)?((?:\([a-z]+\)\s*){12})'
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            # Extract words, removing all delimiters
            words = re.findall(r'[a-z]+', match, re.IGNORECASE)
            # Validate: 12 unique words
            if len(words) == 12 and len(set(words)) == 12:
                return words
    return []

def search_videos(search_term, developer_key):
    """
    Search for YouTube videos based on a search term
    """
    youtube = googleapiclient.discovery.build(
        "youtube", "v3", developerKey=developer_key
    )
    request = youtube.search().list(
        part="id",
        q=search_term,
        type="video",
        maxResults=5
    )
    response = request.execute()

    # Extract video IDs from search results
    video_ids = [
        item['id']['videoId']
        for item in response.get('items', [])
        if item['id'].get('kind') == 'youtube#video'
    ]
    return video_ids

def get_youtube_comments(video_id, developer_key):
    """
    Retrieve comments for a specific YouTube video
    """
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    youtube = googleapiclient.discovery.build(
        "youtube", "v3", developerKey=developer_key
    )
    request = youtube.commentThreads().list(
        part="snippet,replies",
        videoId=video_id,
        maxResults=100
    )
    response = request.execute()
    return response.get("items", [])

def filter_comments(comments):
    """
    Analyze comments to extract potential cryptocurrency seed phrases
    """
    filtered_comments = []
    for item in comments:
        snippet = item["snippet"]["topLevelComment"]["snippet"]
        text = snippet["textOriginal"]

        # Only process comments mentioning wallet
        if "wallet" in text.lower():
            words = text.split()
            preceding_word = None
            # Get word before "wallet" (potential wallet type)
            for i, word in enumerate(words):
                if "wallet" in word.lower() and i > 0:
                    preceding_word = words[i - 1]
                    break

            mnemonics = []
            # Method 1: Specialized extraction for formatted phrases
            specialized_mnemonics = extract_specialized_seed_phrase(text)
            if specialized_mnemonics:
                mnemonics.append(" ".join(specialized_mnemonics))

            # Method 2: Look for explicit seed phrase markers
            if not mnemonics:
                method1_matches = re.findall(r'(?:SEED|seedphrase|seed phrase):\s*[(-]?([\w\s-]+)[)-]?', text, re.IGNORECASE)
                for match in method1_matches:
                    mnemonic_words = re.findall(r'\b\w+\b', match)
                    if len(mnemonic_words) >= 12:
                        mnemonics.append(" ".join(mnemonic_words[:12]))
                        break

            # Method 3: Strict word sequence extraction
            if not mnemonics:
                word_sequences = re.findall(
                    r'\b([a-z]+ [a-z]+ [a-z]+ [a-z]+ [a-z]+ [a-z]+ [a-z]+ [a-z]+ [a-z]+ [a-z]+ [a-z]+ [a-z]+)\b',
                    text,
                    re.IGNORECASE
                )
                for sequence in word_sequences:
                    words = re.findall(r'\b\w+\b', sequence.lower())
                    # Validate potential seed phrase
                    common_words = ['the', 'and', 'but', 'just', 'that', 'was', 'my', 'i', 'to', 'is', 'are', 'have']
                    if (len(words) == 12 and
                        all(word.islower() for word in words) and
                        len(set(words)) == 12 and
                        not any(word in common_words for word in words[:5]) and
                        all(2 < len(word) < 10 for word in words)):
                        mnemonics.append(" ".join(words))
                        break

            # Add to filtered results if we found something interesting
            if preceding_word or mnemonics:
                filtered_comments.append({
                    "author": snippet["authorDisplayName"],
                    "text": snippet["textOriginal"],
                    "timestamp": snippet["publishedAt"],
                    "preceding_word": preceding_word,
                    "mnemonics": mnemonics
                })
    return filtered_comments

def process_search_term(search_term, developer_key):
    """
    Process a search term: find videos and extract potential seed phrases from comments
    """
    print(f"\n{'='*60}\nProcessing search term: {search_term}\n{'='*60}")

    # Get videos matching search term
    video_ids = search_videos(search_term, developer_key)
    print(f"Found {len(video_ids)} videos for search term: {search_term}")

    # Process comments from each video
    search_results = []
    for video_id in video_ids:
        print(f"\nProcessing comments for video ID: {video_id}")
        comments = get_youtube_comments(video_id, developer_key)
        filtered_comments = filter_comments(comments)

        # Add metadata to results
        for comment in filtered_comments:
            comment['video_id'] = video_id
            comment['search_term'] = search_term
        search_results.extend(filtered_comments)
    return search_results

def write_unique_mnemonics_to_json(results, filename="mnemonics.json"):
    """
    Write unique mnemonics and their source metadata to JSON
    """
    seen = set()
    unique_results = []
    for item in results:
        for mnemonic in item.get("mnemonics", []):
            normalized = ' '.join(mnemonic.lower().split())
            if normalized not in seen:
                seen.add(normalized)
                unique_results.append({
                    "mnemonic": normalized,
                    "author": item.get("author"),
                    "text": item.get("text"),
                    "timestamp": item.get("timestamp"),
                    "video_id": item.get("video_id"),
                    "search_term": item.get("search_term")
                })

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(unique_results, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {len(unique_results)} unique mnemonics to {filename}")

def main():
    """
    Main function to scan YouTube for crypto wallet seed phrases in comments
    """
    # Get API key from environment
    developer_key = os.getenv('YOUTUBE_API_KEY')
    if not developer_key:
        raise ValueError("No YouTube API key found. Please set YOUTUBE_API_KEY in .env file.")

    # Search terms targeting crypto-related content
    search_terms = [
        "crypto tron",
        "okx wallet crypto",
        "crypto wallet",
        "ethereum wallet",
        "blockchain wallet"
    ]

    # Process all search terms
    all_results = []
    for search_term in search_terms:
        search_results = process_search_term(search_term, developer_key)
        all_results.extend(search_results)

    # Print summary
    print(f"\n{'='*70}\nSUMMARY OF ALL RESULTS\n{'='*70}")
    print(f"Total potential mnemonics found: {len(all_results)}\n")
    for item in all_results:
        print(f"Search Term: {item['search_term']}")
        print(f"Video ID: {item['video_id']}")
        print(f"Author: {item['author']}")
        print(f"Mnemonics: {', '.join(item['mnemonics']) if item['mnemonics'] else 'None'}")
        print("-" * 50)

    # Save unique results to file
    write_unique_mnemonics_to_json(all_results)

if __name__ == "__main__":
    main()
