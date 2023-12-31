from datetime import datetime
import logging
import os
import random
import re
import sqlite3
import time
import urllib.request
import requests
from bs4 import BeautifulSoup

DATABASE_PATH = r'Z:\Utils\Databases\scenes.db'
DOWNLOAD_PATH = r'Z:\Downloads\Python'
DOWNLOAD_DIRECTORY = r'Z:\Python\Downloading'
# DOWNLOAD_PATH = r'/Users/guru/Downloads'
# DATABASE_PATH = r'/Users/guru/Desktop/scenes-dev.db'

SELECT_NETWORKS = 'SELECT * FROM networks WHERE subscriptionStatus = ?'
SELECT_SUBSITES = 'SELECT * FROM subSites WHERE network = ?'
SELECT_SCENES_BY_SITE = 'SELECT * FROM scenes WHERE siteName = ?'

def setUpLogging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def sqliteConnect():
    return sqlite3.connect(DATABASE_PATH)

def getCookies():
    cookieInput = input("Enter the cookies: ")
    cookies = {'Cookie': cookieInput}
    
    return cookies

def getActiveNetworks():
    conn = sqliteConnect()

    try:
        conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')

        cursor = conn.execute(SELECT_NETWORKS, ('active',))

        columnNames = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        resultList = [dict(zip(columnNames, row)) for row in rows]

        return resultList
    except sqlite3.Error as e:
        logging.error(f"Error retrieving networks from the database: {e}")
        return None

def getSubSites(networkName):
    conn = sqliteConnect()

    try:
        conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')

        cursor = conn.execute(SELECT_SUBSITES, (networkName,))

        columnNames = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        resultList = [dict(zip(columnNames, row)) for row in rows]

        return resultList
    except sqlite3.Error as e:
        logging.error(f"Error retrieving subSites from the database: {e}")
        return None

def getSubSitesList():
    conn = sqliteConnect()

    try:
        conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')

        cursor = conn.execute('''
            SELECT * FROM subSites
        ''')

        columnNames = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        resultList = [dict(zip(columnNames, row)) for row in rows]

        return resultList
    except sqlite3.Error as e:
        logging.error(f"Error retrieving subSites from the database: {e}")
        return None

def getSceneBySite(siteName):
    conn = sqliteConnect()

    try:
        conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')

        cursor = conn.execute(SELECT_SCENES_BY_SITE, (siteName,))

        columnNames = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        resultList = [dict(zip(columnNames, row)) for row in rows]

        return resultList
    except sqlite3.Error as e:
        logging.error(f"Error retrieving scenes from the database: {e}")
        return None

def getScenes(downloadStatus):
    conn = sqliteConnect()

    try:
        conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')

        if downloadStatus == 'waiting information':
            downloadStatus = ('waiting information',)
        elif downloadStatus == 'ready to download':
            downloadStatus = ('queued', 'started')
        else:
            downloadStatus = (downloadStatus.lower(),)

        query = '''
            SELECT * FROM scenes
            WHERE downloadStatus IN ({})
        '''.format(','.join('?' for _ in downloadStatus))

        cursor = conn.execute(query, downloadStatus)

        columnNames = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        resultList = [dict(zip(columnNames, row)) for row in rows]

        return resultList
    except sqlite3.Error as e:
        logging.error(f"Error retrieving scenes from the database: {e}")
        return None

def updateDatabase(table, updateFields, whereField, whereValue):
    setClause = ', '.join(f'{key} = ?' for key in updateFields.keys())
    params = list(updateFields.values()) + [whereValue]

    sqlQuery = f'''
        UPDATE {table}
        SET {setClause}
        WHERE {whereField} = ?
    '''

    try:
        with sqliteConnect() as conn:
            logging.debug(f"Executing SQL query: {sqlQuery}")
            logging.debug(f"Parameters: {params}")

            cursor = conn.execute(sqlQuery, params)
            conn.commit()

            rowsAffected = cursor.rowcount
            logging.debug(f"Rows affected: {rowsAffected}")

    except sqlite3.Error as e:
        logging.error(f"Error updating record in the database: {e}")

def insertDatabase(table, insertFields):
    conn = sqliteConnect()

    try:
        columns = ', '.join(insertFields.keys())
        valuesPlaceholder = ', '.join('?' for _ in insertFields.values())

        sqlQuery = f'''
            INSERT INTO {table} ({columns})
            VALUES ({valuesPlaceholder})
        '''

        params = list(insertFields.values())

        logging.debug(f"Executing SQL query: {sqlQuery}")
        logging.debug(f"Parameters: {params}")

        cursor = conn.execute(sqlQuery, params)
        conn.commit()

        logging.debug(f"Record inserted successfully.")

    except sqlite3.Error as e:
        conn.rollback()
        logging.error(f"Error inserting record into the database: {e}")

