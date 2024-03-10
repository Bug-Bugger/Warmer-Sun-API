import pandas as pd
import folium
from folium.plugins import HeatMap

def process_csv(filename):
    data = pd.read_csv(filename)
    return data

def calculate_zoom_level(data):
    lat_range = data['latitude'].max() - data['latitude'].min()
    lon_range = data['longitude'].max() - data['longitude'].min()
    max_range = max(lat_range, lon_range)

    if max_range < 0.02:
        return 15
    elif max_range < 0.05:
        return 14
    elif max_range < 0.1:
        return 13
    elif max_range < 0.2:
        return 12
    elif max_range < 0.5:
        return 11
    else:
        return 10
    

def create_heatmap(data):
    map_center = [data['latitude'].mean(), data['longitude'].mean()]
    pollution_map = folium.Map(location=map_center,tiles='CartoDB Voyager', zoom_start=calculate_zoom_level(data))

    heat_data = [[row['latitude'], row['longitude']] for index, row in data.iterrows()]

    HeatMap(heat_data, radius=20, blur=20, min_opacity=0.2).add_to(pollution_map)

    map_filename = 'pollution_heatmap.html'
    pollution_map.save(map_filename)
    return map_filename
