# EbayKleinanzeigenAPI

This is a small code snippet which runs a FastAPI application where you can find new items for a keyword on the Ebay Kleinanzeigen site. The API has a GET method (/search) that takes a keyword, a timestamp, and a list of IDs to ignore. It returns a list of dict items with the following keys:

 - Timestamp of item.
 - Link of item page.
 - Item ID.
 - Title of the item.
 - Price.
 - Address.

The Android application which uses this endpoint and gives push notifications for new listing will be found here: [EbayKleinanzeigenNotifier](https://github.com/fucskonorbi/EbayKleinanzeigenNotifier).