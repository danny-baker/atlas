# Welcome

**Inspired by Microsoft's [Encarta World Atlas (1997)](https://www.youtube.com/watch?v=QpbrFoXPXdU), the mission of this project is "to make important global datasets more accessible, for everyone"**

This is the open-sourced repository for my [worldatlas.org](https://worldatlas.org) concept. It's a web application that visualises thousands of datasets using Plotly Dash, built in Python. With over 2,500 curated datasets, it's taken me around two years to build as a passion project. For a more detailed background with jokes, see my [white paper](https://medium.com/towards-data-science/ive-built-a-public-world-atlas-with-2-500-datasets-to-explore-8b9ae799e345) published in Towards Data Science (medium.com).

For those who are learning and want to discover a bit more about the capabilities of Plotly [Dash](https://dash.plotly.com/introduction) and Python through this project, welcome. I've added notes in this readme file *especially* for you. For developers who may wish to contribute and enhance my shabby codebase, also, welcome. This is my first open-source project and I don't know how it works or if anyone wants to help. I've provided lots of technical detail on how the site works in the sections below. I've also provided a backlog of things I'd like to improve.

Please note this is a self-funded experiment with no seed funding. I've purchased the worldatlas.org domain out of my own savings and I personally pay for all the cloud infrastructure (virtual machines, hosting, etc). I'd really love some help to try to turn this prototype into something real; something that could become a learning center for all ages. (Pull requests are welcomed with open arms :heart_eyes:)

I hope you find something useful here.

Dan Baker :heart:

# Latest Updates (Nov 2024)
* The app now accesses all data from a cloud store at run-time (data lake in Azure blob)
* Previously all data was static and stored in the repo and I'd periodically update it and run a data pipeline on local disk to reprocess it.
* The new cloud-based data architecture is a vast improvement as it  allows massive parallel processing of files during pipeline builds, and facilitates adding new datasets much more easily. Potentially also automatic data updates.
* The drawback with the new architecture means the app needs to connect to a private Azure Blob storage account (requiring credentials). This adds complexity, and I inject these secrets during the app deployment.
* This means you can no longer easily get a version of the app running on your local machine. 
* The app now requires a .env in the project root directory which contains credentials to connect to an Azure Storage Account.
* For anyone who wants to spin the full project up on their own machine, I've snapshotted a previous branch where all the data was static and housed in the repo itself, which is called `main_static_data`. This has a data pipeline that can be run locally on disk and is a complete self-contained version of the project. It also contains the processed data so it is ready to go. It's a good option if you are just wanting to get the whole thing running on your local machine. 
* To run the version containing a full snapshot dataset in the repo itself, clone the whole repo and checkout the `main_static_data` branch. I.e. `git checkout main_static_data`. Then you can use the quickstart guides below to spin it up directly or via docker.


# Quick Start

* The following sections will outline how to spin up the app on your local machine.
* Note this is a Dash-Python app wrapped in a Flask App
* The functional code (python files) for the app itself are housed in `/flask_app/dash_app/` and the core app logic is in `/flask_app/dash_app/app.py`
* Everything else is largely supporting stuff for deployment in production, and you can disregard.
* System requirements: ~4GB memory (RAM) on your local machine.

## Run from a local machine *without* Docker 

This is the least complex way to run the app as we will spin it up directly from your local webserver on your Python installation. However it is also fidly on some operating systems like Windows (especially if you are running Annaconda). If you're on Linux or MacOs, you should be fine.

#### 1. Clone repository to your machine 

Recommend using [Github Desktop](https://desktop.github.com/) or Git command line interface (CLI) in a terminal

`git clone https://github.com/danny-baker/atlas.git` (using https)

`git clone git@github.com:danny-baker/atlas.git` (requires ssh keys)

`cd atlas` (change current working directory to the new atlas directory)

`git checkout main_static_data` (check-out the self contained branch)

#### 2. Setup virtual environment 

This varies slightly between Linux, MacOS, Windows. 

`python3 -m venv venv`

`source venv/bin/activate`

#### 3. Ensure you are in the project root folder

`cd atlas` (or similar)

#### 4. Install python packages

`pip3 install -r requirements.txt`

Note you may struggle if trying to install with Annaconda with 'conda install'. This is because the site is built and tested in linux with the 'pip3' python package installer. If you get stuck here and can't use pip3 for some reason, I recommend using the Docker approach in the next section. This means the app will be built in a linux container and will run perfectly every time.

#### 5. Spin up the app in your local web browser!

`python3 wsgi.py`

This is the app entry point. The above command should start everything happening. Give it 30 seconds to spin up, and the console should spit out a URL. Copy-paste this URL into your browser and hopefully you can play with the site locally. 

<br>



## Run from a local machine *with* Docker (build image)

If you are planning to help contribute to the project and modify code with a pull request, then this is the way to go. In the following steps I'll show you how I build the Docker image from the codebase. Special note that this *will not* work on an Apple M1 processor as the build process has some package compiling that requires the traditional 64bit intel/amd architectures. If you're running a linux or windows 64bit machine, it should work. If you're running a non-M1 MacOs, it might work. If you're running an M1 MacOs, you're totally screwed :sob:

#### 1. Install Docker to your local machine

Follow the relevant pathway for your operating system, on their website [here](https://docs.docker.com/get-docker/).

#### 2. Clone repository to your machine 

Recommend using [Github Desktop](https://desktop.github.com/) or Git command line interface (CLI) in a terminal

`git clone git@github.com:danny-baker/atlas.git`

Checkout the branch containing static data (older branch)

`git checkout main_static_data`

#### 3. Build the Docker image

From a terminal in the main repo root directory

`docker build . --tag atlas_app`

The above command will build the main Python web application into a Docker image, based on the `Dockerfile` in the repo. It will take a good 3-5 minutes to complete but you should see a bunch of outputs in the terimal window. During this build, an Ubuntu virtualised linux operating system is utilised, and all the python modules and dependencies will be installed. The main image file is around 3GB when finished. The reason it's so large is that all of my data files are currently being containerised also, so the app has direct access to them at run-time. Totally aware there are better ways to do this.

#### 4. Run the Docker image (spin up the container)

`docker run -dp 80:8050 atlas_app`

For developer contributors (on main branch):

`sudo docker run -p 80:8050 -v /home/dan/atlas/.env:/usr/src/app/.env ghcr.io/danny-baker/atlas/atlas_app:latest`

The above command can be used to spin up the current production app locally as a single container and mounts to .env file to allow connection to Azure blob

Once the image is built, you can bring it up and view it on your local machine's web browser with the above command. The default TCP port for the app is `8050` so in the snippet above, we are simply binding the container's  port (8050) to your local machine's port 80 (http web traffic) so we can view the running app via a browser.


#### 5. View running container from your web browser

Once the container is running (check in docker desktop dashboard or with `docker ps` in terminal) You should just be able to open a web browser and punch in whatever the IP and port is displayed in the terminal output from Docker. This doesn't always work. Sometimes I've found this can be buggy on Docker desktop on Windows and Mac. For example if you have another running container that is already using port 80, there will be a conflict when this container comes up and tries to bind to port 80. I've also had situations where no other containers are running except my container. It's on port 80. But I open the browser and it just doesn't work. When I switched my development environment over to true linux operating system, all these problems went away.

The reality with development I have found over 2 years on this project: if the final running app is going to be deployed on a linux operating system (I.e. Ubuntu 18.04 linux server), then *develop* it on a local machine using a linux operating system, with no compromises. MacOS is good, but not perfect. Windows subsytem for linux is ok, but even less perfect. Linux is reliable and pain free, ensuring issues you solve on your local machine, will likely also be solved on the production server. Case in point: I can't even build the docker image on my M1 Mac due to a compiling issue.

# Documentation

### What is this site?

It's an educational website (prototype) that allows you to visualise thousands of public datasets about the world. Inspired by Microsoft Encarta 1995, it's mission is to make important data more accessible, for everyone. The idea was something like a modernised replacement for the paper World Atlas, in the same way Wikipedia replaced the paper encyclopaedia.

### How it works (generally)

It's a Plotly Dash App encased in a proper Flask app, which is containerised and run on a linux webserver. It acts as a generalised Python engine for ingesting county-scale geodatasets and visualising them in a variety of ways with interactive maps & charts. The idea being: it should be fun and easy to explore a dataset that interests you. The visualisations are courtesy of Plotly Dash open-source, which provides a powerful library of interactive javascript charts which are available out-of-the box in Dash web apps. 

 <img src="https://github.com/danny-baker/atlas/blob/main/flask_app/static/img/diagram.png?raw=true" alt="alt text" width="600">

### How it works (nerd level detail)

In the following sections I'll outline the core aspects of the system in the hope you might help me improve it. Please also note this has been a solo project, so I've cut lots of corners and kept it as lean as possible with minimal 3rd party tools and systems. For example, I do not use any SQL databases. Instead I use .csv files for metadata and .parquet (pyArrow) binary files to store processed data, with massive compression and read-time advantages.

#### Flyover of what each file does (needs a bit of an update)

There are an annoying number of files in the project repository now. It didn't start off this way. Here is a quick guide to highlight the important stuff in the root directory. Notably, the repository contains more than just the code to build the Dash app, it also has code to describe the infrastructure to host it on AND it houses all the data used by the app. I am fully aware this is not best practice. It feels good to ignore best practice sometimes.

* `./github/workflows/build.yml` describes how to build the app into a container (github actions)

* `./github/workflows/deploy.yml` describes how to deploy app onto cloud infrastructure (github actions)

* `data/` contains ALL the data including raw datasets, geojson polygons, configuration files, processed data.

* `infrastructure/` contains relevant files for building cloud infrastructure and configuring containers

* `flask_app/` this directory houses the flask app, which in turn houses the dash_app

* `flask_app/dash_app/app.py` the Python Dash app code (primary file)

* `flask_app/dash_app/data_processing.py` a key python file used to process all the datasets and other helper functions

* `wsgi.py` Flask app entry point 

* `Dockerfile` describes how to construct the web app Docker image in yaml

* `docker-compose.yml` describes how to orchestrate the 4 containers when deploying in production environment

* `requirements.txt` outlines all the Python modules, version locked

Note: Update on data-lakehouse section to be inserted.

#### 0. Core Systems

The app is hosted on a single beefy virtual machine in an Azure datacenter in the UK, with no CDN, load balancing or anything fancy. The main reason for this is I need lots of memory (RAM) as each instance of the app is 1GB (due to the large main dataframe) and I want to run a few in parallel. This ruled out app services like Heroku pretty quickly as it is ram-poor in its offerings.

The deployed app is an orchestration of 4 containers on a single host:
1. The web application (Flask-Dash container)
2. NGINX container (reverse proxy that receives incoming connections, does HTTP caching and pipes to the app)
3. Certbot container (for refreshing TLS/HTTPS certificates)
4. Datadog container (for observability and logging)

So basically when someone hits the site they first hit the NGINX container with 2 workers that can handle up to 8096 simultaneous connections (with HTTP caching), they are then routed to the underlying web app container which has 1-3 Gunicorn workers running about 5 threads each. Each Gunicorn worker requires the full app memory footprint (1GB) and can serve true parallel incoming HTTP requests. Each thread can share the data of their parent g-worker, so this helps with queueing and resource optimisation. The certbot and datadog containers are just for maintenance stuff. I'm sure there are better ways to do this, but the key thing I found I needed was full hardware control of dedicated virtual machines (so I could specify my memory requirements), and this is why I've gone down this rather low-level manual path of web hosting. 

Obviously there is geographical latency based on your distance from the UK datacenter (where the host is). I'd love to fix that via CDN caching etc, but ultimately I assume I'd need to have a host in every major datacenter and route traffic to the closest node. If there are any cloud engineer guns out there: please help. 

#### 1. Data Processing

In order to build a generalised engine to ingest country-scale datasets, the key enabler is standardisation. We need to group all data for a given region in an accurate and precise way. Now you might assume (as I did) that all this would be easy. Surely, published datasets from sources like UN Data Portal, World Bank, Open-Numbers would be easy to interweave. The truth is: it's not that simple. Country and region names vary over time (borders change) and in the way they are spelt. Furthermore, ASCII character encoding (e.g. UTF-8) can vary and cause anomalies. Yes it's true that we have standardised unique region identifiers to solve that very problem, such as the [United Nations M49](https://unstats.un.org/unsd/methodology/m49/) integer based system (New Zealand = 554) or the International Organization for Standardisation ISO-A3 (New Zealand = NZL). These systems are useless if your dataset hasn't been tagged with them. So a LOT of my time was spent curating the datasets, or converting between standards, or manually checking to ensure I had all data standardised to M49 integer, which is the basis for my main dataset.

I've now personally collected around 2,600 country-scale statistical datasets (5GB of csv files). I've curated them and standardised to M49 format. After data processing they are stored as an 86MB parquet binary file (note 5GB -> 86MB compression ratio), which is decompressed into a 1GB dataframe in memory at run-time, which forms the backbone of the app.

 I also tag each dataset based on the type of data it is (continuous, quantitative, ratio etc.). For example, is the value for each country in a dataset a percentage or is it an actual number? This classification allows the graphs and charts to behave appropriately. This is not perfect because I'm not a statistician, but I've done a first pass to classify the various data types for thousands of datasets. If you are a statistician: I'd love some help auditing, correcting, and refining.

 A note on polygons. In order to colour regions in the main map, we need to be able to trace a line (polygon) around them. I've used geojson data from [Natural Earth](https://www.naturalearthdata.com/) who basically prepare alot of this stuff for free. Lots of testing and experimentation was used here, but essentially this allows us to have low and high resolution lines around regions. This is also the basis for how the 3d charts are built and coloured (Jigsaw, Globe).

All raw datasets for the app are stored in `/data/...`

All datasets are tagged with metadata via `/data/dataset_lookup.csv`

All processed datasets are collectively stored in `/data/master.parquet`

All polygons (geojson) used for colouring regions on 2d & 3d maps are stored in `/data/geojson/...`

The `/flask_app/dash_app/data_processing.py` is the primary file used for helper functions such as processing raw datasets, rebuilding the main .parquet file, cleaning polygon data etc.

#### 2. Web App

 The web app is a Plotly Dash app encased by a Flask app. It's entry point is `wsgi.py` i.e. run `python3 wsgi.py` if wanting to run it on a local webserver (with no containers). To properly build the web app as a Docker image using the `Dockerfile` in the root project folder, follow the [quick-start guide](https://github.com/danny-baker/atlas#run-from-a-local-machine-with-docker-build-image).

**Where the magic happens**

The main Python file is `/flask_app/dash_app/app.py`.

**Technical approach: performance at all costs**

I wanted absolute MAX performance in terms of being able to seamlessly switch between datasets, and bring up interactive charts to explore data in this project. This has led to a number of interesting design choices. I've used no disk storage (SQL tables) for any data and instead opted for a complete in-memory solution for the main dataset. This is basically 2,500 CSV datasets condensed into a 5GB pandas dataframe with around 12 million rows. The cleaned and processed main dataset is stored on disk in a .parquet binary `/data/master.parquet`. When the app starts up, it immediately reads the parquet file into the main pandas dataframe (this takes around 4 seconds). From then on, ALL DATA is in memory and can be queried as fast as Python can query the pandas dataframe. 

I’ll add here that I have looked at using non-pandas data structures such as [Dask](https://docs.dask.org/en/stable/dataframe.html) and [Vaex](https://vaex.io/docs/index.html) but these add a lot of complexity and have reduced features, and I don’t think they are really necessary unless the main dataset gets beyond 10GB. These should be considered down the track. For now, through strong data-typing of the dataframe columns (using categoricals for Country and Series names, and unsigned integers uint16 for the year) I’ve reduced the main dataframe size by 87%, down to about 1GB per instance of the app, and reduced query time.

If you are a skilled data engineer, I'd love some help in refining/rebuilding my technical approach to make a more robust and maintainable framework.

**Start-up**

The high-level flow of things that happen when the Dash app comes up are:
1. Read in main dataset
2. Read in configuration files (meta data, dictionaries, lookups etc)
3. Construct the overhead navigation menu based on the meta data (`/data/dataset_lookup.csv`). Note this happens at run-time so we can easily add more datasets or change where they are nested in the navigation by changing the csv.
4. Construct the Dash layout (render main map, overhead navigation, footer, buttons etc)
5. Initialise the main callback `callback_main`, which acts like a catch-all for user input

**Core Logic**

There is quite a bit of complexity trying to get everything to initialise, however at base the app is quite simple. There is a central callback loop that is watching for any user input such as clicking on the main map, or a button or the navigation menu item. Once an input is detected other actions are called, such as other call backs or chart/model renders, and then everything cascades back to the main callback.

That's really it. Is it clean? No. Is it easy to maintain and read? No. Does it work? Yes.

**No Framework used = fundamentally flawed**

It may be that the Dash app has been scaled out to be a little too large to be easily maintained. After all, I'm not really following a framework approach, I've just tried to use basic logic and half decent naming conventions. I'm not a front-end developer (as you will see from my horrible in-line css) so I really just don't know if there is a cleaner way to build out the Dash app while keeping complexity as low as possible. The reality is I'm relying purely on Python for everything (including user input detection like navigation menu and button clicks). I think it's now apparent to me the limitations of wrapping javascript and HTML in a Python API (i.e. Dash). I'm trying to do normal website things and it just seems over complicated now. 

I think the way forward would be to go pure javascript react web app. This would allow the most interactive experience. I just can't code javascript at all, so I opted for the best solution I could find: Plotly Dash.

#### 3. Infrastructure & Deployment

Basically this is a GitOps deployment pipeline. I'm using github actions for a full end-end build from a code-push to deployed infrastructure. All infrastructure is running on Microsoft Azure, which is defined as infrastructure-as-code IaC in the `infrastructure/` directory of the repo. I have not split this out into a separate repository because it's just been easier to keep it all in one.

The virtual machine template is defined in `/infrastructure/azure-deploy/create-vm.bicep` which allows flexibility to build any machine I want using the domain specific language Bicep, released in Aug 2020. I've not bothered with using cloud agnostic tooling like Terraform as it is more complexity than I think the project needs.

As you will see from the code base, there are zero tests in the build and deploy pipeline. This is mainly because I don't know how to do this effectively. I've just been manually testing the site as a human after each build.

**Pipeline**
* Code push to repo
* Trigger `Build` (which builds the main web app container and pushes to github container registry)
* Successful `Build` triggers `Deploy`
* This tears down the cloud infrastructure, rebuilds it, and binds the static IP to the virtual network interface card of the new VM
* Configure virtual machine (Github actions runner SSH to new VM and run `setup-vm.sh` bash script)
* Inject secrets (TLS certs etc.)
* Pull Docker images 
* Bring up all containers 

#### 4. Security & VPN

I'm storing all secrets using GitHub secrets, and I manually inject these in as needed during build and deployment using bash scripts. To protect the provisioned VM, everything is behind a Wireguard VPN via [Tailscale](https://tailscale.com/kb/1151/what-is-tailscale/). This means no public ports are open on the VM except 80 (HTTP) and 443 (HTTPS). I've also rebased the git history of the repo to remove all keys & secrets.

If I have done something stupid, please tell me so I can fix it.

## Backlog

July 2024: I'm working on building out a proper backlog. Here are some quick notes.

**Expanding the mapping capabilities beyond Plotly charts**

Presently the site is built as a Flask app, wrapping a Plotly Dash (Python) web app. Most of the visualisations such as charts and maps are out-of-the box Plotly javascript charts. Some I've pushed hard but, at base, I think the main map is limited as it is really just a Choropleth chart. I'd love to explore more open frameworks for map specific stuff, like Leaflet and Mapbox.

**Automatically update data via APIs**

Presently a big limitation is all these datasets are a snapshot in time of what I scraped a few years ago. It's not a big deal as most of these datasets are only updated every 2-4 years, but it does mean the site ages and loses data currency. Many of the data stores such as UN data portal have APIs to connect, so I think it would be cool to build a proper data processing pipeline that periodicaly polls this data and updates the app when new data is available. It would probably still need a lot of human oversight.


**Upgrading metatdata csv files to PostGres database tables**

The curation, tagging and categorisation of all datasets is presently in a giant file `/data/dataset_lookup.csv`. This is I tag each dataset by the type of data it is, and set where it sits in the overhead navigation menu, which is all constructed at run-time dynamically. It's now over 2500 rows and is pretty cumbersome to manually manage. It might be wise to convert it to proper postgres table. I'm not sure. I get by with csv for now.

**TLS Certificate Cycling (is manual)**

It would be good to get TLS certs cycling properly. Certbot container is not refreshing them. Could explore Tailscale (which now supports TLS cert generation). 

Background
* Every 3 months, I have to cycle out the TLS (HTTPS) certificates.
* Presently this is a manual process as I am running an NGINX container (reverse proxy) which must have valid TLS certs 
* I'm also running a certbot container which can successfully generate new certs and inject them into NGINX, however it does not seem to be cycling them out, despite me trying to get this working with a script in the docker-compose.yml file.
* TLS certs are stored as Github secrets, and baked in during a full pipeline build
* So as long as there are valid certs as secrets, we are good, I just need to generate them.

Generating new certs (my task list)
* SSH to production server
* Bring all containers down with `sudo docker stop $(sudo docker ps -a -q)`
* Check they are down with `docker ps`
* Restart all services with the appropriate script `. start-up-generate-certs.sh`
* (Note the new certs only exist in the NGINX container, so we need to extract them. It's easiest to do whilst it is running)
* Obtain the container ID for NGINX container with `docker ps`
* Copy both keys from running NGINX container to $HOME as files 

`docker cp -L e9e73443e9f2:/etc/letsencrypt/live/worldatlas.org/privkey.pem ~/privkey.pem`

`docker cp -L e9e73443e9f2:/etc/letsencrypt/live/worldatlas.org/fullchain.pem ~/fullchain.pem`

Noting the e9e73443e9f2 above is the containerID of the nginx container

* Copy the content of each key file into GITHUB SECRETS (repo > settings > secrets > actions > ...)
* (OPTIONAL) Rebuild whole deployment by manually rerunning the github actions for `deploy` (takes 15 mins and can be a bitch)

**More datasets**

There are a ton of new datasets I'd like to bring in, that include:
* shipwrecks (how cool would it be to see shipwrecks, like the titanic on the 3d globe view)
* census data (have not yet explored this layer of granularity)

