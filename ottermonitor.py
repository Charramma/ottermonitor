import socket
import argparse
import requests
from bs4 import BeautifulSoup
from flask import Flask
from prometheus_client import Gauge, generate_latest

app = Flask(__name__)

otter_up_gauge = Gauge('otter_up', "Node alived status", ['node', 'role'])
delay_time_gauge = Gauge('pipeline_delay_time', 'Pipeline delay time', ['Channel', 'Pipeline'])
last_coll_time_gauge = Gauge('pipeline_last_coll_time', 'The time interval between Pipeline and the last binlog collection', ['Channel', 'Pipeline'])


def check_port_open(host, port):
    """ 判断指定主机端口是否可联通，以此判断otter节点是否存活 """
    try:
        sock = socket.create_connection((host, port), timeout=3)
        sock.close()
        return True
    except socket.timeout:
        print(f"Connection timed out while connecting to {host}:{port}")
        return False
    except ConnectionRefusedError:
        print(f"Connection refused while connecting to {host}:{port}")
        return False
    except OSError as e:
        print(f"Error occurred while connecting to {host}:{port}: {str(e)}")
        return False


def check_otter_node_alived():
    """ 判断otter节点是否存活 """
    try:
        # 判断主节点是否存活
        mgr_host, mgr_port = args.otter_address.split(':')
        if check_port_open(mgr_host, mgr_port):
            otter_up_gauge.labels(node=f'{mgr_host}:{mgr_port}', role='otter-mgr').set(1)
        else:
            otter_up_gauge.labels(node=f'{mgr_host}:{mgr_port}', role='otter-mgr').set(0)
        
        # 判断从节点是否存活
        url = f"http://{mgr_host}:{mgr_port}/node_list.htm"
        response = requests.get(url)
        html_code = response.text
        soup = BeautifulSoup(html_code, "html.parser")

        table = soup.find("table", class_="list changecolor_w")
        if table:
            rows = table.find_all("tr")
            for row in rows[1:]:
                cells = row.find_all("td")
                if len(cells) >= 4:
                    node_ip = cells[2].get_text().strip()
                    node_port = cells[3].get_text().strip()
                    if check_port_open(node_ip, node_port):
                        otter_up_gauge.labels(node=f'{node_ip}:{node_port}', role='otter-node').set(1)
                    else:
                        otter_up_gauge.labels(node=f'{node_ip}:{node_port}', role='otter-node').set(0)
    except requests.RequestException as e:
        print(f"Error occurred while making requests: {str(e)}")


def get_pipeline_delay():
    """ 获取Pipeline延迟时间及最后采集时间 """
    mgr_host, mgr_port = args.otter_address.split(':')
    url = f"http://{mgr_host}:{mgr_port}/analysis_top_stat.htm"

    response = requests.get(url)
    html_code = response.text
    soup = BeautifulSoup(html_code, "html.parser")
    table = soup.find("table", class_="list changecolor_w")

    if table:
        rows = table.find_all("tr")
        for row in rows[1:]:
            cells = row.find_all("td")
            if len(cells) >= 4:
                Channel = cells[1].get_text().strip()
                Pipeline = cells[2].get_text().strip()
                delay_time = cells[3].get_text().strip().strip(' s')
                last_coll_time = cells[4].get_text().strip().strip(' s')
                delay_time_gauge.labels(Channel=Channel, Pipeline=Pipeline).set(delay_time)
                last_coll_time_gauge.labels(Channel=Channel, Pipeline=Pipeline).set(last_coll_time)

@app.route('/')
def index():
    return '<h1>Otter Exporter</h1><p>Click <a href="/metrics">Metrics</a> to view metrics.</p>'

@app.route('/metrics')
def metrics():
    try:
        check_otter_node_alived()
        get_pipeline_delay()
        return generate_latest(), 200, {'Content-Type': 'text/plain; version=0.0.4'}
    except Exception as e:
        app.logger.error(f"Error occurred: {str(e)}")
        return 'Inter Server Error', 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Otter Exporter')
    parser.add_argument('--listen-address', type=str, default='127.0.0.1:9310', help='Address and port to listen on')
    parser.add_argument('--otter-address', type=str, default='127.0.0.1:3100', help='Address and port of otter mgr')
    args = parser.parse_args()

    host, port = args.listen_address.split(':')
    app.run(host=host, port=port)
