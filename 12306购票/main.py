from funk12306 import Funk12306
import sys
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='12306购票助手')
    parser.add_argument('--test', action='store_true', help='启用测试模式，不实际提交订单')
    args = parser.parse_args()
    
    funk = None
    try:
        username = input('请输入12306账号：')
        password = input('请输入12306密码：')
        funk = Funk12306(username, password, test_mode=args.test)
        funk.run()
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        sys.exit(1)
    finally:
        # 确保无论成功失败都执行登出
        if funk:
            funk.logout()
        print("程序已正常结束")
        sys.exit(0)