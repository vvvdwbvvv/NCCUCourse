from constant import USERNAME, PASSWORD
import requests
from util import get_login_url, get_addtrack_url, get_deltrack_url, get_track_url

class User:
  _username: str
  _password: str
  _token: str
  
  def __init__(self) -> None:
    self._username = USERNAME
    self._password = PASSWORD
    res = requests.get(get_login_url(self._username, self._password))
    res = res.json()
    print(res)
    try:
      self._token = res[0]["encstu"]
    except:
      raise Exception("token error")
  
  def add_track(self, course_id: str):
    addres = requests.post(get_addtrack_url(self._token, course_id)).json()
    if(addres[0]["procid"] != "1"): raise Exception("Add fail: " + course_id)
  
  def delete_track(self, course_id: str):
    deleteres = requests.delete(get_deltrack_url(self._token, course_id)).json()
    if(deleteres[0]["procid"] != "9"): raise Exception("Delete fail: " + course_id)
    
  def get_track(self):
    courseres = requests.get(get_track_url(self._token)).json()
    return courseres