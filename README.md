# Client

This is a web version of text alignment application. It consists of backend and frontend parts.

## Backend

- /be

Flask/uwsgi backend REST API service. It's pretty simple and contains all the alignment logic.

### Run for development

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
