import React, { createContext, useState, useContext } from 'react';
import * as Location from 'expo-location';
import { locationAPI } from '../services/api';

const LocationContext = createContext(null);

export const LocationProvider = ({ children }) => {
  const [coords, setCoords] = useState(null);
  const [locationName, setLocationName] = useState(null);
  const [loading, setLoading] = useState(false);

  const requestLocation = async () => {
    setLoading(true);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setLoading(false);
        return { success: false, error: 'Location permission denied' };
      }
      const loc = await Location.getCurrentPositionAsync({});
      const { latitude, longitude } = loc.coords;
      setCoords({ lat: latitude, lon: longitude });

      try {
        const res = await locationAPI.set(latitude, longitude);
        if (res.data.success) {
          setLocationName(res.data.location_name);
        }
      } catch {}

      setLoading(false);
      return { success: true, lat: latitude, lon: longitude };
    } catch {
      setLoading(false);
      return { success: false, error: 'Failed to get location' };
    }
  };

  return (
    <LocationContext.Provider value={{ coords, locationName, loading, requestLocation }}>
      {children}
    </LocationContext.Provider>
  );
};

export const useLocation = () => useContext(LocationContext);
export default LocationContext;
