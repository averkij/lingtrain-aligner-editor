# Lingtrain Aligner. ML powered application for extracting parallel corpora. 

## 1. Upload raw texts
![Upload](/img/1.png)

## 2. Check the splitted documents
![Splitted](/img/2.png)

## 3. Align documents

![Visualization](/img/3.png)

## 4. Check the result and edit if needed

![Edit](/img/4.png)

## 5. Set the quality threshold

![Threshold](/img/5.png)

## 6. Download the corpora

![Dowload](/img/6.png)

## Running from Docker Hub

You can simply run the application on your computer using docker

```
docker pull lingtrain/aligner:st
docker run -p 80:80 lingtrain/aligner:st
```

After that application will be available on your browser on the localhost address.

## Running in development mode

## Backend

- /be

Flask/uwsgi backend REST API service. It's pretty simple and contains all the alignment logic.

```
python main.py
```

## Frontend

- /fe

SPA. Vue + vuex + vuetify. UI for managing alignment process using BE and a tool for translators to edit processing documents.

### Setup

```
npm install
```

### Compile and run with hot-reloads for development

```
npm run serve
```