def getPageContent(url, cookies):
    sleep_time = random.uniform(1, 15)
    time.sleep(sleep_time)
    response = requests.get(url, cookies=cookies)
    if response.status_code == 200:
        return response.text
    else:
        logging.error(f"Error getting page content. Returned status code: {response.status_code}")
        return None

def pageParser(url, cookies):
    pageContent = getPageContent(url, cookies)

    if pageContent:
        soup = BeautifulSoup(pageContent, 'html.parser')
        return soup

def getVideoLink(soup):
    linkTag = soup.select_one('a.dropdown-downloads-link:-soup-contains("1920x1080")')
    return linkTag.get('href') if linkTag else None

def getFileSize(filePath):
    sizeInBytes = os.path.getsize(filePath)
    sizeInGb = sizeInBytes / (1024 ** 3)
    sizeInGb = format(sizeInGb, '.2f')
    return sizeInGb

def getMovieName(soup):
    titleDiv = soup.find('div', class_='col-12 col-md-7 col-lg-5 content-pane-title')
    if titleDiv:
        movieName = titleDiv.find('h2').get_text(strip=True)
        movieName = re.sub(r'S\d+:E\d+', lambda match: match.group().replace(":", ""), movieName)
        return movieName
    else:
        return None

def getDate(soup):
    dateSpan = soup.find('span', class_='date')
    return dateSpan.get_text(strip=True) if dateSpan else None

def convertDate(date):
    try:
        originalDate = datetime.strptime(date, '%b %d, %Y')
        return originalDate.strftime('%Y-%m-%d')
    except ValueError:
        logging.error(f"Error converting the date")
        return None
    
def getSiteInfo(row, originalSite, subSites):
    for mapping in subSites:
        if mapping['mapping'] == originalSite:
            return row['siteName']
    return None

def getSite(soup, row, subSites):
    siteSpan = soup.find('a', class_='site-link')
    originalSite = siteSpan.get_text(strip=True) if siteSpan else None
    mappedSite = getSiteInfo(row, originalSite, subSites)
    return mappedSite

def getPerformers(soup):
    performers = soup.find_all('a', class_='content-pane-performer model')
    performerList = [performer.get_text(strip=True) for performer in performers]
    return " & ".join(performerList)

def createDirectory(network, siteName, fileName):    
    networkDirectory = os.path.join(DOWNLOAD_PATH, network)
    siteDirectory = os.path.join(networkDirectory, siteName)
    
    os.makedirs(siteDirectory, exist_ok=True)
    
    downloadLocation = os.path.join(siteDirectory, fileName)

    return downloadLocation

def prepareSceneToDownload(row, cookies):
    try:
        soup = pageParser(row['movieUrl'], cookies)

        if soup:

            sceneDownloadLink = getVideoLink(soup)
            # sceneDownloadLocation = createDirectory(row['network'], row['siteName'], row['fileName'])
            sceneDownloadLocation = os.path.join(DOWNLOAD_DIRECTORY, row['fileName'])

            downloadStartDate = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            updateFields = {'downloadStartDate': downloadStartDate, 'downloadStatus': 'started'}
            updateDatabase('scenes', updateFields, 'ID', row['ID'])
            downloadScene(sceneDownloadLink, sceneDownloadLocation, row)
    except Exception as e:
        logging.error(f"Error processing movie: {row['fileName']}. Reason: {str(e)}")

def downloadScene(sceneDownloadLink, sceneDownloadLocation, row):
    try:
        if sceneDownloadLink and not sceneDownloadLink.startswith("https:"):
            sceneDownloadLink = "https:" + sceneDownloadLink

        urllib.request.urlretrieve(sceneDownloadLink, sceneDownloadLocation)

        downloadFinishedDate = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        sceneSize = getFileSize(sceneDownloadLocation)
        updateFields = {'downloadFinishedDate': downloadFinishedDate, 'originalSize': sceneSize, 'downloadStatus': 'downloaded'}
        updateDatabase('scenes', updateFields, 'ID', row['ID'])
    except Exception as e:
        logging.error(f"Error processing movie: {row['movieName']}. Reason: {str(e)}")

if __name__ == "__main__":
    pass
