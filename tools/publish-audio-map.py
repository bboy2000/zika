# -*- coding: utf-8 -*-
"""
发布 audio_map 到小程序数据目录：audio_build/audio_map.json -> mp/static/data/audio_map.json

- 丢弃 build 期字段，只留 entries
- fileID 从云端清单回填（tools/upload-audio.py 上传后生成的 fileid_map.json），
  没有就置 null —— 小程序端没有 fileID 不播（H5 预览走 /audio/ 相对路径不受影响）

用法：
  python tools/publish-audio-map.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(os.path.dirname(ROOT), 'audio_build', 'audio_map.json')
FILEIDS = os.path.join(os.path.dirname(ROOT), 'audio_build', 'fileid_map.json')
DST = os.path.join(ROOT, 'mp', 'static', 'data', 'audio_map.json')


def main():
    src = json.load(open(SRC, encoding='utf-8'))
    fileids = {}
    if os.path.exists(FILEIDS):
        fileids = json.load(open(FILEIDS, encoding='utf-8'))

    entries = {}
    for key, e in src['entries'].items():
        entries[key] = {
            'file': e['file'],
            'text': e['text'],
            'kind': e['kind'],
            'fileID': fileids.get(key),
        }

    doc = {
        'voice': src['voice'],
        'rate': src['rate'],
        'version': 'p3-1',
        'total': len(entries),
        'cloud': bool(fileids),
        'entries': entries,
    }
    json.dump(doc, open(DST, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    n_cloud = len([1 for e in entries.values() if e['fileID']])
    print('写出 %s：%d 条（%d 条已有云 fileID）' % (DST, len(entries), n_cloud))


if __name__ == '__main__':
    main()
