import re

import trafilatura
from youtube_transcript_api import YouTubeTranscriptApi


def scrape_text_from_url(url):
    try:
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded, include_formatting=True)
        if text is None:
            return []
        text_chunks = text.split("\n")
        article_content = [text for text in text_chunks if text]
        return article_content
    except Exception as e:
        print(f"Error: {e}")


def extract_youtube_transcript(youtube_url):
    try:
        video_id_match = re.search(r"(?<=v=)[^&]+|(?<=youtu.be/)[^?|\n]+", youtube_url)
        video_id = video_id_match.group(0) if video_id_match else None
        if video_id is None:
            return "no transcript"
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['ru', ])  # 'en'
        transcript_text = ' '.join([item['text'] for item in transcript.fetch()])
        return transcript_text

    except Exception as e:
        print(f"Error: {e}")
        return "no transcript"


def retrieve_yt_transcript_from_url(youtube_url):
    output = extract_youtube_transcript(youtube_url)

    if output == 'no transcript':
        raise ValueError("There's no valid transcript in this video.")
    """
    output_sentences = output.split(' ')
    output_chunks = []
    current_chunk = ""
    for sentence in output_sentences:
        if len(current_chunk) + len(sentence) + 1 <= config.CHUNK_SIZE:
            current_chunk += sentence + ' '
        else:
            output_chunks.append(current_chunk.strip())
            current_chunk = sentence + ' '
    
    if current_chunk:
        output_chunks.append(current_chunk.strip())
    return output_chunks
    """
    return output

# Поиск результатов
# from duckduckgo_search import AsyncDDGS
# DDG_REGION = env.str("DDG_REGION", "ru-ru")
# async def search_results(keywords):
#  print(keywords, ddg_region)
#    results = await AsyncDDGS().text(keywords, region=ddg_region, safesearch='off', max_results=3)
#    return results
