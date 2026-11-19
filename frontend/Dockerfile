# 使用轻量级 Nginx 镜像来托管静态文件
FROM nginx:1.25-alpine

# 将本地静态文件复制到 Nginx 默认的网页目录
COPY . /usr/share/nginx/html

# 用我们自己的配置覆盖默认的 Nginx 配置
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# 在前台运行 Nginx
CMD ["nginx", "-g", "daemon off;"]