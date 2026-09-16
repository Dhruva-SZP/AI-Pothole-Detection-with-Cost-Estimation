import { useState, useCallback } from 'react';

/**
 * Custom React hook for acquiring device GPS coordinates with multi-tier fallback:
 * 1. High-accuracy HTML5 Geolocation (GPS/Sensors)
 * 2. Low-accuracy HTML5 Geolocation (Cell/Wi-Fi)
 * 3. Fast IP-based Geolocation fallback (works on desktops without GPS)
 */
export function useGeolocation() {
  const [coords, setCoords] = useState({ latitude: '', longitude: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fallbackToIp = async (userCallback) => {
    try {
      const res = await fetch('https://ipapi.co/json/', { signal: AbortSignal.timeout(5000) });
      if (res.ok) {
        const data = await res.json();
        if (data && data.latitude && data.longitude) {
          const newCoords = {
            latitude: Number(data.latitude).toFixed(7),
            longitude: Number(data.longitude).toFixed(7),
            city: data.city || '',
            region: data.region || ''
          };
          setCoords(newCoords);
          setError(null);
          setLoading(false);
          if (userCallback) userCallback(newCoords);
          return;
        }
      }
    } catch (ipErr) {
      // Secondary IP fallback
      try {
        const res2 = await fetch('https://freeipapi.com/api/json', { signal: AbortSignal.timeout(4000) });
        if (res2.ok) {
          const data2 = await res2.json();
          if (data2 && data2.latitude && data2.longitude) {
            const newCoords = {
              latitude: Number(data2.latitude).toFixed(7),
              longitude: Number(data2.longitude).toFixed(7),
              city: data2.cityName || '',
              region: data2.regionName || ''
            };
            setCoords(newCoords);
            setError(null);
            setLoading(false);
            if (userCallback) userCallback(newCoords);
            return;
          }
        }
      } catch (err2) {
        // Fallback failed
      }
    }
    setError('Could not detect location. Please enter coordinates manually or allow location access in your browser.');
    setLoading(false);
  };

  const getPosition = useCallback((onSuccess) => {
    setLoading(true);
    setError(null);

    if (!navigator.geolocation) {
      fallbackToIp(onSuccess);
      return;
    }

    // Tier 1: Try standard HTML5 geolocation
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const newCoords = {
          latitude: position.coords.latitude.toFixed(7),
          longitude: position.coords.longitude.toFixed(7),
        };
        setCoords(newCoords);
        setLoading(false);
        setError(null);
        if (onSuccess) onSuccess(newCoords);
      },
      (err) => {
        // Tier 2: Try low accuracy
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            const newCoords = {
              latitude: pos.coords.latitude.toFixed(7),
              longitude: pos.coords.longitude.toFixed(7),
            };
            setCoords(newCoords);
            setLoading(false);
            setError(null);
            if (onSuccess) onSuccess(newCoords);
          },
          () => {
            // Tier 3: Fallback to IP geolocation
            fallbackToIp(onSuccess);
          },
          { enableHighAccuracy: false, timeout: 8000, maximumAge: 300000 }
        );
      },
      { enableHighAccuracy: true, timeout: 8000, maximumAge: 60000 }
    );
  }, []);

  return { coords, setCoords, loading, error, getPosition };
}

export default useGeolocation;
