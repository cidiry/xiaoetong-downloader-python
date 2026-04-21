# -*- coding: utf-8 -*-
from datetime import datetime
import random
import requests

from app_config import load_config

REQUEST_TIMEOUT = 20


def _get_runtime_config():
    config = load_config()
    app_id = config.get('app_id', '')
    user_id = config.get('user_id', '')
    base_url = config.get('base_url', '')
    cookies = config.get('cookies', {})
    if not app_id or not user_id or not base_url or not cookies:
        raise ValueError('请先在界面中填写并保存 cookies 配置')
    return app_id, user_id, base_url, cookies


def _request_json(method, url, **kwargs):
    _, _, _, cookies = _get_runtime_config()
    response = requests.request(method, url, cookies=cookies, timeout=REQUEST_TIMEOUT, **kwargs)
    response.raise_for_status()
    return response.json()


def get_purchased_info():
    app_id, _, base_url, _ = _get_runtime_config()
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,en-GB;q=0.6,zh-TW;q=0.5',
        'App-Id': app_id,
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Referer': f'{base_url}/bought',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0',
        'sec-ch-ua': '"Microsoft Edge";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    page = 1
    all_list = []
    while True:
        params = {
            'app_id': app_id,
            'page_index': str(page),
            'page_size': '30',
        }
        data_list = _request_json('GET', f'{base_url}/api/xe.shop.purchased.get/1.0.0', params=params, headers=headers)['data']['list']
        if not data_list:
            break
        all_list.extend((data['purchase_name'], data['resource_id']) for data in data_list)
        page += 1
    return all_list


def get_course_list(p_id):
    _, _, base_url, _ = _get_runtime_config()
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,en-GB;q=0.6,zh-TW;q=0.5',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': base_url,
        'Pragma': 'no-cache',
        'Referer': f'{base_url}/p/t_pc/course_pc_detail/big_column/{p_id}',
        'Req-UUID': f"{datetime.now().strftime('%Y%m%d%H%M%S')}000{random.randint(100000, 999999)}",
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0',
        'retry': '1',
        'sec-ch-ua': '"Microsoft Edge";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    page = 1
    all_list = []
    while True:
        json_data = {
            'column_id': p_id,
            'page_size': 20,
            'page_index': page,
            'content_app_id': None,
            'isDesc': 1,
        }
        data_list = _request_json('POST', f'{base_url}/xe.course.business.topic.items.get/2.0.0', headers=headers, json=json_data)['data']['list']
        if not data_list:
            break
        all_list.extend((data['resource_title'], data['resource_id']) for data in data_list)
        page += 1
    return all_list


def get_course_details_list(p_id):
    _, _, base_url, _ = _get_runtime_config()
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,en-GB;q=0.6,zh-TW;q=0.5',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': base_url,
        'Pragma': 'no-cache',
        'Referer': f'{base_url}/p/t_pc/course_pc_detail/big_column/{p_id}',
        'Req-UUID': f"{datetime.now().strftime('%Y%m%d%H%M%S')}000{random.randint(100000, 999999)}",
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0',
        'retry': '1',
        'sec-ch-ua': '"Microsoft Edge";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    page = 1
    all_list = []
    while True:
        json_data = {
            'column_id': p_id,
            'page_size': 20,
            'page_index': page,
            'content_app_id': None,
        }
        data_list = _request_json('POST', f'{base_url}/xe.course.business_go.column.items.get/2.0.0', headers=headers, json=json_data)['data']['list']
        if not data_list:
            break
        all_list.extend((data['resource_title'], data['resource_id'], data['resource_type']) for data in data_list)
        page += 1
    return all_list


def get_alive_m3u8(alive_id):
    app_id, _, base_url, _ = _get_runtime_config()
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,en-GB;q=0.6,zh-TW;q=0.5',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Referer': f'{base_url}/p/t_pc/live_pc/pc/{alive_id}',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0',
        'confusion': '2',
        'sec-ch-ua': '"Microsoft Edge";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    params = {
        'app_id': app_id,
        'alive_id': alive_id,
    }
    data = _request_json('GET', f'{base_url}/_alive/api/get_lookback_list', params=params, headers=headers)
    return data['data'][-1]['line_sharpness'][0]['url']


