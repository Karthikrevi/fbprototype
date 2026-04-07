import React, { useEffect, useRef } from 'react';
import { StatusBar, Platform, LogBox } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthProvider, useAuth } from './src/context/AuthContext';
import { LocationProvider } from './src/context/LocationContext';
import AppNavigator from './src/navigation/AppNavigator';
import { COLORS } from './src/constants/theme';
import { SOCKET_URL } from './src/constants/api';

LogBox?.ignoreLogs?.(['Warning:']);

function SocketManager() {
  const { user } = useAuth();
  const socketRef = useRef(null);

  useEffect(() => {
    if (!user?.email) return;

    let socket;
    try {
      const io = require('socket.io-client');
      socket = io.connect(SOCKET_URL, { transports: ['websocket'], forceNew: true });
      socketRef.current = socket;

      socket.on('connect', () => {
        socket.emit('join', { email: user.email });
      });

      socket.on('booking_done', (data) => {
        console.log('Booking done notification:', data);
      });

      socket.on('review_prompt', (data) => {
        console.log('Review prompt:', data);
      });

      socket.on('new_message', (data) => {
        console.log('New message:', data);
      });

      socket.on('booking_confirmed', (data) => {
        console.log('Booking confirmed:', data);
      });
    } catch {}

    return () => {
      if (socket) socket.disconnect();
    };
  }, [user?.email]);

  return null;
}

export default function App() {
  return (
    <SafeAreaProvider>
      <StatusBar barStyle="light-content" backgroundColor={COLORS.primary} />
      <AuthProvider>
        <LocationProvider>
          <SocketManager />
          <AppNavigator />
        </LocationProvider>
      </AuthProvider>
    </SafeAreaProvider>
  );
}
