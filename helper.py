import requests
from lxml import etree
import json
import time
import hashlib
import random
import concurrent.futures

req = requests.session()
WRGGK_URL = 'http://wrggk.whvcse.edu.cn/'
WRGGK_API_URL = 'http://wrggka.whvcse.edu.cn/'
UA = {'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 5.1.1; G011C Build/LMY48Z'}


# def login(session, username, password='1111', ua=None):
#     login_load = {"action": 'login', "username": username, "password": password}
#     login_request = session.get("http://wrggk.whvcse.edu.cn/auth.aspx", params=login_load, headers=ua)
#     if 'SUC' in login_request.text:
#         soup = BeautifulSoup(session.get("http://wrggk.whvcse.edu.cn/web/MyCourse.aspx").text,
#                              "html.parser")  # , from_encoding='utf-8')
#         Name = [_a.get_text() for _a in soup.find_all(name='a', attrs={'class': 'sf-with-ul'})]  # get name
#         return (username, Name[1].strip(), "Log in.")
#     else:
#         return ("Error:", login_request.text)

# 日志记录
def logging(typ='-', text='-'):
    print(f'[{typ}] {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())} {text}')


# 直接对HTML文本执行xpath表达式
def html_xpath(text, xpath):
    tree = etree.HTML(text)
    data = tree.xpath(xpath)
    return data


# 随机User-Agent
def random_user_agent():
    windows_version = ["6.1", "6.2", "10.0"]
    windows_platform = random.choice([["64", "64"], ["32", "86"]])
    chrome_version = f'{random.randrange(76, 97)}.0.{random.randrange(1111, 9999)}.{random.randrange(10, 99)}'
    ua = f'Mozilla/5.0 (Windows NT {random.choice(windows_version)}; Win{windows_platform[0]}; x{windows_platform[1]}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36'
    return ua


'''
login_t
登录函数，同时登录网页端和客户端。

输入：（username=用户名，password=密码）

输出：
    如果登录成功：
        返回类似下面的字典：
            {'uid': '用户ID', 'userImageURL': '头像地址', 'userName': '用户名（学号）', 'userEmail': '用户邮箱', 
            'trueName': '真实姓名', 'status': '登录状态（1）', 'message': '信息（登录成功）'}
    否则：
        返回 -1
'''


def login_t(username, password):
    logging('!', '以' + username + ':' + password + '登录网站')
    access_key = hashlib.md5(str(f'{username}:{password}').encode('UTF-8')).hexdigest()
    try:
        # 获取该用户所需的secretKey，虽然我不知道用secretKey来获取secretKey是什么意思啦...
        kkr = req.get(WRGGK_API_URL + '/api/M_User/GetSecret',
                      params={'userName': username, 'accessKey': access_key, 'secretKey': int(time.time()), },
                      headers=UA).text
        print(kkr)
        secret_key_result = json.loads(kkr)
        if secret_key_result['status'] == '1':
            login_api_result = json.loads(req.get(WRGGK_API_URL + '/api/M_User/Login',
                                                  params={'userName': username, 'password': password,
                                                          'accessKey': access_key,
                                                          'secretKey': secret_key_result['message']}, headers=UA).text)
            if login_api_result['status'] == '1':
                login_web_result = req.get(WRGGK_URL + "auth.aspx",
                                           params={"action": 'login', "username": username, "password": password},
                                           headers=UA).text
                logging('*', login_web_result[6:] + login_api_result['trueName'] + login_api_result['message'] + (programer : mightnire@github))
                return login_api_result
            else:
                logging('!', login_api_result['message'])
                return -1
        else:
            logging('!', secret_key_result['message'])
            return -1
    except:
        logging('!', '请先联网')
        return -1


# GET /api/M_User/GetSecret?userName=2020030826&accessKey=1&secretKey=1
# GET /api/M_User/Login?username=2020030826&password=000009&accessKey=1&secretKey=1
# [{'courseName': '国学概要', 'courseId': '859', 'CourseClassId': '627'}]
# wrggk.whvcse.edu.cn/Web/CourseInfo.aspx?id=859&cid=627

