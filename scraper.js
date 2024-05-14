const axios = require("axios");
const cheerio = require("cheerio");
const path = require("path");
const fs = require("fs");

const url = "https://www.supermicro.com";
const downloadDir = "jsDownload";

// create the download directory if it doesn't exist:
if (!fs.existsSync(downloadDir)) {
  fs.mkdirSync(downloadDir);
}

// set to keep track of the UNIQUE file names":
const uniqueFiles = new Set();

axios
  .get(url)
  .then(async (response) => {
    const $ = cheerio.load(response.data);

    // find links to PDF and text files:
    const links = $('a[href$=".pdf"], a[href$=".txt"]');

    // array to store promises for downloading files:
    const downloadPromises = [];

    // download the unique files only:
    links.each((_, link) => {
      const fileUrl = $(link).attr("href");
      const fullUrl = fileUrl.startsWith("/") ? `${url}${fileUrl}` : fileUrl;
      const filename = path.basename(fullUrl);

      if (!uniqueFiles.has(filename)) {
        uniqueFiles.add(filename);

        const filePath = path.join(downloadDir, filename);

        // push the download promise to the array:
        downloadPromises.push(
          axios
            .get(fullUrl, { responseType: "arraybuffer" })
            .then((fileResponse) => {
              fs.writeFileSync(filePath, fileResponse.data);
              console.log(`🎉 ${filename} was downloaded!`);
            })
            .catch((error) => {
              console.error(`💥 Error downloading ${fullUrl}: ${error}`);
            })
        );
      }
    });

    // wait for all download promises to complete:
    Promise.all(downloadPromises)
      .then(() => {
        // calculate the total number of files downloaded:
        const numOfFiles = uniqueFiles.size;
        console.log(`Total number of files downloaded: ${numOfFiles}`);

        // print the list of downloaded file names:
        [...uniqueFiles].forEach((f, i) =>
          console.log(`File ${i + 1}: ${path.join(downloadDir, f)}`)
        );
      })
      .catch((error) => {
        console.error(`💥 Error: ${error}`);
      });
  })
  .catch((error) => {
    console.error(`💥 Error fetching ${url}: ${error}`);
  });
