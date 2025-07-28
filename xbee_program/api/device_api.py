import requests
from api.config import get_api_base_url  # URL 분리 적용

def get_device_models(token):
    url = f"{get_api_base_url()}/api/device-models"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        return {
            "success": False,
            "message": f"모델 조회 실패: {response.text}",
            "status": response.status_code
        }
    except Exception as e:
        return {"success": False, "message": str(e), "status": 500}

def get_receivers(token):
    url = f"{get_api_base_url()}/api/devices/receivers"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            json_data = response.json()

            # ✅ 응답이 리스트인 경우
            if isinstance(json_data, list):
                return {"success": True, "data": json_data}

            # ✅ 응답이 딕셔너리이면서 "data" 키가 있는 경우
            elif isinstance(json_data, dict) and "data" in json_data:
                return {"success": True, "data": json_data["data"]}

            else:
                return {"success": False, "message": "응답 형식 오류"}

        return {
            "success": False,
            "message": f"수신부 목록 조회 실패: {response.text}",
            "status": response.status_code
        }
    except Exception as e:
        return {"success": False, "message": str(e), "status": 500}

def get_my_devices(token):
    url = f"{get_api_base_url()}/api/devices"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        return {
            "success": False,
            "message": f"장치 목록 조회 실패: {response.text}",
            "status": response.status_code
        }
    except Exception as e:
        return {"success": False, "message": str(e), "status": 500}

def register_device(sn, model_name, device_name, parent_serial, location, company_id, token, ch=None, pan_id=None):
    url = f"{get_api_base_url()}/api/devices"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "serial_number": sn,
        "model_name": model_name,
        "device_name": device_name,
        "parent_serial": parent_serial,
        "location": location,
        "company_id": company_id
    }
    if ch:
        payload["ch"] = ch
    if pan_id:
        payload["pan_id"] = pan_id

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in (200, 201):
            return {"success": True, "data": response.json()}
        return {
            "success": False,
            "message": f"장치 등록 실패: {response.text}",
            "status": response.status_code
        }
    except Exception as e:
        return {"success": False, "message": str(e), "status": 500}
