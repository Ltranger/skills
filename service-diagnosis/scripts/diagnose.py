#!/usr/bin/env python3
import json
import sys
import requests
from datetime import datetime, timedelta

def remove_large_fields(data):
    """递归移除大数据量字段"""
    if isinstance(data, dict):
        # 移除指定的大数据量字段
        fields_to_remove = ['outlinerTss', 'outlinerValues', 'values', 'timeStamps']
        for field in fields_to_remove:
            data.pop(field, None)

        # 递归处理嵌套的字典和列表
        for key, value in data.items():
            data[key] = remove_large_fields(value)
    elif isinstance(data, list):
        return [remove_large_fields(item) for item in data]

    return data

def call_diagnosis_api(service, start_time, end_time):
    """调用诊断 API"""
    url = 'https://xray-ai.devops.xiaohongshu.com/api/diagnosis/analysis/service/analyze'
    headers = {'Content-Type': 'application/json'}
    payload = {
        'service': service,
        'startTime': start_time,
        'endTime': end_time
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {'error': str(e)}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': '请提供服务名称'}))
        sys.exit(1)

    service = sys.argv[1]

    # 处理时间参数
    if len(sys.argv) >= 4:
        start_time = sys.argv[2]
        end_time = sys.argv[3]
    else:
        # 默认最近一小时
        end = datetime.now()
        start = end - timedelta(hours=1)
        start_time = start.strftime('%Y-%m-%d %H:%M:%S')
        end_time = end.strftime('%Y-%m-%d %H:%M:%S')

    # 调用 API
    result = call_diagnosis_api(service, start_time, end_time)

    # 移除大数据量字段
    filtered_result = remove_large_fields(result)

    # 输出 JSON
    print(json.dumps(filtered_result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
