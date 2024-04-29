import os
from pathlib import Path
import JSON
import csv

def convert_to_unicode_lookalikes(text):
    replacements = {
        '<': u'\uff1c', '>': u'\uff1e', ':': u'\uff1a', '"': u'\uff02',
        '/': u'\uff0f', '\\': u'\uff3c', '|': u'\uff5c', '?': u'\uff1f', '*': u'\uff0a'
    }
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text

def find_episode_path(root_directory, show, season, episode_info):
    for channel in os.listdir(root_directory):
        channel_path = Path(root_directory) / channel
        if channel_path.is_dir():
            # Construct potential show path
            show_path = channel_path / show / f"Season {season}" / episode_info
            if show_path.exists():
                return show_path
    return None  # Return None if the path is not found

def check_files_exist(directory, required_files):
    if directory is None:
        return False
    existing_files = {file.name for file in directory.iterdir() if file.is_file()}
    return all(req_file in existing_files for req_file in required_files)

def scan_videos(expected_videos, root_directory):
    missing_videos = []
    required_files = ['.description', '.info.json', '.mp4', '.png']

    for video_id, metadata in expected_videos.items():
        converted_title = convert_to_unicode_lookalikes(metadata['title'])
        episode_info = f"{metadata['date']} - ({video_id})"
        filename_pattern = f"{metadata['date']} - S{metadata['season']}E{metadata['episode']} - {converted_title} ({video_id})"

        # Attempt to find the correct show and episode path
        episode_path = find_episode_path(root_directory, metadata['show'], metadata['season'], episode_info)
        files_exist = check_files_exist(episode_path, [filename_pattern + ext for ext in required_files])

        if not files_exist:
            missing_videos.append((video_id, episode_path if episode_path else "Path not found"))

    return missing_videos

def load_expected_files(csv_path):
    videos = {}
    with open(csv_path, encoding='utf-8', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            videos[row['rt_id']] = row
    return videos

# Example usage
root_directory = 'F:/Downloads'
expected_videos = load_expected_files('data_local/checklist.csv')  # Assuming this CSV contains the structure you mentioned
missing_videos = scan_videos(expected_videos, root_directory)
for missing in missing_videos:
    print(f"Missing: {missing}")
