import base64
import json
import math
import opencc
import os
import requests
import sys
import threading
import time

from fire import Fire
from joblib import Parallel, delayed, cpu_count
from prettytable import PrettyTable
from requests.adapters import HTTPAdapter
from threading import Thread

class LrcDownloader(object):
    format_list = ['.mp3', '.flac', '.ape', '.wav', '.m4a']
    headers = {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
    }

    @staticmethod
    def support_format(filename):
        for f in LrcDownloader.format_list:
            l = len(f)
            if filename.lower().endswith(f):
                return f
        return None

    def singer_song_comp(self, singer: str = None, song: str = None):
        cc = opencc.OpenCC('t2s')
        if singer is None:
            is_singer = True
        else:
            if ((cc.convert(singer.lower()) in cc.convert(self.singer.lower())) or 
                (cc.convert(self.singer.lower()) in cc.convert(singer.lower()))):
                is_singer = True
            else:
                is_singer = False
        if song is None:
            is_song = True
        else:
            if ((cc.convert(song.lower()) in cc.convert(self.song.lower())) or 
                (cc.convert(self.song.lower()) in cc.convert(song.lower()))):
                is_song = True
            else:
                is_song = False
        return is_singer and is_song

    def __init__(self, music_filename: str):
        self.music_filename = music_filename
        self.base_name = os.path.basename(self.music_filename)
        self.music_dir = os.path.dirname(self.music_filename)
        self.format = None
        for f in LrcDownloader.format_list:
            l = len(f)
            if self.base_name.lower().endswith(f):
                self.base_name = self.base_name[:-l]
                self.lrc_name = self.base_name + '.lrc'
                self.format = f
                break
        try:
            self.singer, self.song = self.base_name.split('-')
            self.singer = self.singer.strip()
            self.song = self.song.strip()
        except Exception as e:
            self.singer = None
            self.song = None
        if self.format is None:
            ValueError(f'input file {music_filename} is a music file that don\'t support.')

    def search(self):
        NotImplementedError('search NotImplementedError')
    
    def get_lrc(self, info):
        NotImplementedError('get_lrc NotImplementedError')

    def download_lrc(self, lrc_dir = None):
        if lrc_dir is None:
            lrc_dir = self.music_dir
        info = self.search()

        if info is not None:
            lrc_text = self.get_lrc(info)
            if lrc_text is not None:
                with open(os.path.join(lrc_dir, self.lrc_name), 'w', encoding='utf-8') as f:
                    f.write(lrc_text)
                return True
        return False

class LrcDownloaderNetease(LrcDownloader):
    def search(self):
        s = requests.Session()
        s.mount('http://', HTTPAdapter(max_retries=5))
        s.mount('https://', HTTPAdapter(max_retries=5))
        req = s.get('http://www.hjmin.com/search', 
                    params={'keywords': self.song or self.base_name}, 
                    headers=LrcDownloader.headers, 
                    timeout=None)
        resp = req.json()

        try:
            if self.singer is not None:
                for x in resp['result']['songs']:
                    for artist in x['artists']:
                        if self.singer_song_comp(singer=artist['name']):
                            return x['id']
                return resp['result']['songs'][0]['id']
            return resp['result']['songs'][0]['id']
        except:
            return None
    
    def get_lrc(self, info):
        s = requests.Session()
        s.mount('http://', HTTPAdapter(max_retries=5))
        s.mount('https://', HTTPAdapter(max_retries=5))
        req = s.get('http://www.hjmin.com/lyric', 
                    params={'id': info}, 
                    headers=LrcDownloader.headers, 
                    timeout=None)
        resp = req.json()
        
        try:
            return resp['lrc']['lyric']
        except:
            return None

