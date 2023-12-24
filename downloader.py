import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import urllib.request
from concurrent.futures import ThreadPoolExecutor
import logging
import time
import sqlite3

DOWNLOAD_DIRECTORY = r'S:\Movies Queue\Nubiles-Porn'
database_path = r"Z:\Utils\Databases\movies.db"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

SITE_NAME_MAPPING = {
    'BadTeensPunished.com': 'Bad Teens Punished',
    'BountyHunterPorn.com': 'Bounty Hunter Porn',
    'CaughtMyCoach.com': 'Caught My Coach',
    'CheatingSis.com': 'Cheating Sis',
    'CumSwappingSis.com': 'Cum Swapping Sis',
    'DaddysLilAngel.com': "Daddy's Lil Angel",
    'DetentionGirls.com': 'Detention Girls',
    'DriverXXX.com': 'Driver XXX',
    'FamilySwap.xxx': 'Family Swap',
    'LilSis.com': 'Lil Sis',
    'MomsTeachSex.com': 'Moms Teach Sex',
    'MyFamilyPies.com': 'My Family Pies',
    'Nubiles-Casting.com': 'Nubiles Casting',
    'NubilesET.com': 'Nubiles Entertainment',
    'Nubiles-Porn.com': 'Nubiles Porn',
    'NubilesUnscripted.com': 'Nubiles Unscripted',
    'PetiteBallerinasFucked.com': 'Petite Ballerinas Fucked',
    'PetiteHDPorn.com': 'Petite HD Porn',
    'PrincessCum.com': 'Princess Cum',
    'Smashed.xxx': 'Smashed XXX',
    'StepSiblingsCaught.com': 'Step Siblings Caught',
    'TeacherFucksTeens.com': 'Teacher Fucks Teens',
    'YoungerMommy.com': 'Younger Mommy'
}

def get_page_content(url, cookies):
    response = requests.get(url, cookies=cookies)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Request error: {response.status_code}")
        return None

def get_movie_name(soup):
    title_div = soup.find('div', class_='col-12 col-md-7 col-lg-5 content-pane-title')
    if title_div:
        movie_name = title_div.find('h2').get_text(strip=True)
        movie_name = re.sub(r'S\d+:E\d+', lambda match: match.group().replace(":", ""), movie_name)
        return movie_name
    else:
        return None

def get_date(soup):
    date_span = soup.find('span', class_='date')
    return date_span.get_text(strip=True) if date_span else None

def convert_date(date):
    try:
        original_date = datetime.strptime(date, '%b %d, %Y')
        return original_date.strftime('%Y-%m-%d')
    except ValueError:
        print(f"Error converting the date in the file")
        return None

def get_site(soup):
    site_span = soup.find('a', class_='site-link')
    original_site = site_span.get_text(strip=True) if site_span else None
    mapped_site = SITE_NAME_MAPPING.get(original_site, original_site)
    return mapped_site

def get_video_link(soup):
    link_tag = soup.select_one(f'a.dropdown-downloads-link:-soup-contains("1920x1080")')
    return link_tag.get('href') if link_tag else None

def get_actresses(soup, excluded_actresses):
    performers = soup.find_all('a', class_='content-pane-performer model')
    actress_list = [performer.get_text(strip=True) for performer in performers]
    filtered_actress_list = [actress for actress in actress_list if actress not in excluded_actresses]
    return " & ".join(filtered_actress_list)

def download_video(url, video_link, file_name, download_directory, site):
    if video_link and not video_link.startswith("https:"):
        video_link = "https:" + video_link
    
    site_directory = os.path.join(download_directory, site)
    os.makedirs(site_directory, exist_ok=True)
    
    full_path = os.path.join(site_directory, file_name)
    
    logging.info(f'Starting download of {url}')
    urllib.request.urlretrieve(video_link, full_path)
    size = file_size(full_path)
    save_update_database(url, size)

def save_insert_database(url, site, release_date, actresses, movie_name):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO movies (Network, Site, Movie_URL, Release_Date, Actresses, Movie_Name, Original_Size, Download_Start_Date, Download_Finished_Date, Download_Status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', ('Nubiles-Porn', site, url, release_date, actresses, movie_name, None, str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')), None, 'started'))
    conn.commit()
    conn.close()

