import os

from subprocess import getoutput, run
from slackbot.bot import respond_to
from glob import glob
from datetime import datetime
from multiprocessing import Process, Queue


@respond_to('help')
def helper(message):
    message.reply('\n'
                  'diff [-p(pull)] filename: filename同士のdiffを取る\n'
                  'error [Code]:エラーコードの詳細表示\n'
                  'ls:ディレクトリの中身を表示\n'
                  'のいずれかを入力してください。')


@respond_to('error(.*)')
def error_helper(message, something=''):
    error_code = int(something.strip())
    if error_code == 1:
        message.reply('エラーコード1:\n'
                      '指定されたファイル名が見つからなかった為、diffを取ることができませんでした。\n'
                      'ファイル名を今一度ご確認ください。')
    elif error_code == 2:
        message.reply(
            'エラーコード2:\n'
            '指定されたファイル名が *1つしか* 見つからなかった為、diffを取ることができませんでした。\n'
            '異なるディレクトリに同じ名前のファイルが複数存在しているか確認してください。')
    else:
        message.reply('そのようなエラー（コード' + str(error_code) + '）はありません。')


@respond_to('diff(.*)')
def diff(message, something=''):
    if something == 'bot':
        return
    if '-p' in something.strip().split(' ')[0]:
        message.reply('ファイル同期(pull)中です。')
        pull(glob('../*[a-z]/'))
        message.reply('同期完了')
    filename_in = something.strip().split(' ')[-1]
    files = set(glob('../*[a-z]/' + filename_in))
    if len(filename_in) < 1 or len(files) < 1:
        message.reply('`エラー` コード *1* :ファイルが無い')
        return
    if len(files) < 2:
        message.reply('`エラー` コード *2* :ファイルが足りない')
        return

    message.reply('今からdiffを取ります。')

    q = Queue()

    def _diff(f1, f2):
        output = getoutput('diff {0} {1}'.format(f1, f2))
        if output:
            # q.put(output)
            q.put('{0} : {1}\n{2}'.format(f1, f2, output))
        else:
            q.put((f1, f2))
        q.close()

    from itertools import combinations
    processes = [Process(target=_diff, args=(f1, f2)) for (f1, f2) in combinations(sorted(files), 2)]

    for p in processes:
        p.start()

    outputs = []
    for _ in processes:
        outputs.append(q.get())
    reply_strlist = ['{0} と {1} は全く同じです!! :+1:'.format(f1.split('/', 1)[1], f2.split('/', 1)[1])
                     for (f1, f2) in filter(lambda e: not isinstance(e, str), outputs)]
    message.reply('\n'.join(reply_strlist))

    outputs = list(filter(lambda e: isinstance(e, str) and e, outputs))
    if not outputs:
        return

    nowdate = datetime.now().strftime("%Y_%m_%d %H-%M-%S").split(' ')
    output_filename = nowdate[0] + '/' + nowdate[1] + filename_in
    output_dir = '../output0/' + nowdate[0]
    run(args=['mkdir', '-p', output_dir])
    output_path = '../output0/' + output_filename
    print('\n'.join(outputs), file=open(output_path, mode='w'))

    push('output0')
    message.reply(
        '相違があったファイル同士のdiff結果は別のテキストファイルに書き出しました。\n'
        'ファイルはここにあります。\n'
        'https://github.com/kamuiroeru/SyncRepository00/blob/master/' + output_filename)


def pull(lis):
    lis.remove('../diffbot/')
    lis.remove('../diff_bot/')

    def _pull(path):
        os.chdir(path)
        run(args=['git', 'pull', 'origin', 'master'])

    processes = [Process(target=_pull, args=(file.rsplit('/', 1)[0],)) for file in lis]
    for p in processes:
        p.start()
    for p in processes:
        p.join()


def push(s=''):
    os.chdir('../' + s)
    run(args=['git', 'add', '.'])
    run(args=['git', 'commit', '-m', '"hoge"'])
    run(args=['git', 'push', 'origin', 'master'])
    os.chdir('../diffbot')


@respond_to('ls(.*)')
def ls(message, something):
    message.reply(getoutput('ls ../' + str(something.strip())))
