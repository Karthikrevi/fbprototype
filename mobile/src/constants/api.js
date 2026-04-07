import { Platform } from 'react-native';

const getBaseUrl = () => {
  if (Platform.OS === 'web') {
    return '/api/v1';
  }
  const DEV_HOST = process.env.EXPO_PUBLIC_API_HOST || 'localhost:5000';
  return `http://${DEV_HOST}/api/v1`;
};

export const API_BASE = getBaseUrl();

export const SOCKET_URL = Platform.OS === 'web'
  ? ''
  : `http://${process.env.EXPO_PUBLIC_API_HOST || 'localhost:5000'}`;
