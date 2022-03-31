import concurrent.futures
import hashlib
import json
import random
import time

import requests
from lxml import etree

req = requests.session()
global_wrggk_url = 'http://wrggk.whvcse.edu.cn/'
global_wrggk_api_url = 'http://wrggka.whvcse.edu.cn/'
global_user_agent = {'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 5.1.1; G011C Build/LMY48Z'}


# 日志记录
def logging(typ='-', text='-'):
    print(f'[{typ}] {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())} {text}')


# 直接对HTML文本执行xpath表达式
def html_xpath(text, xpath):
    tree = etree.HTML(text)
    data = tree.xpath(xpath)
    return data


# 足够随机的User-Agent
'''
random_user_agent()
生成User-Agent的函数。

输入：
    无
输出：
    一条User-Agent（str字符串型）
    Mozilla/5.0 (Windows NT 6.1; Win32; x86; rv:86.0) Gecko/20100101 Firefox/86.0
    或者：
    Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.5486.59 Safari/537.36
'''


def random_user_agent():
    windows_version = ["6.1", "6.2", "6.3", "10.0"]
    windows_platform = random.choice([["64", "64"], ["32", "86"]])
    browser_main_version = f'{random.randrange(76, 98)}'
    return str(random.choices([
        f'Mozilla/5.0 (Windows NT {random.choice(windows_version)}; Win{windows_platform[0]}; '
        f'x{windows_platform[1]}; rv:{browser_main_version}.0) Gecko/20100101 '
        f'Firefox/{browser_main_version}.0',
        f'Mozilla/5.0 (Windows NT {random.choice(windows_version)}; Win{windows_platform[0]}; '
        f'x{windows_platform[1]}) AppleWebKit/537.36 (KHTML, like Gecko) '
        f'Chrome/{browser_main_version}.0.{random.randrange(1111, 9999)}.'
        f'{random.randrange(10, 150)} Safari/537.36']))


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
    # 获取该用户所需的secretKey，虽然我不知道用secretKey来获取secretKey是什么意思啦...
    kkr = req.get(global_wrggk_api_url + '/api/M_User/GetSecret',
                  params={'userName': username, 'accessKey': access_key, 'secretKey': int(time.time()), },
                  headers=global_user_agent).text
    print(kkr)
    secret_key_result = json.loads(kkr)
    if secret_key_result['status'] == '1':
        login_api_result = json.loads(req.get(global_wrggk_api_url + '/api/M_User/Login',
                                              params={'userName': username, 'password': password,
                                                      'accessKey': access_key,
                                                      'secretKey': secret_key_result['message']},
                                              headers=global_user_agent).text)
        if login_api_result['status'] == '1':
            login_web_result = req.get(global_wrggk_url + "auth.aspx",
                                       params={"action": 'login', "username": username, "password": password},
                                       headers=global_user_agent).text
            logging('*', login_web_result[6:] + login_api_result['trueName'] + login_api_result[
                'message'] + '(programer : mightnire@github)')
            return login_api_result
        else:
            logging('!', login_api_result['message'])
            return -1
    else:
        logging('!', secret_key_result['message'])
        return -1


'''
get_undone_courses
获取用户所有状态为“学习中”的课程信息。

返回值：
    [{'courseName': '美国历史与文化', 'courseId': '939', 'CourseClassId': '692'}, 
    {'courseName': '海洋文明', 'courseId': '930', 'CourseClassId': '683'}, 
    {'courseName': '武器发展简史', 'courseId': '925', 'CourseClassId': '678'}]
'''


def get_undone_courses(userid):
    courses = []
    course_result = req.get(global_wrggk_url + 'web/MyCourse.aspx', headers=global_user_agent).text
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
    print(courses)
    return courses


def get_unwatched_video_or_exam(courseId, CourseClassId, mode):
    course_learn_page = req.get(f'{global_wrggk_url}/Web/CourseInfo.aspx?id={courseId}&cid={CourseClassId}',
                                headers=global_user_agent).text
    if mode == 'video':
        videos = [video for video in html_xpath(course_learn_page, '//*[@class="h4 c-font-normal"]/a/@href') if
                  '/Viewer' in video]
        logging('*', f'该课程获取到 {len(videos)} 条视频观看链接')
        print(videos)
        return videos
    else:
        exams = [exam for exam in html_xpath(course_learn_page, '//*[@class="c-font-normal"]/a/@href') if
                 '/Viewer' in exam]
        logging('*', f'该课程获取到 {len(exams)} 条考试链接')
        return exams


