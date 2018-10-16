# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from builtins import open

import time

from inscrawler import InsCrawler
import sys
import argparse
import json
from io import open
import pymysql

def usage():
    return '''
        python crawler.py posts -u cal_foodie -n 100 -o ./output
        python crawler.py posts_full -u cal_foodie -n 100 -o ./output
        python crawler.py profile -u cal_foodie -o ./output
        python crawler.py hashtag -t taiwan -o ./output

        The default number for fetching posts via hashtag is 100.
    '''


def connect_db():
    return pymysql.connect(host='localhost',
                           port=3306,
                           user='root',
                           # password='12345678',
                           database='kasama',
                           autocommit=True,
                           charset='utf8mb4')


con = connect_db()


def insert_row(table_name, column_names, values_format, values):
    if len(values) == 0:
        print('no row!')
        return

    cur = con.cursor();
    try:
        sql_str = "REPLACE INTO {0}({1}) VALUES({2})".format(table_name, column_names, values_format)
        print('=============')
        print(sql_str)
        print(values)
        insert_count = cur.executemany(sql_str, values)
        con.commit()
        if insert_count > 0:
            return cur.lastrowid
        else:
            return 0
    except Exception as e:
        print(e)
        con.rollback()
        print('===================insert operation error')
        raise
    finally:
        cur.close();


def get_posts_by_user(username, number, detail, debug):
    ins_crawler = InsCrawler(has_screen=debug)
    return ins_crawler.get_user_posts(username, number, detail)


def get_profile(username):
    ins_crawler = InsCrawler()
    return ins_crawler.get_user_profile(username)


def get_posts_by_hashtag(tag, number):
    ins_crawler = InsCrawler()
    return ins_crawler.get_latest_posts_by_tag(tag, number)


def arg_required(args, fields=[]):
    for field in fields:
        if not getattr(args, field):
            parser.print_help()
            sys.exit()


def output(data, filepath, tag):
    if tag == 'philippinespoverty':
        tag = 'philippineslending'
    # 保存到数据库
    cur_time = int(round(time.time() * 1000))
    for post in data:
        content = post['content']
        if tag == 'philippineslending':
            content.replace('#philippinespoverty', '#philippineslending')
        last_row_id = insert_row('t_post',
                   'tag_name, jhi_key, datetime,author_avatar,author_name,content,create_date',
                   '%s, %s, %s, %s, %s, %s, %s',
                   [(tag, post['key'], post['datetime'], post['author_avatar'], post['author_name'],
                   post['content'], cur_time)])
        if last_row_id == 0:
            continue
        # 插入图片
        if 'img_urls' in post:
            for img_url in post['img_urls']:
                insert_row('t_post_image_url',
                           'img_url, post_id',
                           '%s, %s',
                           [(img_url, last_row_id)])
        # 插入跟帖
        if 'comments' in post:
            for comment in post['comments']:
                insert_row('t_post_comment',
                           'author, jhi_comment, post_id',
                           '%s, %s, %s',
                           [(comment['author'], comment['comment'], last_row_id)])
    # 保存到文本文件
    # out = json.dumps(data, ensure_ascii=False)
    # if filepath:
    #     with open(filepath, 'w', encoding='utf8') as f:
    #         f.write(out)
    # else:
    #     print(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Instagram Crawler',
                                     usage=usage())
    parser.add_argument('mode',
                        help='options: [posts, posts_full, profile, hashtag]')
    parser.add_argument('-n', '--number',
                        type=int,
                        help='number of returned posts')
    parser.add_argument('-u', '--username',
                        help='instagram\'s username')
    parser.add_argument('-t', '--tag',
                        help='instagram\'s tag name')
    parser.add_argument('-o', '--output', help='output file name(json format)')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.mode in ['posts', 'posts_full']:
        arg_required('username')
        output(
            get_posts_by_user(
                args.username,
                args.number,
                args.mode == 'posts_full',
                args.debug
            ),
            args.output)
    elif args.mode == 'profile':
        arg_required('username')
        output(get_profile(args.username), args.output)
    elif args.mode == 'hashtag':
        arg_required('tag')
        param_tag = args.tag
        tags = ['philippinescar','philippinespoverty','philippineswedding', 'philippinestravel', 'philippinesshopping', 'philippinesinsurance','philippinesparty']
        for tag in tags:
            print('tag:-----'+tag)
            output(
                get_posts_by_hashtag(tag, args.number or 100), args.output, tag)
    else:
        usage()
