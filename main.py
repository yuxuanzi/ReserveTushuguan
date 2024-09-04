
import json
import time
import argparse
import os
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


from utils import reserve, get_user_credentials
get_current_time = lambda action: time.strftime("%H:%M:%S", time.localtime(time.time() + 8*3600)) if action else time.strftime("%H:%M:%S", time.localtime(time.time()))
get_current_dayofweek = lambda action: time.strftime("%A", time.localtime(time.time() + 8*3600)) if action else time.strftime("%A", time.localtime(time.time()))


SLEEPTIME = 0.1 # 每次抢座的间隔
ENDTIME = "11:19:00" # 根据学校的预约座位时间+1min即可

ENABLE_SLIDER = False # 是否有滑块验证
MAX_ATTEMPT = 5 # 最大尝试次数
RESERVE_NEXT_DAY = True # 预约后天而不是今天的

                

def login_and_reserve(users, usernames, passwords, action, success_list=None):
    logging.info(f"Global settings: \nSLEEPTIME: {SLEEPTIME}\nENDTIME: {ENDTIME}\nENABLE_SLIDER: {ENABLE_SLIDER}\nRESERVE_NEXT_DAY: {RESERVE_NEXT_DAY}")
    # 检查用户数量与配置是否匹配
    if action and len(usernames.split(",")) != len(users):
        raise Exception("user number should match the number of config")
    # 初始化成功列表和尝试次数列表
    if success_list is None:
        success_list = [False] * len(users)
    attempt_counts = [0] * len(users)  # 新增尝试次数列表
    current_dayofweek = get_current_dayofweek(action)
    # 循环直到所有用户都成功或者达到结束时间
    while True:
        for index, user in enumerate(users):
            username, password, times, roomid, seatid, daysofweek = user.values()
            if action:
                username, password = usernames.split(',')[index], passwords.split(',')[index]
            if (current_dayofweek not in daysofweek) or success_list[index]:
                continue  # 跳过今天不预约的用户或已成功的用户
            
            # 记录尝试的用户
            logging.info(f"----------- {username} -- {times} -- {seatid} try -----------")
            s = reserve(sleep_time=SLEEPTIME, max_attempt=MAX_ATTEMPT, enable_slider=ENABLE_SLIDER, reserve_next_day=RESERVE_NEXT_DAY)
            s.get_login_status()
            s.login(username, password)
            s.requests.headers.update({'Host': 'office.chaoxing.com'})
            
            # 提交预约
            suc = s.submit(times, roomid, seatid, action)
            success_list[index] = suc
            
            # 更新尝试次数
            attempt_counts[index] += 1
            
            # 达到最大尝试次数，检查是否需要重试
            if not suc and attempt_counts[index] >= MAX_ATTEMPT:
                logging.info(f"{username} has reached the maximum attempts and will retry.")
                attempt_counts[index] = 0  # 清空尝试次数

        current_time = get_current_time(action)
        
        # 检查是否到达结束时间
        if current_time >= ENDTIME and all(success_list):
            break  # 如果所有用户都成功，退出循环
    return success_list


def main(users, action=False):
    current_time = get_current_time(action)
    logging.info(f"start time {current_time}, action {'on' if action else 'off'}")
    attempt_times = 0
    usernames, passwords = None, None
    if action:
        usernames, passwords = get_user_credentials(action)
    success_list = [False] * len(users)
    current_dayofweek = get_current_dayofweek(action)
    # today_reservation_num = sum(1 for d in users if current_dayofweek in d.get('daysofweek'))
    while current_time < ENDTIME:
        attempt_times += 1
        # try:
        success_list = login_and_reserve(users, usernames, passwords, action, success_list)
        # 检查哪些用户没有预约成功
        failed_users = [users[i] for i in range(len(users)) if not success_list[i]]
        # except Exception as e:
        #     print(f"An error occurred: {e}")
        print(f"attempt time {attempt_times}, time now {current_time}, success list {success_list}")
        if not failed_users:  # 如果没有失败的用户，结束循环
            print("All reservations are successful!")
            return
        
        if not failed_users:  # 如果所有用户成功预约，结束
            print("All users have successfully reserved!")
            return
          
        current_time = get_current_time(action)
        # if sum(success_list) == today_reservation_num:
        #     print(f"reserved successfully!")
        #     return

def debug(users, action=False):
    logging.info(f"Global settings: \nSLEEPTIME: {SLEEPTIME}\nENDTIME: {ENDTIME}\nENABLE_SLIDER: {ENABLE_SLIDER}\nRESERVE_NEXT_DAY: {RESERVE_NEXT_DAY}")
    suc = False
    logging.info(f" Debug Mode start! , action {'on' if action else 'off'}")
    if action:
        usernames, passwords = get_user_credentials(action)
    current_dayofweek = get_current_dayofweek(action)
    for index, user in enumerate(users):
        username, password, times, roomid, seatid, daysofweek = user.values()
        if type(seatid) == str:
            seatid = [seatid]
        if action:
            username ,password = usernames.split(',')[index], passwords.split(',')[index]
        if(current_dayofweek not in daysofweek):
            logging.info("Today not set to reserve")
            continue
        logging.info(f"----------- {username} -- {times} -- {seatid} try -----------")
        s = reserve(sleep_time=SLEEPTIME,  max_attempt=MAX_ATTEMPT, enable_slider=ENABLE_SLIDER)
        s.get_login_status()
        s.login(username, password)
        s.requests.headers.update({'Host': 'office.chaoxing.com'})
        suc = s.submit(times, roomid, seatid, action)
        if suc:
            return
    

def get_roomid(args1, args2):
    username = input("请输入用户名：")
    password = input("请输入密码：")
    s = reserve(sleep_time=SLEEPTIME, max_attempt=MAX_ATTEMPT, enable_slider=ENABLE_SLIDER, reserve_next_day=RESERVE_NEXT_DAY)
    s.get_login_status()
    s.login(username=username, password=password)
    s.requests.headers.update({'Host': 'office.chaoxing.com'})
    encode = input("请输入deptldEnc：")
    s.roomid(encode)


if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    parser = argparse.ArgumentParser(prog='Chao Xing seat auto reserve')
    parser.add_argument('-u','--user', default=config_path, help='user config file')
    parser.add_argument('-m','--method', default="reserve" ,choices=["reserve", "debug", "room"], help='for debug')
    parser.add_argument('-a','--action', action="store_true",help='use --action to enable in github action')
    args = parser.parse_args()
    func_dict = {"reserve": main, "debug":debug, "room": get_roomid}
    with open(args.user, "r+") as data:
        usersdata = json.load(data)["reserve"]
    func_dict[args.method](usersdata, args.action)
