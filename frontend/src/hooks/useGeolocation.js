import { useState, useCallback } from 'react';

/**
 * Custom React hook for acquiring device GPS coordinates.
 */
export function useGeolocation() {
  const [coords, setCoords] = useState({ latitude: '', longitude: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getPosition = useCallback(() => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser.');
      return;
    }

    setLoading(true);
    setError(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setCoords({
          latitude: position.coords.latitude.toFixed(7),
          longitude: position.coords.longitude.toFixed(7),
        });
        setLoading(false);
      },
      (err) => {
        let msg = 'Failed to acquire GPS location.';
        if (err.code === 1) msg = 'Location permission denied by user.';
        else if (err.code === 2) msg = 'Location unavailable or GPS signal lost.';
        else if (err.code === 3) msg = 'Location request timed out.';
        setError(msg);
        setLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  }, []);

  return { coords, setCoords, loading, error, getPosition };
}

export default useGeolocation;
