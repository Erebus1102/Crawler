import os
import time
import pandas as pd
import random  
from DrissionPage import WebPage
from DrissionPage.common import Actions
from DrissionPage.errors import ElementNotFoundError, ElementLostError

wp = WebPage()
wp.get('https://www.xiaohongshu.com')
wp.wait.doc_loaded()

ac = Actions(wp)

all_data = []
info = []

total_scroll = 0
max_scroll = 20000

search_keyword = "伥鬼朋友"  # 关键词可修改
search_input = wp.ele('xpath://input[@id="search-input"]')
if search_input:
    search_input.click()
    search_input.input(search_keyword)
    
    time.sleep(2)

    search_button = wp.ele('xpath://div[@class="input-button"]')
    if search_button:
        search_button.click()
else:
    print("未找到搜索框，将直接爬取首页内容")

time.sleep(5)

wp.listen.start(['web/v1/search/notes', 'api/sns/web/v1/feed'])

while total_scroll < max_scroll:
    packet = wp.listen.wait()
    elements = wp.eles('xpath://a[@class="cover ld mask"]')
    
    for index, element in enumerate(elements):
        try:
            href = element.attr('href')  # 尝试获取 href 属性
        except ElementLostError:
            print(f"第 {index + 1} 个元素已失效，跳过")
            continue  
        
        if href not in info:
            info.append(href)
            try:
                wp.run_js('arguments[0].click();', element)
            except Exception as e:
                print(f"无法点击第 {index + 1} 个元素 (href: {href}): {e}")
                continue

            try:
                wp.wait.ele_displayed('xpath://div[@class="note-detail-mask"]', timeout=5)
            except ElementNotFoundError:
                print(f"第 {index + 1} 个元素 (href: {href}) 页面加载超时，跳过")
                continue

            title = content = ''
            comments = []
            
            try:
                title = wp.ele('xpath://div[@class="note-detail-mask"]//div[@id="noteContainer"]//div[contains(@class, "title")]').text
            except ElementNotFoundError:
                print(f"第 {index + 1} 个元素 (href: {href}) 未找到标题")
            
            try:
                content = wp.ele('xpath://div[@class="note-detail-mask"]//div[@id="noteContainer"]//div[contains(@class, "desc")]//span[@class="note-text"]').text
            except ElementNotFoundError:
                print(f"第 {index + 1} 个元素 (href: {href}) 未找到内容")
            
            try:
                comment_elements = wp.eles('xpath://div[@class="note-detail-mask"]//div[@id="noteContainer"]//div[@class="comments-el"]//div[@class="parent-comment"]//div[@class="comment-item"]//div[@class="right"]//span[@class="note-text"]')
                comments = [comment.text for comment in comment_elements]
            except ElementNotFoundError:
                print(f"第 {index + 1} 个元素 (href: {href}) 未找到评论")

            if title or content or comments:
                data = [title, content] + comments
                all_data.append(data)
                print(f"已抓取第 {index + 1} 个元素 (href: {href}): 标题: {title}, 内容: {content[:30]}..., 评论数: {len(comments)}")
            else:
                print(f"第 {index + 1} 个元素 (href: {href}) 没有有效数据")
            
            try:
                wp.ele('xpath://div[@class="close close-mask-dark"]').click(by_js=True)
            except Exception as e:
                print(f"无法关闭第 {index + 1} 个元素 (href: {href}) 的详情页: {e}")
                wp.run_js('document.querySelector(".close.close-mask-dark").click();')
            
            # 生成一个介于 1 和 5 秒之间的随机整数  
            wait_time = random.randint(2, 5)
            time.sleep(wait_time)

    ac.scroll(delta_y=1000)
    total_scroll += 1000
    time.sleep(1.5)  

    print(f"已滚动 {total_scroll} 像素")

max_comments = max(len(row) - 2 for row in all_data) if all_data else 0
columns = ['标题', '内容'] + [f'评论{i+1}' for i in range(max_comments)]
df = pd.DataFrame(all_data, columns=columns)

if not os.path.exists('data'):
    os.makedirs('data')

file_name = f"data/{search_keyword}_result.xlsx"

df.to_excel(file_name, index=False, engine='openpyxl')
print(f"数据已保存到 '{file_name}' 文件中")