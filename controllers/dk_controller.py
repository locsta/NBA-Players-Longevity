from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
import subprocess
import os
import errno
import json
import time
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common import exceptions
from pprint import pprint
from datetime import date
from datetime import timedelta
from datetime import datetime
import requests
import re
import logging
import logging.handlers
import sys
import numpy as np

class DraftKingsController():
    """This class object aims to give control of draftkings.co.uk
    """
    def __init__(self, headless=False):
        """DraftKingsController will open a real Chrome web browser by default and give you the ability to perform methods on DraftKings
        
        Args:
            headless (bool, optional): If the headless option is set to True, the Chrome web driver will be running in the background and not open a real browser. Defaults to False.
        """
        self.options = webdriver.ChromeOptions()
        if headless:
            self.options.add_argument('--headless')
            self.options.add_argument('--disable-gpu')
        else:
            self.options.add_argument("--start-maximized")
        self.browser = webdriver.Chrome(options=self.options)
        self.actionChains = ActionChains(self.browser)
        self.dk = "https://www.draftkings.co.uk"
        self.email = None
        self.password = None
        self.logged_in = False
        self.sport = "NBA"
        self.date = date.today().strftime("%d_%m_%Y")
        self.yesterday = (date.today()- timedelta(days=1)).strftime("%d_%m_%Y")
        self.download_path = os.path.normpath(os.path.expanduser("~/Downloads"))
        self.root_path = os.path.normpath(os.path.expanduser("~/Documents/NBA/"))
        self.path_folder = os.path.join(self.root_path, "draft_kings_data")
        self.path_today = os.path.join(self.path_folder, self.date)
        self.path_yesterday = os.path.join(self.path_folder, self.yesterday)
        self.delay = 8
        self.set_login()
        self.set_logging_params()

    def make_sure_path_exists(self, path):
        """This method create a path and the corresponding folders if the path doesn't exists yet
        
        Args:
            path (str): The path you want to make sure exists
        """
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    #TODO: update scraper depending on sports (one or many)
    def set_sport(self, sport="NBA"):
        """This method set the sport or sports you want to use the controller for
        
        Args:
            sport (str, optional): The sport you want to use DraftKingsController for. Defaults to "NBA".
        """
        sports_list = ["SOC", "NBA", "GOLF", "TEN", "XLF", "NHL", "EL", "NAS", "LOL", "CBB", "NFL", "MLB", "MMA", "CFL", "CFB"]
        if sport not in sports_list:
            logging.error(f"{sport} is not available, chose one from the following: {' '.join(sports_list)}")
        else:
            self.sport = sport
    
    def set_logging_params(self, path=None, filename="dk_controller.log", root_level="DEBUG",console_level="INFO", file_level="WARNING"):
        """This method set logging parameters 
        
        Args:
            path (str, optional): The path to the folder where you want the log file to be written. Defaults to the root path of the class object.
            filename (str, optional): The name of the log file (including the extension). Defaults to "dk_controller.log".
            root_level (str, optional): The root level. Defaults to "DEBUG".
            console_level (str, optional): The console level. Defaults to "INFO".
            file_level (str, optional): The file level. Defaults to "WARNING".
        """
        
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        root_level = root_level.upper()
        console_level = console_level.upper()
        file_level = file_level.upper()
        if not path:
            path = self.root_path
        for level_name, level in {"root level":root_level, "console level":console_level, "file level":file_level}.items():
            if level not in levels:
                logging.error(f"logging setting {level} unavailable for {level_name}")
                logging.info(f"Only the following levels are available: {' '.join(levels)}")
                return
        if path:
            pass
        if filename:
            pass
        rootLogger = logging.getLogger()
        rootLogger.setLevel(getattr(logging, root_level))
        logFormatter = logging.Formatter("%(asctime)s [%(levelname)-4.4s]  %(message)s")

        fileHandler = logging.FileHandler(os.path.join(path, filename))
        fileHandler.setLevel(getattr(logging, file_level))
        fileHandler.setFormatter(logFormatter)
        rootLogger.addHandler(fileHandler)

        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(getattr(logging, console_level))
        consoleHandler.setFormatter(logFormatter)
        rootLogger.addHandler(consoleHandler)

    def set_login(self, email=None, password=None, from_json=None):
        """This method set the login paramaters (email and password), if no paramaters are given it will load the following json file ~/Documents/.mdp.json
        
        Args:
            email (str, optional): Your email. Defaults to None.
            password (str, optional): Your password. Defaults to None.
            from_json (str, optional): A json file containing a dictionnary of 2 items, with keys, email and password. Defaults to None.
        """
        if email:
            self.email = email
        if password:
            self.password = password
        if email or password:
            return
        if bool(from_json):
            data = self.load_json(from_json)
        else:
            data = self.load_json(os.path.normpath(os.path.expanduser("~/Documents/.mdp.json")))
        self.email = data["email"]
        self.password = data["password"]
    
    def get_yesterday_contests(self, path_csv=None):
        """Loads yesterday's tournaments for a csv file and returns the list of tournament ids
        
        Args:
            path_csv (bool, optional): A path to a csv file to use as yesterday's contest. Defaults to None.
        
        Returns:
            lst: List of tournaments ids from yesterday
        """
        if path_csv:
            path = os.path.join(self.path_yesterday, path_csv)
        else:
            path = os.path.join(self.path_yesterday, f"{self.yesterday}_contests.csv")
        try:
            df = self.load_csv(path)
            return list(df.contest_id)
        except:
            logging.error("No csv file for yesterdays contests, please specify a path in get_yesterday_contests() to load contests")

    def save_json(self, data, json_file_name):
        """This method save data given in paramater as a json file
        
        Args:
            data ([str, lst, dict and other types of data]): The data you want to save as json file
            json_file_name (str): The json filename (including path)
        """
        self.make_sure_path_exists(self.path_today)
        json_file_name = os.path.join(self.path_today, f"{json_file_name}.json")
        with open(json_file_name, 'w') as outfile:
            json.dump(data, outfile)

    def load_json(self, file_path):
        """This method load a json file and returns it
        
        Args:
            file_path (str): The path to the json file you want to load
        
        Returns:
            [any type]: The loaded json file
        """
        if not os.path.isfile(file_path) and not file_path.endswith(".json"):
            file_path += ".json"
        if not os.path.isfile(file_path):
            logging.error(f"The path provided doesn't lead to a json file\nPath provided:{file_path}")
            return False
        try:
            with open(file_path) as json_file:
                return json.load(json_file)
        except:
            logging.error(f"Unable to load json file, make sure {file_path} is the right path")

    def load_csv(self, file_path):
        """This method load a csv file and returns it as a pandas DataFrame
        
        Args:
            file_path (str): The path to the csv file you want to load as a pandas DataFrame
        
        Returns:
            pandas DataFrame: The csv file as a pandas DataFrame
        """
        if not os.path.isfile(file_path) and not file_path.endswith(".csv"):
            file_path += ".csv"
        if not os.path.isfile(file_path):
            logging.error(f"The path provided doesn't lead to a csv file\nPath provided:{file_path}")
            return
        try:
            df = pd.read_csv(file_path)
            return df
        except:
            logging.error(f"There was a problem loading csv file: {file_path}")

    def save_csv(self, df, file_path, params={"index" : None}):
        """This method saves a pandas DataFrame in a csv file
        
        Args:
            df (pandas DataFrame): The pandas DataFrame you want to save
            file_path (str): The path of the csv file you want to create (including filename and extension)
            params (dict, optional): The pandas "df.to_csv" paramaters. Defaults to {"index" : None}.
        """
        if not isinstance(df, pd.DataFrame):
            logging.error(df, "\nThe file printed above need to be a DataFrame in order to be used by the method save_csv()")
            return
        if not file_path.endswith(".csv"):
            file_path += ".csv"
        parent = os.path.abspath(os.path.join(file_path, os.pardir))
        self.make_sure_path_exists(parent)
        if params:
            df.to_csv(file_path, **params)
        else:
            df.to_csv(file_path)

    def run_bash(self, command):
        """This method runs simple bash command from a string (doesn't allow substring, ex: echo 'this is an example' >> test.txt WONT WORK) 
        
        Args:
            command (str): The string corresponding to the command you want to run
        """
        if type(command) == str:
            command = command.split()
            try:
                process = subprocess.Popen(command, stdout=subprocess.PIPE)
                output = process.communicate()[0]
            except:
                logging.error(f"Unable to run bash command {command}")
    
    def close_popup(self):
        """This method close pop-ups
        """
        try:
            self.browser.find_element_by_id("fancybox-close").click()
        except:
            pass
        try:
            self.browser.find_element_by_class_name("close-circle").click()
        except:
            pass
    
    def set_driver_options(self, options): #TODO: fix
        """This method allow you to set options to the selenium browser
        
        Args:
            options (lst): The options you want to set for the web driver
        """
        if type(options) == list:
            for option in options:
                self.options.add_argument(option)
        else:
            self.options.add_argument(option)

    def login(self, link=None):
        """This method will login into draftkings.co.uk
        
        Args:
            link (str, optional): If a link is provided it will go to the link and login to the page from that specific link. Defaults to None.
        """
        # If already logged-in do nothing
        if self.logged_in:
            return
        if link:
            self.browser.get(link)
            login_button = self.browser.find_elements_by_class_name("log-in-sign-up-button")
            login_button[0].click()
        else:
            self.browser.get(self.dk)
            self.browser.find_element_by_id("top-right-sign-in").click()
        self.browser.find_element_by_name('username').send_keys(self.email)
        self.browser.find_element_by_name('password').send_keys(self.password)
        logbtn = self.browser.find_elements_by_class_name("_dk-ui_dk-btn")
        logbtn[-1].click() #last login button
        try:
            WebDriverWait(self.browser, 5).until(EC.presence_of_element_located((By.XPATH, '//a[contains(@href,"secure.draftkings.co.uk/app/deposit")]')))
        except:
            logging.critical("Could not verify if logged-in or not")
        self.logged_in = True
        logging.info("Logged in on draftkings.co.uk")

    def logout(self):
        """This method will logout the browser from draftkings.co.uk
        """
        self.browser.get(f"{self.dk}/account/logout")
        self.logged_in = False
    
    def get_salaries(self, contest_ids_param=False):
        """This method will download the salaries for each contest_ids fed in the contest_ids parameter
        
        Args:
            contest_ids ([str, list, path, pd.DataFrame]): contest_ids can be a single contest id, a list of ids, a pandas DataFrame coming from get_contests or a path to a csv file coming from get_constests
        """

        #TODO: check the existing salaries scraped and change the salary id thing in order to set the id of the tournament (more reliable)
        if not contest_ids_param:
            if os.path.isfile(os.path.join(self.path_today, f"{self.date}_tournaments.csv")):
                df_path = os.path.join(self.path_today, f"{self.date}_tournaments.csv")
                df = pd.read_csv(df_path)
                contest_ids = list(set(df.salary_id.astype(int)))
        elif type(contest_ids_param) == list:
            contest_ids = contest_ids_param
        elif type(contest_ids_param) == str:
            contest_ids = [contest_ids_param]
        else:
            logging.error(f"Contests ids are of type {type(contest_ids_param)} but are supposed to be in list or str format")
            return

        #TODO: if go lobby skip page <span>Go to Lobby</span>
        #TODO: no need for enumerate (delete it)
        for i, contest_id in enumerate(contest_ids):
            if type(contest_ids_param) == str:
                to = os.path.join(self.download_path, f"salaries_for_contest_{contest_ids_param}.csv")
            else:
                salaries_path = os.path.join(self.path_today, "salaries")
                to = os.path.join(salaries_path, f"salary_{contest_id}.csv")
                self.make_sure_path_exists(salaries_path)
            link = f"{self.dk}/draft/contest/{contest_id}"
            self.browser.get(link)
            path_not_scraped = os.path.join(os.path.join(salaries_path, f'{contest_id}_couldnt_be_downloaded'))
            try:
                WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.CLASS_NAME, 'ContestInformation_contest-name')))
                err_started = len(self.browser.find_elements_by_class_name("ContestStartedView_title"))
                err_resa = len(self.browser.find_elements_by_class_name("ReservationView_title"))
                if err_started:
                    logging.warning(f"Contest {contest_id} has already started, therefore salaries are not accessible")
                    self.run_bash(f"touch {os.path.join(salaries_path, f'{contest_id}_already_started')}")
                    continue
                if err_resa:
                    logging.warning(f"Contest {contest_id} is reservation only mode, therefore salaries are not accessible")
                    self.run_bash(f"touch {os.path.join(salaries_path, f'{contest_id}_reservation_only')}")
                    continue
                # self.browser.find_element_by_class_name("close-circle").click()
                try:
                    self.close_popup()
                    csvbtn = self.browser.find_elements_by_class_name("Link_link")
                    # Check if a DKsalaries.csv is already in the Downloads folder and delete it if it is
                    dk_salary_path = os.path.join(self.download_path, "DKSalaries.csv")
                    if os.path.isfile(dk_salary_path):
                        self.run_bash(f"rm {dk_salary_path}")
                        logging.info("Removed DKSalaries.csv that was hanging in the Downloads folder")
                    csvbtn[-1].click()
                except:
                    self.close_popup()
                    logging.warning(f"Contest {contest_id} has already started, therefore salaries are not accessible")
                    self.run_bash(f"touch {path_not_scraped}")
                    pass
            except TimeoutException:
                logging.warning(f"Trying to get salaries for contest {contest_id} took too much time!")
                try:
                    self.close_popup()
                    WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.CLASS_NAME, 'Link_link')))
                    try:
                        csvbtn = self.browser.find_elements_by_class_name("Link_link")
                        csvbtn[-1].click()
                    except:
                        with open(os.path.join(salaries_path, f"{contest_id}_salary_html"), "w") as f:
                            f.write(self.browser.get_attribute('innerHTML'))
                            logging.error(f"Couldnt get data from the webpage, html webpage for salary id {contest_id} was saved in {salaries_path}")
                        continue
                except TimeoutException:
                    self.run_bash(f"touch {path_not_scraped}")
                    logging.error(f"Salaries for {contest_id} are not accessible!")
                    continue
                pass
            
            csv_path = os.path.join(self.download_path, "DKSalaries.csv")
            time.sleep(2)
            self.run_bash(f"mv {csv_path} {to}")
        self.clean_salaries_folder()

    def get_contests(self):
        """This method will scrape the lobby of DraftKings and save the data in a csv file
        """
        self.login()
        try:
            WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.XPATH, '//a[contains(@href,"NBA")]')))
            NBA = self.browser.find_element_by_xpath('//a[contains(@href,"NBA")]').click()
        except TimeoutException:
            logging.info("Loading Draft Kings lobby took a long time!")
            try:
                WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.XPATH, '//a[contains(@href,"NBA")]')))
                NBA = self.browser.find_element_by_xpath('//a[contains(@href,"NBA")]').click()
            except TimeoutException:
                logging.error("Loading Draft Kings lobby failed!")
        time.sleep(3)
        try:
            sort_entries = WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.XPATH, '//div[contains(@id, "slickgrid") and contains(@id, "entries")]')))
            # sort_entries = self.browser.find_element_by_xpath('//div[contains(@id, "slickgrid") and contains(@id, "entries")]') #TODO: check if this work
            sort_entries.click()
            time.sleep(1)
            sort_entries.click()
        except TimeoutException:
            logging.error("Loading table header with entries took too much time!")

        retry_nb = 2
        rows_to_jump = 5
        rows_pixel_size = 40
        contest_links = []
        table_height = self.browser.execute_script(f'return document.getElementsByClassName("slick-viewport")[0].scrollHeight')
        number_of_rows = round(table_height / rows_pixel_size)
        blocks_to_scrape = round(number_of_rows / rows_to_jump)
        tournaments = []
        ids_to_avoid = []

        # Get already scraped ids if csv file exists
        if os.path.isfile(f"{os.path.join(self.path_today, f'{self.date}_contests.csv')}"):
            logging.info("Importing contests already scraped from the lobby")
            contests_loaded = self.load_csv(f"{os.path.join(self.path_today, f'{self.date}_contests.csv')}")
            ids_to_avoid = list(contests_loaded.contest_id)
        for retry in range(retry_nb):
            for group in range(1, blocks_to_scrape):
                table = self.browser.find_element_by_class_name("grid-canvas").get_attribute('innerHTML')
                tournaments_data = re.findall('data-tracking(.{0,100})"', table)
                for i in range(len(tournaments_data)):
                    if "NBA" in tournaments_data[i]:
                        style_html_size = 250
                        name = tournaments_data[i][2:].split("title=\"")[1]
                        name = name.split('" href')[0]
                        if len(name) > 45:
                            style_html_size = 250 + len(name) - 45
                        contest_id = tournaments_data[i+1].split("ContestPop(")[1][:8]
                        select_style = re.findall(f'{contest_id}'+'(.{0,' + f'{style_html_size}' + '})', table)
                        print(name, contest_id)
                        select_style = select_style[0].split('grid-text">')[1]
                        style = select_style.split("</span>")[0]
                        if style.startswith("In-Game"):
                            style = "In-Game Showdown"
                        if style.startswith("Showdown"):
                            style = "Showdown Captain Mode"
                        if contest_id not in ids_to_avoid:
                            tournaments.append({"contest_id":contest_id, "tournament":name, "style":style})
                next_group_location = group * rows_pixel_size * rows_to_jump
                self.browser.execute_script(f'document.getElementsByClassName("slick-viewport")[0].scroll(0,{next_group_location});')
            
            # Fast checking a second time
            rows_to_jump += 2
            time.sleep(1)

        # Create contests DataFrame
        contests_df = pd.DataFrame(tournaments)
        contests_df.drop_duplicates(keep="first",inplace=True)
        self.save_csv(contests_df, f"{os.path.join(self.path_today, f'{self.date}_contests.csv')}")
        logging.info(f"Saved today's contests in {self.date}_contests.csv")
        
    # def get_all_contest_details(self, contest_ids=False):
    #     if not contest_ids:
    #         if os.path.isfile(os.path.join(self.path_today, f"{self.date}_contests.csv")):
    #             df_path = os.path.join(self.path_today, f"{self.date}_contests.csv")
    #             df = self.load_csv(df_path)
    #             logging.info(f"Loaded {self.date}_contests.csv to get all contest details")
    #             ids = list(df.contest_id)
    #         else:
    #             logging.info("Scraping the constest ids before getting contest details")
    #             self.get_contests()
    #             self.get_all_contest_details()
    #     else:
    #         # Load ids using contest_ids parameter
    #         ids = contest_ids
    #         for contest_id in ids:
    #             self.get_contest_details(contest_id=contest_id)

    def contest_details(self, details=True, current_entrants=False):
        """This method will collect informations from each tournament ids located in the current day contest csv file
        
        Args:
            details (bool, optional): If set to True it will collect the payouts and the header (tounament name, multi-entries etc...). Defaults to True.
            current_entrants (bool, optional): If set to True it will collect the name, badges and multi-entries of the players currently registered. Defaults to False.
        """
        self.login()
        time.sleep(3)
        if os.path.isfile(f"{os.path.join(self.path_today, f'{self.date}_contests.csv')}"):
            logging.info("Importing contests already scraped from the lobby")
            contests_loaded = self.load_csv(f"{os.path.join(self.path_today, f'{self.date}_contests.csv')}")
            contests = list(contests_loaded.contest_id)
        else:
            self.get_contests()
            logging.info("Scraping contests ids from the lobby before getting contest details for each of those ids")
            contests_loaded = self.load_csv(f"{os.path.join(self.path_today, f'{self.date}_contests.csv')}")
            contests = list(contests_loaded.contest_id)
        path_details = os.path.join(self.path_today, "tournaments_details")

        for contest_id in contests:
            try:
                tournaments = self.load_csv(os.path.join(self.path_today, f'{self.date}_tournaments.csv'))
                no_need_to_scrape = list(tournaments.contest_id)
            except:
                tournaments = pd.DataFrame()
                no_need_to_scrape = []
            if contest_id in no_need_to_scrape and not current_entrants:
                continue
            self.browser.execute_script(f"return draftKingsMain.ContestPop({contest_id} , true);")
            summary = WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.CLASS_NAME, 'panel-body'))).text
            if details:

                # Getting tournament details
                date = self.browser.find_element_by_class_name("full-date").text
                tournament = self.browser.find_element_by_css_selector("h1").text
                info_block = self.browser.find_element_by_class_name("dk-well")
                paragraphs = info_block.find_elements_by_css_selector("p")
                buyin = paragraphs[0].text.replace("$","").replace(",","")
                entrants = paragraphs[1].text
                registered = entrants.split("/")[0]
                if "K" in registered:
                    registered = int(float(registered.replace("K",""))*1000)
                else:
                    registered = int(registered)
                max_entrants = entrants.split("/")[1]
                if "K" in max_entrants:
                    max_entrants_estimated = int(float(max_entrants.replace("K",""))*1000)
                    summary_words = summary.split()
                    for word in summary_words:
                        if "player" in word:
                            try:
                                max_entrants_true_value = int(word.split("-player")[0])
                            except:
                                max_entrants_true_value = 0
                    if max_entrants_true_value > max_entrants_estimated:
                        max_entrants = max_entrants_true_value
                    else:
                        max_entrants = max_entrants_estimated
                else:
                    max_entrants = int(max_entrants)
                prize = paragraphs[2].text.replace("$","").replace(",","")
                crowns = paragraphs[3].text
                if len(paragraphs) == 4:
                    my_entries = ""
                    multi_entry = ""
                else:
                    my_entries = paragraphs[4].text
                    try:
                        multi_entry = paragraphs[5].text
                    except:
                        multi_entry = info_block.find_element_by_class_name("extra-long").text

                # Getting payouts rows
                payouts = WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.CLASS_NAME, 'prize-payouts')))
                payout_rows = payouts.find_elements_by_css_selector('tr')

                # Creating payouts dict
                payouts_dict = {}
                for row in payout_rows:
                    prize_row = ""
                    payout = ""
                    tds = row.find_elements_by_css_selector('td')
                    place = tds[0].text
                    for suffix in ["st", "th", "rd", "nd"]:
                        place = place.replace(suffix, "")
                    prize_row = tds[1].text

                    # Check if prize is a ticket
                    if "ticket" in prize_row.lower():
                        payout = prize_row
                    elif "no prizes" in prize_row.lower():
                        payout = float(0)
                    else:
                        try:
                            payout = float(prize_row.replace("$","").replace(",",""))
                        except:
                            payout = prize_row
                    payouts_dict[place] = payout

                #TODO:handle NYE problem
                date_format = '%Y %d/%m %H:%M %Z'
                scraped_datetime = datetime.now()
                year = scraped_datetime.today().year
                date = str(year) + " " + date
                date_datetime = datetime.strptime(date, date_format)
                style = contests_loaded[contests_loaded["contest_id"] == int(contest_id)]["style"].values[0]
                salary_id = np.nan
                tournament_details = [{"contest_id":contest_id ,"tournament_date":date_datetime.strftime("%Y-%m-%d %H:%M:%S"), "tournament":tournament, "style": style,"buy_in":buyin, "entrants":registered, "max_entrants":max_entrants, "prize":prize, "crowns":crowns, "my_entries":my_entries,"multi_entry":multi_entry, "scraped_date": scraped_datetime.strftime("%Y-%m-%d %H:%M:%S"), "summary": summary, "payouts": [payouts_dict], "salary_id": salary_id}]
                
                # Export tournament details to csv in a certain order
                details_df = pd.DataFrame(tournament_details)
                details_df = details_df[["contest_id", "tournament_date", "tournament", "style", "buy_in", "entrants", "max_entrants", "prize", "crowns", "my_entries","multi_entry", "scraped_date", "summary", "payouts", "salary_id"]]
                details_df = pd.concat([tournaments, details_df]).drop_duplicates(subset=['contest_id'], keep='last')
                self.save_csv(details_df, f"{os.path.join(self.path_today, f'{self.date}_tournaments.csv')}")
                logging.info(f"Downloaded tournament details for contest id {contest_id}")

            if current_entrants:

                # Getting entrants nicknames, badges and number of entries
                stop = False
                while not stop:
                    try:
                        WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.CLASS_NAME, 'entrants-more'))).click()
                    except:
                        stop = True
                        pass
                tables = self.browser.find_elements_by_css_selector('table')
                rows = tables[0].find_elements_by_css_selector('tr')
                players = []
                for cell in rows:
                    tds = cell.find_elements_by_css_selector('td')
                    for td in tds:
                        nickname = ""
                        experience = 0
                        entries = 1
                        spans = td.find_elements_by_css_selector('span')
                        for span in spans:
                            span_class = span.get_attribute('class')
                            if span_class == "entrant-username":
                                nickname = span.get_attribute('title')
                            if "experienced" in span_class:
                                experience = span_class[-1]
                            if "bdg" in span_class:
                                entries = str(span.get_attribute('title')).split()[0]
                        if len(nickname) > 1:
                            player = {"nickname": nickname, "entries": entries, "experience": experience}
                            players.append(player)

                # Export players informations to csv
                players_df = pd.DataFrame(players)
                self.save_csv(players_df, f"{os.path.join(path_details, f'{contest_id}_players.csv')}")
                logging.info(f"Saved entrants for tournament {contest_id}")

            # Close pop up
            # self.browser.find_element_by_id("fancybox-close").click()
            self.close_popup() #TODO: Check if it works like the previous line
        self.set_salary_ids()
        self.update_tournament_dataset()


    def set_salary_ids(self):
        """This method will set the salary id of each tournament using a tournament id using the same salaries, those ids will be used later to download the salaries csv files
        """

        # Deactivate warning
        pd.set_option('mode.chained_assignment', None)
        if not os.path.isfile(f"{os.path.join(self.path_today, f'{self.date}_tournaments.csv')}"):
            logging.error(f"The tournament file {os.path.join(self.path_today, f'{self.date}_tournaments.csv')} does not exist")
            return
        else:
            # Load tournaments csv
            tournaments_df = self.load_csv(f"{os.path.join(self.path_today, f'{self.date}_tournaments.csv')}")

        # Generate DataFrame containing unique combinations of style / tournament_date / contest_id and keep the row containing the lowest contest_id
        ids_to_scrape = pd.DataFrame(tournaments_df.groupby(['style', 'tournament_date'])['contest_id'].min()).reset_index()

        for row in range(len(tournaments_df)):

            # Setting the salary_id valule for each row of details_df
            tournaments_df["salary_id"].iloc[row] = ids_to_scrape["contest_id"].loc[(ids_to_scrape["style"] == tournaments_df["style"].iloc[row]) & (ids_to_scrape["tournament_date"] == tournaments_df["tournament_date"].iloc[row])].values[0]
        
        # Saving the details_df as a csv
        self.save_csv(tournaments_df, f"{os.path.join(self.path_today, f'{self.date}_tournaments.csv')}")

    def clean_salaries_folder(self):
        if not os.path.isfile(f"{os.path.join(self.path_today, f'{self.date}_tournaments.csv')}"):
            logging.error(f"The tournament file {os.path.join(self.path_today, f'{self.date}_tournaments.csv')} does not exist")
            return
        else:

            # Load tournaments csv
            tournaments_df = self.load_csv(f"{os.path.join(self.path_today, f'{self.date}_tournaments.csv')}")
            salary_id_in_df = list(set(tournaments_df.salary_id.astype(int)))
            salary_id_in_df = list(map(str, salary_id_in_df))
            salaries_downloaded = os.listdir(os.path.join(self.path_today, "salaries"))
            counter = 0

            # Checking if all the files that are in 
            for sal in salaries_downloaded:
                sal_id = sal.replace("salary_", "").replace(".csv", "")
                if str(sal_id) in salary_id_in_df or "reservation" in str(sal_id) or "already" in str(sal_id) or "downloaded" in str(sal_id):
                    counter += 1
                else:
                    pass

            # Deleting the files that are not needed
            if counter == len(salary_id_in_df):
                for sal in salaries_downloaded:
                    sal_id = sal.replace("salary_", "").replace(".csv", "")
                    if str(sal_id) in salary_id_in_df or "reservation" in str(sal_id) or "already" in str(sal_id) or "downloaded" in str(sal_id):
                        continue
                    else:
                        path_salary_file = os.path.join(os.path.join(self.path_today, "salaries"), f"{sal}")
                        self.run_bash(f"rm {path_salary_file}")
            else:
                logging.error("Some salaries are missing and need to be downloaded")

    def get_contest_results(self, contest_ids=None):
        """This method will collect the csv files containing the results from yesterday tournaments and the most picked players
        
        Args:
            contest_ids (list, optional): Instead of getting the list of tournaments ids from yesterday's tournaments list you can feed a list of tournament ids to the method. Defaults to None.
        """
        self.login()
        if not contest_ids:

            # Load csv contest file from yesterday
            ids = self.get_yesterday_contests()
            logging.info("Loaded yesterday's contests in order to get their results")
        else:
            ids = contest_ids
        
        # Make sure the page has loaded
        try:
            WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.XPATH, '//a[contains(@href,"NBA")]')))
        except TimeoutException:
            logging.error("Loading NBA button took too much time!")
            try:
                WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.XPATH, '//a[contains(@href,"NBA")]')))
            except TimeoutException:
                logging.critical("Loading lobby took too much time!")

        # Loop over contest ids and download corresponding salaries
        no_results = []
        for contest_id in ids:
            link = f"{self.dk}/contest/exportfullstandingscsv/{contest_id}"
            self.browser.get(link)
            csv_zipped_file_path = os.path.join(self.download_path, f'contest-standings-{contest_id}.zip')
            csv_non_zipped_file_path = os.path.join(self.download_path, f'contest-standings-{contest_id}.csv')
            
            # Waiting for csv file to be downloaded
            while not os.path.exists(csv_zipped_file_path) and not os.path.exists(csv_non_zipped_file_path):
                time.sleep(1)
            
            # Read csv zipped file
            if os.path.exists(csv_zipped_file_path):
                csv_downloaded_file_path = csv_zipped_file_path
            else:
                csv_downloaded_file_path = csv_non_zipped_file_path
            
            # Check if the file is fully downloaded
            if int(os.stat(csv_downloaded_file_path).st_size) == 0:
                time.sleep(1) #TODO: Check if the wait is useful or not
                self.run_bash(f"rm {csv_downloaded_file_path}")
                no_results.append(contest_id)
                logging.warning(f"No results available for {contest_id}")
                continue
            df = pd.read_csv(csv_downloaded_file_path, dtype={"Rank": pd.Int64Dtype(), "EntryId": object, "EntryName": object, "TimeRemaining": float, "Points": float, "Lineup": object, "Unnamed: 6": object, "Player":object, "Roster Position":object, "%Drafted":object, "FPTS":float})
            df_results = df[["Rank", "EntryId", "EntryName", "TimeRemaining", "Points", "Lineup"]]
            df_most_picked_players = df[["Player", "Roster Position", "%Drafted", "FPTS"]]
            df_most_picked_players = df_most_picked_players.dropna(how='all')
            df_most_picked_players["%Drafted"] = df_most_picked_players["%Drafted"].map(lambda x: str(x).replace("%", ""))
            df_most_picked_players["%Drafted"] = df_most_picked_players["%Drafted"].astype("float")
            if not contest_ids:
                path = os.path.join(self.path_yesterday, 'results')
            else:
                path = self.download_path
            self.save_csv(df_results, f"{os.path.join(path, f'{contest_id}_results.csv')}")
            logging.info(f"Saved {contest_id}_results.csv")
            self.save_csv(df_most_picked_players, f"{os.path.join(path, f'{contest_id}_most_picked_players.csv')}")
            logging.info(f"Saved {contest_id}_most_picked_players.csv")

            # Delete zip file from Downloads folder
            self.run_bash(f"rm {csv_downloaded_file_path}")
            logging.info(f"Deleted {contest_id}_most_picked_players.csv")
            try:
                # Check if DraftKings is opening a popup to check my location
                location_finder = self.browser.find_element_by_class_name("finding-location")
                if bool(location_finder):
                    self.browser.get(self.dk)
            except:
                pass
        
        # Save contests ids we got no results for
        if not contest_ids:
            self.save_json(no_results, f"{os.path.join(self.path_yesterday, f'{self.yesterday}_no_results.json')}")
            logging.info(f"Saved contests ids having no accesible results in {self.yesterday}_no_results.json")
        else:
            logging.info(f"No result for {contest_id} contest id")

    def create_lineup(self, players_dict):
        """This method will register a players as a lineup on DraftKings
        
        Args:
            players_list (dict): a dictionnary containing the position of players as key and their player_id as values
        """
        pass

    def show_contests_level(self):
        """This method will check the lobby of DraftKings and highlight the tournament rows depending on their predicted difficulties
        """
        # Go to the page
        self.login()
        try:
            WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.XPATH, '//a[contains(@href,"NBA")]')))
            NBA = self.browser.find_element_by_xpath('//a[contains(@href,"NBA")]').click()
        except TimeoutException:
            logging.info("Loading Draft Kings lobby took a long time!")
            try:
                WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.XPATH, '//a[contains(@href,"NBA")]')))
                NBA = self.browser.find_element_by_xpath('//a[contains(@href,"NBA")]').click()
            except TimeoutException:
                logging.error("Loading Draft Kings lobby failed!")
        time.sleep(3)
        try:
            WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.XPATH, '//div[contains(@id, "slickgrid") and contains(@id, "entries")]')))
            sort_entries = self.browser.find_element_by_xpath('//div[contains(@id, "slickgrid") and contains(@id, "entries")]')
            sort_entries.click()
            time.sleep(1)
            sort_entries.click()
        except TimeoutException:
            logging.error("Loading table header with entries took too much time!")

        retry_nb = 1
        rows_to_jump = 5
        rows_pixel_size = 40
        contest_links = []
        table_height = self.browser.execute_script(f'return document.getElementsByClassName("slick-viewport")[0].scrollHeight')
        number_of_rows = round(table_height / rows_pixel_size)
        blocks_to_scrape = round(number_of_rows / rows_to_jump)
        blocks_to_scrape = 5
        rows = []
        for retry in range(retry_nb):
            for group in range(1, blocks_to_scrape):
                div = self.browser.find_elements_by_class_name("ui-widget-content")
                for i in range(rows_to_jump):
                    rows.append(div[i].get_attribute('innerHTML'))
                next_group_location = group * rows_pixel_size * rows_to_jump
                self.browser.execute_script(f'document.getElementsByClassName("slick-viewport")[0].scroll(0,{next_group_location});')
        print(rows)

    def update_tournament_dataset(self):
        """This method create a single csv file using tournaments from each
        """
        path = os.path.join(self.root_path, "datasets")

        # List folders in draft_kings_data
        folders = os.listdir(self.path_folder)
        csv_list = []

        # Look for file ending by "tournaments.csv"
        for folder in folders:
            current_path = os.path.join(self.path_folder, folder)
            for f in os.listdir(current_path):
                if f.endswith("tournaments.csv"):
                    csv_list.append(os.path.join(current_path, f))
        tournaments_path = os.path.join(path, "tournaments.csv")

        # Load tournament csv file if file exists
        if not os.path.isfile(tournaments_path):
            tournaments = pd.DataFrame()
        else:
            tournaments = self.load_csv(os.path.join(path, 'tournaments.csv'))

        # Loop over everyday tournaments files
        for f in csv_list:
            current_df = self.load_csv(f)
            current_df = pd.concat([tournaments, current_df]).drop_duplicates(subset=['contest_id'], keep='last')
            self.save_csv(current_df, f"{os.path.join(path, 'tournaments.csv')}")
            logging.info(f"Updated tournaments.csv in {path}")

            # Assign freshly updated DataFrame to df tournaments to be updated
            tournaments = current_df

    def process_results(self, csvs=None):
        """This method format the results csv coming from draftkings.co.uk in a nice way
        
        Args:
            csvs (list): A list of csv results paths to process. Defaults to None
        """
        positions = ["SF", "C", "P", "SG", "PG", "G", "CPT","UTIL", "PF", "F", "T1", "T2", "T3", "T4", "T5", "T6"]
        if not csvs:
            # Load results from yesterday
            result_path = os.path.join(self.path_yesterday, "results")
            csvs_filenames = os.listdir(result_path)
            csvs = [os.path.join(result_path, csvs_filename) for  csvs_filename in csvs_filenames]
        for csv in csvs:
            
            # Data folder path
            data_folder = os.path.join(self.root_path, "datasets")

            if not csv.endswith("_results.csv"):
                if csv.endswith("_most_picked_players.csv"):
                    contest_id = csv.split("_most_picked_players.csv")[0][-8:]
                    mpdf = pd.read_csv(csv, dtype={"Player":object, "Roster Position":object, "%Drafted":float, "FPTS":float})
                    mpdf.rename(columns={"Player": "player", "Roster Position":"position", "%Drafted": "pct_drafted", "FPTS": "points"}, inplace=True)
                    folder_mp = os.path.join(data_folder, "most_picked")
                    self.make_sure_path_exists(folder_mp)
                    path_to_mp_file = os.path.join(folder_mp, f"{contest_id}.csv")
                    self.save_csv(mpdf, path_to_mp_file)
                    continue
                logging.error(f"The path provided does not lead to a csv result file")
                continue

            # Load csv results file
            df = pd.read_csv(csv, dtype={"Rank":pd.Int64Dtype(), "EntryId":object, "EntryName":object, "TimeRemaining":object, "Points":float, "Lineup":object})
            df.dropna(how='all',inplace=True)

            # Set column nickname
            df["nickname"] = df["EntryName"].map(lambda x: x.split()[0])

            # Set column entries
            df["entries"] = df["EntryName"].map(self.get_entries)

            # Set column entry nb
            df["entry_nb"] = df["EntryName"].map(self.get_entry_nb)
            lineups = list(df.Lineup)
            lineups_list = []

            # Create a list of dictionnaries containing lineups for each draft king players
            for ln in lineups:
                ln_splitted = str(ln).split()
                lineup = {}
                name = []
                position = ""
                for j, cell in enumerate(ln_splitted):
                    if cell in positions:
                        if j != 0:
                            lineup[position] = ' '.join(name)
                            name = []
                        position = cell
                    else:
                        name.append(cell)
                lineup[position] = ' '.join(name)
                position = ""
                name = []
                lineups_list.append(lineup)

            # Create a pandas dataframe with lineups as rows and positions as columns
            df1 = pd.DataFrame(lineups_list)

            # Delete empty column if it exists
            if "" in df1.columns:
                df1.drop([""], axis=1, inplace=True)

            # Delete unwanted columns
            df.drop(["Lineup", "EntryId", "EntryName", "TimeRemaining"], axis=1, inplace=True)

            # Join the two dataframes on indexes and rename the columns
            df = df.join(df1)
            df.rename(columns={"Rank": "rank", "Points":"points"}, inplace=True)

            # Create path for result file
            contest_id = csv.split("_results.csv")[0][-8:]
            folder_results = os.path.join(data_folder, "results")
            self.make_sure_path_exists(folder_results)
            path_to_result_file = os.path.join(folder_results, contest_id)

            # Export the dataframe as a csv file
            self.save_csv(df, path_to_result_file)

    def get_entries(self, entry_name):
        l = entry_name.split()
        if len(l) == 2:
            return l[1].split("/")[1].replace(")", "")
        else:
            return 1

    def get_entry_nb(self, entry_name):
        l = entry_name.split()
        if len(l) == 2:
            return l[1].split("/")[0].replace("(", "")
        else:
            return 1

    def daily(self):
        self.get_contest_results()
        self.process_results()
        self.get_contests()
        self.contest_details()
        self.set_salary_ids()
        self.get_salaries()
        self.clean_salaries_folder()
        self.update_tournament_dataset()
        logging.info("Sleep for 45 minutes before collecting entrants in order to not get block for making too many requests")
        time.sleep(45*60)
        self.contest_details(details=False, current_entrants=True)
    
    def register_contest(self, contest_id, lineup):
        """[summary]
        
        Args:
            contest_id ([type]): [description]
            lineup ([type]): [description]
        """
        #TODO: check if reservation only
        # <button class="_dk-ui_dk-btn _dk-ui_dk-btn-success "><span>Reserve Entry</span></button>
        # <div class="ReservationView_title"><span>Reservation Only</span></div>
        pass

    def replace_player_in_lineups(self, player_id_to_replace, new_player_id):
        pass

    def replace_lineup_by_lineup(self, lineup_id_to_replace, new_lineup_id):
        pass

    def replace_player_everywhere(self, player_id):
        pass

    def player_out(self, player_id):
        pass

    def invite_player(self, player_nickname, tournament_id):
        # Create a private contest 
        pass


