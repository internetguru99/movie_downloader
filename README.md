# Documentation for Porn Video Downloader

## Introduction

This documentation provides an overview of this Python script designed for downloading videos from porn websites.
At the moment, the script supports the following sites:

* Nubiles-Porn

The support extends to all sub-sites associated to the main site.

The script utilizes web scraping techniques to extract information about videos and initiates the download process. The downloaded videos are organized and tracked in a SQLite database.

## Dependencies

Before running the script, ensure that the following dependencies are installed:

* BeautifulSoup: Used for parsing HTML content.
* requests: Handles HTTP requests to the website.
* urllib: Facilitates URL-related operations.
* concurrent.futures: Enables concurrent execution of tasks.
* logging: Provides logging functionality for tracking script progress.
* sqlite3: Interacts with the SQLite database.

Install the dependencies using the following command:

~~~bash
pip install beautifulsoup4 requests urllib3 futures
~~~

## Configuration

* DOWNLOAD_DIRECTORY: Set the directory where downloaded videos will be stored.
* database_path: Specify the path to the SQLite database.


### Site Name Mapping

The SITE_NAME_MAPPING dictionary maps original site names to more readable names for better organization. Update this according to your needs.

### Input Files

* male_exclusion_list.txt: Contains a list of actresses to be excluded from the file name and the sqlite storage. In my case, male actors are excluded.
* links.txt: Contains the list of Nubiles-Porn video URLs to be processed.

### Cookies
Update the cookies dictionary in the main() function with valid cookies. These cookies are necessary for authentication and accessing restricted content on the website.
To get the cookies, follow these steps on Google Chrome:

* Open Chrome Developer Tools
* Go to the "Network" Tab
* Open any video from the main page, ensuring that you are logged-in.
* Click on Docs and click on your request. You'll see the request headers, and there are your cookies.
* Copy the cookies and paste on the script.

## Functions

#### get_page_content(url, cookies)

Fetches the HTML content of a given URL using the provided cookies.

#### get_movie_name(soup)

Extracts the name of the video from the HTML soup.
#### get_date(soup)

Retrieves the release date of the video from the HTML soup.
#### convert_date(date)

Converts the date format from '%b %d, %Y' to '%Y-%m-%d'.
#### get_site(soup)

Determines the site of the video using the HTML soup.
#### get_video_link(soup)

Retrieves the download link for the video with a resolution of 1920x1080.
#### get_actresses(soup, excluded_actresses)

Extracts the list of actresses from the HTML soup, excluding those listed in excluded_actresses.

#### download_video(url, video_link, file_name, download_directory, site)

Downloads the video using the provided URL, video link, file name, download directory, and site information.

#### save_insert_database(url, site, release_date, actresses, movie_name)

Inserts a new record into the SQLite database with the specified information.

#### save_update_database(url, file_size)

Updates the SQLite database with the file size and marks the download as finished.

#### file_size(file_path)

Calculates the size of a file in gigabytes.

#### process_url(url, current_cookies, excluded_actresses)

Processes a given URL, initiates the download, and updates the database accordingly.

#### main()

The main function that orchestrates the entire download process. Reads input files, prepares necessary data, and uses ThreadPoolExecutor for concurrent execution.

## Running the Script

Ensure that the dependencies are installed and the input files are configured.

Run the script by executing the following command:

~~~bash
python downloader.py
~~~

Monitor the script's progress through the console logs.

## Conclusion

This script provides a convenient way to download videos from the supported websites while maintaining organized records in an SQLite database.
Users can customize the configuration to suit their needs, and the script handles concurrent downloads efficiently.