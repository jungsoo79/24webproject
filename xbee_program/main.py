import sys
import os
from PyQt5 import QtWidgets
from ui.widgets.login_dialog import LoginDialog
from mainwindow import XBeeConfigurator
from api.auth_manager import AuthManager
from database.backup_db import init_db

def main():
    init_db()
    app = QtWidgets.QApplication(sys.argv)

    while True:
        login_dialog = LoginDialog()
        if login_dialog.exec_() == QtWidgets.QDialog.Accepted:
            auth = AuthManager.get_instance()
            token = auth.get_token()
            user_info = auth.get_user_info()

            if token and user_info:
                main_window = XBeeConfigurator()
                main_window.show()
                app.exec_()
            else:
                QtWidgets.QMessageBox.critical(
                    None, "로그인 오류", "인증 정보가 유효하지 않습니다."
                )
        else:
            break

if __name__ == "__main__":
    main()
