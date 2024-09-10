# GOES-16 Global Lightning Mapper: GRLevelX & WSV3 Placefile Generator
# Written By Derek @ FreeLightning.com
# 09/09/2024

import os
import re
import datetime
import xarray as xr
import requests
from bs4 import BeautifulSoup
from glob import glob

now = datetime.datetime.now(datetime.timezone.utc)
current_year = now.year
julian_day = now.timetuple().tm_yday
current_utc_hour = f"{now.hour:02d}"

glm_catalog = "https://thredds-test.unidata.ucar.edu/thredds/catalog/satellite/goes/east/grb/GLM/LCFA/current/catalog.html"
glm_source = f"https://noaa-goes16.s3.amazonaws.com/GLM-L2-LCFA/{current_year}/{julian_day}/{current_utc_hour}/"

def get_file_links(glm_catalog):
    response = requests.get(glm_catalog)
    soup = BeautifulSoup(response.text, 'html.parser')
    links = []
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if re.match(r'.*\.(nc)$', href):
            links.append(href)
    return links

def download_files(links, base_glm_catalog, num_files):
    for i, link in enumerate(links[:num_files]):
        file_glm_catalog = base_glm_catalog + link
        file_name = link.split('/')[-1]
        new_url = f"{glm_source}{file_name}"
        #print(f"[debug] {new_url}")
        
        try:
            response = requests.get(new_url, stream=True)
            response.raise_for_status()
            with open(file_name, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            print(f"[save] {file_name}")
        except requests.exceptions.RequestException as e:
            print(f"[fail] {file_name}")
            #pass

def process_files(num_of_files):
    glm_files = glob(f'OR_GLM-L2-LCFA_G16_*.nc')
    time_stamp = datetime.datetime.now().strftime("%I:%M:%S %p")
    flash_data = []
    
    header = "Title: GLM Lightning Flashes (" + time_stamp +  ")\nRefreshSeconds: 30\nIconFile: 1, 20, 20, 10, 10, glm_bolt_icon.png\n\n"

    for i in range(num_of_files):
        if i < len(glm_files):
            ds = xr.open_dataset(glm_files[-(i+1)])
            for lat, lon in zip(ds.flash_lat.data, ds.flash_lon.data):
                lon = float(lon)
                lat = float(lat)
                IconStatement = f"Icon: {lat}, {lon}, 000, 1, 1\n"
                flash_data.append(IconStatement)
    
    with open(f'Lightning_Flashes(GLM).txt', 'w') as f:
        f.write(header)
        for line in flash_data:
            f.write(line)
            
def delete_nc_files(directory_path):
    nc_files = glob(f'OR_GLM-L2-LCFA_G16_*.nc')
    for file in nc_files:
        try:
            os.remove(file)
        except Exception as e:
            pass

def main():

    print(f"\n[info] GLM Lightning Placefile Generator [author] Derek @ FreeLightning.com [date] 9/9/2024\n")
    base_glm_catalog = glm_catalog.rsplit('/', 1)[0] + '/'

    print(f"[get] THREDDS GLM Catalog..\n")
    file_links = get_file_links(glm_catalog)
    file_links.sort(reverse=True)
    
    print(f"[sort] Latest GLM Files..\n")
    download_files(file_links, base_glm_catalog, 11)
    
    print(f"\n[build] Lightning Placefile..\n")
    process_files(num_of_files=11)
    
    print(f"[clean] Old GLM Data..\n")
    delete_nc_files('/')
    print(f"[done] Placefile Saved As => Lightning_Flashes(GLM).txt\n")

if __name__ == "__main__":
    main()