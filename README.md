# TrialCrawler
A web crawler for scraping clinical trials from clinicaltrials.gov
The program scrapes all NCTID, and then downloads clinical trial information according to the NCTID. Each trial is saved as a seperate file named by its ID in serialized format (python pickle), and then all the files will be merged into one file.
