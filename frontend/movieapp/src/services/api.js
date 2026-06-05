import axios from 'axios';

const BASE_URL = 'http://localhost:8000';

export const getRecommendations = async (userId, topN = 10) => {
  const res = await axios.post(`${BASE_URL}/recommendations`, {
    userId: parseInt(userId),
    topN,
  });
  return res.data.recommendations;
};