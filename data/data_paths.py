# REPURPOSE FOR BLOB
# Consider dictionary as alternate structure

# A centralised location for all relative data paths, to assist in data lakehouse architecture

# STAGING
FASTTRACK_PATH_STAGING = "statistics/gapminder-fast-track/"
SYSTEMAGLOBALIS_PATH_STAGING = "statistics/gapminder-systema-globalis/"
WDINDICATORS_PATH_STAGING = "statistics/world-development-indicators/"
WS_PATH_STAGING = "statistics/world-standards-unofficial-website/"
COUNTRY_LOOKUP_PATH_STAGING = "meta/country_lookup.csv"


UNDATA_PATH_STAGING = "/data_lakehouse/staging/statistics/undata/"
SDG_PATH_STAGING = "/data_lakehouse/staging/statistics/sdgindicators/"
MAP_JSON_LOW_PATH_STAGING = "/data_lakehouse/staging/geojson/natural_earth/map/ne_110m.geojson" #not sure if I ever needed to process this
MAP_JSON_MED_PATH_STAGING = "/data_lakehouse/staging/geojson/natural_earth/map/ne_50m.geojson" #sourced from natural earth
MAP_JSON_HIGH_PATH_STAGING = "/data_lakehouse/staging/geojson/natural_earth/map/ne_10m.geojson"
GLOBE_JSON_LAND_HIGH_PATH_STAGING = "/data_lakehouse/staging/geojson/natural_earth/globe/working/ne_50m_land.geojson"
GLOBE_JSON_OCEAN_HIGH_PATH_STAGING = "/data_lakehouse/staging/geojson/natural_earth/globe/working/ne_50m_ocean.geojson"
GLOBE_JSON_LAND_LOW_PATH_STAGING = "/data_lakehouse/staging/geojson/natural_earth/globe/working/ne_110m_land_cultural.geojson"
GLOBE_JSON_OCEAN_LOW_PATH_STAGING = "/data_lakehouse/staging/geojson/natural_earth/globe/working/ne_110m_ocean.geojson"
PWR_STN_PATH_STAGING = "/data_lakehouse/staging/geojson/global-power-stations/"
BIG_MAC_PATH_STAGING = "/data_lakehouse/staging/statistics/big-mac-index/big-mac-adjusted-index.csv"

# COPPER
COUNTRY_LOOKUP_PATH_COPPER = "meta/country_lookup.csv"

UNDATA_PATH_COPPER = "/data_lakehouse/copper/statistics/undata/"
SDG_PATH_COPPER ="/data_lakehouse/copper/statistics/sdgindicators/"
WS_PATH_COPPER = "/data_lakehouse/copper/statistics/world-standards-unofficial-website/"
BIG_MAC_PATH_COPPER = "/data_lakehouse/copper/statistics/big-mac-index/"

#IRON

FASTTRACK_PATH_IRON = "/data_lakehouse/iron/statistics/gapminder-fast-track/"
SYSTEMAGLOBALIS_PATH_IRON = "/data_lakehouse/iron/statistics/gapminder-systema-globalis/"
WDINDICATORS_PATH_IRON = "/data_lakehouse/iron/statistics/world-development-indicators/"
UNDATA_PATH_IRON = "/data_lakehouse/iron/statistics/undata/"
SDG_PATH_IRON = "/data_lakehouse/iron/statistics/sdgindicators/"
IRON_STATS_PATH = "/data_lakehouse/iron/statistics/" #smelting
WS_PATH_IRON = "/data_lakehouse/iron/statistics/world-standards-unofficial-website/"
BIG_MAC_PATH_IRON = "/data_lakehouse/iron/statistics/big-mac-index/"

# TITANIUM
MASTER_STATS_PATH = "/data_lakehouse/titanium/statistics/master_stats.parquet" 
MASTER_CONFIG_PATH = "/data_lakehouse/titanium/meta/master_config.csv"
MASTER_META_PATH = "/data_lakehouse/titanium/meta/master_meta.parquet" 
MAP_JSON_LOW_PATH_TITANIUM = "/data_lakehouse/titanium/geojson/map/ne_110m.geojson" 
MAP_JSON_MED_PATH_TITANIUM = "/data_lakehouse/titanium/geojson/map/ne_50m.geojson" 
MAP_JSON_HIGH_PATH_TITANIUM = "/data_lakehouse/titanium/geojson/map/ne_10m.geojson"
MAP_JSON_PATH = "/data_lakehouse/titanium/geojson/map/"
GLOBE_JSON_LAND_HIGH_PATH_TITANIUM = "/data_lakehouse/titanium/geojson/globe/ne_50m_land.geojson"
GLOBE_JSON_OCEAN_HIGH_PATH_TITANIUM = "/data_lakehouse/titanium/geojson/globe/ne_50m_ocean.geojson"
GLOBE_JSON_LAND_LOW_PATH_TITANIUM = "/data_lakehouse/titanium/geojson/globe/ne_110m_land_cultural.geojson"
GLOBE_JSON_OCEAN_LOW_PATH_TITANIUM = "/data_lakehouse/titanium/geojson/globe/ne_110m_ocean.geojson"
GLOBE_JSON_PATH = "/data_lakehouse/titanium/geojson/globe/"
PWR_STN_PATH_TITANIUM = "/data_lakehouse/titanium/geojson/global-power-stations/"
PWR_STN_STATS_FILEPATH = "/data_lakehouse/titanium/geojson/global-power-stations/xp1_global_power_plant_database.parquet"
PWR_STN_JSON_FILEPATH = "/data_lakehouse/titanium/geojson/global-power-stations/xp1_countries.geojson"





