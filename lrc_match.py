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
from fuzzywuzzy import fuzz
from joblib import Parallel, delayed, cpu_count
from prettytable import PrettyTable
from requests.adapters import HTTPAdapter
from threading import Thread
from typing import List, Union


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
    
    def get_best_index(self, singers: List[Union[List, str]], songs: List[str]):
        # return best_index, best_name, best_score
        if len(singers) != len(songs):
            return None
        if (not isinstance(singers, list)) or (not isinstance(songs, list)):
            return None
        if len(singers) == 0:
            return None
        cc = opencc.OpenCC()
        if self.singer is not None and self.song is not None:
            target_name = cc.convert('{} - {}'.format(self.singer, self.song))
        else:
            target_name = self.singer or self.song
        if target_name is None:
            return 0, None, 0
        score = [0] * len(singers)
        names = [None] * len(singers)
        for i in range(len(singers)):
            a_song = str(songs[i])
            if isinstance(singers[i], str):
                a_singer = singers[i]
            elif isinstance(singers[i], list):
                a_singer = '、'.join(singers[i])
            else:
                a_singer = str(singers[i])
            obj_name = cc.convert('{} - {}'.format(a_singer, a_song))
            score[i] = (fuzz.token_set_ratio(target_name, obj_name) + fuzz.token_sort_ratio(target_name, obj_name)) / 2
            names[i] = obj_name
        max_index = 0
        max_score = score[0]
        for i, s in enumerate(score):
            if s > max_score:
                max_score = s
                max_index = i
        return max_index, names[max_index], score[max_index]

    def __init__(self, music_filename: str):
        self.music_filename = music_filename
        self.base_name = os.path.basename(self.music_filename)
        self.music_dir = os.path.dirname(self.music_filename)
        self.format = LrcDownloader.support_format(self.base_name)
        if self.format is None:
            ValueError(f'input file {music_filename} is a music file that don\'t support.')
        self.base_name = self.base_name[:-len(self.format)]
        self.lrc_name = self.base_name + '.lrc'
        self.best_name = None
        self.best_name_score = 0.
        try:
            s = self.base_name.split('-')
            s = [i.strip() for i in s]
            self.singer = s[0]
            self.song = ' '.join(s[1:])
        except Exception as e:
            self.singer = None
            self.song = None

    def search(self):
        NotImplementedError('search NotImplementedError')
    
    def get_lrc(self, info):
        NotImplementedError('get_lrc NotImplementedError')

    def download_lrc(self):
        info = self.search()

        if info is not None:
            lrc_text = self.get_lrc(info)
            return lrc_text
        return None
    
    def save_lrc(self, lrc_dir = None, lrc_text = None):
        if lrc_dir is None:
            lrc_dir = self.music_dir
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
        resp = {}
        try:
            req = s.get('http://www.hjmin.com/search', 
                        params={'keywords': self.base_name,
                                'limit': 100}, 
                        headers=LrcDownloader.headers, 
                        timeout=None)
            resp = req.json()
        except:
            return None

        try:
            ids = []
            songs = []
            singers = []
            for x in resp['result']['songs']:
                ids.append(x['id'])
                songs.append(x['name'])
                tmp = []
                for artist in x['artists']:
                    tmp.append(artist['name'])
                singers.append(tmp if len(tmp) > 0 else '')
            best_index, best_name, best_score = self.get_best_index(singers=singers, songs=songs)
            self.best_name = best_name
            self.best_name_score = best_score
            return ids[best_index]
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
                            'keyword': self.base_name,
                            'plat': 0,
                            'pagesize': 100}, 
                    headers=LrcDownloader.headers, 
                    timeout=None)
        resp = req.json()

        try:
            infos = []
            songs = []
            singers = []
            for x in resp['data']['info']:
                infos.append((x['filename'], x['hash']))
                s = x['filename'].split(' - ')
                songs.append(s[1])
                singers.append(x['singername'])
            best_index, best_name, best_score = self.get_best_index(singers=singers, songs=songs)
            self.best_name = best_name
            self.best_name_score = best_score
            return infos[best_index]
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
                          'keyword': info[0],
                          'hash': info[1]}, 
                  timeout=None)
        resp = r.json()
        
        id = None
        key = None
        try:
            id_keys = []
            songs = []
            singers = []
            for x in resp['candidates']:
                id_keys.append((x['id'], x['accesskey']))
                songs.append(x['song'])
                singers.append(x['singer'])
            best_index, best_name, best_score = self.get_best_index(singers=singers, songs=songs)
            id, key = id_keys[best_index]
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
                  params={'w': self.base_name, 
                          'format': 'json',
                          'n': 50,
                          't': 0}, 
                  timeout=None, 
                  headers=LrcDownloader.headers)
        resp = r.json()

        try:
            songmids = []
            songs = []
            singers = []
            for x in resp['data']['song']['list']:  # t=0 song, t=7 lyric
                songmids.append(x['songmid'])
                songs.append(x['songname'])
                tmp = []
                for artist in x['singer']:
                    tmp.append(artist['name'])
                singers.append(tmp if len(tmp) > 0 else '')
            best_index, best_name, best_score = self.get_best_index(singers=singers, songs=songs)
            self.best_name = best_name
            self.best_name_score = best_score
            return songmids[best_index]
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

def download_lrc(music_file, only_search):
    downloaders = {'酷狗': LrcDownloaderKugou, 
                   'QQ': LrcDownloaderQQ}
    #    '网易': LrcDownloaderNetease
    if os.path.exists(music_file):
        downloader_result = {}  # [name]: (is_succ, obj, lrc*)
        for downloader_name, c in downloaders.items():
            ld = c(music_file)
            lrc_text = ld.download_lrc()
            downloader_result[downloader_name] = (lrc_text is not None, ld, lrc_text)
        # get best lrc
        best_downloader_name = None
        best_score = -1.
        for downloader_name, r in downloader_result.items():
            _, ld, __ = r
            # print(downloader_name, _, ld.best_name, ld.best_name_score)
            if ld.best_name_score > best_score:
                best_downloader_name = downloader_name
                best_score = ld.best_name_score
        if best_downloader_name is not None:
            is_succ, ld, lrc = downloader_result[best_downloader_name]
            if not is_succ:
                return '\033[32m无歌词\033[0m', best_downloader_name, ld.best_name, ld.best_name_score
            if only_search:
                status = '搜索'
            else:
                if not ld.save_lrc(lrc_dir=None, lrc_text=lrc):
                    return '\033[31m保存失败\033[0m', best_downloader_name, ld.best_name, ld.best_name_score
                status = '下载'
            return status, best_downloader_name, ld.best_name, ld.best_name_score
        else:
            return '\033[31m失败\033[0m', best_downloader_name, '', 0.
    else:
        return '\033[31m无此文件\033[0m', None, '', 0.

def main(music_dir = '.', 
         music_file = None,
         force = False, 
         only_search = False,
         threads = None):
    if threads is None:
        threads = 2 * cpu_count()
    else:
        threads = int(threads)
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
    rs = Parallel(n_jobs=threads, prefer='threads', verbose=1)(
            delayed(download_lrc)(f, only_search)
            for f in music_files
        )
    tb = PrettyTable()
    tb.add_column('文件名', music_files, align='l')
    tb.add_column('状态', [i[0] for i in rs])
    tb.add_column('源', [i[1] for i in rs])
    tb.add_column('匹配名', [i[2] for i in rs], align='l')
    tb.add_column('匹配度', [i[3] for i in rs], align='r')
    print(tb)

if __name__ == '__main__':
    Fire(main)
