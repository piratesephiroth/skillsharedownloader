import requests
import json
import sys
import re
import os


class Downloader(object):
    def __init__(
        self,
        cookie,
        download_path=os.environ.get('FILE_PATH', './courses'),
        pk='BCpkADawqM2OOcM6njnM7hf9EaK6lIFlqiXB0iWjqGWUQjU7R8965xUvIQNqdQbnDTLz0IAO7E6Ir2rIbXJtFdzrGtitoee0n1XXRliD-RH9A-svuvNW9qgo3Bh34HEZjXjG4Nml4iyz3KqF',
        brightcove_account_id=3695997568001,
    ):
        self.cookie = cookie.strip().strip('"')
        self.download_path = download_path
        self.pk = pk.strip()
        self.brightcove_account_id = brightcove_account_id
        self.pythonversion = 3 if sys.version_info >= (3, 0) else 2

    def fix_name(self, name):
        forbidden = ["<", ">", ":", "\"", "/", "\\", "|", "?", "*"]
        for char in forbidden:
            name = name.replace (char, "_")
        return name

    def download_course_by_url(self, url):
        m = re.match(r'https://www.skillshare.com/classes/.*?/(\d+)', url)

        if not m:
            raise Exception('Failed to parse class ID from URL')

        self.download_course_by_class_id(m.group(1))

    def download_course_by_class_id(self, class_id):
        data = self.fetch_course_data_by_class_id(class_id=class_id)
        teacher_name = None

        if 'full_name' in data['_embedded']['teacher']:
            teacher_name = data['_embedded']['teacher']['full_name']

        if not teacher_name:
            teacher_name = data['_embedded']['teacher']['vanity_username']

        if not teacher_name:
            raise Exception('Failed to read teacher name from data')

        teacher_name = self.fix_name(teacher_name)
        title = self.fix_name(data['title'])

        for s in data['_embedded']['sessions']['_embedded']['sessions']:
            
            video_id = None

            if 'video_hashed_id' in s and s['video_hashed_id']:
                video_id = s['video_hashed_id'].split(':')[1]

            if not video_id:
                # NOTE: this happens sometimes...
                # seems random and temporary but might be some random
                # server-side check on user-agent etc?
                # ...think it's more stable now with those set to
                # emulate an android device
                raise Exception('Failed to read video ID from data')

            s_title = self.fix_name(s['title'])
            
            base_path = os.path.abspath(
                os.path.join(
                    self.download_path,
                    teacher_name,
                    title,
                    'Unit {}'.format(str(s['unit_id'] + 1).zfill(2))
                )
            ).rstrip('/')
            
            if not os.path.exists(base_path):
                os.makedirs(base_path)
            
            # remove unit and index from title, if present
            s_title = re.sub("^\d+?\s\d+?\s", "", s_title)
            # combine index to title, for the file name
            file_name = '{} - {}'.format( str(s['index'] + 1).zfill(3), s_title,)

            self.download_video(
                fpath='{base_path}/{session}.mp4'.format(
                    base_path=base_path,
                    session=file_name,
                ),
                video_id=video_id,
            )

            print('')

    def fetch_course_data_by_class_id(self, class_id):
        res = requests.get(
            url='https://api.skillshare.com/classes/{}'.format(class_id),
            headers={
                'cookie': self.cookie
            }
        )

        if not res.status_code == 200:
            raise Exception('Fetch error, code == {}'.format(res.status_code))

        return res.json()

    def download_video(self, fpath, video_id):
        meta_url = 'https://edge.api.brightcove.com/playback/v1/accounts/{account_id}/videos/{video_id}'.format(
            account_id=self.brightcove_account_id,
            video_id=video_id,
        )

        meta_res = requests.get(
            meta_url,
            headers={
                'Accept': 'application/json;pk={}'.format(self.pk),
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
                'Origin': 'https://www.skillshare.com'
            }
        )

        if meta_res.status_code != 200:
            raise Exception('Failed to fetch video meta')

        for x in meta_res.json()['sources']:
            if 'container' in x:
                if x['container'] == 'MP4' and 'src' in x:
                    dl_url = x['src']
                    break

        print('Downloading {}...'.format(fpath))

        if os.path.exists(fpath):
            print('Video already downloaded, skipping...')
            return

        with open(fpath, 'wb') as f:
            response = requests.get(dl_url, allow_redirects=True, stream=True)
            total_length = response.headers.get('content-length')

            if not total_length:
                f.write(response.content)

            else:
                dl = 0
                total_length = int(total_length)

                for data in response.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)
                    done = int(50 * dl / total_length)
                    sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50 - done)))
                    sys.stdout.flush()

            print('')
