import assert from 'node:assert/strict'
import test from 'node:test'
import { api, getCurrentUser } from '../src/components/api.js'

test('loads the canonical user endpoint and validates the response', async () => {
  const originalAdapter = api.defaults.adapter
  try {
    api.defaults.adapter = async (config) => {
      assert.equal(config.url, '/api/users/me/')
      return {
        data: { id: 1, displayname: 'admin', level: 3 },
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      }
    }
    assert.equal((await getCurrentUser()).displayname, 'admin')
    api.defaults.adapter = async (config) => ({
      data: '<html>SPA fallback</html>',
      status: 200,
      statusText: 'OK',
      headers: {},
      config,
    })
    await assert.rejects(getCurrentUser(), /Invalid current user response/)
  } finally {
    api.defaults.adapter = originalAdapter
  }
})
