---
layout:     post
title:      "「 Intermediate Python 」 使用C扩展"
subtitle:   " \"它是一本开脑洞的书。无论你是Python初学者，还是Python高手，它显现给你的永远是Python里最美好的事物。\""
date:       2016-04-22 12:00:00
author:     "Jingh"
header-img: "img/in-post/post-Intermediate/intermediatePython-01.jpg"
catalog: true
tags:
    - 读书笔记
    - Python
---

> 本书的原文原址[intermediatePython](http://book.pythontips.com)

## 使用C扩展
CPython还为开发者实现了一个有趣的特性，使用Python可以轻松调用C代码

开发者有三种方法可以在自己的Python代码中来调用C编写的函数-```ctypes```，```SWIG```，```Python/C API```。每种方式也都有各自的利弊。

首先，我们要明确为什么要在Python中调用C？

常见原因如下：
-  你要提升代码的运行速度，而且你知道C要比Python快50倍以上
-  C语言中有很多传统类库，而且有些正是你想要的，但你又不想用Python去重写它们
-  想对从内存到文件接口这样的底层资源进行访问
-  不需要理由，就是想这样做


## CTypes

Python中的[ctypes模块](https://docs.python.org/2/library/ctypes.html)可能是Python调用C方法中最简单的一种。ctypes模块提供了和C语言兼容的数据类型和函数来加载dll文件，因此在调用时不需对源文件做任何的修改。也正是如此奠定了这种方法的简单性。

示例如下

实现两数求和的C代码，保存为```add.c```
```C
//sample C file to add 2 numbers - int and floats

#include <stdio.h>

int add_int(int, int);
float add_float(float, float);

int add_int(int num1, int num2){
    return num1 + num2;

}

float add_float(float num1, float num2){
    return num1 + num2;

}
```

接下来将C文件编译为```.so```文件(windows下为DLL)。下面操作会生成adder.so文件
```Shell
#For Linux
$  gcc -shared -Wl,-soname,adder -o adder.so -fPIC add.c

#For Mac
$ gcc -shared -Wl,-install_name,adder.so -o adder.so -fPIC add.c

```

现在在你的Python代码中来调用它
```Python
from ctypes import *

#load the shared object file
adder = CDLL('./adder.so')

#Find sum of integers
res_int = adder.add_int(4,5)
print "Sum of 4 and 5 = " + str(res_int)

#Find sum of floats
a = c_float(5.5)
b = c_float(4.1)

add_float = adder.add_float
add_float.restype = c_float
print "Sum of 5.5 and 4.1 = ", str(add_float(a, b))

```

输出如下
```
Sum of 4 and 5 = 9
Sum of 5.5 and 4.1 =  9.60000038147
```

在这个例子中，C文件是自解释的，它包含两个函数，分别实现了整形求和和浮点型求和。

在Python文件中，一开始先导入ctypes模块，然后使用CDLL函数来加载我们创建的库文件。这样我们就可以通过变量```adder```来使用C类库中的函数了。当```adder.add_int()```被调用时，内部将发起一个对C函数```add_int```的调用。ctypes接口允许我们在调用C函数时使用原生Python中默认的字符串型和整型。

而对于其他类似布尔型和浮点型这样的类型，必须要使用正确的ctype类型才可以。如向```adder.add_float()```函数传参时, 我们要先将Python中的十进制值转化为c_float类型，然后才能传送给C函数。这种方法虽然简单，清晰，但是却很受限。例如，并不能在C中对对象进行操作。


## SWIG

SWIG是Simplified Wrapper and Interface Generator的缩写。是Python中调用C代码的另一种方法。在这个方法中，开发人员必须编写一个额外的接口文件来作为SWIG(终端工具)的入口。

Python开发者一般不会采用这种方法，因为大多数情况它会带来不必要的复杂。而当你有一个C/C++代码库需要被多种语言调用时，这将是个非常不错的选择。

示例如下(来自[SWIG官网](http://www.swig.org/tutorial.html))

```example.c```文件中的C代码包含了不同的变量和函数
```C
#include <time.h>
double My_variable = 3.0;

int fact(int n) {
    if (n <= 1) return 1;
    else return n*fact(n-1);

}

int my_mod(int x, int y) {
    return (x%y);

}

char *get_time()
{
    time_t ltime;
    time(&ltime);
    return ctime(&ltime);

}
```

编译它
```Shell
unix % swig -python example.i
unix % gcc -c example.c example_wrap.c \
    -I/usr/local/include/python2.1
unix % ld -shared example.o example_wrap.o -o _example.so

```

最后，Python的输出
```Python
>>> import example
>>> example.fact(5)
120
>>> example.my_mod(7,3)
1
>>> example.get_time()
'Sun Feb 11 23:01:07 1996'
>>>
```

我们可以看到，使用SWIG确实达到了同样的效果，虽然下了更多的工夫，但如果你的目标是多语言还是很值得的。


## Python/C API

[Python/C API](https://docs.python.org/2/c-api/)可能是被最广泛使用的方法。它不仅简单，而且可以在C代码中操作你的Python对象。

这种方法需要以特定的方式来编写C代码以供Python去调用它。所有的Python对象都被表示为一种叫做PyObject的结构体，并且```Python.h```头文件中提供了各种操作它的函数。例如，如果PyObject表示为PyListType(列表类型)时，那么我们便可以使用```PyList_Size()```函数来获取该结构的长度，类似Python中的```len(list)```函数。大部分对Python原生对象的基础函数和操作在```Python.h```头文件中都能找到。

示例

编写一个C扩展，添加所有元素到一个Python列表(所有元素都是数字)

来看一下我们要实现的效果，这里演示了用Python调用C扩展的代码
```Python
#Though it looks like an ordinary python import, the addList module is implemented in C
import addList

l = [1,2,3,4,5]
print "Sum of List - " + str(l) + " = " +  str(addList.add(l))

```

上面的代码和普通的Python文件并没有什么分别，导入并使用了另一个叫做```addList```的Python模块。唯一差别就是这个模块并不是用Python编写的，而是C。

接下来我们看看如何用C编写```addList```模块，这可能看起来有点让人难以接受，但是一旦你了解了这之中的各种组成，你就可以一往无前了。

```C
//Python.h has all the required function definitions to manipulate the Python objects
#include <Python.h>

//This is the function that is called from your python code
static PyObject* addList_add(PyObject* self, PyObject* args){

    PyObject * listObj;

    //The input arguments come as a tuple, we parse the args to get the various variables
    //In this case it's only one list variable, which will now be referenced by listObj
    if (! PyArg_ParseTuple( args, "O", &listObj ))
        return NULL;

    //length of the list
    long length = PyList_Size(listObj);

    //iterate over all the elements
    int i, sum =0;
    for (i = 0; i < length; i++) {
        //get an element out of the list - the element is also a python objects
        PyObject* temp = PyList_GetItem(listObj, i);
        //we know that object represents an integer - so convert it into C long
        long elem = PyInt_AsLong(temp);
        sum += elem;
    }

    //value returned back to python code - another python object
    //build value here converts the C long to a python integer
    return Py_BuildValue("i", sum);

}

//This is the docstring that corresponds to our 'add' function.
static char addList_docs[] =
"add(  ): add all elements of the list\n";

/* This table contains the relavent info mapping -
   <function-name in python module>, <actual-function>,
   <type-of-args the function expects>, <docstring associated with the function>
 */
static PyMethodDef addList_funcs[] = {
    {"add", (PyCFunction)addList_add, METH_VARARGS, addList_docs},
    {NULL, NULL, 0, NULL}

};

/*
   addList is the module name, and this is the initialization block of the module.
   <desired module name>, <the-info-table>, <module's-docstring>
 */
PyMODINIT_FUNC initaddList(void){
    Py_InitModule3("addList", addList_funcs,
            "Add all ze lists");

}

```

逐步解释
- ```Python.h```头文件中包含了所有需要的类型(Python对象类型的表示)和函数定义(对Python对象的操作)
- 接下来我们编写将要在Python调用的函数, 函数传统的命名方式由{模块名}_{函数名}组成，所以我们将其命名为```addList_add```
- 然后填写想在模块内实现函数的相关信息表，每行一个函数，以空行作为结束
- 最后的模块初始化块签名为```PyMODINIT_FUNC init{模块名}```。

函数```addList_add```接受的参数类型为PyObject类型结构(同时也表示为元组类型，因为Python中万物皆为对象，所以我们先用PyObject来定义)。传入的参数则通过```PyArg_ParseTuple()```来解析。第一个参数是被解析的参数变量。第二个参数是一个字符串，告诉我们如何去解析元组中每一个元素。字符串的第n个字母正是代表着元组中第n个参数的类型。例如，"i"代表整形，"s"代表字符串类型, "O"则代表一个Python对象。接下来的参数都是你想要通过```PyArg_ParseTuple()```函数解析并保存的元素。这样参数的数量和模块中函数期待得到的参数数量就可以保持一致，并保证了位置的完整性。例如，我们想传入一个字符串，一个整数和一个Python列表，可以这样去写
```C
int n;
char *s;
PyObject* list;
PyArg_ParseTuple(args, "siO", &n, &s, &list);

```

在这种情况下，我们只需要提取一个列表对象，并将它存储在```listObj```变量中。然后用列表对象中的```PyList_Size()```函数来获取它的长度。就像Python中调用```len(list)```。

现在我们通过循环列表，使用```PyList_GetItem(list, index)```函数来获取每个元素。这将返回一个```PyObject*```对象。既然Python对象也能表示```PyIntType```，我们只要使用```PyInt_AsLong(PyObj *)```函数便可获得我们所需要的值。我们对每个元素都这样处理，最后再得到它们的总和。

总和将被转化为一个Python对象并通过```Py_BuildValue()```返回给Python代码，这里的i表示我们要返回一个Python整形对象。

现在我们已经编写完C模块了。将下列代码保存为```setup.py```
```Python
#build the modules

from distutils.core import setup, Extension

setup(name='addList', version='1.0',  \
      ext_modules=[Extension('addList', ['adder.c'])])
```

并且运行
```Shell
python setup.py install

```

现在应该已经将我们的C文件编译安装到我们的Python模块中了。

在一番辛苦后，让我们来验证下我们的模块是否有效
```Python
#module that talks to the C code
import addList

l = [1,2,3,4,5]
print "Sum of List - " + str(l) + " = " +  str(addList.add(l))
```

输出结果如下
```
Sum of List - [1, 2, 3, 4, 5] = 15

```

如你所见，我们已经使用Python.h API成功开发出了我们第一个Python C扩展。这种方法看似复杂，但你一旦习惯，它将变的非常有效。

Python调用C代码的另一种方式便是使用[Cython](http://cython.org/)让Python编译的更快。但是Cython和传统的Python比起来可以将它理解为另一种语言，所以我们就不在这里过多描述了。
