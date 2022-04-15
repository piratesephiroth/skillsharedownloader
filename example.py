from downloader import Downloader


phpsessid = "PHPSESSID=0123456789abcdef0123456789abcdef"
language = "accept_language=en-US,en;q=0.5"
cookie = phpsessid + ";" + language


dl = Downloader(cookie=cookie)

# download by class URL:
dl.download_course_by_url('https://www.skillshare.com/classes/Art-Fundamentals-in-One-Hour/189505397')

# or by class ID:
# dl.download_course_by_class_id(189505397)
