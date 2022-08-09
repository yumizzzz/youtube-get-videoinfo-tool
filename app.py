import os
import feedparser
import urllib.error
import urllib.request
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pytz import timezone
import pandas as pd
from googleapiclient.discovery import build
import streamlit as st
import requests
from bs4 import BeautifulSoup

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
SAVE_ROOT = 'results'


def download_file(url: str, dst_path: str) -> None:
    try:
        with urllib.request.urlopen(url) as web_file:
            data = web_file.read()
            with open(dst_path, mode='wb') as local_file:
                local_file.write(data)
    except urllib.error.URLError as e:
        print(e)


def main():

    st.title('YouTube Get VideoInfo Tool')
    api_key = st.text_input('YouTube API KEY', value='')
    channel_url = st.text_input('Channel URL', placeholder='ex. https://www.youtube.com/user/HikakinTV')
    max_results = st.number_input('動画本数', min_value=0, max_value=50, value=50)
    selected_order = st.radio('動画の優先度', ('新しい順', '評価の高い順', '再生回数順'))

    if st.button('Download'):

        if api_key == '':
            st.error('YouTube API KEY Error!!')
            return
        elif channel_url == '':
            st.error('Channel URL Error!!')
            return

        # 'www.youtube.com/user/' or # 'www.youtube.com/channel/'の場合、ソースコードよりchannel_id取得
        if 'www.youtube.com/channel/' not in channel_url:

            html = requests.get(channel_url)
            soup = BeautifulSoup(html.content, "html.parser")
            include_channel_id_url = 'https://www.youtube.com/feeds/videos.xml?channel_id='

            for link in soup.find_all('link'):
                if include_channel_id_url in link.attrs['href']:
                    channel_id = link.attrs['href'].split('channel_id=')[-1]
                    break
        else:
            channel_id = channel_url.split('/')[-1]

        if selected_order == '新しい順':
            order = 'date'
        elif selected_order == '評価の高い順':
            order = 'rating'
        elif selected_order == '再生回数順':
            order = 'viewCount'

        youtube = build(
            YOUTUBE_API_SERVICE_NAME,
            YOUTUBE_API_VERSION,
            developerKey=api_key
        )

        # https://developers.google.com/youtube/v3/docs/search?hl=ja
        search_response = youtube.search().list(
            channelId=channel_id,
            part='snippet',
            maxResults=max_results,
            order=order
        ).execute()

        dfs = []
        for search_result in search_response.get("items", []):

            if search_result["id"]["kind"] != "youtube#video":
                pass

            # from search_result
            if 'videoId' in search_result['id'].keys():
                video_id = search_result["id"]["videoId"]
            elif 'playlistId' in search_result['id'].keys():
                video_id = search_result["id"]["playlistId"]

            channel_title = search_result["snippet"]['channelTitle'].replace('/', '')
            title = search_result["snippet"]['title'].replace('/', '')
            publish_time = search_result["snippet"]['publishTime']
            video_url = 'https://www.youtube.com/watch?v={}'.format(video_id)
            image_url = 'https://img.youtube.com/vi/{}/hq720.jpg'.format(video_id)

            # from video_id
            # https://developers.google.com/youtube/v3/docs/channels?hl=ja
            video_response = youtube.videos().list(id=video_id, part='statistics').execute()
            video_statistics = video_response['items'][0]['statistics']
            view_count = video_statistics['viewCount']
            try:
                like_count = video_statistics['likeCount']
            except:
                like_count = '-'
            try:
                comment_count = video_statistics['commentCount']
            except:
                comment_count = '-'

            # time
            analysis_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
            publish_time = datetime.strptime(publish_time, '%Y-%m-%dT%H:%M:%S%z')
            publish_time = publish_time.strftime('%Y%m%d_%H%M%S')[2:]

            filename = '{}_{}.png'.format(publish_time, channel_title)

            save_path = os.path.join(SAVE_ROOT, channel_title)
            os.makedirs(save_path, exist_ok=True)
            download_file(image_url, os.path.join(save_path, filename))

            output_dict = {
                'analysis time': analysis_time,
                'channel': channel_title,
                'title': title,
                'video_url': video_url,
                'image_url': image_url,
                'filename': filename,
                'view_count': view_count,
                'like_count': like_count,
                'comment_count': comment_count,
            }
            dfs.append(output_dict)

        df = pd.DataFrame(dfs)
        df.to_csv(os.path.join(save_path, 'result.csv'), index=False)


if __name__ == '__main__':
    main()
