FROM nginx:alpine

WORKDIR /app

COPY entrypoint.sh /app 

COPY index.html style.css script.js config.js.template /usr/share/nginx/html/

RUN chmod +x entrypoint.sh 

ENTRYPOINT ["/app/entrypoint.sh"]

CMD [ "nginx","-g","daemon off;"]
