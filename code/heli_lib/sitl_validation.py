"""Pure validation of heli SITL navigation messages; fail closed."""
import math

HOME_LAT = 34.95416
HOME_LON = -117.87323
MAX_HOME_SEPARATION_DEG = 0.02


def valid_navigation(lat, lon, alt_m):
    if not all(isinstance(v, (int,float)) and math.isfinite(v)
               for v in (lat,lon,alt_m)):
        return False
    if lat == 0.0 and lon == 0.0:
        return False
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return False
    return (abs(lat-HOME_LAT)<MAX_HOME_SEPARATION_DEG
            and abs(lon-HOME_LON)<MAX_HOME_SEPARATION_DEG
            and abs(alt_m)<1000)
