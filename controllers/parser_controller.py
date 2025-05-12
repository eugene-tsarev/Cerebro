import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from db.db_session import get_session
from models.models import Comment
from dotenv import load_dotenv
import os
load_dotenv()


def extract_mention(text):
    at_pos = text.find('@')
    if at_pos != -1:
        text = text[at_pos:].lstrip()
    else:
        text = text.lstrip()

    match = re.match(r'^(@{1,2})(\S+)\s+', text)
    if match:
        mention = match.group(2)
        cleaned_text = text[match.end():]
    else:
        match_alt = re.match(r'^(@{1,2})(\S+)', text)
        if match_alt:
            raw_mention = match_alt.group(2)
            split_pos = re.search(r'[а-яА-Я]', raw_mention)
            if split_pos:
                idx = split_pos.start()
                mention = raw_mention[:idx]
                cleaned_text = raw_mention[idx:] + text[match_alt.end():]
            else:
                mention = raw_mention
                cleaned_text = text[match_alt.end():]
        else:
            mention = None
            cleaned_text = text

    return (mention.strip() if mention else None, cleaned_text.strip())


youtube_api_key = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=youtube_api_key)


def fetch_comments(video_id):
    comments = []
    request = youtube.commentThreads().list(
        part="snippet,replies",
        videoId=video_id,
        maxResults=100,
        textFormat="plainText"
    )

    while request:
        try:
            response = request.execute()
        except HttpError as e:
            if e.resp.status == 403:
                print(f"⚠️ Комментарии отключены для видео: {video_id}")
                return []
            else:
                raise e

        for item in response.get("items", []):
            top_comment = item["snippet"]["topLevelComment"]["snippet"]
            comment_data = {
                "cid": item["snippet"]["topLevelComment"]["id"],
                "text": top_comment["textDisplay"],
                "author": top_comment.get("authorDisplayName", "Unknown"),
                "channel": f"/@{top_comment.get('authorChannelId', {}).get('value', 'unknown')}" if top_comment.get('authorChannelId') else "unknown",
                "video_channel_url": f"/@{top_comment.get('authorChannelId', {}).get('value', 'unknown')}" if top_comment.get('authorChannelId') else "unknown",
                "video_id": item["snippet"].get("videoId", video_id),
                "published_time": top_comment["publishedAt"].split("T")[0],
                "edited": top_comment["publishedAt"] != top_comment.get("updatedAt", top_comment["publishedAt"]),
                "votes": top_comment.get("likeCount", 0),
                "embedding": None
            }
            comments.append(comment_data)

            replies = item.get("replies", {}).get("comments", [])
            for reply in replies:
                reply_snippet = reply["snippet"]
                reply_data = {
                    "cid": reply["id"],
                    "text": reply_snippet["textDisplay"],
                    "author": reply_snippet.get("authorDisplayName", "Unknown"),
                    "channel": f"/@{reply_snippet.get('authorChannelId', {}).get('value', 'unknown')}" if reply_snippet.get('authorChannelId') else "unknown",
                    "video_channel_url": f"/@{reply_snippet.get('authorChannelId', {}).get('value', 'unknown')}" if reply_snippet.get('authorChannelId') else "unknown",
                    "video_id": item["snippet"].get("videoId", video_id),
                    "published_time": reply_snippet["publishedAt"].split("T")[0],
                    "edited": reply_snippet["publishedAt"] != reply_snippet.get("updatedAt", reply_snippet["publishedAt"]),
                    "votes": reply_snippet.get("likeCount", 0),
                    "embedding": None
                }
                comments.append(reply_data)

        request = youtube.commentThreads().list_next(request, response)

    return comments


def save_comments_to_db(video_id):
    try:
        new_comments = fetch_comments(video_id)
    except HttpError as e:
        if e.resp.status == 403:
            return "Комментарии отключены"
        else:
            raise e

    added_count = 0

    with get_session() as db:
        for comment_data in new_comments:
            text = comment_data['text']
            mention, cleaned_text = extract_mention(text)

            comment = Comment(
                cid=comment_data['cid'],
                text=cleaned_text,
                mention=mention if mention else None,
                author=comment_data['author'],
                channel=comment_data['channel'],
                video_channel_url=comment_data['video_channel_url'],
                video_id=comment_data['video_id'],
                published_time=comment_data['published_time'],
                edited=comment_data['edited'],
                votes=comment_data['votes'],
                embedding=comment_data['embedding']
            )

            db.add(comment)
            try:
                db.commit()
                added_count += 1
            except IntegrityError:
                db.rollback()
                continue

    return added_count
