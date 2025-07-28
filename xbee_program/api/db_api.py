import requests
from api.config import get_api_base_url

def send_sensor_data_batch(token, company_id, device_serial, data_list, receiver_serial=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "company_id": company_id,
        "device_serial": device_serial,
        "data": data_list
    }

    if receiver_serial:
        payload["receiver_serial"] = receiver_serial

    base_url = get_api_base_url()
    if not base_url or base_url == "http://":
        print("[ERROR] base_url이 설정되지 않았습니다. 로그인 후 다시 시도하세요.")
        return False

    url = f"{base_url}/api/sensor-data/batch"
    print(f"[BATCH 전송] POST {url} → payload: {payload}")

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=3)
        if res.status_code == 201:
            print(f"[BATCH 전송 성공] {res.status_code}")
            return True
        else:
            print(f"[BATCH 전송 실패] {res.status_code} - {res.text}")
            return False
    except Exception as e:
        print(f"[예외] BATCH 전송 실패: {e}")
        return False
