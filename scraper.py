# %%
import requests
from bs4 import BeautifulSoup
import lxml
import os
import re
from urllib.parse import urlparse, urljoin
from transformers import pipeline
from collections import Counter
from urllib.parse import urljoin


# %% Func:
def scrape_and_classify(base_url, file_extensions, candidate_labels, download_dir):
    to_visit = [base_url]
    visited = set()
    unique_files = set()
    classifier = pipeline(
        task="zero-shot-classification", model="facebook/bart-large-mnli"
    )
    category_counts = Counter()

    # store internal urls (with same domain):
    links_intern = set()
    # store external urls (with different domain):
    links_extern = set()

    depth = 1  # set the desired crawling depth

    while to_visit:
        url = to_visit.pop(0)
        print("🌈1", url)
        if url in visited:
            continue
        visited.add(url)

        try:
            response = requests.get(url)
            html_content = response.content.decode("utf-8", errors="ignore")

            try:
                soup = BeautifulSoup(html_content, "lxml")
            except Exception:
                print("🏪 lxml parser failed, falling back to html.parser")
                soup = BeautifulSoup(html_content, "html.parser")

            links = soup.find_all(
                "a",
                href=re.compile(
                    r".*?\.({})\b".format("|".join(file_extensions)), re.IGNORECASE
                ),
            )

            for link in links:
                file_url = link.get("href")

                if not file_url.startswith("http"):
                    file_url = urljoin(base_url, file_url)
                    print("2️⃣", file_url)

                    parsed_file_url = urlparse(file_url)
                    file_name = os.path.basename(parsed_file_url.path)
                    file_path = os.path.join(download_dir, file_name)

                    if file_name not in unique_files:
                        try:
                            file_response = requests.get(file_url)
                            with open(file_path, "wb") as file:
                                file.write(file_response.content)
                            unique_files.add(file_name)
                            print(
                                f"✅ The file {file_name} was successfully downloaded!"
                            )

                            category = classifier(file_url, candidate_labels)["labels"][
                                0
                            ]
                            print(
                                f"🎉 The file {file_name} has been classified as a '{category}'."
                            )
                            category_counts[category] += 1

                        except requests.exceptions.RequestException as e:
                            print(f"💥 Error downloading {file_name}: {e}")

                    else:
                        print("❌ Duplicate files")

            # implement the BFS crawling strategy from the provided reference code:
            current_url_domain = urlparse(base_url).netloc

            for anchor in soup.findAll("a"):
                href = anchor.attrs.get("href")
                if href != "" and href is not None:
                    href = urljoin(base_url, href)
                    href_parsed = urlparse(href)
                    href = (
                        f"{href_parsed.scheme}://{href_parsed.netloc}{href_parsed.path}"
                    )
                    final_parsed_href = urlparse(href)
                    is_valid = bool(final_parsed_href.scheme) and bool(
                        final_parsed_href.netloc
                    )

                    if is_valid:
                        if current_url_domain not in href and href not in links_extern:
                            print("Extern - {}".format(href))
                            links_extern.add(href)
                        elif current_url_domain in href and href not in links_intern:
                            print("Intern - {}".format(href))
                            links_intern.add(href)
                            if depth > 0:
                                to_visit.append(href)

        except requests.exceptions.RequestException as e:
            print(f"💥 Error scraping {url}: {e}")

    return unique_files, category_counts


# %% provide arguments:
base_url = "https://www.supermicro.com"

file_extensions = ["pdf", "txt"]

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

download_dir = "py_download"
if not os.path.exists(download_dir):
    os.makedirs(download_dir)


# %% call the func with the provided arguments:
unique_files, category_counts = scrape_and_classify(
    base_url, file_extensions, candidate_labels, download_dir
)


# %%
num_of_files = len(unique_files)
print(f"Total num of files downloaded: {num_of_files}")

files_list = list(unique_files)
for i, f in enumerate(files_list):
    print(f"File {i+1}: {f}")

for k, v in category_counts.items():
    print(f"{v} files have been classified under the '{k}' category.")

# %%
