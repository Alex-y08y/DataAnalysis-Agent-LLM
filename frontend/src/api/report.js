import request from './request'

export function getReportTemplates() {
  return request.get('/reports/templates')
}

export function createReport(data) {
  return request.post('/reports', data)
}

export function getReports(params) {
  return request.get('/reports', { params })
}

export function getReport(id) {
  return request.get(`/reports/${id}`)
}

export function deleteReport(id) {
  return request.delete(`/reports/${id}`)
}

export function exportReport(id, format) {
  return request.get(`/reports/${id}/export`, {
    params: { format },
    responseType: 'blob',
  })
}

export function createSchedule(data) {
  return request.post('/reports/schedules', data)
}

export function getSchedules() {
  return request.get('/reports/schedules')
}

export function deleteSchedule(id) {
  return request.delete(`/reports/schedules/${id}`)
}
