FROM allinurl/goaccess:latest
RUN apk add --no-cache inotify-tools
COPY watch.sh /watch.sh
RUN chmod +x /watch.sh
ENTRYPOINT ["/watch.sh"]
