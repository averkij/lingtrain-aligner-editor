#build web app
FROM node:lts-alpine as build-stage
WORKDIR /app
COPY ./fe ./
RUN npm install
RUN npm run build

#setup flask app
FROM tiangolo/uwsgi-nginx-flask:python3.8 as production-stage

#serve static/index.html
ENV STATIC_INDEX 1

ENV LISTEN_PORT 80

COPY ./be /app
RUN pip install -r /app/requirements.txt;

RUN mkdir /app/static
COPY --from=build-stage /app/dist /app/static