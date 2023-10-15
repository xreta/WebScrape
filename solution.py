import json
import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import concurrent.futures 


def xpath_route(web_driver, xpath):
    try:
        web_driver.find_element(By.XPATH, xpath)
    except NoSuchElementException:
        return False
    return True


def conv_json(scraped_data):
    with open('dataISbeautiful.json', 'w') as fp:
        json.dump(scraped_data, fp)

def dept_struct(dept, job):
    dept_struct_dets = {}
    job_map_list = []
    for j in job:
        job_posted_by, job_desc, job_qualification, location = None, None, None, None
        job_header = j.find('header', class_='jobad-header').find_all('a')
        for t in job_header:
            job_posted_by = t.get('title').strip()
        if job_posted_by.lower() == 'indodana':
            if j.find('div', itemprop='qualifications') is not None:
                job_qualification = j.find('div', itemprop='qualifications').text.strip()
            job_desc = j.find('div', itemprop='responsibilities').text.strip()
        elif job_posted_by.lower() == 'cermati.com':
            job_qualification = j.find('div', itemprop='responsibilities').text.strip()
            job_desc = j.find('div', class_='wysiwyg').text.strip()
        job_location = j.find_all('spl-job-location')
        for loc in job_location:
            location = loc.get('formattedaddress').strip()
        job_map = {
            "title": j.find('h1', class_='job-title').text.strip(),
            "description": job_desc,
            "posted by": job_posted_by,
            "qualification": job_qualification,
            "location": location
        }
        if dept not in dept_struct_dets.keys():
            dept_struct_dets[dept] = list()
        job_map_list.append(job_map)
    dept_struct_dets[dept].extend(job_map_list)
    return dept_struct_dets


def qualif_and_deets(dept_ele, thread_num):  
    dept_jobs_cat = {}
    for k, v in dept_ele.items():
        for url in v:
            response = requests.get(url)
            parsed_html = BeautifulSoup(response.content, 'html.parser')
            job = parsed_html.find_all('div', class_='jobad site')
            dept_map = dept_struct(k, job)
            for key, val in dept_map.items():
                if key not in dept_jobs_cat:
                    dept_jobs_cat[key] = list()
                dept_jobs_cat[key].extend(val)
    conv_json(dept_jobs_cat)


def all_the_url(e):
    dept_ele = {}
    job_list_wrapper_element = e.find_elements(By.CLASS_NAME, 'page-job-list-wrapper')
    index = 1
    total = len(job_list_wrapper_element)
    for el in job_list_wrapper_element:
        if index <= total:
            key = el.find_element(By.XPATH, f'//*[@id="career-jobs"]/div/div[6]/div/div[{index}]/p[1]'). \
                text.strip()
            value = el.find_element(By.XPATH, f'//*[@id="career-jobs"]/div/div[6]/div/div[{index}]/a'). \
                get_attribute('href')
            if key not in dept_ele.keys():
                dept_ele[key] = list()
            index += 1
            dept_ele[key].append(value)
    return dept_ele


def job_details(web_driver, e, thread_num):  
    dept_and_job_url = {}
    btn_num = 1
    while xpath_route(web_driver, f'//button[text()="{btn_num}"]'):
        try:
            btn_num += 1
            for k, v in all_the_url(e).items():
                if k not in dept_and_job_url:
                    dept_and_job_url[k] = list()
                dept_and_job_url[k].extend(v)
            web_driver.find_element(By.XPATH, f'//button[text()="{btn_num}"]').click()
            time.sleep(5)
        except NoSuchElementException:
            pass
    qualif_and_deets(dept_and_job_url, thread_num)


def jobPosts(web_driver, url):
    web_driver.get(url)
    view_all_jobs_button = WebDriverWait(web_driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="career-landing"]/div/div[4]/div/a')))
    view_all_jobs_button.click()
    WebDriverWait(web_driver, 10).until(EC.url_changes(url))
    dept_and_job_url = dict()
    try:
        elements = web_driver.find_elements(By.XPATH, '//*[@id="career-jobs"]/div/div[6]/div')
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:  
            for i, e in enumerate(elements, 1):
                executor.submit(job_details, web_driver, e, i)  
    except NoSuchElementException:
        print("Element not present")

if __name__ == '__main__':
    job_post_url = f'https://www.cermati.com/karir'
    driver = webdriver.Chrome()
    jobPosts(driver, job_post_url)
    driver.quit()