def get_undone_course(userid):
    courses = []
    course_result = req.get(WRGGK_URL + 'web/MyCourse.aspx', headers=UA).text
    # 这里content1是指未完成的课程，而content2就是已完成的课程啦
    #                                                   ↓ 就在这里
    for course in html_xpath(course_result, '//*[@id="content1"]/div/div[2]/div[2]/div[2]/a'):
        courses.append(
            {'courseName': course.xpath('./../../../div[1]/a/text()')[0],
             'courseId': course.xpath('./@href')[0][
                         course.xpath('./@href')[0].find('?id=') + 4:course.xpath('./@href')[0].find('&cid=')],
             'CourseClassId': course.xpath('./@href')[0][course.xpath('./@href')[0].find('&cid=') + 5:]}
        )
        logging('!', '发现未学课程 ' + courses[-1]['courseName'])
    logging('*', '未学课程共 ' + str(len(courses)) + ' 条')
    return courses


def get_unwatched_video(courseId, CourseClassId):
    course_learn_page = req.get(f'{WRGGK_URL}/Web/CourseInfo.aspx?id={courseId}&cid={CourseClassId}', headers=UA).text
    videos = [video for video in html_xpath(course_learn_page, '//*[@class="h4 c-font-normal"]/a/@href') if
              '/Viewer' in video]
    logging('*', f'该课程获取到 {len(videos)} 条视频观看链接')
    return videos


def turn_video_to_request_then_play_it(video_url):
    video_time = str(int(random.randint(100000, 1000000)))
    thread = str(int(random.randint(1111, 9999)))
    video_url_info = []
    for video_info in video_url.split('&'):
        video_url_info.append(video_info.split('=')[1])
    video_time_request = f'{WRGGK_URL}/Viewer/timetop.aspx?cpid={video_url_info[3]}' \
                         f'&bjtime={str(video_time)}' \
                         f'&courseid={video_url_info[1]}&stepid={video_url_info[3]} &courseClassId={video_url_info[4]}&t=60'
    logging(f'thread{thread}', video_time_request)
    video_request = req.get(video_time_request, headers=UA)
    logging(f'thread{thread}', video_request.text)
    if '1' in video_request.text:
        logging(f'thread{thread}', "Done! Exiting...")
        return True
    else:
        return False


def turn_video_to_request_then_play_it_old(video_url):
    video_time = str(int(random.randint(100000, 1000000)))
    thread = str(int(random.randint(111, 999)))
    video_play_page = req.get(f'{WRGGK_URL}{video_url}', headers=UA).text
    video_control_script = html_xpath(video_play_page, '/html/body/script[1]/text()')[0]
    video_time_request = video_control_script[video_control_script.find('jQuery.post("'):]
    video_time_request = WRGGK_URL + video_time_request[13:video_time_request.find('" + flga);')] + '60'
    video_time_request = video_time_request.replace('" + playerOther.video.time + "',
                                                    video_time)
    logging(f'thread{thread}', video_time_request)
    video_request = req.get(video_time_request, headers=UA)
    video_result = json.loads(video_request)
    if video_result['BaseType'] == '1':
        logging(f'thread{thread}', "Done! Exiting...")
        return True
    else:
        return False


def from_course_list_2_done(course):
    thread = str(int(random.randint(11, 99)))
    logging(f'thread{thread}', course['courseName'])
    unwatched_videos = get_unwatched_video(courseId=course['courseId'],
                                           CourseClassId=course['CourseClassId'])
    logging(f'thread{thread}', unwatched_videos)
    threads = min(10, len(unwatched_videos))
    if threads:
        with concurrent.futures.ThreadPoolExecutor(threads) as executor:
            executor.map(turn_video_to_request_then_play_it, unwatched_videos)
            # executor.map(turn_video_to_request_then_play_it_old, unwatched_videos)
    else:
        logging(f'thread{thread}', "Nothing to do!")
    logging(f'thread{thread}', 'Thread Exit!')


def main(username, password):
    UA['User-Agent'] = random_user_agent()
    login_status = login_t(username, password)
    logging('i', login_status)
    if login_status != -1:
        course_list = get_undone_course(login_status['uid'])
        logging('i', course_list)
        if course_list != '':
            threads = min(5, len(course_list))
            if threads:
                with concurrent.futures.ThreadPoolExecutor(threads) as executor:
                    executor.map(from_course_list_2_done, course_list)
            else:
                logging('!', "Nothing to do!")
    logging('!',"Almost Done! (programer : mightnire@github)")

if __name__ == '__main__':
    main('2020030816', 'whrj123456!@')