def turn_video_to_request_then_play_it(video_url):
    video_time = str(int(random.randint(10000, 100000)))
    thread = str(int(random.randint(1, 9)))
    video_url_info = []
    for video_info in video_url.split('&'):
        video_url_info.append(video_info.split('=')[1])
    video_time_request = f'{global_wrggk_url}/Viewer/timetop.aspx?cpid={video_url_info[3]}' \
                         f'&bjtime={str(video_time)}' \
                         f'&courseid={video_url_info[1]}&stepid={video_url_info[3]} &courseClassId={video_url_info[4]}&t=60'
    logging(f'thread{thread}', video_time_request + str(time.time()))
    video_request = req.get(video_time_request, headers=global_user_agent)
    logging(f'thread{thread}', video_request.text + str(time.time()))
    if '1' in video_request.text:
        logging(f'thread{thread}', "Done! Exiting..." + str(time.time()))
        return True
    else:
        return False


def turn_video_to_request_then_play_it_old(video_url):
    video_time = str(int(random.randint(100000, 1000000)))
    thread = str(int(random.randint(1, 9)))
    video_play_page = req.get(f'{global_wrggk_url}{video_url}', headers=global_user_agent).text
    video_control_script = html_xpath(video_play_page, '/html/body/script[1]/text()')[0]
    video_time_request = video_control_script[video_control_script.find('jQuery.post("'):]
    video_time_request = global_wrggk_url + video_time_request[13:video_time_request.find('" + flga);')] + '60'
    video_time_request = video_time_request.replace('" + playerOther.video.time + "',
                                                    video_time)
    logging(f'thread{thread}', video_time_request)
    video_request = req.get(video_time_request, headers=global_user_agent)
    video_result = json.loads(video_request.text)
    if video_result['BaseType'] == '1':
        logging(f'thread{thread}', "Done! Exiting..." + str(time.time()))
        return True
    else:
        return False


def from_course_list_2_done(course):
    thread = str(int(random.randint(1, 9)))
    logging(f'thread{thread}', course['courseName'])
    unwatched_videos = get_unwatched_video_or_exam(courseId=course['courseId'],
                                                   CourseClassId=course['CourseClassId'], mode='video')
    unwatched_exams = get_unwatched_video_or_exam(courseId=course['courseId'],
                                                  CourseClassId=course['CourseClassId'], mode='exam')
    logging('exams', unwatched_exams)
    logging(f'thread{thread}', unwatched_videos)
    threads = min(100, len(unwatched_videos))
    if threads:
        with concurrent.futures.ThreadPoolExecutor(threads) as executor:
            executor.map(turn_video_to_request_then_play_it, unwatched_videos)
            # executor.map(turn_video_to_request_then_play_it_old, unwatched_videos)
    else:
        logging(f'thread{thread}', "Nothing to do!")
    logging(f'thread{thread}', 'Thread Exit!' + str(time.time()))


