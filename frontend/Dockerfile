FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_DJANGO_URL=http://localhost:8000
ARG VITE_PAYMENT_URL=http://localhost:8001
ENV VITE_DJANGO_URL=$VITE_DJANGO_URL VITE_PAYMENT_URL=$VITE_PAYMENT_URL
RUN npm run build
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80