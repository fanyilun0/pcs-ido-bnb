import requests
import json
import re
import time
import logging
import os
from datetime import datetime
from bs4 import BeautifulSoup

def load_config():
    """Load configuration from config.json file"""
    with open('config.json', 'r') as f:
        return json.load(f)

def setup_logging(log_file):
    """Setup logging configuration"""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def fetch_bnb_balance(url, cookie):
    """Fetch the BNB balance from the provided URL"""
    session = requests.Session()
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
        'cache-control': 'no-cache',
        'cookie': cookie,
        'pragma': 'no-cache',
        'referer': 'https://bscscan.com/token/0x9c8b5ca345247396bdfac0395638ca9045c6586e?a=0xd3fbaa9baec8620dcfc9d76c71efdfce4c544e19',
        'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-bitness': '"64"',
        'sec-ch-ua-full-version': '"136.0.7103.93"',
        'sec-ch-ua-full-version-list': '"Chromium";v="136.0.7103.93", "Google Chrome";v="136.0.7103.93", "Not.A/Brand";v="99.0.0.0"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"10.0.0"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
    }
    session.headers.update(headers)

    proxies = {
        'http': 'http://127.0.0.1:7890',
        'https': 'http://127.0.0.1:7890',
    }

    try:
        response = session.get(url, proxies=proxies)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type')
        content_encoding = response.headers.get('Content-Encoding')
        # logging.info(f"Response Content-Type: {content_type}")
        # logging.info(f"Response Content-Encoding: {content_encoding} (requests auto-decompresses gzip, deflate, br)")

        try:
            with open("response_decoded_text.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            # logging.info("Decoded HTML text response saved to response_decoded_text.html")
        except Exception as e_save_text:
            logging.error(f"Error saving response.text: {e_save_text}")

        try:
            with open("response_raw_content.html", "wb") as f:
                f.write(response.content)
            # logging.info("Raw (potentially decompressed by requests) HTML content response saved to response_raw_content.html")
        except Exception as e_save_content:
            logging.error(f"Error saving response.content: {e_save_content}")

        soup = BeautifulSoup(response.text, 'html.parser')

        # Regex to capture the full number string (integer part, optional decimal part with various separators)
        # e.g., "12,345.67", "12,345 . 67", "12,345"
        # The first group (balance_candidate_str) will capture "12,345.67" or "12,345 . 67" or "12,345"
        bnb_full_pattern = r'([\d,]+(?:\s*[\.\xb7]\s*\d+)?)?\s*BNB'
        # Regex to extract only the integer part (with commas) from the above candidate string
        integer_part_pattern = r'([\d,]+)'

        balance_h4 = soup.find('h4', string=re.compile(r'BNB Balance', re.IGNORECASE))
        if balance_h4:
            balance_container_div = balance_h4.find_next_sibling('div')
            if balance_container_div:
                actual_balance_div = balance_container_div.find('div')
                if actual_balance_div:
                    balance_text_content = actual_balance_div.get_text(separator=' ', strip=True)
                    match_full_num = re.search(bnb_full_pattern, balance_text_content)
                    if match_full_num:
                        balance_candidate_str = match_full_num.group(1)
                        if balance_candidate_str: # Ensure group 1 actually captured something
                            match_integer_part = re.match(integer_part_pattern, balance_candidate_str.strip())
                            if match_integer_part:
                                balance_to_log = match_integer_part.group(1)
                                # logging.info(f"Balance (integer part) found via H4 structure: {balance_to_log}")
                                return balance_to_log
                            else:
                                logging.warning(f"Could not extract integer part from H4 candidate: '{balance_candidate_str}'")
                        else:
                            logging.warning(f"Full BNB pattern matched but group 1 was empty for H4 text: '{balance_text_content}'")
                    else:
                        logging.warning(f"Regex for full BNB number failed on H4 text: '{balance_text_content}'")
                else:
                    logging.warning("Could not find the innermost div containing the balance value after h4.")
            else:
                logging.warning("Could not find the sibling div to 'BNB Balance' h4.")

        logging.info("Specific H4 search failed or didn't yield balance, trying broader search...")
        all_text_nodes = soup.find_all(string=True)
        for text_node in all_text_nodes:
            # text_node itself is a string
            match_full_num = re.search(bnb_full_pattern, text_node)
            if match_full_num:
                balance_candidate_str = match_full_num.group(1)
                if balance_candidate_str: # Ensure group 1 captured
                    parent = text_node.parent # Use original text_node's parent for context
                    found_header_nearby = False
                    for _ in range(3): # Check up to 3 levels up
                        if parent is None: break
                        for sibling in parent.previous_siblings:
                            if isinstance(sibling, type(soup.new_tag("div"))) and "BNB Balance" in sibling.get_text(strip=True):
                                found_header_nearby = True; break
                        if found_header_nearby: break
                        if "BNB Balance" in parent.get_text(strip=True):
                            found_header_nearby = True; break
                        parent = parent.parent
                    
                    if found_header_nearby:
                        match_integer_part = re.match(integer_part_pattern, balance_candidate_str.strip())
                        if match_integer_part:
                            balance_to_log = match_integer_part.group(1)
                            logging.info(f"Balance (integer part) found via broader search with header context: {balance_to_log}")
                            return balance_to_log
                        else:
                             logging.warning(f"Could not extract integer part from broader search (header context) candidate: '{balance_candidate_str}'")
                    else:
                        # If no header context, but it's a potential match from general search
                        match_integer_part = re.match(integer_part_pattern, balance_candidate_str.strip())
                        if match_integer_part:
                            balance_to_log = match_integer_part.group(1)
                            # Check if the original text_node was just the number itself,
                            # or if it's a more complex string where our regex might be too greedy.
                            # For now, we'll log it as potential if it's not in a clear "BNB Balance" context.
                            logging.info(f"Potential BNB balance (integer part) found via general text search: {balance_to_log}. Original text node: '{text_node[:100]}...'")
                            # To be safer, we might only return this if other methods fail or add stricter context checks.
                            # For now, let's return it.
                            return balance_to_log
                        else:
                            logging.warning(f"Could not extract integer part from broader search (no header context) candidate: '{balance_candidate_str}'")
                # else: Full pattern matched but group 1 was empty - shouldn't happen if pattern is correct

        logging.error("Could not find BNB balance (integer part) on the page using multiple methods.")
        return None

    except requests.exceptions.RequestException as e:
        if 'response' in locals() and response is not None:
            try:
                with open("response_error_content.html", "wb") as f:
                    f.write(response.content)
                logging.info("HTML content (on error) saved to response_error_content.html")
            except Exception as ex_save:
                logging.error(f"Could not save HTML content on error: {ex_save}")
        logging.error(f"Error fetching data: {e} for url: {url}")
        return None

def main():
    """Main function to run the monitoring process"""
    config = load_config()
    setup_logging(config['log_file'])
    
    url = config['url']
    cookie = config['cookie']
    frequency = config['frequency_seconds']
    
    logging.info(f"Starting BNB balance monitoring for {url}")
    logging.info(f"Monitoring frequency: {frequency} seconds")
    
    while True:
        try:
            balance = fetch_bnb_balance(url)
            if balance:
                logging.info(f"Current BNB Balance: {balance} BNB")
            
            time.sleep(frequency)
            
        except KeyboardInterrupt:
            logging.info("Monitoring stopped by user")
            break
        except Exception as e:
            logging.error(f"Unexpected error in main loop: {e}")
            # It's important to continue monitoring even if one attempt fails
            time.sleep(frequency)

if __name__ == "__main__":
    main() 