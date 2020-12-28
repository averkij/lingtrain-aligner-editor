#--- ENV CONFIG VARIABLES ---

#VAR_BATCHSIZE (50)
#VAR_WINDOW (40)
#VAR_MAX_BATCHES (4)
#VAR_PROCESSORS_COUNT (2)

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
# COPY ./config-templates/config.py /app
# COPY ./prestart.sh /app

RUN pip install -r /app/requirements.txt;

RUN mkdir /app/static
COPY --from=build-stage /app/dist /app/static
