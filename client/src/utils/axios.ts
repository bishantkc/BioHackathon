import axios from "axios";

const axiosInstance = axios.create({
    baseURL: `${import.meta.env.VITE_BACKEND_URL}/`
});

axiosInstance.interceptors.request.use(async (config) => {
    return config;
}, error => {
    return Promise.reject(error);
});

export default axiosInstance;