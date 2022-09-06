#!/usr/bin/env python3
from collections import defaultdict
from typing import Any, Dict

import os
import yaml
import requests

BASE = os.path.dirname(os.path.abspath(__file__))


def load_config() -> Dict[str, Any]:
    path = os.path.join(BASE, 'settings.yaml')
    if not os.path.isfile(path):
        print('Please create a settings.yaml by copy from settings.example.yaml. \n'
              'Then edit it to your preference.')
    with open(path, 'r') as f:
        output = yaml.load(f, Loader=yaml.FullLoader)
    return output


def load_last_status() -> Dict[str, Any]:
    path = os.path.join(BASE, 'last_status.yaml')
    if os.path.isfile(path):
        with open(path, 'r') as f:
            output = yaml.load(f, Loader=yaml.FullLoader)
        return output if output else {}
    return {}


def update_last_status(data):
    path = os.path.join(BASE, 'last_status.yaml')
    with open(path, 'w') as f:
        f.write(yaml.dump(data))


def test_urls(config, last_status) -> (Dict[str, Any], Dict[str, Any]):
    report_lines = []
    new_status = defaultdict(dict)
    for target in config['targets']:
        name = target['name']
        url = target['url']
        retry = 0
        ok = False
        while not ok and retry < 3:
            res = requests.get(url, headers={'User-Agent': 'check_http'}, timeout=60)
            if 200 <= res.status_code < 400:
                print('checking {} ... OK'.format(name))
                ok = True
            else:
                print('checking {} ... ERROR'.format(name))
                retry += 1
        new_status[name]['ok'] = ok
        if last_status.get(name, {}).get('ok') != ok:
            report_lines.append('{} change status to {}.'.format(
                name, 'UP' if ok else 'DOWN'
            ))
    return report_lines, dict(new_status)


def make_report_message(report_lines):
    if not report_lines:
        return None
    message = '\n'.join(report_lines)
    return message


def send_report(config, message):
    if message:
        print('======\n'
              'Report\n'
              '======\n')
        print(message)
        requests.post(
            'https://api.pushover.net/1/messages.json',
            data={
                'token': config['pushover']['token'],
                'user': config['pushover']['user'],
                'message': message,
                'title': 'Web monitor update',
                'priority': 1,
            }
        )


if __name__ == '__main__':
    my_config = load_config()
    status = load_last_status()
    report, status = test_urls(my_config, status)
    report_message = make_report_message(report)
    update_last_status(status)
    send_report(my_config, report_message)
