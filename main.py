import sys
from time import sleep
import pandas as pd
from tqdm import tqdm

from webdriver_manager.chrome import ChromeDriverManager

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


class RedditCrawler:
    BASE_URL = "https://www.reddit.com"

    def __init__(self):
        option = webdriver.ChromeOptions()
        # option.add_argument("headless")  # 注释可以显示浏览器
        option.add_argument('no-sandbox')
        option.add_argument(
            "user-agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 "
            "Safari/537.36'")

        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)
        self.browser = webdriver.Chrome(service=service, options=option)
        self.browser.maximize_window()

        self.wait = WebDriverWait(self.browser, 5)

    def getUrls(self, keyword, number):
        self.number = number
        self.browser.get(f"https://www.reddit.com/r/{keyword}/")

        urls = []

        post_num = 0
        total_comments = 0

        while total_comments < number:
            posts = self.wait.until(
                EC.presence_of_all_elements_located((By.XPATH, "//shreddit-post"))
            )
            for post in posts[post_num:]:
                urls.append(self.BASE_URL + post.get_attribute("permalink"))
                comment_number = post.get_attribute("comment-count")
                comment_number = int(comment_number)
                total_comments += comment_number
            post_num = len(posts)
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        return urls

    def getDetails(self, urls):
        authors = []
        comments = []
        for url in tqdm(urls, desc=f"get_details", file=sys.stdout):
            self.browser.get(url)
            last_height = self.browser.execute_script("return document.body.scrollHeight")
            try:
                while True:
                    while True:
                        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        sleep(1)
                        new_height = self.browser.execute_script("return document.body.scrollHeight")
                        if new_height == last_height:
                            break
                        last_height = new_height
                    self.wait.until(
                        EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'View more comments')]"))
                    ).click()
                    last_height = new_height
            except:
                pass

            comment_tree = self.wait.until(
                EC.presence_of_element_located((By.ID, "comment-tree"))
            )

            shreddit_comments = comment_tree.find_elements(By.XPATH, "shreddit-comment")

            for shreddit in shreddit_comments:
                try:
                    author = shreddit.get_attribute("author")
                    comment_div = shreddit.find_element(By.XPATH, ".//div[@slot='comment']")
                    comment = comment_div.find_element(By.ID, "-post-rtjson-content").text
                    if comment != "":
                        authors.append(author)
                        comments.append(comment)
                except:
                    pass
            print(f"当前爬取有效数量:{len(comments)}")
            if len(comments) >= self.number:
                break


        result = pd.DataFrame()
        result['author'] = authors
        result['comment'] = comments
        result.to_csv("result.csv", index=False)
        print(f"共爬取有效评论{len(result)}条")


    def run(self, keyword, number):
        urls = self.getUrls(keyword, number)
        self.getDetails(urls)


if __name__ == '__main__':
    r = RedditCrawler()
    r.run("ChatGPT", 500)
