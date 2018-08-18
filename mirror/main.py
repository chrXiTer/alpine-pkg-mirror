# -*- coding: utf-8 -*-

__VERSION__ = '0.1.0'

import os
import sys
import json

from packages import click
from utils import get_file
from repositories import Repository
from multiprocessing import Pool

filePath=os.path.abspath(__file__)
print(filePath)
currDir = os.path.dirname(filePath)
print(currDir)
if os.path.isfile(currDir):
    currDir = os.path.dirname(currDir)
    print(currDir)
print("3333")
DEFAULT_CONFIG_PATH=os.path.join(currDir , '../.repositories.json')

@click.group()
@click.option('-c', '--config', type=click.File('r'), 
            default=DEFAULT_CONFIG_PATH, help='the path to configuration file (.repositories.json)')
@click.version_option(__VERSION__)
@click.pass_context
def cli(ctx, config):
    ''' command line interface to Alpine package mirrorer
    '''
    ctx.obj = dict()
    ctx.obj['current_path'] = currDir
    try:
        ctx.obj['repositories'] = json.load(config)
    except IOError as err:
        print >> sys.stderr, '[ERROR] Cannot parse the configuration file, %s [%s]' % (config, err)
        sys.exit(1)

def downAGroup(urlPaths):
    try:
        pid = os.getpid()
        print("子进程 {0} 开始".format(pid))
        for item in urlPaths:
            print("[NEW {0}] {1}".format(pid, item["url"]))
            get_file(item["url"], item["path"])
        print("子进程结束")
    except Exception as e:
        msg = "子进程错误:%s" % e
        print(msg)

def getRepo(ctx, repository):
    if repository not in ctx.obj['repositories']:
        print('[ERROR] The repository does not exist, %s' % repository, file=sys.stderr)
        sys.exit(1)
    try:
        mirror_path = os.path.realpath(
            os.path.join(ctx.obj['current_path'],ctx.obj['repositories'][repository]['mirror-path'])
        )
    except KeyError  as err:
        print >> sys.stderr, '[ERROR] Incorrect repositories configuration file, repository: %s [%s]' % (repository, err)
        sys.exit(1)
    repo = Repository(repository, mirror_path, **ctx.obj['repositories'][repository])
    return repo


@cli.command()
@click.argument('repository')
@click.pass_context
def clean(ctx, repository):
    repo = getRepo(ctx, repository)
    repo.deleteOld()

@cli.command()
@click.argument('repository')
@click.pass_context
def update(ctx, repository):
    ''' update repository(-ies)
    '''
    repo = getRepo(ctx, repository)
    get_file(repo.index_url, repo._index_path)
    threadNum = 20
    urlPathGroup = repo.getNeedUrlPathsNGroup(threadNum)
    po=Pool(threadNum)
    for i in range(0, threadNum):
        po.apply_async(downAGroup, args=(urlPathGroup[i],))
    po.close() #关闭进程池， 关闭后po不再接收新的请求
    po.join() #等待po中所有⼦进程执⾏完成， 必须放在close语句之后
    print("父进程结束")


    