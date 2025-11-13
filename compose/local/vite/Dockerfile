FROM node:18-bullseye-slim

WORKDIR /app/frontend

COPY ./frontend/package.json /app/frontend
COPY ./.envs/.local/.env.development ${APP_HOME}/frontend/.env.development

COPY ./compose/local/vite/entrypoint /entrypoint
RUN sed -i 's/\r//' /entrypoint
RUN chmod +x /entrypoint

RUN npm install && npm cache clean --force

ENV PATH ./node_modules/.bin/:$PATH

ENTRYPOINT ["/entrypoint"]
