from datetime import datetime
import logging
import concurrent.futures
import commons

commons.setUpLogging()

siteList = []

def getDesiredNetwork(networkList):
    logging.info("Displaying active network subscriptions:")
    for i, network in enumerate(networkList, start=1):
        logging.info(f"{i}. {network['network']}")

    while True:
        try:
            choice = int(input("Enter the number of the desired network: "))
            if 1 <= choice <= len(networkList):
                chosenNetworkValue = networkList[choice - 1]['network']
                logging.info(f"Selected network: {chosenNetworkValue}")
                break
            else:
                logging.warning("Invalid choice. Please try again.")
        except ValueError:
            logging.warning("Invalid input. Please enter a number.")

    return chosenNetworkValue

def getNetworkInfo(networkList, desiredNetworkName):
    for networkInfo in networkList:
        if networkInfo['network'] == desiredNetworkName:
            return networkInfo
    return None

def getSceneUrl(cookies, siteId, baseUrl, movieUrlList):
    page = 0
    newSceneUrl = set()

    while True:
        url = f"{baseUrl}/video/gallery/website/{siteId}/{page}"
        soup = commons.pageParser(url, cookies)

        contentItems = soup.find_all('div', class_='content-grid-item col-12 col-sm-6 col-lg-4')

        found_new_urls = False

        for row in contentItems:
            captionHeader = row.find('div', class_='caption-header')
            titleSpan = captionHeader.find('span', class_='title')
            titleLink = titleSpan.find('a')['href']
            finalUrl = f"{baseUrl}{titleLink}"

            if finalUrl not in movieUrlList and finalUrl not in newSceneUrl:
                newSceneUrl.add(finalUrl)
                found_new_urls = True

        page += 12

        if not contentItems or not found_new_urls:
            break

    return newSceneUrl

def processSubSite(cookies, networkInfo, row):
    sceneList = commons.getSceneBySite(row['siteName'])
    movieUrlList = [scene['movieUrl'] for scene in sceneList]
    logging.info(f"Collecting information for site: {row['siteName']}")
    newSceneUrl = getSceneUrl(cookies, row['siteId'], networkInfo['baseUrl'], movieUrlList)

    subSiteLastUpdate = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    if not newSceneUrl:
        logging.info(f"No new scenes found for site: {row['siteName']}")
        updateFields = {'lastUpdate': subSiteLastUpdate}
        commons.updateDatabase('subSites', updateFields, 'siteName', row['siteName'])
    else:
        logging.info(f"Found {len(newSceneUrl)} new scenes for site: {row['siteName']}.")
        for sceneUrl in newSceneUrl:
            insertFields = {'siteName': row['siteName'], 'network': networkInfo['network'], 'movieUrl': sceneUrl, 'downloadStatus': 'waiting information'}
            commons.insertDatabase('scenes', insertFields)
        numberOfScenes = len(newSceneUrl) + (row['numberOfScenes'] if row['numberOfScenes'] is not None else 0)
        updateFields = {'lastUpdate': subSiteLastUpdate, 'numberOfScenes': numberOfScenes}
        commons.updateDatabase('subSites', updateFields, 'siteName', row['siteName'])

def updateSubsiteNumbers(cookies):
    networkList = commons.getActiveNetworks()
    if networkList:
        networkName = getDesiredNetwork(networkList)
        networkInfo = getNetworkInfo(networkList, networkName)

        if networkInfo:
            siteList = commons.getSubSites(networkName)

            for row in siteList:
                processSubSite(cookies, networkInfo, row)
        else:
            logging.error(f"The network '{networkName}' was not found")

def updateSceneInformation(cookies):
    queue = commons.getScenes('waiting information')
    subSites = commons.getSubSitesList()

    if queue:
        total_rows = len(queue)

        for index, row in enumerate(queue, start=1):
            soup = commons.pageParser(row['movieUrl'], cookies)

            if soup:
                logging.info(f"Processing from {row['siteName']} - Item {index}/{total_rows}")

                movieName = commons.getMovieName(soup)
                date = commons.getDate(soup)
                convertedDate = commons.convertDate(date)
                siteName = commons.getSite(soup, row, subSites)
                videoLink = commons.getVideoLink(soup)
                performers = commons.getPerformers(soup)

                if videoLink:
                    fileName = f"{siteName} {convertedDate} - {performers} - {movieName}.mp4"
                    updateFields = {'siteName': siteName, 'releaseDate': convertedDate, 'performers': performers, 'movieName': movieName, 'fileName': fileName, 'downloadStatus': 'queued'}
                    commons.updateDatabase('scenes', updateFields, 'ID', row['ID'])

def downloadQueue(cookies):
    queue = commons.getScenes('ready to download')

    if queue:
        total_rows = len(queue)

        for index, row in enumerate(queue, start=1):
            logging.info(f"Processing from {row['siteName']}, movie {row['movieName']} - Download {index} of {total_rows}")
            commons.prepareSceneToDownload(row, cookies)

def main():
    logging.info("Starting the main program")
    cookies = commons.getCookies()
    updateSubsiteNumbers(cookies)
    updateSceneInformation(cookies)
    downloadQueue(cookies)

if __name__ == "__main__":
    main()
