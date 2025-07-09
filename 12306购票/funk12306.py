import requests
import json
import urllib.parse
from datetime import datetime
import pprint
import time
import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# 配置日志
dataclass(logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'))

@dataclass
class Station:
    name: str
    code: str
    pinyin: str
    simple_pinyin: str

def parse_station_info(data: str) -> Dict[str, Station]:
    """解析车站信息，返回名称到车站信息的映射"""
    station_data = data.split('=')[1].strip(';')
    stations = json.loads(station_data)
    return {station['name']: Station(**station) for station in stations}


def validate_date(date_str: str) -> bool:
    """验证日期格式是否正确并是否为当前日期或之后"""
    try:
        input_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        return input_date >= datetime.now().date()
    except ValueError:
        return False

class Funk12306:
    def __init__(self, username, password, test_mode=False):  # 新增test_mode参数
        self.username = username
        self.password = password
        self.test_mode = test_mode  # 新增：测试模式标志
        self.s = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://kyfw.12306.cn/otn/resources/login.html'
        }
        self.station_info = {}
        self.passenger_list = []
        self.init_session()
        self.logger = logging.getLogger(__name__)

    def init_session(self):
        """初始化会话，获取基础cookies"""
        try:
            url = 'https://www.12306.cn/index/'
            response = self.s.get(url, headers=self.headers, timeout=10)
            self.logger.info("会话初始化完成")
            return True
        except requests.exceptions.RequestException as e:
            self.logger.error(f"会话初始化失败: {str(e)}")
            return False

    def logout(self):
        """账号登出，清理会话"""
        if not hasattr(self, 's'):
            return
            
        try:
            # 12306登出接口
            logout_url = 'https://kyfw.12306.cn/passport/web/logout'
            response = self.s.post(logout_url, headers=self.headers, timeout=10)
            result = response.json()
            
            if result.get('result_code') == 0:
                self.logger.info("账号已成功退出")
            else:
                self.logger.warning(f"登出失败: {result.get('result_message')}")
        except Exception as e:
            self.logger.error(f"登出过程出错: {str(e)}")
        finally:
            # 关闭会话释放资源
            self.s.close()
            self.logger.debug("会话已关闭")

    def login(self) -> bool:
        """处理登录流程，包括验证码"""
        try:
            # 1. 获取验证码图片
            captcha_url = 'https://kyfw.12306.cn/passport/captcha/captcha-image?login_site=E&module=login&rand=sjrand'
            captcha_response = self.s.get(captcha_url, headers=self.headers, timeout=10)
            
            # 使用绝对路径保存图片
            current_dir = os.path.dirname(os.path.abspath(__file__))
            captcha_path = os.path.join(current_dir, 'captcha.jpg')
            
            # 保存验证码图片
            with open(captcha_path, 'wb') as f:
                f.write(captcha_response.content)
            
            # 新增：自动打开图片的异常处理
            try:
                import webbrowser
                webbrowser.open(captcha_path)
            except Exception as e:
                self.logger.warning(f"无法自动打开验证码图片，请手动查看: {captcha_path}, 错误: {str(e)}")
            
            self.logger.info(f"验证码图片已保存至: {captcha_path}")
            self.logger.info("请输入验证码坐标（例如：35,45,100,100）")
            
            # 2. 获取用户输入的验证码坐标
            captcha_position = input("请输入验证码坐标: ")
            
            # 用户输入后清理图片
            if os.path.exists(captcha_path):
                try:
                    os.remove(captcha_path)
                    self.logger.debug("验证码图片已清理")
                except Exception as e:
                    self.logger.warning(f"清理验证码图片失败: {str(e)}")
            
            # 3. 验证验证码
            check_url = 'https://kyfw.12306.cn/passport/captcha/captcha-check'
            check_data = {
                'answer': captcha_position,
                'login_site': 'E',
                'rand': 'sjrand'
            }
            check_response = self.s.post(check_url, data=check_data, headers=self.headers, timeout=10)
            check_result = check_response.json()
            
            if check_result.get('result_code') != '4':
                self.logger.error(f"验证码验证失败: {check_result.get('result_message')}")
                return False
            
            # 4. 提交登录请求
            login_url = 'https://kyfw.12306.cn/passport/web/login'
            login_data = {
                'username': self.username,
                'password': self.password,
                'appid': 'otn'
            }
            response = self.s.post(login_url, json=login_data, headers=self.headers, timeout=10)
            result = response.json()
            
            if result.get('result_code') == 0:
                self.logger.info("登录成功")
                return True
            else:
                self.logger.error(f"登录失败: {result.get('result_message')}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"网络请求错误: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"登录过程中发生异常: {str(e)}")
            return False

    def get_station_info(self) -> bool:
        """获取车站信息并解析"""
        try:
            url = 'https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version=1.9076'
            response = self.s.get(url, headers=self.headers, timeout=10)
            # 解析车站信息
            self.station_info = parse_station_info(response.text)
            self.logger.info("车站信息获取完成")
            return True
        except requests.exceptions.RequestException as e:
            self.logger.error(f"获取车站信息失败: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"解析车站信息失败: {str(e)}")
            return False

    def query_tickets(self, train_date, from_station, to_station):
        """查询车票信息"""
        if not validate_date(train_date):
            self.logger.error("日期格式或有效性验证失败")
            return []

        try:
            # 获取车站编码
            from_station_code = self._get_station_code(from_station)
            to_station_code = self._get_station_code(to_station)

            if not from_station_code or not to_station_code:
                self.logger.error("车站编码未找到")
                return []

            url = f'https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date={train_date}&leftTicketDTO.from_station={from_station_code}&leftTicketDTO.to_station={to_station_code}&purpose_codes=ADULT'
            response = self.s.get(url, headers=self.headers, timeout=10)
            ticket_data = response.json()

            # 解析车次信息
            if ticket_data['status']:
                self.logger.info("车次信息查询成功")
                return ticket_data['data']['result']
            else:
                self.logger.warning("车次信息查询失败")
                return []
        except requests.exceptions.RequestException as e:
            self.logger.error(f"网络请求错误: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"查询车票过程中发生异常: {str(e)}")
            return []

    def _get_station_code(self, station_name):
        """根据车站名称获取编码"""
        station = self.station_info.get(station_name)
        if not station:
            self.logger.warning(f"未找到车站编码: {station_name}")
            return None
        return station.code

    def get_passenger_info(self) -> List[Dict[str, str]]:
        """获取乘客信息列表"""
        try:
            url = 'https://kyfw.12306.cn/otn/confirmPassenger/getPassengerDTOs'
            response = self.s.post(url, headers=self.headers, timeout=10)
            self.passenger_list = self.parse_passenger(json.loads(response.content))
            self.logger.info('获取乘客信息完成')
            return self.passenger_list
        except requests.exceptions.RequestException as e:
            self.logger.error(f"获取乘客信息失败: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"解析乘客信息失败: {str(e)}")
            return []

    def parse_passenger(self, passenger_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """解析乘客信息"""
        passengers = []
        # 示例解析逻辑
        for p in passenger_data.get('data', {}).get('normal_passengers', []):
            passenger = {
                'name': p.get('passenger_name'),
                'id_type': p.get('passenger_id_type_code'),
                'id_number': p.get('passenger_id_no'),
                'phone': p.get('mobile_no')
            }
            # 验证必要字段
            if all(passenger.values()):
                passengers.append(passenger)
            else:
                self.logger.warning(f"发现不完整的乘客信息: {passenger}")
        return passengers

    def initialize_order(self, train_info: Dict[str, str], passenger_info: Dict[str, str]) -> Optional[str]:
        """初始化订单"""
        try:
            url = 'https://kyfw.12306.cn/otn/confirmPassenger/initDc'
            data = {
                'train_date': train_info['date'],
                'train_no': train_info['train_no'],
                'stationTrainCode': train_info['station_train_code'],
                # 其他必要参数
            }
            response = self.s.post(url, data=data, headers=self.headers, timeout=10)
            # 获取REPEAT_SUBMIT_TOKEN等必要参数
            result = json.loads(response.content)
            token = result.get('data', {}).get('submitToken')
            
            if token:
                self.logger.info("订单初始化成功")
            else:
                self.logger.error("订单初始化失败")
            
            return token
        except requests.exceptions.RequestException as e:
            self.logger.error(f"网络请求错误: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"初始化订单过程中发生异常: {str(e)}")
            return None

    def submit_order(self, token: str, train_info: Dict[str, str], passenger_info: Dict[str, str]) -> Dict[str, Any]:
        """提交订单"""
        try:
            url = 'https://kyfw.12306.cn/otn/confirmPassenger/confirmSingleForQueue'
            # 构造乘客信息字符串
            passengerTicketStr = self._construct_passenger_ticket_str(passenger_info, train_info)
            oldPassengerStr = self._construct_old_passenger_str(passenger_info)

            data = {
                'passengerTicketStr': passengerTicketStr,
                'oldPassengerStr': oldPassengerStr,
                'REPEAT_SUBMIT_TOKEN': token,
                # 其他必要参数
            }
            response = self.s.post(url, data=data, headers=self.headers, timeout=10)
            return json.loads(response.content)
        except requests.exceptions.RequestException as e:
            self.logger.error(f"网络请求错误: {str(e)}")
            return {'status': False, 'messages': [str(e)]}
        except Exception as e:
            self.logger.error(f"提交订单过程中发生异常: {str(e)}")
            return {'status': False, 'messages': [str(e)]}

    def _construct_passenger_ticket_str(self, passenger, train_info):
        """构造乘客车票信息字符串"""
        # 实际实现需根据12306要求的格式构造
        return f"{passenger['name']},1,{passenger['id_type']},{passenger['id_number']},1,{train_info['seat_type']},"

    def _construct_old_passenger_str(self, passenger):
        """构造老乘客信息字符串"""
        return f"{passenger['name']},{passenger['id_type']},{passenger['id_number']},1_"

    def query_order_status(self, order_id):
        """查询订单状态"""
        url = f'https://kyfw.12306.cn/otn/confirmPassenger/queryOrderWaitTime?orderId={order_id}'
        response = self.s.get(url, headers=self.headers)
        return json.loads(response.content)

    def run(self):
        """运行购票流程"""
        # 1. 登录
        if not self.login():
            return

        # 2. 获取车站信息
        self.get_station_info()

        # 3. 获取用户输入
        while True:
            from_station = input('请输入出发站：')
            to_station = input('请输入到达站：')
            train_date = input('请输入乘车日期(YYYY-MM-DD)：')
            seat_type = input('请输入坐席类型(一等座/二等座/硬座/硬卧)：')
            
            if not validate_date(train_date):
                print("日期格式错误或已过期，请重新输入")
                continue
            
            # 检查车站是否存在
            if from_station not in self.station_info or to_station not in self.station_info:
                print("出发站或到达站不存在，请重新输入")
                continue
            
            break
        
        # 4. 查询车票
        tickets = self.query_tickets(train_date, from_station, to_station)
        if not tickets:
            print("未查询到可用车次或车站信息错误")
            # 新增：提供重试选项
            retry = input("是否重新输入查询信息？(y/n): ")
            if retry.lower() == 'y':
                self.run()
            return

        # 5. 选择车次（简化实现，实际需展示车次列表供选择）
        selected_train = tickets[0]  # 示例：选择第一个车次

        # 6. 获取乘客信息
        self.get_passenger_info()
        passenger_index = int(input('输入要购票的乘车人的下标：'))
        selected_passenger = self.passenger_list[passenger_index]

        # 7. 初始化订单
        token = self.initialize_order(selected_train, selected_passenger)
        if not token:
            print("订单初始化失败")
            return
        
        # 新增：测试模式判断
        if self.test_mode:
            print("\n===== 测试模式 =====")
            print(f"模拟提交订单: {selected_train}")
            print(f"模拟购票乘客: {selected_passenger['name']}")
            print(f"订单令牌: {token}")
            print("===== 测试模式结束 =====")
            return  # 跳过实际提交

        # 8. 提交订单 (仅在非测试模式执行)
        order_result = self.submit_order(token, selected_train, selected_passenger)
        if order_result.get('status'):
            print("订单提交成功")
            order_id = order_result.get('data', {}).get('orderId')
            # 9. 查询订单状态
            max_attempts = 30  # 最多查询30次
            attempts = 0
            while attempts < max_attempts:
                status = self.query_order_status(order_id)
                print(f"订单状态：{status}")
                if status.get('data', {}).get('orderStatus') == 9:
                    print("购票成功！")
                    break
                attempts += 1
                if attempts >= max_attempts:
                    print("查询订单状态超时")
                    break
                time.sleep(2)
            else:
                print(f"订单提交失败：{order_result.get('messages')}")
