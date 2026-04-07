import React from 'react';
import { View, StyleSheet } from 'react-native';
import { createMaterialTopTabNavigator } from '@react-navigation/material-top-tabs';
import { COLORS } from '../constants/theme';
import GroomersScreen from './GroomersScreen';
import VetsScreen from './VetsScreen';
import BoardingScreen from './BoardingScreen';

const TopTab = createMaterialTopTabNavigator();

export default function DiscoverScreen() {
  return (
    <View style={styles.container}>
      <TopTab.Navigator
        screenOptions={{
          tabBarActiveTintColor: COLORS.primary,
          tabBarInactiveTintColor: COLORS.grey,
          tabBarIndicatorStyle: { backgroundColor: COLORS.primary },
          tabBarLabelStyle: { fontSize: 13, fontWeight: '600', textTransform: 'none' },
          tabBarStyle: { backgroundColor: COLORS.white },
        }}
      >
        <TopTab.Screen name="Groomers" component={GroomersScreen} />
        <TopTab.Screen name="Vets" component={VetsScreen} />
        <TopTab.Screen name="Boarding" component={BoardingScreen} />
      </TopTab.Navigator>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: 40, backgroundColor: COLORS.white },
});
