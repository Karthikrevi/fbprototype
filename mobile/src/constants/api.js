import { Platform } from 'react-native';

const REPLIT_HOST = '5c976824-2f0f-4905-be9e-11f0c7c01fd0-00-1azd9rldtqmnw.spock.replit.dev';

const getBaseUrl = () => {
  if (Platform.OS === 'web') {
    return '/api/v1';
  }
  const host = process.env.EXPO_PUBLIC_API_HOST || REPLIT_HOST;
  return `https://${host}/api/v1`;
};

export const API_BASE = getBaseUrl();

export const SOCKET_URL = Platform.OS === 'web'
  ? ''
  : `https://${process.env.EXPO_PUBLIC_API_HOST || REPLIT_HOST}`;
