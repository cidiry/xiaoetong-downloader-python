# -*- coding: utf-8 -*-
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).with_name('config.json')
DEFAULT_CONFIG = {
    'app_id': '',
    'user_id': '',
    'base_url': '',
    'cookies': {},
    'cookie_string': '',
}


def load_config():
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG.copy()
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_CONFIG.copy()

    config = DEFAULT_CONFIG.copy()
    config.update(data if isinstance(data, dict) else {})
    if not isinstance(config.get('cookies'), dict):
        config['cookies'] = {}
    return config


def save_config(config):
    merged = DEFAULT_CONFIG.copy()
    merged.update(config)
    CONFIG_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding='utf-8')
    return merged


def parse_cookie_string(cookie_string):
    cookies = {}
    for part in str(cookie_string).split(';'):
        item = part.strip()
        if not item or '=' not in item:
            continue
        key, value = item.split('=', 1)
        cookies[key.strip()] = value.strip()
    return cookies


def build_config_from_cookie_string(cookie_string):
    cookies = parse_cookie_string(cookie_string)
    if not cookies:
        raise ValueError('未解析到任何 cookies 项')

    shop_info_raw = cookies.get('shopInfo', '')
    base_url = ''
    if shop_info_raw:
        try:
            shop_info = json.loads(shop_info_raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f'shopInfo 不是合法 JSON：{exc}') from exc
        pc_custom_domain = (
            shop_info.get('domain', {}).get('pc_custom_domain')
            or shop_info.get('domain', {}).get('pc_custom_url', '')
        )

        if pc_custom_domain:
            base_url = pc_custom_domain if str(pc_custom_domain).startswith('http') else f'https://{pc_custom_domain}'


    user_info_raw = cookies.get('userInfo', '')
    user_id = ''
    if user_info_raw:
        try:
            user_info = json.loads(user_info_raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f'userInfo 不是合法 JSON：{exc}') from exc
        user_id = user_info.get('user_id', '')
        pc_user_key = user_info.get('pc_user_key', '')
        if pc_user_key:
            cookies["pc_user_key"] = pc_user_key

    app_id = str(cookies.get('app_id') or cookies.get('appId') or '').strip().strip('"')
    cookies.pop('shopInfo', None)

    if not base_url:
        raise ValueError('无法从 shopInfo 中提取 BASE_URL')
    if not app_id:
        raise ValueError('无法从 cookies 中提取 APP_ID')
    if not user_id:
        raise ValueError('无法从 userInfo 中提取 USER_ID')

    return {
        'app_id': app_id,
        'user_id': user_id,
        'base_url': base_url,
        'cookies': cookies,
        'cookie_string': cookie_string.strip(),
    }


def has_valid_config(config=None):
    current = config or load_config()
    return bool(current.get('app_id') and current.get('user_id') and current.get('base_url') and current.get('cookies'))
