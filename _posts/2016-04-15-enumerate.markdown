---
layout:     post
title:      "「 Intermediate Python 」 枚举"
subtitle:   " \"它是一本开脑洞的书。无论你是Python初学者，还是Python高手，它显现给你的永远是Python里最美好的事物。\""
date:       2016-04-15 12:00:00
author:     "Jingh"
header-img: "img/in-post/post-Intermediate/intermediatePython-01.jpg"
catalog: true
tags:
    - 读书笔记
    - Python
---

> 本书的原文原址[intermediatePython](http://book.pythontips.com)

## 枚举

枚举(```enumerate```)是Python内置函数。它的用处很难在简单的一行中说明，但是大多数的新人，甚至一些高级程序员都没有意识到它。

它允许我们遍历数据并自动计数，

下面是一个例子：

```python
for counter, value in enumerate(some_list):
    print(counter, value)
```
不只如此，```enumerate```也接受一些可选参数，这使它更有用。

```python
my_list = ['apple', 'banana', 'grapes', 'pear']
for c, value in enumerate(my_list, 1):
    print(c, value)

# 输出:
(1, 'apple')
(2, 'banana')
(3, 'grapes')
(4, 'pear')
```

上面这个可选参数允许我们定制从哪个数字开始枚举。
你还可以用来创建包含索引的元组列表，
例如：

```python
my_list = ['apple', 'banana', 'grapes', 'pear']
counter_list = list(enumerate(my_list, 1))
print(counter_list)
# 输出: [(1, 'apple'), (2, 'banana'), (3, 'grapes'), (4, 'pear')]
```