def get_video_m3u8(v_id, p_id):
    _, _, base_url, _ = _get_runtime_config()
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,en-GB;q=0.6,zh-TW;q=0.5',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': base_url,
        'Pragma': 'no-cache',
        'Req-UUID': f"{datetime.now().strftime('%Y%m%d%H%M%S')}000{random.randint(100000, 999999)}",
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0',
        'retry': '1',
        'sec-ch-ua': '"Microsoft Edge";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    data = {
        'resource_id': v_id,
        'opr_sys': 'Win32',
        'product_id': p_id,
        'content_app_id': '',
    }
    payload = _request_json('POST', f'{base_url}/xe.course.business.video.detail_info.get/2.0.0', headers=headers, data=data)
    return payload['data']['video_info']['play_sign']


def get_video_play_url(play_sign):
    app_id, user_id, base_url, _ = _get_runtime_config()
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,en-GB;q=0.6,zh-TW;q=0.5',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': base_url,
        'Pragma': 'no-cache',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0',
        'sec-ch-ua': '"Microsoft Edge";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    json_data = {
        'org_app_id': '',
        'app_id': app_id,
        'user_id': user_id,
        'play_sign': [play_sign],
        'play_line': 'A',
        'opr_sys': 'Win32',
    }
    payload = _request_json('POST', f'{base_url}/xe.material-center.play/getPlayUrl', headers=headers, json=json_data)
    play_data = payload['data'][play_sign]
    support_list = play_data['support_list']

    preferred_key = ''
    for support in support_list:
        if '_' in support:
            preferred_key = support
            break
    if not preferred_key and support_list:
        preferred_key = support_list[0]
    if not preferred_key:
        raise ValueError('未找到可用播放地址')
    return play_data['play_list'][preferred_key]['play_url']


def get_course_list_2(p_id):
    app_id, _, base_url, _ = _get_runtime_config()
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,en-GB;q=0.6,zh-TW;q=0.5',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': base_url,
        'Pragma': 'no-cache',
        'Referer': f'{base_url}/p/t_pc/course_pc_detail/camp_pro/{p_id}',
        'Req-UUID': f"{datetime.now().strftime('%Y%m%d%H%M%S')}000{random.randint(100000, 999999)}",
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0',
        'retry': '1',
        'sec-ch-ua': '"Microsoft Edge";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    page = 1
    all_list = []
    while True:
        data = {
            'app_id': app_id,
            'course_id': p_id,
            'order': 'asc',
            'p_id': '0',
            'page': str(page),
            'page_size': '50',
            'sub_course_id': '',
            'resource_id': '',
            'is_display_auth_sections': '0',
        }
        data_list = _request_json('POST', f'{base_url}/xe.course.business_go.avoidlogin.e_course.resource_catalog_list.get/1.0.0', headers=headers, data=data)['data']['list']
        if not data_list:
            break
        all_list.extend((item['resource_title'], item['resource_id']) for item in data_list)
        page += 1
    return all_list


def get_course_details_list_2(p_id, chap_id):
    app_id, _, base_url, _ = _get_runtime_config()
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,en-GB;q=0.6,zh-TW;q=0.5',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': base_url,
        'Pragma': 'no-cache',
        'Referer': f'{base_url}/p/t_pc/course_pc_detail/camp_pro/{p_id}',
        'Req-UUID': f"{datetime.now().strftime('%Y%m%d%H%M%S')}000{random.randint(100000, 999999)}",
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0',
        'retry': '1',
        'sec-ch-ua': '"Microsoft Edge";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    page = 1
    all_list = []
    while True:
        data = {
            'app_id': app_id,
            'resource_id': '',
            'course_id': p_id,
            'p_id': chap_id,
            'order': 'asc',
            'page': str(page),
            'page_size': '50',
            'sub_course_id': '',
            'is_display_auth_sections': '0',
        }
        data_list = _request_json('POST', f'{base_url}/xe.course.business_go.avoidlogin.e_course.resource_catalog_list.get/1.0.0', headers=headers, data=data)['data']['list']
        if not data_list:
            break
        all_list.extend((item['resource_title'], item['resource_id']) for item in data_list)
        page += 1
    return all_list
