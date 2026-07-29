import request from './request'

export function getKnowledgeDocs(params) {
  return request.get('/knowledge', { params })
}

export function uploadKnowledgeDoc(data, onProgress) {
  return request.post('/knowledge/upload', data, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress,
  })
}

export function deleteKnowledgeDoc(id) {
  return request.delete(`/knowledge/${id}`)
}

export function rebuildIndex(id) {
  return request.post(`/knowledge/${id}/rebuild`)
}

export function searchKnowledge(params) {
  return request.get('/knowledge/search', { params })
}

export function updateKnowledgeDoc(id, data) {
  return request.put(`/knowledge/${id}`, data)
}
