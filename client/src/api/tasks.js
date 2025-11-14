/**
 * DSBP Tasks API
 */
import http from './http';

const getBoardTasks = (boardId, statusFilter = null) => {
  const url = statusFilter 
    ? `/tasks/board/${boardId}?status_filter=${statusFilter}`
    : `/tasks/board/${boardId}`;
  return http.get(url);
};

const getTask = (id) => http.get(`/tasks/${id}`);
const createTask = (data) => http.post('/tasks', data);
const updateTask = (id, data) => http.patch(`/tasks/${id}`, data);
const deleteTask = (id) => http.delete(`/tasks/${id}`);

export default {
  getBoardTasks,
  getTask,
  createTask,
  updateTask,
  deleteTask,
};

