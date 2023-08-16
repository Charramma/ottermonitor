# ottermonitor

用于监控Otter同步状态的工具，功能较少，目前只能监控节点存活状态、Pipeline同步延迟时间、Pipeline最后采集延迟时间。



[alibaba/otter](https://github.com/alibaba/otter): 阿里巴巴分布式数据库同步系统



## 使用方式

部署在任意一台可以访问到Otter web页面的服务器上



**启动参数**

| 参数             | 描述                       | 默认值         |
| ---------------- | -------------------------- | -------------- |
| --listen-address | ottermonitor监听的ip和端口 | 127.0.0.1:9310 |
| --otter-address  | Otter web页面的地址        | 127.0.0.1:3100 |



**启动命令：**

```
./ottermonitor --listen-address=127.0.0.1:9310 --otter-address=127.0.0.1:3100
```



**Systemd script**

```
[Unit]
Description=ottermonitor
After=network.target

[Service]
Type=simple
PIDFile=
ExecStart=/path/to/ottermonitor --listen-address=0.0.0.0:9310 --otter-address=127.0.0.1:3100
ExecStop=/bin/kill -HUP $MAINPID
Restart=Always

[Install]
WantedBy=multi-user.target
```



**配置Prometheus**

```yaml
scrape_configs:
  - job_name: 'ottermonitor'
    static_configs:
      - targets: ['127.0.0.1:9310']
```



结合Grafana进行图表展示

| 指标                    | 描述                     |
| ----------------------- | ------------------------ |
| otter_up                | Otter节点存活情况        |
| pipeline_delay_time     | Pipeline同步延迟时间     |
| pipeline_last_coll_time | Pipeline最后采集延迟时间 |

