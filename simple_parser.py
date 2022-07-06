import itertools
import os

import requests
import pickle
import calendar

from datetime import datetime
from time import sleep
from multiprocessing.pool import ThreadPool
from dateutil import parser
from bs4 import BeautifulSoup

website = "stratege"

class simple_parser:

    @staticmethod
    def clean_string(string_in, keep_spaces=True):
        if keep_spaces == False:
            string_out = string_in.translate({ord(i): None for i in ' \n\t'})
        else:
            string_out = string_in.translate({ord(i): None for i in '\n\t'})
        return string_out

    @staticmethod
    def load_pickle_all(filename):
        read_results = []
        file_obj = open(filename, 'rb')
        while True:
            try:
                read_results.append(pickle.load(file_obj))
            except EOFError:
                file_obj.close()
                return read_results

    @staticmethod
    def loadall(filename):
        result = []
        file_obj = open(filename, "rb")
        while True:
            try:
                result += pickle.load(file_obj)
            except EOFError:
                file_obj.close()
                return result

    def __init__(self, game_name, pages):
        self.game_name = game_name
        self.pages = pages
        self.time_start = None

    def get_ids(self, filename):
        file = open(filename, 'wb')

        for page in range(1, self.pages + 1):
            url = 'https://psnprofiles.com/game-leaderboard/' + self.game_name + '?page=' + str(page)
            try:
                while (True):
                    page_value = requests.get(url).text
                    if 'Checking your browser before accessing' in page_value:
                        sleep(1)
                        print('AntiSpam filter is on!')
                    else:
                        break
                if (page % 2 == 0 or page == self.pages):
                    print("Parsed " + str(page) + " out of " + str(self.pages))

                soup = BeautifulSoup(page_value)
                percent = soup.find(class_="progress-bar")
                result = self.clean_string(percent.text)
                percentage_value = int(result[:-1])

                if percentage_value > 30:
                    result_arr = []
                    results = soup.find_all('a', class_="title")

                    for result in results:
                        result_arr.append(self.clean_string(result.text))

                    pickle.dump(result_arr, file)
                else:
                    break
            except:
                file_err = open(self.game_name + '_err.txt', 'a+')
                print(url + ' is unreachable!')
                file_err.writelines(url + '\n')
                file_err.close()
                file.close()
        file.close()

    def get_timestamp(self, nickname):

        result_arr = [nickname]
        url = 'https://psnprofiles.com/trophies/' + self.game_name + '/' + nickname + '?order=date'
        try:
            while (True):
                page_value = requests.get(url).text
                if "503 Service Temporarily Unavailable" in page_value:
                    sleep(1)
                else:
                    if 'Checking your browser before accessing' in page_value:
                        sleep(1)
                        print('AntiSpam filter is on!')
                    break

            soup = BeautifulSoup(page_value)
            trophytimes_raw = soup.find_all(class_="separator right")
            trophynames_raw = soup.find_all('a', class_="title")

            for i in range(0, len(trophytimes_raw)):
                if (trophytimes_raw[i].text != '\nMissing\nTimestamp\n'):
                    date_time_obj = parser.parse(trophytimes_raw[i].text)
                    trophy_timestamp = calendar.timegm(date_time_obj.utctimetuple())
                    result_arr.append((trophy_timestamp, trophynames_raw[i + 1].text))
                else:
                    result_arr.append(("0", trophynames_raw[i + 1].text))

            if len(result_arr) == 1:
                print(nickname + ' has no trophies!')
        except:
            file_err = open(self.game_name + '_err.txt', 'a+')
            print(url + ' is unreachable!')
            file_err.writelines(url + '\n')
            file_err.close()

        return result_arr

    def parse_ids(self, nicknames, game_name):
        if self.time_start is None:
            self.time_start = datetime.now()

        file_ts = open('./' + self.game_name + '/timestamps_' + game_name + '.txt', 'wb')

        thread_results = ThreadPool(10).imap_unordered(self.get_timestamp, nicknames)

        for thread_result in thread_results:
            pickle.dump(thread_result, file_ts)
            # only for LOGGING
            if (nicknames.index(thread_result[0]) + 1) % 10 == 0:
                time = datetime.now() - self.time_start
                current_id = nicknames.index(thread_result[0])
                ids_left = len(nicknames) - nicknames.index(thread_result[0])
                time_left = ids_left * time.total_seconds() / current_id
                print('[' + str(current_id + 1) + "] Time passed " + str(round(time.seconds / 60, 2)) + ", time left min ~ " + str(round(time_left / 60, 2)))

            print('[' + self.game_name + '] ' + thread_result[0] + ' ID parsed ' + str(nicknames.index(thread_result[0]) + 1) + '/' + str(len(nicknames)))

        file_ts.close()

    def parse(self):
        self.check_game_name()
        print('Loading pages from ' + self.game_name)

        if not os.path.exists(self.game_name):
            os.mkdir(self.game_name)

        file_name = './' + self.game_name + '/names_' + self.game_name + '.txt'

        if not os.path.exists(file_name) or os.path.getsize(file_name) == 0:
            self.get_ids(file_name)

        print('Loading COMPLETE')

        print('Getting timestamps from ' + self.game_name)

        if website == "stratege":
            name_load = self.load_pickle_all('./' + self.game_name + '/namepairs_' + self.game_name + '.txt')
            nicknames_list = list(itertools.chain(*name_load))
            nicknames = [a_tuple[1] for a_tuple in nicknames_list]
        else:
            nicknames = self.loadall(file_name)

        self.parse_ids(nicknames, self.game_name)

    def check_game_name(self):
        url = 'https://psnprofiles.com/game-leaderboard/' + self.game_name

        page_value = requests.get(url)
        url_game_name = page_value.url[41:]
        if url_game_name != self.game_name:
            self.game_name = url_game_name