def main(username, password):
    global_user_agent['User-Agent'] = random_user_agent()
    login_status = login_t(username, password)
    logging('i', login_status)
    if login_status != -1:
        # course_list = get_undone_courses(login_status['uid'])
        course_list = [{'courseName': '美国历史与文化', 'courseId': '939', 'CourseClassId': '692'},
                       {'courseName': '西方文化史', 'courseId': '928', 'CourseClassId': '681'},
                       {'courseName': '中国史纲要', 'courseId': '918', 'CourseClassId': '671'},
                       {'courseName': '儿童与心理', 'courseId': '907', 'CourseClassId': '660'},
                       {'courseName': '植物与生命', 'courseId': '932', 'CourseClassId': '685'},
                       {'courseName': '哲学导论', 'courseId': '926', 'CourseClassId': '679'},
                       {'courseName': '中国文化地理', 'courseId': '915', 'CourseClassId': '668'},
                       {'courseName': '设计美学', 'courseId': '913', 'CourseClassId': '666'},
                       {'courseName': '海洋文明', 'courseId': '930', 'CourseClassId': '683'},
                       {'courseName': '从水浒看刑法', 'courseId': '897', 'CourseClassId': '650'},
                       {'courseName': '化学与人类文明', 'courseId': '933', 'CourseClassId': '686'},
                       {'courseName': '中国古代科技发展史', 'courseId': '920', 'CourseClassId': '673'},
                       {'courseName': '西方绘画艺术', 'courseId': '934', 'CourseClassId': '687'},
                       {'courseName': '中国建筑文化史', 'courseId': '927', 'CourseClassId': '680'},
                       {'courseName': '摄影艺术', 'courseId': '936', 'CourseClassId': '689'},
                       {'courseName': '武器发展简史', 'courseId': '925', 'CourseClassId': '678'},
                       {'courseName': '数学与人类文明', 'courseId': '905', 'CourseClassId': '658'},
                       {'courseName': '认识电影', 'courseId': '901', 'CourseClassId': '654'},
                       {'courseName': '印度文明', 'courseId': '899', 'CourseClassId': '652'},
                       {'courseName': '营销的方法与艺术', 'courseId': '931', 'CourseClassId': '684'},
                       {'courseName': '认识大脑：脑科学导论', 'courseId': '906', 'CourseClassId': '659'},
                       {'courseName': '中国传统养生文化', 'courseId': '929', 'CourseClassId': '682'},
                       {'courseName': '中国传统文化', 'courseId': '923', 'CourseClassId': '676'},
                       {'courseName': '灯彩概论', 'courseId': '902', 'CourseClassId': '655'},
                       {'courseName': '管理的原理与方法', 'courseId': '896', 'CourseClassId': '649'},
                       {'courseName': '世界现代舞蹈艺术', 'courseId': '903', 'CourseClassId': '656'},
                       {'courseName': '中国现当代文学作品欣赏', 'courseId': '900', 'CourseClassId': '653'},
                       {'courseName': '中国哲学史', 'courseId': '898', 'CourseClassId': '651'}]
        logging('i', course_list)
        if course_list != '':
            threads = min(10, len(course_list))
            if threads:
                with concurrent.futures.ThreadPoolExecutor(threads) as executor:
                    executor.map(from_course_list_2_done, course_list)
            else:
                logging('!', "Nothing to do!")
    logging('!', "Almost Done! (programer : mightnire@github)")


