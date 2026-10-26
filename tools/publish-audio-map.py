# -*- coding: utf-8 -*-
"""
发布 audio_map 到小程序数据目录：audio_build/audio_map.json -> mp/common/data-json/audio_map.json

- 丢弃 build 期字段，只留 entries
- 包内【不写 fileID】：每条 120+ 字符的完整 fileID 会让主包超 2MB 上限，
  小程序端用 common/audio.js 里的 CLOUD_PREFIX + file 运行时拼回。
  fileid_map.json 只用来确认 cloud 标志位（H5 预览走 /audio/ 相对路径不受影响）

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
DST = os.path.join(ROOT, 'mp', 'common', 'data-json', 'audio_map.json')


def main():
    src = json.load(open(SRC, encoding='utf-8'))
    fileids = {}
    if os.path.exists(FILEIDS):
        fileids = json.load(open(FILEIDS, encoding='utf-8'))

    entries = {}
    n_cloud = 0
    for key, e in src['entries'].items():
        it = {
            'file': e['file'],
            'text': e['text'],
            'kind': e['kind'],
        }
        if e.get('fallbackWord'):
            it['fallbackWord'] = e['fallbackWord']  # 无替身读音降级播组词（fix-tts-standin.py）
        if key in fileids:
            n_cloud += 1
        entries[key] = it

    doc = {
        'voice': src['voice'],
        'rate': src['rate'],
        'version': 'p3-2',
        'total': len(entries),
        'cloud': n_cloud == len(entries),
        'entries': entries,
    }
    json.dump(doc, open(DST, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('写出 %s：%d 条（%d 条已有云 fileID，包内不存 fileID 由端上拼接）' % (DST, len(entries), n_cloud))


if __name__ == '__main__':
    main()
