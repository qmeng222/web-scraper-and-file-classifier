# %%
import requests
from bs4 import BeautifulSoup  # for scraping
import re
import os
from urllib.parse import urlparse
from transformers import pipeline
from collections import Counter


# %%
unique_files = set()  # track UNIQUE files
category_counts = Counter()  # k: categoy, v: counts

# predefined categories:
candidate_labels = [
    "success_story",
    "case_study",
    "brochure",
    "datasheet",
    "guide",
    "brief",
    "white_paper",
    "misc",
]


# %% init a pipeline for text classification:
classifier = pipeline(task="zero-shot-classification",
                      model="facebook/bart-large-mnli")


# %% directory for saving the downloaded files:
download_dir = "py_download"
if not os.path.exists(download_dir):
    os.makedirs(download_dir)


# %% get the HTML content:
url = "https://www.supermicro.com"
response = requests.get(url)
html_content = response.content


# %% find links to the files (PDF and TXT):
soup = BeautifulSoup(html_content, "html.parser")

# IMPROVEMENT 1: By employing a regular expression with re.compile(), the find_all() function can now capture links that end with a query attribute (e.g., '?mlg=0') alongside those ending with '.pdf' or '.txt'. This ensures that URLs like 'https://www.supermicro.com/solutions/Product_Guide_RedHat-SMCI.pdf?mlg=0' are not overlooked.
links = soup.find_all("a", href=re.compile(r".*?\.(pdf|txt)", re.IGNORECASE))
# links = soup.find_all(
#     "a", href=lambda href: href and (href.endswith(".pdf") or href.endswith(".txt"))
# )
# print("👀", links)


# %% set to keep track of the UNIQUE files:
unique_files = set()

for link in links:
    file_url = link.get("href") # eg: /white_paper/eGuide_Data_Center_Refresh.pdf
    print("------------")
    # print("1️⃣", file_url)

    # construct the absolute url if it's relative:
    if not file_url.startswith("http"): # http or https
        file_url = url + file_url # eg: https://www.supermicro.com/white_paper/eGuide_Data_Center_Refresh.pdf
    print("2️⃣", file_url) # print all absolute file_urls

    # IMPROVEMENT 2: break down the url into its components & fetch the file name without the query attribute
    parsed_file_url = urlparse(file_url) # ParseResult(scheme='https', netloc='www.supermicro.com', path='/solutions/Product_Guide_RedHat-SMCI.pdf', params='', query='mlg=0', fragment='')
    file_name = os.path.basename(parsed_file_url.path)
    file_path = os.path.join(download_dir, file_name)
    # print(f"3️⃣ {file_name} @ {file_path}")

    # check duplicate files:
    if file_name not in unique_files:
        try:
            file_response = requests.get(file_url)
            with open(file_path, "wb") as file:
                file.write(file_response.content)
            unique_files.add(file_name)
            print(f"✅ The file {file_name} was successfully downloaded!")  # confirmation msg

            # file classifier:
            category = classifier(file_url, candidate_labels)["labels"][0]
            print(f"🎉 The file {file_name} has been classified as a '{category}'. ")
            category_counts[category] += 1
            # print(f"📦 updated category_counts: {category_counts}")

        except requests.exceptions.RequestException as e:
            print(f"💥 Error downloading {file_name}: {e}")

    else:
        print("❌ duplicate files")


# %% result display:
# calculate the total num of files downloaded:
num_of_files = len(unique_files)
print(f"Total num of files downloaded: {num_of_files}")

# print a list of downloaded file names:
files_list = list(unique_files)
for i, f in enumerate(files_list):
    print(f"File {i+1}: {f}")

# %% documents into predefined groupings with the per-category file counts:
for k, v in category_counts.items():
    print(f"{v} files are classfied as {k}")

# %%