class LrcDownloaderKugou(LrcDownloader):
    def search(self):
        s = requests.Session()
        s.mount('http://', HTTPAdapter(max_retries = 5))
        s.mount('https://', HTTPAdapter(max_retries = 5))
        req = s.get('http://mobileservice.kugou.com/api/v3/lyric/search', 
                    params={'version': 9108, 
                            'highlight': 1,
                            'keyword': self.base_name,
                            'plat': 0}, 
                    headers=LrcDownloader.headers, 
                    timeout=None)
        resp = req.json()

        hash = None
        try:
            hash = resp['data']['info'][0]['hash']
            if self.singer is not None:
                for x in resp['data']['info']:
                    if self.singer_song_comp(singer=x['singername']):
                        hash = x['hash']
                        break
            return hash
        except:
            return None
    
    def get_lrc(self, info):
        s = requests.Session()
        s.mount('http://', HTTPAdapter(max_retries = 5))
        s.mount('https://', HTTPAdapter(max_retries = 5))
        r = s.get('http://lyrics.kugou.com/search', 
                  params={'ver': 1,
                          'man': 'yes',
                          'client': 'pc', 
                          'keyword': self.base_name,
                          'hash': info}, 
                  timeout=None)
        resp = r.json()
        
        id = None
        key = None
        try:
            id = resp['candidates'][0]['id']
            key = resp['candidates'][0]['accesskey']
            if self.singer is not None and self.song is not None:
                for x in resp['candidates']:
                    if self.singer_song_comp(singer=x['singer'], song=x['song']):
                        id = x['id']
                        key = x['accesskey']
                        break
        except:
            return None

        if id is not None and key is not None:
            r = s.get('http://lyrics.kugou.com/download', 
                    params={'ver': 1,
                            'client': 'pc', 
                            'id': id,
                            'accesskey': key,
                            'fmt': 'lrc',
                            'charset': 'utf8'}, 
                    timeout=None)
            resp = r.json()
            try:
                lrc = base64.b64decode(resp['content']).decode('utf-8')
                return lrc
            except:
                return None

class LrcDownloaderQQ(LrcDownloader):
    def search(self):
        s = requests.Session()
        s.mount('http://', HTTPAdapter(max_retries = 5))
        s.mount('https://', HTTPAdapter(max_retries = 5))
        r = s.get('https://c.y.qq.com/soso/fcgi-bin/client_search_cp', 
                  params={'w': self.base_name, 'format': 'json'}, 
                  timeout=None, 
                  headers=LrcDownloader.headers)
        resp = r.json()

        try:
            if self.singer is not None and self.song is not None:
                for x in resp['data']['song']['list']:
                    for singer_r in x['singer']:
                        if self.singer_song_comp(singer=singer_r['name'], song=x['songname']):
                            return x['songmid']
            return resp['data']['song']['list'][0]['songmid']
        except:
            return None

    def get_lrc(self, info):
        headers_append = {
            'Referer': 'https://y.qq.com/portal/player.html',
            'Host': 'c.y.qq.com'
        }
        s = requests.Session()
        s.mount('http://', HTTPAdapter(max_retries = 5))
        s.mount('https://', HTTPAdapter(max_retries = 5))
        r = s.get('https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg', 
                  params={'songmid': info, 
                          'format': 'json'}, 
                  timeout=None, 
                  headers={**LrcDownloader.headers, **headers_append})
        resp = r.json()
        
        try:
            return base64.b64decode(resp['lyric']).decode('utf-8')
        except:
            return None

def download_lrc(music_file):
    if os.path.exists(music_file):
        ld = LrcDownloaderKugou(music_file)
        if ld.download_lrc():
            return '酷狗'
        ld = LrcDownloaderQQ(music_file)
        if ld.download_lrc():
            return 'QQ'
        ld = LrcDownloaderNetease(music_file)
        if ld.download_lrc():
            return '网易'
        return '\033[31m失败\033[0m'
    else:
        return '\033[31m无此文件\033[0m'

def main(music_dir = '.', 
         music_file = None,
         force = False):
    music_files = []
    if music_file is not None:
        if isinstance(music_file, str):
            music_files = [music_file]
        elif isinstance(music_file, list):
            music_files = music_file
    else:
        for root, dirs, files in os.walk(music_dir):
            for file in files:
                file_suffix = LrcDownloader.support_format(file)
                if file_suffix is not None:
                    if force or not os.path.exists(os.path.join(root, file[:-len(file_suffix)] + '.lrc')):
                        music_file = os.path.join(root, file)
                        music_files.append(music_file)
    rs = Parallel(n_jobs=2 * cpu_count(), prefer='threads', verbose=1)(
            delayed(download_lrc)(f)
            for f in music_files
        )
    tb = PrettyTable()
    tb.add_column('文件', music_files, align='l')
    tb.add_column('状态', rs)
    print(tb)

if __name__ == '__main__':
    Fire(main)
