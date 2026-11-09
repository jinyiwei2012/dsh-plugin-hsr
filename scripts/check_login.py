# -*- coding: utf-8 -*-
"""检查扫码登录结果是否落库。"""
import sys

ROOT = r'C:\Users\Administrator\dsh-plugins\dsh-plugin-hsr'
sys.path.insert(0, ROOT + r'\service')

from hsr.store import db

accs = db.list_accounts()
print('已绑定账号数:', len(accs))
for a in accs:
    has = '有 Cookie' if a.cookie else '仅 UID'
    nick = a.nickname or '(未校验)'
    print(f'  UID {a.uid}  {nick}  Lv{a.level}  {has}')
    if a.cookie:
        print(f'    Cookie 长度 {len(a.cookie)}，前 16 字符: {a.cookie[:16]}...')

print()
ticket = db.get_setting('login_ticket')
print('待确认 ticket:', repr(ticket))

# 最近一次查询的 ticket 状态
if ticket:
    from hsr.api import qrlogin
    try:
        st = qrlogin.query_status(ticket)
        print('该 ticket 状态:', st.status, '已确认:', st.confirmed)
        if st.confirmed:
            print('  tokens 数量:', len(st.tokens))
            for t in st.tokens:
                print('   token_type =', t.get('token_type'), ' 长度', len(str(t.get('token') or '')))
            print('  user_info:', st.user_info)
    except Exception as e:
        print('查询 ticket 失败:', e)
