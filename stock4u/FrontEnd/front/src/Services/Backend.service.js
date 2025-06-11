import axios from 'axios';

const backendUrl = `http://${window.location.hostname}:5266`;

const usersPath = '/Users';
const positionsPath = '/Positions';
const achievementsPath = '/Achievements';
const investingAdvisorPath = '/InvestingAdvisor';
const stocksPath = '/Stocks';

// Users

export const getUserRiskLevel = async (userId) => await axios.get(`${backendUrl}${usersPath}/GetUserRiskLevel?userId=${userId}`);

export const login = async (userId, password) => await axios.post(`${backendUrl}${usersPath}/Login`, { userId, password });

export const register = async (registerData) => await axios.post(`${backendUrl}${usersPath}/Register`, registerData);

// Positions

export const getInvestorStatus = async (userId) => await axios.get(`${backendUrl}${positionsPath}/GetUserInvestmentStatus?userId=${userId}`);

export const getTopTenUsers = async () => await axios.get(`${backendUrl}${positionsPath}/GetTopTenUsers`);

export const getUserPositionsHistory = async (userId) => await axios.get(`${backendUrl}${positionsPath}/GetUserPositionsHistory?userId=${userId}`);

export const enterPosition = async (enterPositionData) => await axios.post(`${backendUrl}${positionsPath}/EnterPosition`, enterPositionData);

export const closePosition = async (closePositionData) => await axios.post(`${backendUrl}${positionsPath}/ClosePosition`, closePositionData);

export const editStopLimit = async (stopLimitData) => await axios.put(`${backendUrl}${positionsPath}/EditStopLimit`, stopLimitData);

// Investing Advisor

export const getStockRiskLevel = async (symbol) => await axios.get(`${backendUrl}${investingAdvisorPath}/GetStockRiskLevel?symbol=${symbol}`);

export const getRecommendedStocks = async (riskLevel) => await axios.get(`${backendUrl}${investingAdvisorPath}/GetRecommendedStocksByRisk?riskLevel=${riskLevel}`);

// Stocks

export const getRealTimeStock = async (symbol) => await axios.get(`${backendUrl}${stocksPath}/GetRealTimeStock?symbol=${symbol}`);

export const getStockHistory = async (symbol, daysBack) => await axios.get(`${backendUrl}${stocksPath}/GetStockHistory?symbol=${symbol}&daysBack=${daysBack}`);

// Achievements

export const getAllAchievements = async () => await axios.get(`${backendUrl}${achievementsPath}/GetAllAchievements`);

export const getUserAchievements = async (userId) => await axios.get(`${backendUrl}${achievementsPath}/GetUserAchievements?userId=${userId}`);