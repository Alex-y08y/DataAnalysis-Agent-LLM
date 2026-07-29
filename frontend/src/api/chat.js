import request from './request'

export function sendMessage(data) {
  return request.post('/chat/message', data)
}

export function getChatHistory(sessionId) {
  return request.get(`/chat/history/${sessionId}`)
}

export function getSessions() {
  return request.get('/chat/sessions')
}

export function createSession(data) {
  return request.post('/chat/sessions', data)
}

export function deleteSession(sessionId) {
  return request.delete(`/chat/sessions/${sessionId}`)
}

export function stopGeneration() {
  return request.post('/chat/stop')
}

export function exportChat(sessionId, format) {
  return request.get(`/chat/export/${sessionId}`, { params: { format } })
}
