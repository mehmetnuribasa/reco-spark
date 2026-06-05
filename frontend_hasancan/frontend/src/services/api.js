import axios from 'axios';

const BASE_URL = 'http://localhost:8000';

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
});

export const getRecommendations = async (userId, topN = 10) => {
  const res = await client.post('/recommendations', {
    userId: parseInt(userId),
    topN: parseInt(topN),
  });
  return res.data;
};

export const checkHealth = async () => {
  const res = await client.get('/health');
  return res.data;
};
