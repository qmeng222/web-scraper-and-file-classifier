# %%
import requests
from bs4 import BeautifulSoup  # for scraping
import os
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
links = soup.find_all(
    "a", href=lambda href: href and (href.endswith(".pdf") or href.endswith(".txt"))
)
# print("👀", links)


# %% set to keep track of the UNIQUE files:
unique_files = set()

for link in links:
    file_url = link.get("href")  # eg: /white_paper/eGuide_Data_Center_Refresh.pdf
    # print("------------")
    # print("1️⃣", file_url)

    if file_url.startswith("/"):
        # eg: https://www.supermicro.com/white_paper/eGuide_Data_Center_Refresh.pdf
        file_url = url + file_url
        # print("2️⃣", file_url)

    file_name = os.path.basename(file_url)  # get the base name in each path
    file_path = os.path.join(download_dir, file_name)
    # print(f"3️⃣ {file_name} @ {file_path}")

    # check duplicate files:
    if file_name not in unique_files:
        try:
            file_response = requests.get(file_url)
            with open(file_path, "wb") as file:
                file.write(file_response.content)
            unique_files.add(file_name)
            # print(f"🎉 {file_name} was downloaded!")  # confirmation msg

            # file classifier:
            category = classifier(file_url, candidate_labels)["labels"][0]
            print(f"🤴 {file_name} is classified as {category}")
            category_counts[category] += 1
            # print(f"📦 updated category_counts: {category_counts}")

        except requests.exceptions.RequestException as e:
            print(f"💥 Error downloading {file_name}: {e}")


# %% calculate the total num of files downloaded:
num_of_files = len(unique_files)
print(f"Total num of files downloaded: {num_of_files}")

# print a list of downloaded file names:
files_list = list(unique_files)
for i, f in enumerate(files_list):
    print(f"File {i+1}: {f}")


# %% categorize the documents into predefined groupings with the per-category file counts:
for k, v in category_counts.items():
    print(f"{v} files are classfied as {k}")

# %%
