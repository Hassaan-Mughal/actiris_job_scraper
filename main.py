import os
import time
import pandas as pd
from selenium.webdriver.common.by import By
from utils import (
    get_normal_driver, check_element_is_clickable,
    _read_done_set,create_xpath_1, clean_job_info,
    create_xpath_2, safe_get_job_detail
)


def main():
    keyword = input("\nEnter the VDAB search keyword (e.g., python): ").strip().lower()
    output_dir = 'scraped_data'
    done_dir = 'done'
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(done_dir, exist_ok=True)
    output_file_name = os.path.join(output_dir, f"{keyword.title()}_jobs_actiris.csv")
    done_file_name = os.path.join(done_dir, f"{keyword}_done.txt")
    url = f"https://www.actiris.brussels/nl/burgers/vacatures/?keywords={keyword}&page=1"
    nxt_page_locator = (By.XPATH, "(//button[@class= 'icon-button'])[3]")
    job_links = []
    page_counter = 1
    driver = get_normal_driver()
    done_urls = _read_done_set(done_file_name)
    try:
        driver.get(url)
        while True:
            links = []  # Ensure links is always defined
            # Use explicit wait for job links
            for _ in range(5):
                found_links = driver.find_elements(By.XPATH, "//h3[@class= 'title']/parent::a")
                if found_links:
                    links = found_links
                    break
                time.sleep(1)
            job_links.extend([link.get_attribute("href") for link in links if link.get_attribute("href")])
            nxt_page_btn = check_element_is_clickable(driver, nxt_page_locator)
            if nxt_page_btn:
                page_counter += 1
                print(f"Navigating to page {page_counter}...")
                nxt_page_btn.click()
                time.sleep(1)
            else:
                print("No more pages to navigate.")
                break
        print(f"Total job links collected: {len(job_links)}")
        for link in job_links:
            if link in done_urls:
                print(f"Skipping already processed URL: {link}")
                continue
            print(f"Processing URL: {link}")
            try:
                driver.get(link)
                title = safe_get_job_detail(driver, (By.CSS_SELECTOR, "div.bloc-title > h1"), "text")
                refrence = safe_get_job_detail(driver, (By.CSS_SELECTOR, "p.state > span"), "text").split(" ")[-1].strip()
                created_at = safe_get_job_detail(driver, (By.CSS_SELECTOR, "p.state"), "text").split("|")[-1].strip()
                if "Gecreëerd op" in created_at:
                    created_at = created_at.replace("Gecreëerd op", "").strip()
                working_hours = clean_job_info(safe_get_job_detail(driver, (By.XPATH, create_xpath_1('Arbeidstijd')), "text"))
                contract_type = clean_job_info(safe_get_job_detail(driver, (By.XPATH, create_xpath_1('Type contract')), "text"))
                occupational_group = clean_job_info(safe_get_job_detail(driver, (By.XPATH, create_xpath_1('Beroepengroep')), "text"))
                experience = clean_job_info(safe_get_job_detail(driver, (By.XPATH, create_xpath_1('Aantal jaren ervaring')), "text"))
                location = clean_job_info(safe_get_job_detail(driver, (By.XPATH, create_xpath_1('Plaats')), "text"))
                driving_license = clean_job_info(safe_get_job_detail(driver, (By.XPATH, create_xpath_1('Rijbewijs')), "text"))
                job_description = safe_get_job_detail(driver, (By.XPATH, "(//div[contains(@class, 'bloc-emploi__text')])[1]"), "text")
                name_of_employer = safe_get_job_detail(driver, (By.XPATH, create_xpath_2('Naam van de werkgever', 'div')), "text")
                contact_person = safe_get_job_detail(driver, (By.XPATH, create_xpath_2('Contactpersoon', 'div')), "text")
                presentation_method = safe_get_job_detail(driver, (By.XPATH, create_xpath_2('Presentatiewijze', 'div')), "text")
                website = safe_get_job_detail(driver, (By.XPATH, create_xpath_2('Website', 'a')), "href")
                email = safe_get_job_detail(driver, (By.XPATH, create_xpath_2('E-mail', 'a')), "text")
                job_data = {
                    "Job Title": title,
                    "Reference": refrence,
                    "Created At": created_at,
                    "Working Hours": working_hours,
                    "Contract Type": contract_type,
                    "Occupational Group": occupational_group,
                    "Experience": experience,
                    "Location": location,
                    "Driving License": driving_license,
                    "Job Description": job_description,
                    "Name of Employer": name_of_employer,
                    "Contact Person": contact_person,
                    "Presentation Method": presentation_method,
                    "Website": website,
                    "Email": email,
                    "Job URL": link
                }
                print(f"Extracted data for job: {title}")
                df = pd.DataFrame([job_data])
                if not os.path.exists(output_file_name):
                    df.to_csv(output_file_name, mode='w', header=True, index=False, encoding='utf-8-sig',
                              lineterminator='\n')
                else:
                    df.to_csv(output_file_name, mode='a', header=False, index=False, encoding='utf-8-sig',
                              lineterminator='\n')
                with open(done_file_name, 'a', encoding='utf-8') as f:
                    f.write(link + '\n')
                done_urls.add(link)
                print(f"Data saved for URL: {link}")
            except Exception as e:
                print(f"Error processing job URL {link}: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if driver:
            try:
                driver.quit()
                print("Driver closed.")
            except Exception as e:
                print(f"Error closing driver: {e}")


if __name__ == "__main__":
    main()