def fetch_all_exams(username, password):
    all_exams = []
    all_exams_login_url = []
    global_user_agent['User-Agent'] = random_user_agent()
    url = 'http://wrggk.whvcse.edu.cn/Viewer/CourseExam.aspx?id=901&sid=10517&mid=3391&courseClassId=654&chapterId=10517'  # &pid=0ea5c0c5-af42-4166-be80-714879e770c5'
    login_status = login_t(username, password)
    logging('i', login_status)
    if login_status != -1:
        # course_list = get_undone_courses(login_status['uid'])
        course_list = [{'courseName': '美国历史与文化', 'courseId': '939', 'CourseClassId': '692'},
                       {'courseName': '西方文化史', 'courseId': '928', 'CourseClassId': '681'},
                       {'courseName': '中国史纲要', 'courseId': '918', 'CourseClassId': '671'},
                       {'courseName': '儿童与心理', 'courseId': '907', 'CourseClassId': '660'},
                       {'courseName': '植物与生命', 'courseId': '932', 'CourseClassId': '685'},
                       {'courseName': '哲学导论', 'courseId': '926', 'CourseClassId': '679'},
                       {'courseName': '中国文化地理', 'courseId': '915', 'CourseClassId': '668'},
                       {'courseName': '设计美学', 'courseId': '913', 'CourseClassId': '666'},
                       {'courseName': '海洋文明', 'courseId': '930', 'CourseClassId': '683'},
                       {'courseName': '从水浒看刑法', 'courseId': '897', 'CourseClassId': '650'},
                       {'courseName': '化学与人类文明', 'courseId': '933', 'CourseClassId': '686'},
                       {'courseName': '中国古代科技发展史', 'courseId': '920', 'CourseClassId': '673'},
                       {'courseName': '西方绘画艺术', 'courseId': '934', 'CourseClassId': '687'},
                       {'courseName': '中国建筑文化史', 'courseId': '927', 'CourseClassId': '680'},
                       {'courseName': '摄影艺术', 'courseId': '936', 'CourseClassId': '689'},
                       {'courseName': '武器发展简史', 'courseId': '925', 'CourseClassId': '678'},
                       {'courseName': '数学与人类文明', 'courseId': '905', 'CourseClassId': '658'},
                       {'courseName': '认识电影', 'courseId': '901', 'CourseClassId': '654'},
                       {'courseName': '印度文明', 'courseId': '899', 'CourseClassId': '652'},
                       {'courseName': '营销的方法与艺术', 'courseId': '931', 'CourseClassId': '684'},
                       {'courseName': '认识大脑：脑科学导论', 'courseId': '906', 'CourseClassId': '659'},
                       {'courseName': '中国传统养生文化', 'courseId': '929', 'CourseClassId': '682'},
                       {'courseName': '中国传统文化', 'courseId': '923', 'CourseClassId': '676'},
                       {'courseName': '灯彩概论', 'courseId': '902', 'CourseClassId': '655'},
                       {'courseName': '管理的原理与方法', 'courseId': '896', 'CourseClassId': '649'},
                       {'courseName': '世界现代舞蹈艺术', 'courseId': '903', 'CourseClassId': '656'},
                       {'courseName': '中国现当代文学作品欣赏', 'courseId': '900', 'CourseClassId': '653'},
                       {'courseName': '中国哲学史', 'courseId': '898', 'CourseClassId': '651'}]
        logging('i', course_list)
        for course in course_list:
            logging('!', course['courseName'])
            for exam in get_unwatched_video_or_exam(courseId=course['courseId'], CourseClassId=course['CourseClassId'],
                                                    mode='exam'):
                exam_page = req.get(url=f'{global_wrggk_url}{exam}', headers=global_user_agent).text
                exam_url = html_xpath(exam_page, '//*[@id="exam_page"]/iframe')[0].get('src')
                # exams_login_file.writelines(f'{exam_url}\n')
                exam_id = exam_url.split("&paperid=")[-1].split("&")[0]
                test_area = req.get(url=f'{exam_url}&view=1', headers=global_user_agent).text.replace(
                    'style="display: none"', '').replace(login_status['trueName'], 'Mightnire').replace(
                    '<font color="red">',
                    '<font color="red">-1</font><font color="red" style="display: none">').replace('<head>',
                                                                                                   '<head>\n    <meta charset="UTF-8">\n <meta http-equiv="X-UA-Compatible" content="IE=edge">\n <meta name="viewport" content="width=device-width, initial-scale=1.0">')
                with open(f'{exam_id}.html', 'w', encoding='UTF-8') as file:
                    file.writelines(test_area)
                logging('!', f'{exam_id}.html 写入成功！')
                print(exam_url)

        # for course in course_list:
        #     logging('!', course['courseName'])
        #     all_exams.extend(
        #         get_unwatched_video_or_exam(courseId=course['courseId'], CourseClassId=course['CourseClassId'],
        #                                     mode='exam'))
        #     break
        # all_exams = set(all_exams)
        # # exam_file = open('allexams.txt','w')
        # # exams_login_file = open('allexamlogin.txt','w')
        # for exam in all_exams:
        #     # exam_file.writelines(f'{global_wrggk_url}{exam}\n')
        #     exam_page = req.get(url=f'{global_wrggk_url}{exam}', headers=global_user_agent).text
        #     exam_url = html_xpath(exam_page, '//*[@id="exam_page"]/iframe')[0].get('src')
        #     # exams_login_file.writelines(f'{exam_url}\n')
        #     exam_id = exam_url.split("&paperid=")[-1].split("&")[0]
        #     test_area = req.get(url=f'{exam_url}&view=1', headers=global_user_agent).text.replace(
        #         'style="display: none"', '').replace(login_status['trueName'], 'Mightnire').replace(
        #         '<font color="red">',
        #         '<font color="red">-1</font><font color="red" style="display: none">').replace('<head>',
        #                                                                                            '<head>\n    <meta charset="UTF-8">\n <meta http-equiv="X-UA-Compatible" content="IE=edge">\n <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        #     with open(f'{exam_id}.html', 'w', encoding='UTF-8') as file:
        #         file.writelines(test_area)
        #     logging('!', f'{exam_id}.html 写入成功！')
        #     print(exam_url)
        #     break


def fetch_all_answer():
    pass


if __name__ == '__main__':
    # for uid in range(,):
    #     main(str(uid), '')

    fetch_all_exams('', '')

    # 用于获取大量账号课程信息的测试代码
    # course_list = []
    # for username in range(2020010101, 2020010222):
    #     login_status = login_t(str(username), 'Default Password')
    #     logging('!', login_status)
    #     if login_status != -1:
    #         course_list.extend(get_undone_courses(login_status['uid']))
    # print('--------------')
    # print(course_list)
    # print(len(course_list))
    # with open('result.txt', 'w') as file:
    #     file.writelines(str(course_list))
