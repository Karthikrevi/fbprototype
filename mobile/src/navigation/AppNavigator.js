import React, { useState, useEffect } from 'react';
import { Dimensions, Platform } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Feather } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { COLORS } from '../constants/theme';
import { useAuth } from '../context/AuthContext';
import LoadingScreen from '../components/LoadingScreen';

import WelcomeScreen from '../screens/WelcomeScreen';
import LoginScreen from '../screens/LoginScreen';
import RegisterScreen from '../screens/RegisterScreen';
import GDPRConsentScreen from '../screens/GDPRConsentScreen';

import HomeScreen from '../screens/HomeScreen';
import DiscoverScreen from '../screens/DiscoverScreen';
import BookingsScreen from '../screens/BookingsScreen';
import MarketplaceScreen from '../screens/MarketplaceScreen';
import ProfileScreen from '../screens/ProfileScreen';

import PetsScreen from '../screens/PetsScreen';
import AddPetScreen from '../screens/AddPetScreen';
import EditPetScreen from '../screens/EditPetScreen';
import PetDetailScreen from '../screens/PetDetailScreen';
import PassportScreen from '../screens/PassportScreen';
import GroomersScreen from '../screens/GroomersScreen';
import VendorProfileScreen from '../screens/VendorProfileScreen';
import GroomerListingScreen from '../screens/GroomerListingScreen';
import GroomerProfileScreen from '../screens/GroomerProfileScreen';
import BookingScreen from '../screens/BookingScreen';
import ReviewScreen from '../screens/ReviewScreen';
import VendorShopScreen from '../screens/VendorShopScreen';
import CartScreen from '../screens/CartScreen';
import OrdersScreen from '../screens/OrdersScreen';
import HandlersScreen from '../screens/HandlersScreen';
import HandlerDetailScreen from '../screens/HandlerDetailScreen';
import HandlerBookScreen from '../screens/HandlerBookScreen';
import HandlerInvoiceScreen from '../screens/HandlerInvoiceScreen';
import MyHandlerBookingsScreen from '../screens/MyHandlerBookingsScreen';
import CommunityScreen from '../screens/CommunityScreen';
import StrayScreen from '../screens/StrayScreen';
import StrayDetailScreen from '../screens/StrayDetailScreen';
import ConversationsScreen from '../screens/ConversationsScreen';
import MessageScreen from '../screens/MessageScreen';
import VetsScreen from '../screens/VetsScreen';
import BoardingScreen from '../screens/BoardingScreen';
import SettingsScreen from '../screens/SettingsScreen';
import FurrWingsServicesScreen from '../screens/FurrWingsServicesScreen';
import FurrWingsManagementScreen from '../screens/FurrWingsManagementScreen';
import ReportIssuesScreen from '../screens/ReportIssuesScreen';
import NotificationsScreen from '../screens/NotificationsScreen';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

const screenOptions = {
  headerStyle: { backgroundColor: COLORS.primary, elevation: 0, shadowOpacity: 0 },
  headerTintColor: COLORS.white,
  headerTitleStyle: { fontWeight: '600' },
  headerBackTitleVisible: false,
};

function AuthStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Welcome" component={WelcomeScreen} />
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Register" component={RegisterScreen} />
    </Stack.Navigator>
  );
}

