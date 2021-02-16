# Lingtrain Aligner. ML powered application for extracting parallel corpora.

## Introduction

Lingtrain Aligner is a tool for extracting parallel corpora from texts in different languages.

![Parallel corpus example](/img/prince_parallel.png)

## Models

Automated alignment process relies on the sentence embeddings models. Embeddings are multidimensional vectors of a special kind which are used to calculate a distance between the sentences. You can also plug your own model using the interface described in models directory. Supported languages list depend on the selected backend model.

- **distiluse-base-multilingual-cased-v2**
  - more reliable and fast
  - moderate weights size — 500MB
  - supports 50+ languages
  - full list of supported languages can be found in [this paper](https://arxiv.org/abs/2004.09813)
- **LaBSE (Language-agnostic BERT Sentence Embedding)**
  - can be used for rare languages
  - pretty heavy weights — 1.8GB
  - supports 100+ languages
  - full list of supported languages can be found [here](https://arxiv.org/abs/2007.01852)

## Credits

<table>
<tr><td><img src="/img/hse.jpg" alt="Higher School of Economics logo" width="200"/></td>
<td>The project was supported by the Center for Academic Development of Students within the framework of the Competition of initiative collective research projects of students of the National Research University "Higher School of Economics".</td></tr>
</table>

## Demo

For the quick overview of the alignment process and main functionality you can watch the demo which was helded on the [AINL Conference](https://ainlconf.ru/2020/program).


<a href="https://www.youtube.com/watch?v=W6N7vJ4RqS4"><img src="/img/demo.png" alt="Higher School of Economics logo" width="800"/></a>

## How-to

Alignment process is pretty straightforward. After you have the app up and running follow the instructions to start the process. To start the app locally see the [Running from Docker Hub](#running-from-docker-hub) section.

### 1. Upload raw texts
![Upload](/img/1.png)

### 2. Check the splitted documents
![Splitted](/img/2.png)

### 3. Align documents

![Visualization](/img/3.png)

### 4. Check the result and edit if needed

![Edit](/img/4.png)

### 5. Set the quality threshold

![Threshold](/img/5.png)

### 6. Download the corpora

![Dowload](/img/6.png)

## Running on local machine

You can run the application on your computer using docker.

1. Make sure that docker is installed by typing the <code>docker version</code> command in your console.
2. Images configured to run locally are available on Docker Hub.

3. Run the following commads in your console:
<code>docker pull lingtrain/aligner:st</code>
<code>docker run -p 80:80 lingtrain/aligner:st</code>

4. App will be available in your browser on the <code>localhost</code> address.

## Deployment

You can deploy and run the app on your server using docker.

### Prepare the image

On your local machine.

1. Clone the repo.
    - <code>git clone https://github.com/averkij/lingtrain-aligner.git</code>
2. Edit the following line in **./fe/src/common/config.js** file.
    - <code>export const API_URL = "http://[IP_ADRESS]:[PORT]";</code>
      For example:
    - <code>export const API_URL = "http://89.23.34.12:5000";</code>
3. Build the app image. Run in the **root** folder of the repo:
    - <code>docker build . -t aligner:v1</code>
    - where **aligner:v1** is a tag (some king of the image name).
4. Now you have your image stored locally. You need to push it to Docker Hub.
    - Create an account on [Docker Hub](https://hub.docker.com/). It's a free and publicly available docker registry.
    - Login into your account
      - <code>docker login</code>
    - Tag the image that you've built
      - <code>docker tag aligner my_docker_hub_account/aligner:v1</code>
    - Push the image to registry
      - <code>docker push my_docker_hub_account/aligner:v1</code>
    - After a while your image will be uploaded and can be used for deployment.

### Deploy it

On your server.

1. Make sure that docker is installed by typing the <code>docker version</code> command in your console.
2. Make directories for storing the app results.
    - <code>mkdir /opt/data /opt/img</code>
3. Pull the prepared image
    - <code>docker pull my_docker_hub_account/aligner:v1</code>
    - Wait for downloading. After that you will have the image stored locally.
4. Start the app
    - <code>docker run -v /opt/data:/app/data -v /opt/img:/app/static/img -p [PORT]:80 my_docker_hub_account/aligner:v1</code>
    - where **/opt/data**, **/opt/img** are folder on your server
    - and **/app/data**, **/app/static/img** are folder inside the container. Don't change them.
    - [PORT] is the port that you have configured while building the image.

## Running in development mode

### Backend

- /be

Flask/uwsgi backend REST API service. It's pretty simple and contains all the alignment logic.

<code>python main.py</code>

### Frontend

- /fe

SPA. Vue + vuex + vuetify. UI for managing alignment process using BE and a tool for translators to edit processing documents.

#### Setup

<code>npm install</code>

#### Compile and run with hot-reloads for development

<code>npm run serve</code>
