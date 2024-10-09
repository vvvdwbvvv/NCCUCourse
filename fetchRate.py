from bs4 import BeautifulSoup
import requests

def fetch_rate(url: str):
  res = requests.get(url.replace("https://", "http://"))
  res.raise_for_status()
  soup = BeautifulSoup(res.content, "html.parser")
  rates = soup.find('table', {"border": "1"}).find_all('tr')
  
  return [x.find('td').get_text(strip=True) for x in rates]


if __name__ == "__main__":
  print(fetch_rate("https://newdoc.nccu.edu.tw/teaschm/1011/statisticText.jsp-y=1002&tnum=101476&snum=000346021.htm"))