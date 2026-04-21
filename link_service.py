# -*- coding: utf-8 -*-
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from xiaoetong_api import (
    get_alive_m3u8,
    get_course_details_list,
    get_course_details_list_2,
    get_course_list,
    get_course_list_2,
    get_purchased_info,
    get_video_m3u8,
    get_video_play_url,
)

VIDEO_RESOURCE_TYPE = 3
LIVE_RESOURCE_TYPE = 4
SUPPORTED_RESOURCE_TYPES = {VIDEO_RESOURCE_TYPE, LIVE_RESOURCE_TYPE}
RESOURCE_TYPE_LABELS = {
    VIDEO_RESOURCE_TYPE: '视频',
    LIVE_RESOURCE_TYPE: '直播',
}


def list_purchased_courses():
    return [
        {'name': name, 'product_id': product_id}
        for name, product_id in get_purchased_info()
    ]


def list_course_nodes(product_id):
    if str(product_id).startswith('course_'):
        course_list = get_course_list_2(product_id)
    else:
        course_list = get_course_list(product_id)

    return [
        {'name': name, 'course_id': course_id, 'product_id': product_id}
        for name, course_id in course_list
    ]


def list_course_resources(course_id, product_id=None):
    if str(course_id).startswith('chap_'):
        if not product_id:
            raise ValueError('chap_ 类型子课程缺少父级课程 product_id')
        details = get_course_details_list_2(product_id, course_id)
        normalized_details = [(title, resource_id, VIDEO_RESOURCE_TYPE) for title, resource_id in details]
    else:
        normalized_details = get_course_details_list(course_id)

    resources = []
    for title, resource_id, resource_type in normalized_details:
        resources.append(
            {
                'title': title,
                'resource_id': resource_id,
                'resource_type': resource_type,
                'resource_type_label': RESOURCE_TYPE_LABELS.get(resource_type, f'类型{resource_type}'),
                'supported': resource_type in SUPPORTED_RESOURCE_TYPES,
            }
        )
    return resources


def resolve_resource_play_url(resource_id, resource_type, parent_course_id):
    resource_id = str(resource_id)
    if resource_id.startswith('v_'):
        play_sign = get_video_m3u8(resource_id, parent_course_id)
        return get_video_play_url(play_sign)
    if resource_id.startswith('l_'):
        return get_alive_m3u8(resource_id)
    raise ValueError(f'暂不支持的资源ID: {resource_id}')


def extract_links_for_resources(course_id, course_name, resources, progress_callback=None, status_callback=None, log_callback=None, product_id=None, max_workers=3, delay_seconds=0.0):
    selected_resources = [item for item in resources if item.get('supported')]
    total = len(selected_resources)
    result_items = []
    completed_count = 0

    max_workers = max(1, min(20, int(max_workers)))
    delay_seconds = round(float(delay_seconds), 1)
    delay_seconds = max(0.0, min(5.0, delay_seconds))

    if status_callback:
        if total:
            status_callback(f'开始获取 {course_name} 的下载链接，共 {total} 个资源，线程数 {max_workers}，每轮完成后延迟 {delay_seconds:.1f}s')
        else:
            status_callback('当前没有可处理的视频或直播资源')

    def worker(item):
        title = item['title']
        resource_id = item['resource_id']
        resource_type = item['resource_type']
        parent_course_id = product_id if str(course_id).startswith('chap_') and product_id else course_id

        try:
            play_url = resolve_resource_play_url(resource_id, resource_type, parent_course_id)
            return {
                'title': title,
                'resource_id': resource_id,
                'resource_type': resource_type,
                'resource_type_label': item['resource_type_label'],
                'url': play_url,
                'status': 'success',
                'error': '',
            }
        except Exception as exc:
            return {
                'title': title,
                'resource_id': resource_id,
                'resource_type': resource_type,
                'resource_type_label': item['resource_type_label'],
                'url': '',
                'status': 'failed',
                'error': str(exc),
            }

    for batch_start in range(0, total, max_workers):
        batch = selected_resources[batch_start:batch_start + max_workers]
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(worker, item) for item in batch]
            for future in as_completed(futures):
                result = future.result()
                result_items.append(result)
                completed_count += 1
                title = result['title']
                if status_callback:
                    if result['status'] == 'success':
                        status_callback(f'已获取 {completed_count}/{total}：{title}')
                    else:
                        status_callback(f'获取失败 {completed_count}/{total}：{title}')
                if progress_callback:
                    progress_callback(completed_count, total, title)

        has_next_batch = batch_start + max_workers < total
        if has_next_batch and delay_seconds > 0:
            if log_callback:
                log_callback(f'当前批次已完成，等待 {delay_seconds:.1f}s 后继续...')
            time.sleep(delay_seconds)

    success_count = sum(1 for item in result_items if item['status'] == 'success')
    failed_count = sum(1 for item in result_items if item['status'] == 'failed')

    return {
        'course_name': course_name,
        'total': total,
        'success': success_count,
        'failed': failed_count,
        'items': result_items,
    }


def extract_links_for_course(course_id, course_name, product_id=None, progress_callback=None, status_callback=None):
    resources = list_course_resources(course_id, product_id=product_id)
    return extract_links_for_resources(
        course_id,
        course_name,
        resources,
        progress_callback,
        status_callback,
        product_id=product_id,
    )


def format_link_results(result):
    lines = [
        f"课程：{result['course_name']}",
        f"总数：{result['total']}",
        f"成功：{result['success']}",
        f"失败：{result['failed']}",
        '',
    ]

    for item in result['items']:
        if item['status'] == 'success':
            lines.append(f"[成功][{item['resource_type_label']}] {item['title']}")
            lines.append(item['url'])
        else:
            lines.append(f"[失败][{item['resource_type_label']}] {item['title']} - {item['error']}")
        lines.append('')

    return '\n'.join(lines).strip()


def sanitize_filename(name):
    sanitized = re.sub(r'[\\/:*?"<>|]+', '_', str(name)).strip()
    return sanitized or '导出结果'


def build_export_lines(result):
    lines = []
    for item in result['items']:
        if item['status'] == 'success' and item['url']:
            lines.append(f"{item['url']}----{item['title']}")
    return lines


def export_links_to_txt(result, output_dir):
    export_dir = Path(output_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{sanitize_filename(result['course_name'])}.txt"
    file_path = export_dir / file_name
    lines = build_export_lines(result)
    file_path.write_text('\n'.join(lines), encoding='utf-8')
    return str(file_path)
