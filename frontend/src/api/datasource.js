import request from './request'

export function getDataSources(params) {
  return request.get('/datasources', { params })
}

export function getDataSource(id) {
  return request.get(`/datasources/${id}`)
}

export function createDataSource(data) {
  return request.post('/datasources', data)
}

export function updateDataSource(id, data) {
  return request.put(`/datasources/${id}`, data)
}

export function deleteDataSource(id) {
  return request.delete(`/datasources/${id}`)
}

export function testConnection(id) {
  return request.post(`/datasources/${id}/test`)
}

export function getTables(id) {
  return request.get(`/datasources/${id}/tables`)
}

export function getTableSchema(id, tableName) {
  return request.get(`/datasources/${id}/tables/${tableName}/schema`)
}
