/**
 * DSBP Invitations API
 */
import http from './http';

const createInvitation = (data) => http.post('/invitations', data);
const getProjectInvitations = (projectId) => http.get(`/invitations/project/${projectId}`);
const acceptInvitation = (token) => http.post(`/invitations/accept/${token}`);

export default {
  createInvitation,
  getProjectInvitations,
  acceptInvitation,
};

