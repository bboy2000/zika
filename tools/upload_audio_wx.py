# -*- coding: utf-8 -*-
"""
微信云开发云存储批量上传（P3-3，微信服务器 API 版）
token -> /tcb/uploadfile 取 COS 上传凭证 -> multipart 上传 -> fileid_map.json
用法:
  WX_APPID=xx WX_SECRET=xx WX_ENV=xx python tools/upload_audio_wx.py [--limit N] [--force]
"""
import json, os, sys, time, uuid, mimetypes
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request, urllib.error

ABDIR = r'E:/字卡项目/audio_build'
MAP = os.path.join(ABDIR, 'audio_map.json')
OUT = os.path.join(ABDIR, 'fileid_map.json')

APPID = os.environ.get('WX_APPID', '')
SECRET = os.environ.get('WX_SECRET', '')
ENV = os.environ.get('WX_ENV', '')
FORCE = '--force' in sys.argv
LIMIT = None
if '--limit' in sys.argv:
    LIMIT = int(sys.argv[sys.argv.index('--limit') + 1])

def log(msg):
    print(time.strftime('%H:%M:%S ') + msg, flush=True)

def http_json(url, data=None, headers=None, timeout=30):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                 headers=headers or {}, method='POST' if data is not None else 'GET')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def get_token():
    u = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={SECRET}'
    r = http_json(u)
    if 'access_token' not in r:
        raise RuntimeError(f'获取 token 失败: {r}')
    return r['access_token']

def get_upload_cred(token, cloud_path):
    r = http_json(f'https://api.weixin.qq.com/tcb/uploadfile?access_token={token}',
                  {'env': ENV, 'path': cloud_path})
    if r.get('errcode', 0) != 0:
        raise RuntimeError(f'uploadfile 接口失败: {r}')
    return r

def cos_upload(cred, local_path, cloud_path):
    boundary = uuid.uuid4().hex
    url = cred['url']
    fields = [
        ('key', cloud_path),
        ('Signature', cred['authorization']),
        ('x-cos-security-token', cred['token']),
        ('x-cos-meta-fileid', cred['cos_file_id']),
    ]
    body = b''
    for k, v in fields:
        body += f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    with open(local_path, 'rb') as f:
        data = f.read()
    ctype = mimetypes.guess_type(local_path)[0] or 'application/octet-stream'
    body += (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{os.path.basename(cloud_path)}"\r\n'
             f'Content-Type: {ctype}\r\n\r\n').encode() + data + f'\r\n--{boundary}--\r\n'.encode()
    req = urllib.request.Request(url, data=body, method='POST', headers={
        'Content-Type': f'multipart/form-data; boundary={boundary}'})
    with urllib.request.urlopen(req, timeout=60) as r:
        if r.status not in (200, 204):
            raise RuntimeError(f'COS 上传 HTTP {r.status}')

def upload_one(key, entry, token):
    f = entry['file']
    local = os.path.join(ABDIR, f)
    cloud_path = 'audio/' + f
    cred = get_upload_cred(token, cloud_path)
    cos_upload(cred, local, cloud_path)
    from urllib.parse import urlparse
    bucket = urlparse(cred['url']).hostname.split('.')[0]
    return key, f'cloud://{ENV}.{bucket}/{cloud_path}'

def main():
    m = json.load(open(MAP, encoding='utf-8'))
    entries = m['entries']
    keys = list(entries)
    done = {} if FORCE else (json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {})
    todo = [k for k in keys if k not in done and os.path.exists(os.path.join(ABDIR, entries[k]['file']))]
    if LIMIT:
        todo = todo[:LIMIT]
    log(f'总 {len(keys)}  已完成 {len(done)}  待传 {len(todo)}')
    if not todo:
        log('无需上传')
        return

    token = get_token()
    log('token 获取成功')
    tok_time = time.time()

    ok, fail = 0, []
    t0 = time.time()
    def worker(k):
        nonlocal token
        # token 有效期 7200s，单线程批次远快于此，稳妥起见过 6000s 刷新
        for attempt in range(3):
            try:
                return upload_one(k, entries[k], token)
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(2 * (attempt + 1))
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(worker, k): k for k in todo}
        for fu in as_completed(futs):
            k = futs[fu]
            try:
                key, fid = fu.result()
                done[key] = fid
                ok += 1
            except Exception as e:
                fail.append((k, str(e)))
            if (ok + len(fail)) % 50 == 0:
                json.dump(done, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
                rate = (ok + len(fail)) / max(time.time() - t0, 1)
                eta = (len(todo) - ok - len(fail)) / max(rate, 0.1)
                log(f'进度 {ok + len(fail)}/{len(todo)}  成功 {ok}  失败 {len(fail)}  速率 {rate:.1f}/s  剩余约 {eta/60:.0f} 分钟')
    json.dump(done, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    log(f'完成: 成功 {ok}  失败 {len(fail)}')
    for k, e in fail[:10]:
        log(f'FAIL {k}: {e}')

if __name__ == '__main__':
    main()
