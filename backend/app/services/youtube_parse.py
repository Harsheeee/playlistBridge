import re

def parse_title(video_title: str):
    clean_title = re.sub(r'[\(\[][^\]\)]*[\)\]]', '', video_title)
    
    separators = [' - ', ' – ', ' — ', ' | ', ' : ']
    
    artist = ""
    track = clean_title.strip()

    for sep in separators:
        if sep in clean_title:
            parts = clean_title.split(sep)
            track = parts[0].strip()
            artist = parts[1].strip()
            break
            
    return {"artist": artist, "track": track}

def normalize_title(title):
    title = re.sub(r'[\(\[][^\]\)]*[\)\]]', '', title)

    title = re.sub(r'[^a-zA-Z0-9\s]', '', title)
    title = " ".join(title.lower().split())
    
    return title
