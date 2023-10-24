import requests
import os
import threading
import time
import re

VIDEO_URL = "https://m.ok.ru/video/3187538135640"
GENERIC_URL = ""
PARTS_DOWNLOADING = []

HEADERS = {
    'Accept-Encoding': 'identity;q=1, *;q=0',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Host': 'vd420.mycdn.me',
    'Pragma': 'no-cache',
    'Referer': 'https://m.ok.ru/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Range': 'bytes=0-',
    'X-Deliver-To': 'vd420.mycdn.me',
}

def get_ip() -> str:
    return "78.171.215.68"

import html
def find_generic_url():
    global GENERIC_URL
    r = requests.get(VIDEO_URL)
    if r.status_code != 200:
        print("Error: {}".format(r.status_code))
        print(r.headers)
        print(r.text)
        return None
    
    decoded_string = html.unescape(r.text.encode('utf-8').decode('unicode_escape'))
    offset = decoded_string.find("videoSrc") + len("videoSrc\":\"")
    next_string = decoded_string[offset:]
    offset = next_string.find("\"")
    long_url = next_string[:offset]
    GENERIC_URL = long_url
    return long_url

def get_video_link():
    """
    r = requests.get(VIDEO_URL)
    if r.status_code != 200:
        print("Error: {}".format(r.status_code))
        print(r.headers)
        print(r.text)
        return None
    
    print("Long url: {}".format(long_url))
    return
    """
    # url = "https://m.ok.ru/dk/video.mp4?st.cmd=moviePlaybackRedirect&st.sig=bf0a9c4510b708bd374cf51b2bd65b1c43f46487&st.mq=3&st.mvid=4531989776984&st.ip=" + get_ip() + "&st.dla=on&st.exp=1698126648052&st.hls=off&_prevCmd=movieLayer&tkn=2278&__dp=y&__dp=y&vdsig=VlaMgZPIWDS1FvVwiHC7mdjIDgU"
    # url = "https://m.ok.ru/dk/video.mp4?st.cmd=moviePlaybackRedirect&st.sig=86b46501e8745504444ec97de499281f4783c19e&st.mq=3&st.mvid=4532055378520&st.ip=88.233.211.49&st.dla=on&st.exp=1698264301208&st.hls=off&_prevCmd=movieLayer&tkn=1184&__dp=y&__dp=y"
    url = GENERIC_URL
    headers = {
        'authority': 'm.ok.ru',
        'method': 'GET',
        'scheme': 'https',
        'Accept': '*/*',
        'Accept-Encoding': 'identity;q=1, *;q=0',
        'Accept-Language': 'en-US,en;q=0.9,tr;q=0.8',
        'Cache-Control': 'no-cache',
        'Cookie': '_statid=4f61a132-430d-4af1-80e5-5ae278ebaf27; _userIds=""; TimezoneOffset=-180; ClientTimeDiff=-535; cookieChoice=""; DCAPS=dpr%5E1%7Cvw%5E1680%7Cvh%5E901%7Co%5El%7Csw%5E1680%7C; JSESSIONID=ae8eb46f40ee5c7f22533b9625d24b7e494236bf50895127.4c54081; bci=-2928137449571809817; __last_online=1697956461389',
        'Pragma': 'no-cache',
        'Range': 'bytes=0-',
        'Referer': VIDEO_URL,
        'sec-ch-ua': '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'video',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    r = requests.get(url, headers=headers, allow_redirects=False)
    return r.headers['Location']

def get_video_size(url):
    r = requests.head(url, headers=HEADERS)
    if r.status_code != 200:
        print("Error: {}".format(r.status_code))
        print(r.headers)
        print(r.text)
        return None
    if 'content-length' not in r.headers:
        print("Error: No content-length header")
        return None
    return int(r.headers['content-length'])

def download_video_nsize(video_link, range_start, range_end):
    headers = HEADERS.copy()
    headers['Range'] = 'bytes={}-{}'.format(range_start, range_end)
    r = requests.get(video_link, headers=headers, stream=True)
    if r.status_code != 206:
        print("Error: {}".format(r.status_code))
        print(r.headers)
        print(r.text)
        return None
    print(f"Downloaded {range_start}-{range_end} bytes, Total: {len(r.content)} bytes")
    return r.content

def save_raw_bytes(filename, raw_bytes):
    with open(filename, 'wb') as f:
        f.write(raw_bytes)

def download_and_save(video_link, filename, range_start, range_end):
    global PARTS_DOWNLOADING
    PARTS_DOWNLOADING.append(threading.current_thread().name)
    raw_bytes = download_video_nsize(video_link, range_start, range_end)
    if raw_bytes is None:
        print("Error: Download failed")
        return
    print("Saving to {}, size: {}".format(filename, len(raw_bytes)))
    save_raw_bytes(filename, raw_bytes)
    PARTS_DOWNLOADING.remove(threading.current_thread().name)
    remainings = ', '.join([str(x) for x in PARTS_DOWNLOADING])
    if len(remainings) == 0:
        remainings = "None"
    print("Part {} is done, remaining parts: {}".format(threading.current_thread().name, remainings))

def download_all_part(video_size, thread_count = 20):
    # 20 part olcak, toplam size video_size'yi verecek
    part_size = video_size // thread_count
    print("Part size: {}".format(part_size))
    part_count = 1

    for i in range(0, thread_count):
        start_offset = i * part_size
        end_offset = start_offset + part_size - 1
        if i == thread_count - 1:
            end_offset = video_size

        print("Downloading part {}, Range: {}-{}".format(part_count, start_offset, end_offset)) 

        new_link = get_video_link()
        if new_link is None:
            print("Error: get_video_link failed")
            return
        
        threading.Thread(target=download_and_save, args=(new_link, f"part_{part_count}.mp4", start_offset, end_offset), name=part_count).start()
        time.sleep(5)
        # download_and_save(new_link, f"part_{part_count}.mp4", i, i + part_size - 1)
        part_count += 1

        """
        thread = threading.Thread(target=download_and_save, args=(new_link, f"part{i}-{i + part_size - 1}.mp4", i, i + part_size - 1))
        thread.start()
        time.sleep(5)
        """

    # Wait until all threads are done
    while threading.active_count() > 1:
        time.sleep(1)
    print("All parts are downloaded")
    return

def concat_parts():
    count = 1
    with open("output.mp4", "wb") as outfile:
        while os.path.exists(f"part_{count}.mp4"):
            with open(f"part_{count}.mp4", "rb") as infile:
                outfile.write(infile.read())
            count += 1

def download_one_part(video_link, video_size, part_number):
    part_size = video_size // 20
    range_start = (part_number - 1) * part_size
    range_end = part_number * part_size - 1
    print("Downloading part {}, Range: {}-{}".format(part_number, range_start, range_end)) 
    download_and_save(video_link, f"part_{part_number}.mp4", range_start, range_end)

def clear_files():
    count = 1
    while os.path.exists(f"part_{count}.mp4"):
        os.remove(f"part_{count}.mp4")
        count += 1

find_generic_url()
video_link = get_video_link()
video_size = get_video_size(video_link)
print(f"Video size: {video_size}")
thread_count = 20
download_all_part(video_size, thread_count)
concat_parts()
clear_files()