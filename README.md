# Airbnb scraper

## Manual:


- To obey robots.txt file type in terminal:
`scrapy crawl airbnb_crawl -s ROBOTSTXT_OBEY=True`
By default it's ignored.

- To specify ID of the crawled room type in terminal:
`scrapy crawl airbnb_crawl -a ID=your_id`

- To specify output directory and name type in terminal: `scrapy crawl airbnb_crawl -o your/output.json`<br>This will go to the root directory, make a `your` directory and create an `output.json` file.

- <u>**Note:**</u> <br>
  With image urls there are some parameters that change the size of pictures
(these are specified after (?) the question mark), such as: 
  - `aki_policy=profile_x_medium, poster or profile_large`
  - `im_w=240, 480, 720 or 1200`
