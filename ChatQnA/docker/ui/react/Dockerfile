FROM node as vite-app

WORKDIR /usr/app
COPY . /usr/app

ARG BACKEND_SERVICE_ENDPOINT
ARG DATAPREP_SERVICE_ENDPOINT
ENV VITE_BACKEND_SERVICE_ENDPOINT=$BACKEND_SERVICE_ENDPOINT
ENV VITE_DATA_PREP_SERVICE_URL=$DATAPREP_SERVICE_ENDPOINT


RUN ["npm", "ci"]
RUN ["npm", "run", "build"]


FROM nginx:alpine
EXPOSE 80


COPY ./nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=vite-app ./usr/app/dist /usr/share/nginx/html

ENTRYPOINT ["nginx", "-g", "daemon off;"]