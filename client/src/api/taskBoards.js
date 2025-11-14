/**
 * DSBP Task Boards API
 */
import http from './http';

const getProjectBoards = (projectId) => http.get(`/task-boards/project/${projectId}`);
const getBoard = (id) => http.get(`/task-boards/${id}`);
const createBoard = (data) => http.post('/task-boards', data);
const updateBoard = (id, data) => http.patch(`/task-boards/${id}`, data);
const deleteBoard = (id) => http.delete(`/task-boards/${id}`);

export default {
  getProjectBoards,
  getBoard,
  createBoard,
  updateBoard,
  deleteBoard,
};

