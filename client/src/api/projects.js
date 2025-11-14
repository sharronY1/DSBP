/**
 * DSBP Projects API
 */
import http from './http';

const getProjects = () => http.get('/projects');
const getProject = (id) => http.get(`/projects/${id}`);
const createProject = (data) => http.post('/projects', data);
const updateProject = (id, data) => http.patch(`/projects/${id}`, data);
const deleteProject = (id) => http.delete(`/projects/${id}`);

export default {
  getProjects,
  getProject,
  createProject,
  updateProject,
  deleteProject,
};