function HomeStack() {
  return (
    <Stack.Navigator screenOptions={screenOptions}>
      <Stack.Screen name="Home" component={HomeScreen} options={{ headerShown: false }} />
      <Stack.Screen name="PetDetail" component={PetDetailScreen} options={{ title: 'Pet Details' }} />
      <Stack.Screen name="AddPet" component={AddPetScreen} options={{ title: 'Add Pet' }} />
      <Stack.Screen name="EditPet" component={EditPetScreen} options={{ title: 'Edit Pet' }} />
      <Stack.Screen name="Passport" component={PassportScreen} options={{ title: 'Pet Passport' }} />
      <Stack.Screen name="Pets" component={PetsScreen} options={{ title: 'My Pets' }} />
      <Stack.Screen name="VendorProfile" component={VendorProfileScreen} options={{ title: 'Vendor' }} />
      <Stack.Screen name="GroomerListing" component={GroomerListingScreen} options={{ title: 'Groomers' }} />
      <Stack.Screen name="GroomerProfile" component={GroomerProfileScreen} options={{ title: 'Groomer' }} />
      <Stack.Screen name="Booking" component={BookingScreen} options={{ title: 'Book Appointment' }} />
      <Stack.Screen name="Review" component={ReviewScreen} options={{ title: 'Leave Review' }} />
      <Stack.Screen name="VendorShop" component={VendorShopScreen} options={{ title: 'Shop' }} />
      <Stack.Screen name="Cart" component={CartScreen} options={{ title: 'Cart' }} />
      <Stack.Screen name="Orders" component={OrdersScreen} options={{ title: 'My Orders' }} />
      <Stack.Screen name="Marketplace" component={MarketplaceScreen} options={{ headerShown: false }} />
      <Stack.Screen name="Groomers" component={GroomersScreen} options={{ headerShown: false }} />
      <Stack.Screen name="Bookings" component={BookingsScreen} options={{ headerShown: false }} />
      <Stack.Screen name="Handlers" component={HandlersScreen} options={{ title: 'Handlers' }} />
      <Stack.Screen name="HandlerDetail" component={HandlerDetailScreen} options={{ title: 'Handler' }} />
      <Stack.Screen name="HandlerBook" component={HandlerBookScreen} options={{ title: 'Book Handler' }} />
      <Stack.Screen name="HandlerInvoice" component={HandlerInvoiceScreen} options={{ title: 'Invoice' }} />
      <Stack.Screen name="MyHandlerBookings" component={MyHandlerBookingsScreen} options={{ title: 'Travel Bookings' }} />
      <Stack.Screen name="Community" component={CommunityScreen} options={{ title: 'Community' }} />
      <Stack.Screen name="StrayTracker" component={StrayScreen} options={{ title: 'Stray Tracker' }} />
      <Stack.Screen name="StrayDetail" component={StrayDetailScreen} options={{ title: 'Stray Details' }} />
      <Stack.Screen name="Conversations" component={ConversationsScreen} options={{ title: 'Messages' }} />
      <Stack.Screen name="Message" component={MessageScreen} options={({ route }) => ({ title: route.params?.vendorName || 'Chat' })} />
      <Stack.Screen name="Vets" component={VetsScreen} options={{ title: 'Veterinarians' }} />
      <Stack.Screen name="Boarding" component={BoardingScreen} options={{ title: 'Boarding' }} />
      <Stack.Screen name="FurrWingsServices" component={FurrWingsServicesScreen} options={{ title: 'FurrWings Services' }} />
      <Stack.Screen name="FurrWingsManagement" component={FurrWingsManagementScreen} options={{ title: 'FurrWings Management' }} />
      <Stack.Screen name="ReportIssues" component={ReportIssuesScreen} options={{ title: 'Report Issues' }} />
      <Stack.Screen name="Notifications" component={NotificationsScreen} options={{ title: 'Notifications' }} />
      <Stack.Screen name="Settings" component={SettingsScreen} options={{ title: 'Settings' }} />
    </Stack.Navigator>
  );
}

function DiscoverStack() {
  return (
    <Stack.Navigator screenOptions={screenOptions}>
      <Stack.Screen name="DiscoverMain" component={DiscoverScreen} options={{ headerShown: false }} />
      <Stack.Screen name="VendorProfile" component={VendorProfileScreen} options={{ title: 'Vendor' }} />
      <Stack.Screen name="GroomerProfile" component={GroomerProfileScreen} options={{ title: 'Groomer' }} />
      <Stack.Screen name="Booking" component={BookingScreen} options={{ title: 'Book Appointment' }} />
    </Stack.Navigator>
  );
}

