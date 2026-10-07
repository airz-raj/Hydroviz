ATTRIBUTION_SENTINEL = "Contains modified Copernicus Sentinel data 2026."
ATTRIBUTION_DEM = "Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved."
ATTRIBUTION_OSM = "© OpenStreetMap contributors."
ATTRIBUTION_EMS = "European Union, Copernicus Emergency Management Service data"
ATTRIBUTION_KURO_SIWO = "Bountos, N.I., et al. (2024). Kuro Siwo: A global multi-temporal SAR dataset for rapid flood mapping. NeurIPS Datasets and Benchmarks."
ATTRIBUTION_SEN1FLOODS11 = "Bonafilia, D., et al. (2020). Sen1Floods11: A georeferenced dataset to train and test deep learning flood algorithms for Sentinel-1. CVPR Workshops."

def get_all_attributions():
    return {
        "sentinel": ATTRIBUTION_SENTINEL,
        "dem": ATTRIBUTION_DEM,
        "osm": ATTRIBUTION_OSM,
        "ems": ATTRIBUTION_EMS,
        "kuro_siwo": ATTRIBUTION_KURO_SIWO,
        "sen1floods11": ATTRIBUTION_SEN1FLOODS11
    }
