import requests
from api.config import get_api_base_url

def login_request(username, password):
    url = f"{get_api_base_url()}/api/auth/login"
    data = {"username": username, "password": password}
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    try:
        response = requests.post(url, json=data, headers=headers)
        if response is None:
            return {"success": False, "message": "서버 응답 없음", "status": 500}
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        return {
            "success": False,
            "message": f"로그인 실패: {response.text}",
            "status": response.status_code
        }
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"서버 연결 실패: {e}", "status": 503}
    except Exception as e:
        return {"success": False, "message": f"예외 발생: {e}", "status": 500}

def get_my_info(token):
    url = f"{get_api_base_url()}/api/auth/me"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers)
        if response is None:
            return {"success": False, "message": "서버 응답 없음", "status": 500}
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        return {
            "success": False,
            "message": f"내 정보 조회 실패: {response.text}",
            "status": response.status_code
        }
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"서버 연결 실패: {e}", "status": 503}
    except Exception as e:
        return {"success": False, "message": f"예외 발생: {e}", "status": 500}
