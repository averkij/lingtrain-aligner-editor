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

## Running from Docker Hub

You can simply run the application on your computer using docker

```
docker pull lingtrain/aligner:st
docker run -p 80:80 lingtrain/aligner:st
```

After that the app will be available on your browser on the localhost address.

## Running in development mode

### Backend

- /be

Flask/uwsgi backend REST API service. It's pretty simple and contains all the alignment logic.

```
python main.py
```

### Frontend

- /fe

SPA. Vue + vuex + vuetify. UI for managing alignment process using BE and a tool for translators to edit processing documents.

#### Setup

```
npm install
```

#### Compile and run with hot-reloads for development

```
npm run serve
```
