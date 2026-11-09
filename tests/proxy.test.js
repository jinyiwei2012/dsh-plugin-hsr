// 反代地址改写测试
import assert from 'node:assert/strict'
import { test } from 'node:test'

import { rewriteSegments } from '../lib/host/proxy.js'
import { PROXY_PREFIX } from '../lib/host/consts.js'

test('改写 /api/ 开头的图片地址', () => {
  const out = rewriteSegments([{ type: 'image', url: '/api/media/a.png' }])
  assert.equal(out[0].url, PROXY_PREFIX + '/api/media/a.png')
})

test('保留非 /api/ 的地址', () => {
  const out = rewriteSegments([{ type: 'image', url: 'https://example.com/x.png' }])
  assert.equal(out[0].url, 'https://example.com/x.png')
})

test('递归改写 node 子项', () => {
  const out = rewriteSegments([
    { type: 'node', items: [{ type: 'image', url: '/api/media/b.png' }] },
  ])
  assert.equal(out[0].items[0].url, PROXY_PREFIX + '/api/media/b.png')
})

test('空值与异常输入不炸', () => {
  assert.deepEqual(rewriteSegments(null), [])
  assert.deepEqual(rewriteSegments(undefined), [])
  const out = rewriteSegments([null, 42, { type: 'text' }])
  assert.equal(out.length, 3)
  assert.equal(out[2].type, 'text')
})

test('不带 url 的段原样返回', () => {
  const seg = { type: 'html', content: '<b>x</b>' }
  const out = rewriteSegments([seg])
  assert.deepEqual(out[0], seg)
})
