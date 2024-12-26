from bs4 import BeautifulSoup
import requests

url = "https://www.youtube.com/watch?v=lcJzw0JGfeE&list=PLqM7alHXFySENpNgw27MzGxLzNJuC_Kdj"

resp = requests.get(url)

soup = BeautifulSoup(resp, 'html.parser')

for link in soup.find_all('a', id='thumbnail'):
	print(link)

