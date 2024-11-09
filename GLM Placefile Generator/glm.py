# GOES-16 Global Lightning Mapper - GRLevelX Placefile Generator - Version 2.0 [Placefile Edition]
# Written By Derek @ FreeLightning.com
# 11/6/2024

import os
import re
import time
import datetime
import xarray as xr
import requests
from bs4 import BeautifulSoup
from glob import glob

print(f"\n[info] GLM Placefile Generator [version] Placefile Edition v2.0 [author] Derek @ FreeLightning.com\n")

num_of_files = 12
now = datetime.datetime.now(datetime.timezone.utc)
current_year = now.year
julian_day = now.timetuple().tm_yday
current_utc_hour = f"{now.hour:02d}"

glm_catalog = f"https://thredds-test.unidata.ucar.edu/thredds/catalog/satellite/goes/east/grb/GLM/LCFA/current/catalog.html"
glm_source = f"https://noaa-goes16.s3.amazonaws.com/GLM-L2-LCFA/{current_year}/{julian_day}/{current_utc_hour}/"

print(f"[read] GLM Catalog..\n")

response = requests.get(glm_catalog)
response.raise_for_status()

soup = BeautifulSoup(response.text, 'html.parser')

file_links = soup.find_all('a', href=True)
files = []

for link in file_links:
    href = link['href']
    if re.search(r'\.(nc)$', href):
        files.append(href)
files.sort(reverse=True)

print(f"[sort] Latest Data Files..\n")

latest_files = []
for file in files[:num_of_files]:
	new_url = f"{glm_source}{file[-69:]}"
	latest_files.append(new_url)

download_dir = ""

for url in latest_files:
    filename = os.path.basename(url)
    
    try:
        
        file_response = requests.get(url)
        file_response.raise_for_status()

        
        with open(os.path.join(download_dir, filename), 'wb') as file:
            file.write(file_response.content)

        print(f"[+] {filename}")

    except requests.exceptions.RequestException as e:
        print(f"[-] {filename}")
        


print(f"\n[build] GRx Lightning Placefile..\n")

glm_files = glob(f'OR_GLM-L2-LCFA_G16_*.nc')
flash_data = []
time_stamp = datetime.datetime.now().strftime("%I:%M:%S %p")

#header = "Title: GLM Lightning Flashes (" + time_stamp +  ")\nRefreshSeconds: 30\nIconFile: 1, 20, 20, 10, 10, glm.png\n\n"

for i in range(num_of_files):
        if i < len(glm_files):
            ds = xr.open_dataset(glm_files[-(i+1)])
            for lat, lon in zip(ds.flash_lat.data, ds.flash_lon.data):
                lon = float(lon)
                lat = float(lat)
                IconStatement = f"Icon: {lat}, {lon}, 000, 1, 1\n"
                flash_data.append(IconStatement)
    
with open(f'Strikes(GLM).txt', 'w') as f:
        #f.write(header)
        for line in flash_data:
            f.write(line)

nc_files = glob(f'*.nc')
for file in nc_files:
        try:
            os.remove(file)
        except Exception as e:
            pass
            

print(f"[save] Strikes(GLM).txt\n")
