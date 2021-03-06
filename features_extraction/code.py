# This file is responsible to extract code based features from the given URL

import re
from bs4 import BeautifulSoup
from common import utils

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

def compileList(soup: str, tag: str, attr: str = "") -> []:
    outputList = []
    for x in soup.findAll(tag):
        if attr!="":
            try:
                outputList.append(x[attr])
            except KeyError:
                pass
        else:
            outputList.append(x.text)
    return outputList

def isRedirectingToOtherDomain(url: str) -> int:
    try:
        domainOriginal = utils.getDomainAndSuffixFromUrl(url)
        urlAfter = utils.getFinalDestinationUrl(url)
        domainAfter = utils.getDomainAndSuffixFromUrl(urlAfter)
        if domainOriginal != domainAfter:
            return 1
        return 0
    except:
        return -1

def isUsingManyExternalResources(url: str) -> int:
    noOfExtRes = 0
    MANY = 30

    try:
        source = utils.getLoadedHtmlFromUrl(url)
        soup = BeautifulSoup(source, 'html.parser')
        domain = utils.getDomainFromUrl(url)

        imageSources = compileList(soup, 'img', 'src')
        scriptSources = compileList(soup, 'script', 'src')
        styleSources = compileList(soup, 'link', 'href')
        videoSources = compileList(soup, 'video', 'src')
        audioSources = compileList(soup, 'audio', 'src')
        iframeSources = compileList(soup, 'iframe', 'src')
        embedSources = compileList(soup, 'embded', 'src')
        objectSources = compileList(soup, 'object', 'data')
        sourceSources = compileList(soup, 'source', 'src')

        sources = imageSources + scriptSources + styleSources + videoSources + audioSources + iframeSources + embedSources + objectSources + sourceSources

        for s in sources:
            if str(s).startswith('http'):
                if utils.getDomainFromUrl(str(s)) != domain:
                    noOfExtRes += 1

        if noOfExtRes >= MANY:
            return 1
        else:
            return 0
    except:
        return -1

def isOpenningNewWindow(url: str) -> int:
    hasNewWindow = False

    try:
        source = utils.getLoadedHtmlFromUrl(url)
        soup = BeautifulSoup(source, 'html.parser')

        scriptSources = compileList(soup, 'script', 'src')
        scriptInners = compileList(soup, 'script', 'innerHtml')
        anchorTargets = compileList(soup, 'a', 'target')

        for s in scriptSources:
            try:
                script = utils.getHttpResponse(s)
                if re.match('window.open', script):
                    hasNewWindow = True
            except:
                pass

        for i in scriptInners:
            if re.match('window.open', str(i)):
                hasNewWindow = True

        for a in anchorTargets:
            if a=='_blank':
                hasNewWindow = True

        if hasNewWindow:
            return 1
        return 0
    except:
        return -1

def isBlockingRightClick(url: str) -> int:
    isBlocking = False

    try:
        source = utils.getLoadedHtmlFromUrl(url)
        soup = BeautifulSoup(source, 'html.parser')

        scriptSources = compileList(soup, 'script', 'src')
        scriptInners = compileList(soup, 'script')

        # For external scripts
        for s in scriptSources:
            try:
                # Download the script content
                script = utils.getHttpResponse(s)

                # For document.addEventListener('contextmenu', event => event.preventDefault());
                if re.search('contextmenu', script) and re.search('preventDefault', script):
                    isBlocking = True
            except:
                pass

        # For checking <script>CONTENT</script>
        for s in scriptInners:
            if re.search('contextmenu', s) and re.search('preventDefault', s):
                isBlocking = True

        # For checking body <body oncontextmenu="return false;"
        try:
            if soup.body['oncontextmenu'] and re.search('return\sfalse', soup.body['oncontextmenu']):
                isBlocking = True
        except KeyError:
            pass

        if isBlocking:
            return 1
        return 0
    except:
        return -1

def isUsingInceptionBar(url: str) -> int:
    # About Inception Bar: https://jameshfisher.com/2019/04/27/the-inception-bar-a-new-phishing-method/
    options = Options()
    options.headless = True

    try:
        driver = webdriver.Firefox(options=options)
        try:
            # Set the initial size of the window
            driver.set_window_size(500, 500)

            # Load the page
            driver.get(url)
            driver.implicitly_wait(30)

            # Get the count of div elements
            divs = driver.find_elements_by_tag_name('div')
            countBefore = len(divs)

            # Resize the window
            driver.set_window_size(500, 550)

            # Get the count of div elements again
            divs = driver.find_elements_by_tag_name('div')
            countAfter = len(divs)

            # Close browser
            driver.quit()

            if countAfter > countBefore:
                return 1
            return 0
        except:
            driver.quit()
            return -1
    except:
        return -1