function BookingsStack() {
  return (
    <Stack.Navigator screenOptions={screenOptions}>
      <Stack.Screen name="BookingsMain" component={BookingsScreen} options={{ headerShown: false }} />
      <Stack.Screen name="Review" component={ReviewScreen} options={{ title: 'Leave Review' }} />
    </Stack.Navigator>
  );
}

function ShopStack() {
  return (
    <Stack.Navigator screenOptions={screenOptions}>
      <Stack.Screen name="MarketplaceMain" component={MarketplaceScreen} options={{ headerShown: false }} />
      <Stack.Screen name="VendorShop" component={VendorShopScreen} options={{ title: 'Shop' }} />
      <Stack.Screen name="Cart" component={CartScreen} options={{ title: 'Cart' }} />
    </Stack.Navigator>
  );
}

function ProfileStack() {
  return (
    <Stack.Navigator screenOptions={screenOptions}>
      <Stack.Screen name="ProfileMain" component={ProfileScreen} options={{ headerShown: false }} />
      <Stack.Screen name="Settings" component={SettingsScreen} options={{ title: 'Settings' }} />
      <Stack.Screen name="Bookings" component={BookingsScreen} options={{ title: 'My Bookings' }} />
      <Stack.Screen name="Orders" component={OrdersScreen} options={{ title: 'My Orders' }} />
      <Stack.Screen name="Conversations" component={ConversationsScreen} options={{ title: 'Messages' }} />
      <Stack.Screen name="MyHandlerBookings" component={MyHandlerBookingsScreen} options={{ title: 'Travel Bookings' }} />
      <Stack.Screen name="PetDetail" component={PetDetailScreen} options={{ title: 'Pet Details' }} />
      <Stack.Screen name="Pets" component={PetsScreen} options={{ title: 'My Pets' }} />
    </Stack.Navigator>
  );
}

function MainTabs() {
  return (
    <Tab.Navigator screenOptions={({ route }) => ({
      headerShown: false,
      tabBarActiveTintColor: COLORS.primary,
      tabBarInactiveTintColor: COLORS.grey,
      tabBarStyle: { paddingBottom: Platform.OS === 'ios' ? 20 : 8, paddingTop: 8, height: Platform.OS === 'ios' ? 85 : 65 },
      tabBarLabelStyle: { fontSize: 11, fontWeight: '500' },
      tabBarIcon: ({ color, size }) => {
        const icons = { HomeTab: 'home', DiscoverTab: 'search', BookingsTab: 'calendar', ShopTab: 'shopping-bag', ProfileTab: 'user' };
        return <Feather name={icons[route.name]} size={size} color={color} />;
      },
    })}>
      <Tab.Screen name="HomeTab" component={HomeStack} options={{ tabBarLabel: 'Home' }} />
      <Tab.Screen name="DiscoverTab" component={DiscoverStack} options={{ tabBarLabel: 'Discover' }} />
      <Tab.Screen name="BookingsTab" component={BookingsStack} options={{ tabBarLabel: 'Bookings' }} />
      <Tab.Screen name="ShopTab" component={ShopStack} options={{ tabBarLabel: 'Shop' }} />
      <Tab.Screen name="ProfileTab" component={ProfileStack} options={{ tabBarLabel: 'Profile' }} />
    </Tab.Navigator>
  );
}

export default function AppNavigator() {
  const { user, isLoading } = useAuth();
  const [gdprAccepted, setGdprAccepted] = useState(null);

  useEffect(() => {
    (async () => {
      const val = await AsyncStorage.getItem('gdpr_accepted');
      setGdprAccepted(!!val);
    })();
  }, []);

  if (isLoading || gdprAccepted === null) return <LoadingScreen />;

  return (
    <NavigationContainer>
      {!gdprAccepted ? (
        <Stack.Navigator screenOptions={{ headerShown: false }}>
          <Stack.Screen name="GDPR">
            {() => <GDPRConsentScreen onAccept={() => setGdprAccepted(true)} />}
          </Stack.Screen>
        </Stack.Navigator>
      ) : !user ? (
        <AuthStack />
      ) : (
        <MainTabs />
      )}
    </NavigationContainer>
  );
}
