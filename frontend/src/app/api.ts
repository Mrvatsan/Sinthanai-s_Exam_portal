import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

const api = axios.create({
  baseURL: API_URL,
});

export const loginAdmin = async (username: string, password: string) => {
  return api.post('/login/', { username, password, role: 'admin' });
};

export const loginStudent = async (username: string, password: string) => {
  return api.post('/login/', { username, password, role: 'student' });
};

export const uploadDataset = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const getDatasets = async () => {
  return api.get('/datasets/');
}

export const toggleDataset = async (id: number) => {
  return api.post(`/datasets/${id}/toggle/`);
}

export const deleteStudents = async () => {
  return api.delete('/delete-all/');
}

export default api;
