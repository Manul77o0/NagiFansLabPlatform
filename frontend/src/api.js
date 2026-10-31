import axios from 'axios'

export const api = axios.create({
  withCredentials: true, // ★ここでCookie送信を有効にする
})