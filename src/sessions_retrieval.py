from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def fetch_sessions_selenium(url):
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "session-result"))
        )
    except Exception as e:
        print("Timeout waiting for sessions to load:", e)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    sessions = []
    for li in soup.find_all("li", class_=lambda x: x and "session-result" in x):
        title_div = li.find("div", class_=lambda x: x and "catalog-result-title" in x)
        title = title_div.get_text(strip=True) if title_div else ""
        desc_div = li.find("div", class_=lambda x: x and "abstract-component" in x)
        desc = desc_div.get_text(strip=True) if desc_div else ""
        speakers_div = li.find("div", class_=lambda x: x and "speakers-component" in x)
        speakers = []
        if speakers_div:
            for s in speakers_div.find_all(["span", "strong", "br"]):
                text = s.get_text(strip=True)
                if text:
                    speakers.append(text)
            if speakers_div.string and speakers_div.string.strip():
                speakers.append(speakers_div.string.strip())
        time_div = li.find("div", class_=lambda x: x and "times-component" in x)
        time = time_div.get_text(strip=True) if time_div else ""
        sessions.append({
            "time": time,
            "title": title,
            "desc": desc,
            "speakers": speakers
        })
    driver.quit()
    print(f"Extracted {len(sessions)} sessions.")
    return sessions

if __name__ == "__main__":
    urls = [
        ("Milan", "https://aitour.microsoft.com/flow/microsoft/milan26/sessioncatalog/page/sessioncatalog"),
        ("WashingtonDC", "https://aitour.microsoft.com/flow/microsoft/washingtondc26/sessioncatalog/page/sessioncatalog"),
        ("Paris", "https://aitour.microsoft.com/flow/microsoft/paris26/sessioncatalog/page/sessioncatalog"),
    ]
    all_sessions = []
    for city, url in urls:
        sessions = fetch_sessions_selenium(url)
        for session in sessions:
            session['city'] = city
            all_sessions.append(session)
    with open("data/sessions_output.txt", "w", encoding="utf-8") as f:
        for session in all_sessions:
            f.write(f"City: {session['city']}\n")
            f.write(f"Time: {session['time']}\n")
            f.write(f"Title: {session['title']}\n")
            f.write(f"Description: {session['desc']}\n")
            f.write(f"Speakers: {', '.join(session['speakers'])}\n")
            f.write("---\n")
    print("Output written to sessions_output.txt")