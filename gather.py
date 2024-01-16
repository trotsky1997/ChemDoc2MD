import glob
import re
import json
import tqdm

def split_exam_paper_correctly(text):
    # 使用特殊分隔符替换所有找到的题号
    pattern = r'(\n\*\d+\*\。|\n\*\d+\*、|\n\d+\。|\n\d+、|\n\n\d+\.|\n\d+、|\n\d+．|\n\*\*\d+\*\*\.|\ \d+．|\n\*\*\d+．|\n\d+\\\.|\*\*\d+、|\n【例\d+】|\n【训\d+】|\n\ \d+、|\n\*\*\d+\*\*．)'
    separator = "||||||||||||||"
    text_with_separators = re.sub(pattern, r'\1' + separator, text)

    # 使用分隔符切分文本
    parts = text_with_separators.split(separator)

    # 清理并返回结果
    questions = [part.strip() for part in parts if part.strip()]

    cankao = -1
    for i,ix in enumerate(questions):
        if '参考答案' in ix:
            cankao = i
            # print("11111111",cankao,ix)
            if cankao <= 2:
                continue
            
            break
    
    if cankao != -1:
        for i in range(0,cankao+1,-1):
            try:
                questions[i] += questions[-(cankao-i)-1]
            except:
                pass
        # print("\n\n_______划分题目____________\n\n".join(questions))

        return questions[:cankao+1]

    return questions


def process(path):
    with open(path,'r') as f:
        content = f.read()
    return split_exam_paper_correctly(content)

def postp(string):
    pattern = r'(\n\*\d+\*\。|\n\*\d+\*、|\n\d+\。|\n\d+、|\n\n\d+\.|\n\d+、|\n\d+．|\n\*\*\d+\*\*\.|\ \d+．|\n\*\*\d+．|\n\d+\\\.|\*\*\d+、|\n【例\d+】|\n【训\d+】|\n\ \d+、|\n\*\*\d+\*\*．|\n【例\d+】)'
    string = re.sub(pattern,'',string)
    string = re.sub(r'\./(?:[^\/]+\/)*[^\/]*$','',string)
    string = re.sub(r'{width=\"\d+in\"','',string)
    string = re.sub(r'(\\_)+','()',string)
    starts = ['【[(（','】])）']
    for i,ix in enumerate(starts[0]):
        if string.startswith(ix):
            string = string.split(starts[1][i],1)[1]
    if string.startswith('**（'):
        string = string.split('）',1)[1]
    if string.startswith('**【'):
        string = string.split('】',1)[1]
    string = string.replace('\n\n','\n').replace('{.underline}','').replace('菁优网版权所有','').replace('菁优网','')
    bad = ['![网m/.xxk.  .om]()','![XxX/8]()','.underline}','{.underline','来自学科网（ZXXK.COM','学科网  www.zxxK.com',"淘课网"]
    for i in bad:
        string = string.replace(i,'')
    return string

mds = glob.glob('./*/*.md',recursive=True)
lens = []
outputs =[]
for i in tqdm.tqdm(mds):
    a = process(i)[1:]
    # print(i)
    # print(len(a))
    lens.append(len(a))
    # if len(a) <= 10:
    #     print("\n\n_______划分题目____________\n\n".join(a))
    #     raise 99
    outputs += a



def gather(outputs):
    gather_outputs = []
    gathering = outputs[0]
    for i in outputs:
        if '题' in i and len(i) < 10 and not ('【答案】' in i):
            gather_outputs.append(gathering)
            gathering = ""
            continue
        if '【答案】' in i:
            if i.find('【答案】') > 6:
                gather_outputs.append(gathering)
                gathering = i
        else:
            gathering += i
    return gather_outputs

outputs = gather(outputs)
outputs = gather(outputs)
outputs = [postp(i) for i in outputs ]
outputs = gather(outputs)

with open('output.json','w') as f:
    f.write(json.dumps(outputs,ensure_ascii=False,indent=4).replace('![]()',''))

pure_texts = []
for i in tqdm.tqdm(outputs):
    if not ('![' in i or '](' in i):
        pure_texts.append(i) 
with open('pure_texts.json','w') as f:
    f.write(json.dumps(pure_texts,ensure_ascii=False,indent=4))
print('最大题目数：',len(outputs),'纯文本题目数',len(pure_texts))

# len2c = {}
# raw = ''
# for i in outputs:
#     if len(i) not in len2c:
#         len2c[len(i)] = []
#     len2c[len(i)] += [raw+"\n___异常分割____\n"+i]
#     raw = i
# des = sorted(len2c.keys())

# # print(des)
# for i in des[:15]:
#     print(i,[i for i in len2c[i] if '题' not in i])

def tosharegpt(item):
    instruction = '请根据题目内容，回答正确答案。'
    if '【答' in item:
        input = item.split('【答')[0]
        output = '【答' + item.split('【答')[1]
    # elif '解' in item:
    #     input = item.split('解')[0]
    #     output = item.split('解')[1]
    else:
        return ''
    return {'instruction':instruction,'input':input,'output':output,'history':[]}

with open('tosharegpt.jsonl','w') as f:
    for i in tqdm.tqdm(outputs):
        s = tosharegpt(i)
        if s:
            f.write(json.dumps(s,ensure_ascii=False)+'\n')

with open('tosharegpt_puretext.jsonl','w') as f:
    for i in tqdm.tqdm(pure_texts):
        s = tosharegpt(i)
        if s:
            f.write(json.dumps(s,ensure_ascii=False)+'\n')