def save_update_database(url, file_size):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE movies
        SET Original_Size = ?, Download_Finished_Date = ?, Download_Status = 'finished'
        WHERE Movie_Url = ?
    ''', (file_size, str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')), url))
    conn.commit()
    conn.close()

def file_size(file_path):
    size_in_bytes = os.path.getsize(file_path)
    size_in_gb = size_in_bytes / (1024 ** 3)
    size_in_gb = format(size_in_gb, '.2f')

    return size_in_gb

def process_url(url, current_cookies, excluded_actresses):
    max_retries = 3
    retries = 0

    while retries < max_retries:
        try:
            # Check the database for the status of the URL
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()
            time.sleep(3)
            cursor.execute('SELECT Download_Status FROM movies WHERE Movie_URL = ?', (url,))
            result = cursor.fetchone()

            if result:
                download_status = result[0]


                if download_status == 'finished':
                    print(f"URL {url} is already finished. Skipping.")
                    return
                elif download_status == 'started':
                    print(f"URL {url} is already started. Retrying.")
            else:
                print(f"URL {url} not found in the database. Proceeding with the download.")

            page_content = get_page_content(url, current_cookies)

            if page_content:
                soup = BeautifulSoup(page_content, 'html.parser')

                movie_name = get_movie_name(soup)
                date = get_date(soup)
                converted_date = convert_date(date)
                site = get_site(soup)
                video_link = get_video_link(soup)
                actresses = get_actresses(soup, excluded_actresses)

                if video_link:
                    movie_final_name = f"{site} {converted_date} - {actresses} - {movie_name}.mp4"
                    
                    # Update the database to mark the URL as 'started'
                    save_insert_database(url, site, converted_date, actresses, movie_name)

                    # Download the video
                    download_video(url, video_link, movie_final_name, DOWNLOAD_DIRECTORY, site)

                    # Update the database to mark the URL as 'finished'
                    save_update_database(url, file_size(os.path.join(DOWNLOAD_DIRECTORY, site, movie_final_name)))
                else:
                    print(f"Video with resolution 1920x1080 not found for {url}.")
                break
        except Exception as e:
            print(f"Error during download: {e}")
            retries += 1
            if retries < max_retries:
                print(f"Retrying with new cookies (attempt {retries + 1}/{max_retries})")
                new_cookies = input("Enter new cookies: ")
                current_cookies = {'Cookie': new_cookies}

    if retries == max_retries:
        print(f"Failed to download {url} after {max_retries} attempts.")

def main():
    cookies = {'Cookie': "user_viewport_setting=mobile; nativeMobilePlayer=1; thumbnailPreviews=1; _ga_XLYVZ353MD=GS1.1.1701363846.1.1.1701363849.57.0.0; _ga_636CRV8PZX=GS1.1.1701363846.1.1.1701363849.57.0.0; _ga_WY0D4W87CJ=deleted; _ga_WY0D4W87CJ=deleted; PHPSESSID=0q5thde83e5rat8n7ccjrf9lra; SRV=6e7723ab9956; rfid=c9de9d4673ff5af707ecb99a1b74781d; _gid=GA1.2.685201453.1703440111; _gat_gtag_UA_47414451_4=1; GYU0oGrnAxIK=bearer%20%22Mzk5ZTlmZDc3ZGZmMGU1Mjc0YTQ1Y2M3NmFkNWZmY2FzY056RHF1MUZ1OWVEZk9SUXhGOFBydTlXZUpKRk1iOGNYUUpYbzBFU3AyNkRyK3hhNUt1dDNqcGJsZVZ4QVgrR3JwRW1Id3B5Z2cyN0xPUGxYU1E1NlI2cjRNTTRjUWRQOERsb1FUOVFVWEpOelk0bmMvaTVWbERXTXgwbkE1Zg%3D%3D%22; _ga=GA1.1.772481259.1701317445; _ga_WY0D4W87CJ=GS1.1.1703440111.8.1.1703440122.49.0.0"}

    with open('nubiles_porn_male_exclude.txt', 'r') as file:
        excluded_actresses = [line.strip() for line in file]

    with open('links.txt', 'r') as links_file:
        links = [line.strip() for line in links_file]

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_url, link, cookies, excluded_actresses) for link in links]

        while not all(future.done() for future in futures):
            downloading_count = sum(1 for future in futures if not future.done())
            completed_count = sum(1 for future in futures if future.done())
            total_count = len(futures)
            logging.info(f'Downloading: {downloading_count} files | Completed: {completed_count} files | Total: {total_count} files')

            time.sleep(120)

        for future in futures:
            future.result()

if __name__ == "__main__":
    main()
