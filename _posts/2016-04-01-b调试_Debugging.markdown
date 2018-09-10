---
layout:     post
title:      "「 Intermediate Python 」 pdb 调试 Debugging"
subtitle:   " \"它是一本开脑洞的书。无论你是Python初学者，还是Python高手，它显现给你的永远是Python里最美好的事物。\""
date:       2016-04-01 12:00:00
author:     "Jingh"
header-img: "img/in-post/post-Intermediate/intermediatePython-01.jpg"
catalog: true
tags:
    - 读书笔记
    - Python
---

> 本书的原文原址[intermediatePython](http://book.pythontips.com)

# 调试（Debugging）

利用好调试，能大大提高你捕捉代码Bug的。大部分新人忽略了Python debugger(```pdb```)的重要性。 在这个章节我只会告诉你一些重要的命令，你可以从官方文档中学习到更多。

> 译者注，参考：https://docs.python.org/2/library/pdb.html
Or https://docs.python.org/3/library/pdb.html

Python自带的pdb库，发现用pdb来调试程序还是很方便的，当然了，什么远程调试，多线程之类，pdb是搞不定的。

用pdb调试有多种方式可选：

#### 从命令行运行
命令行启动目标程序，加上-m参数，这样调用myscript.py的话断点就是程序的执行第一行之前

你可以在命令行使用Python debugger运行一个脚本， 举个例子：
```bash
$ python -m pdb my_script.py
```

这会触发debugger在脚本第一行指令处停止执行。这在脚本很短时会很有帮助。你可以通过(Pdb)模式接着查看变量信息，并且逐行调试。

#### 从脚本内部运行

同时，你也可以在脚本内部设置断点，这样就可以在某些特定点查看变量信息和各种执行时信息了。这里将使用```pdb.set_trace()```方法来实现。举个例子：
```python
import pdb

def make_bread():
    pdb.set_trace()
    return "I don't have time"

print(make_bread())
```

试下保存上面的脚本后运行之。你会在运行时马上进入debugger模式。现在是时候了解下debugger模式下的一些命令了。

写作一行:
```import pdb; pdb.set_trace()```

#####命令列表：

- ```c```: 继续执行
- ```w```: 显示当前正在执行的代码行的上下文信息
- ```a```: 打印当前函数的参数列表
- ```s```: 执行当前代码行，并停在第一个能停的地方（相当于单步进入）
- ```n```: 继续执行到当前函数的下一行，或者当前行直接返回（单步跳过）

单步跳过（```n```ext）和单步进入（```s```tep）的区别在于， 单步进入会进入当前行调用的函数内部并停在里面， 而单步跳过会（几乎）全速执行完当前行调用的函数，并停在当前函数的下一行。

pdb真的是一个很方便的功能，上面仅列举少量用法，更多的命令强烈推荐你去看官方文档。
