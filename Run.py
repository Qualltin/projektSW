__author__ = 'Mateusz K.'

# instalacja bs4 poprzez "pip install beautifulsoup4"
from bs4 import BeautifulSoup
import urllib.request, urllib.error
import re
import csv
import traceback

# abstrakcyjna klasa Page utworzona po to, by nie powielać metody readUrl() w innych klasach

class Page():

    def readUrl(self, www):
        try:
            return BeautifulSoup(urllib.request.urlopen(www).read())
        except:
            return False

# klasa Mainpage określa główną stronę badanej przez nas witryny
# zawiera metodę getSubpages(), która zwraca listę adresów wszystkich podstron strony głównej

class Mainpage(Page):

    url = "http://www.reviewcentre.com/products1034.html"

    def getSubpages(self):
        pdstr = self.readUrl(self.url).findAll("a", attrs={"class": "PaginationLink"})
        pdstr = int(pdstr[-2].get_text())
        num = 2
        urls = ["http://www.reviewcentre.com/products1034.html"]
        while num <= pdstr:
            urls.append("http://www.reviewcentre.com/products1034-p%s.html" % num)
            num += 1
        return urls

# klasa Listpage określa każdą z podstron strony głównej
# zawiera metodę getFirms(), która zwraca listę adresów stron tych firm,
# które mają 50 lub więcej opinii na swój temat.

class Listpage(Page):

    def __init__(self, start_urls):
        self.start_urls = start_urls

    def getSectionUrls(self, sekcja):
        pattern = r'\d+'
        l_wpisow = int(re.findall(pattern, sekcja.find("p").get_text())[0])
        if l_wpisow >= 50:
            return sekcja.find("a", href=True, text=' reviews').get('href')
        else:
            return False

    def getFirms(self):
        linki_firmy = []
        for url in self.start_urls:
            sekcje_na_stronie = self.readUrl(url).findAll("div", attrs={"class": "SecondSection"})
            for sekcja in sekcje_na_stronie:
                x = self.getSectionUrls(sekcja)
                if x != False:
                    linki_firmy.append(x)
        return linki_firmy

# klasa Firmpage określa każdą ze stron danej firmy
# zawiera metodę getSubpagesUrls(), która zwaraca listę wszystkich linków podstron z opiniami nt. danej firmy

class Firmpage(Page):

    def __init__(self, url):
        self.url = url

    def createUrls(self, first_www, www, typ, l_pdstr):
        num = 0
        linki = [first_www]
        if typ == "normalny":
            for num in range(2, l_pdstr+1):
                linki.append(re.sub(r'_\d+_', "_"+str(num)+"_", www))
        else:
            for num in range(2, l_pdstr+1):
                linki.append(re.sub(r'-p\d+', "-p"+str(num), www))
        return linki

    def getSubpagesUrls(self):
        pdstr = self.readUrl(self.url).findAll("a", attrs={"id": re.compile(r'Pagination\d+-reviews')})
        link_podstr = pdstr[0].get('href')
        l_pdstr = int(pdstr[-1].get_text())
        if re.search(r'r\d+_', link_podstr):
            return self.createUrls(self.url, link_podstr, "normalny", l_pdstr)
        elif re.search(r'-p\d+', link_podstr):
            print('wyjatek')
            return self.createUrls(self.url, link_podstr, "wyjatek", l_pdstr)

# Klasa FirmpageComments określa stronę, na której znajdują się komentarze.
# zawiera metodę readComments(), która pozwala odczytać wszystkie komentarze z danej strony
# i zapisać je do pliku CSV wykorzystując pozostałe metody klasy.

class FirmpageComments(Page):

    def __init__(self, url, last_id):
        self.url = url
        self.last_id = last_id

    def openFile(self):
        f = open('comms.csv', 'a', newline='')
        writer = csv.writer(f, delimiter="|")
        return f, writer

    def closeFile(self):
        self.openFile()[0].close()

    def getCommentsUrls(self):
        urls = []
        pdstr = self.readUrl(self.url).findAll("a", text='Read Full Review')
        for url in pdstr:
            urls.append(url.get('href'))
        return urls

    def readComments(self):
        self.openFile()
        for url in self.getCommentsUrls():
            try:
                comm = self.readUrl(url).find("span", attrs={"property": "v:description"}).text
                comm = re.compile(r"[\n\r\t]").sub("", comm)
                if re.search(r'[\xc2\xa3]', comm):
                    comm = re.compile(r'[\xc2\xa3]').sub("GBP", comm)
                #self.openFile()[1].writerow([comm])
                self.openFile()[1].writerow([self.last_id, comm])
                self.last_id += 1
            except:
                print("Niepoprawny wpis, pomijam.")
                traceback.print_exc()
        self.closeFile()
        print("Pobrano wpisy ze strony.")
        return self.last_id




######################################### RUN ###############################################
if __name__ == '__main__':
    mp = Mainpage()
    print(mp.getSubpages())
    spl = Listpage(mp.getSubpages())
    print(spl.getFirms())
    id = 1
    for el in spl.getFirms():
        try:
            pf = Firmpage(el)
            pf.getSubpagesUrls()
            for url in pf.getSubpagesUrls():
                try:
                    fpc = FirmpageComments(url, id)
                    id = fpc.readComments()
                except:
                    print("Wystąpił problem z ", url)
        except:
            print("Wystąpił problem z ", el)
