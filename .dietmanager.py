#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import argparse

import collections

import time


class Logger:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


class Eat:
    def __init__(self):
        # 食用的食物三大营养素总量
        self.protein_total = 0
        self.fat_total = 0
        self.carbohydrate_total = 0
        # 食用总卡路里 和 计划总卡路里
        self.kcal_total = 0

    def __call__(self, food):
        self.protein_total = self.protein_total + food.protein_total
        self.fat_total = self.fat_total + food.fat_total
        self.carbohydrate_total = self.carbohydrate_total + food.carbohydrate_total
        self.kcal_total = self.kcal_total + food.kcal_total
        return self


class FoodObject:
    def __init__(self, name, type, protein, fat, carbohydrate, kcal, unit):
        self.name = name  # 名称
        self.type = type  # 类型

        if type == 'carbohydrate':
            # 碳水中的蛋白质利用率只有1/2
            self.protein = protein / 2
        else:
            self.protein = protein
        self.fat = fat  # 脂肪
        self.carbohydrate = carbohydrate  # 碳水
        self.kcal = kcal  # 卡路里
        self.unit = unit  # 单位
        self.number = 0  # 数量/份

        self.protein_total = 0
        self.fat_total = 0
        self.carbohydrate_total = 0
        self.kcal_total = 0

    def __call__(self, number=1):
        self.protein_total = self.protein * number
        self.fat_total = self.fat * number
        self.carbohydrate_total = self.carbohydrate * number
        self.kcal_total = self.kcal * number
        self.number = number
        return self

    def add(self, other):
        # 增加
        self.protein_total = self.protein_total + self.protein * other
        self.fat_total = self.fat_total + self.fat * other
        self.carbohydrate_total = self.carbohydrate_total + self.carbohydrate * other
        self.kcal_total = self.kcal_total + self.kcal * other
        self.number = self.number + other
        return self

    def sub(self, other):
        # 减少
        self.protein_total = float('%.6f' % (self.protein_total - self.protein * other))
        self.fat_total = float('%.6f' % (self.fat_total - self.fat * other))
        self.carbohydrate_total = float('%.6f' % (self.carbohydrate_total - self.carbohydrate * other))
        self.kcal_total = float('%.6f' % (self.kcal_total - self.kcal * other))
        self.number = float('%.6f' % (self.number - other))
        return self


FOOD_MENU = {
    "egg": FoodObject('煮鸡蛋', 'protein', 7.3, 6.3, 1.3, 91, '中等'),
    "powder": FoodObject('蛋白粉', 'protein', 27, 0, 1, 115, '30g'),
    "beef": FoodObject('牛里脊', 'protein', 22.2, 0.9, 2.4, 107, '100g'),
    "chicken": FoodObject('鸡胸肉', 'protein', 19.4, 5, 2.5, 133, '100g'),
    "milk": FoodObject('低脂牛奶', 'protein', 8.8, 3.8, 12.3, 118, '250ml'),
    "rice": FoodObject('杂米饭', 'carbohydrate', 4.1, 0.5, 26.8, 125, '100g'),
    "glucose": FoodObject('葡萄糖', 'carbohydrate', 0, 0, 9.6, 39, '10g'),
    "oat": FoodObject('燕麦片', 'carbohydrate', 3, 1.5, 12.5, 76, '25g'),
    "oil": FoodObject('花生油', 'fat', 0, 5, 0, 44, '5ml'),
    "nuts": FoodObject('夏威夷果', 'fat', 0.8, 6.7, 1.9, 71, '10g'),
}

nutrient_map = {
    "high": {
        "alias": "高碳日",
        "DB": 1.8,
        "ZF": 1.2,
        "TS": 3.5,
        "exclude_foods": ['glucose'],
    },
    "middle": {
        "alias": "中碳日",
        "DB": 1.8,
        "ZF": 1.2,
        "TS": 2.5,
        "exclude_foods": ['glucose'],
    },
    "low": {
        "alias": "低碳日",
        "DB": 2,
        "ZF": 1.2,
        "TS": 1.5,
        "exclude_foods": ['glucose'],
    },
    "none": {
        "alias": "断碳日",
        "DB": 2,
        "ZF": 1.2,
        "TS": 0.5,
        "exclude_foods": ['glucose', 'milk', 'egg', 'oat', 'powder'],
    },
    "rest": {
        "alias": "修整日",
        "DB": 2.2,
        "ZF": 1.2,
        "TS": 4.5,
        "exclude_foods": ['glucose'],
    },
    "increase": {
        "alias": "增肌日",
        "DB": 2.2,
        "ZF": 1.2,
        "TS": 4.5,
        "exclude_foods": [],
    },
}


class WeightControlFactory:
    def __init__(self, weight, sex, age, height, food_menu, activity, bfr=0):
        # 当前体重和目标体重
        self.current_weight = weight
        self.week_food = {}
        self.sex = sex
        self.age = age
        self.height = height
        # 体脂率
        self.bfr = bfr
        # 活动强度
        self.activity = activity
        self.food_menu = food_menu

    @property
    def bmi(self):
        # 体脂率公式 这个公式和性别无关
        if self.bfr:
            # BMR = 370 + (21.6 * 瘦体重(kg))
            bmi = 370 + (21.6 * self.current_weight * (1 - self.bfr))
        else:
            if self.sex == 'man':
                # 基础代谢 男
                bmi = (67 + 13.73 * self.current_weight + 5 * self.height - 6.9 * self.age)
            else:
                # 基础代谢 女
                bmi = (665 + 9.6 * self.current_weight + 1.8 * self.height - 4.7 * self.age)
        return bmi

    @property
    def bee(self):
        # 活动代谢
        return self.bmi * self.activity

    def pai(self, schema):
        """计算一天的卡路里"""
        nmap = nutrient_map.get(schema)
        DB = self.current_weight * nmap['DB']
        ZF = self.current_weight * nmap['ZF']
        TS = self.current_weight * nmap['TS']

        plan_kcal_total = (DB + TS) * 4 + ZF * 9
        print(nmap['alias'])
        print("")
        print("三大营养素配比:")
        print("\t蛋白质\t\t %sg" % ('%.0f' % DB))
        print("\t脂肪\t\t %sg" % ('%.0f' % ZF))
        print("\t碳水\t\t %sg" % ('%.0f' % TS))
        print('')
        print('参考饮食可食用食物份量:')
        practical_kcal = self.reference_food(DB, ZF, TS, schema)
        print("")

        print("计划饮食:")
        print("\t总热量 %skcal" % ('%.0f' % plan_kcal_total))

        print("\t大于基础代谢 %s kcal" % ('%.0f' % (plan_kcal_total - self.bmi)))
        print("\t大于活动代谢 %s kcal" % ('%.0f' % (plan_kcal_total - self.bee)))
        print('')
        print("参考饮食:")
        print("\t总热量 %skcal" % ('%.2f' % practical_kcal))

        print("\t大于基础代谢 %s kcal" % ('%.0f' % (practical_kcal - self.bmi)))
        print("\t大于活动代谢 %s kcal" % ('%.0f' % (practical_kcal - self.bee)))
        print('')
        print(Logger.HEADER + '*****************************************************' + Logger.ENDC)

        return plan_kcal_total

    def control_fat(self, plans):
        """
        碳水循环法
        """
        week_kacl_total = 0
        for index, val in enumerate(plans):
            if len(plans) == 7:
                print('星期%s' % (index + 1))

            week_kacl_total = week_kacl_total + self.pai(val)
        return week_kacl_total

    def write_off_weight(self, eat_obj, food):

        eat_obj(food)

        # 统计一周的食物总量
        food_name = "%s(%s/份)" % (food.name, food.unit)

        food_sum = self.week_food.get(food_name)
        if food_sum:
            self.week_food[food_name] = self.week_food.get(food_name) + food.number
        else:
            self.week_food[food_name] = food.number
        if food.number > 0:
            print("")
            print('  %s\t %s 份 (%s/份)\t热量:\t%s kcal' % (
            food.name, round(food.number, 2), food.unit, ('%.0f' % food.kcal_total)))

    def over_fed(self, DB, ZF, TS, prepare_food, record_eat):

        return prepare_food

    def judge_eat(self, DB, ZF, TS, eat, record_eat, foods):

        for food in foods:
            if food.type == 'protein' and DB < record_eat.protein_total:
                while food.number > 0:
                    if DB > (eat.protein_total + food.protein_total):
                        break
                    food.sub(0.1)
            if food.type == 'fat' and ZF < record_eat.fat_total:
                while food.number > 0:
                    if ZF > (eat.fat_total + food.fat_total):
                        break
                    food.sub(0.1)
            if food.type == 'carbohydrate' and TS < record_eat.carbohydrate_total:
                while food.number > 0:
                    if TS > (eat.carbohydrate_total + food.carbohydrate_total):
                        break
                    food.sub(0.1)

            self.write_off_weight(eat, food)

    def reference_food(self, DB, ZF, TS, schema):
        """参考食用的食物"""
        prepare_food = {}
        record_eat = Eat()
        # 先添加指定数量的食物
        for food_name, number in self.food_menu.items():
            if food_name in nutrient_map[schema]['exclude_foods']:
                continue
            if number < 0:
                # 如果数量小于 0 , 指定默认值10
                number = 10
            while number > 0:
                food = FOOD_MENU[food_name](number)
                if food.type == 'protein' and DB < (record_eat.protein_total + food.protein_total):
                    number -= 0.1
                    continue
                if food.type == 'fat' and ZF < (record_eat.fat_total + food.fat_total):
                    number -= 0.5
                    continue
                if food.type == 'carbohydrate' and TS < (record_eat.carbohydrate_total + food.carbohydrate_total):
                    number -= 0.1
                    continue

                if food.type in prepare_food:
                    prepare_food[food.type].append(food)
                else:
                    prepare_food[food.type] = [food]
                record_eat(food)
                break
        eat = Eat()
        # 保证类型顺序
        self.judge_eat(DB, ZF, TS, eat, record_eat, prepare_food.get('carbohydrate', []))
        self.judge_eat(DB, ZF, TS, eat, record_eat, prepare_food.get('protein', []))
        self.judge_eat(DB, ZF, TS, eat, record_eat, prepare_food.get('fat', []))

        # # 剩余可食用脂肪
        zf_residue = ZF - eat.fat_total
        db_residue = DB - eat.protein_total
        ts_residue = TS - eat.carbohydrate_total
        kcal_residue = zf_residue * 9 + (db_residue + ts_residue) * 4
        print("")
        print("参考饮食外还可额外摄入:")
        print("\t脂肪:\t\t %sg" % ('%.1f' % zf_residue))
        print("\t蛋白质:\t\t %sg" % ('%.1f' % db_residue))
        print("\t碳水:\t\t %sg" % ('%.1f' % ts_residue))
        print("")
        print((Logger.FAIL + '\t参考饮食外最多还可摄入%skcal, 建议以蔬菜作为补充' + Logger.ENDC) % ('%.0f' % kcal_residue))

        print("")
        return eat.kcal_total


def simulate(weight, target_weight, food_menu, plans, sex, age, height, activity, bfr, week=0, prediction=False):
    """模拟体重下降的的饮食参考"""
    wf = WeightControlFactory(weight, sex, age, height, food_menu, activity, bfr)
    if prediction:
        print("-------------第%s周-------------" % (week + 1))

    bmi = wf.bmi
    bee = wf.bee
    # 一周摄入的总热量

    week_kcal_total = wf.control_fat(plans)

    # 以计划饮食的三大营养素预估的脂肪燃烧量
    lose_fat = (bee * 7 - week_kcal_total) / 7700
    # 计算当前体重
    wf.current_weight = wf.current_weight - lose_fat
    week += 1
    print('')
    print Logger.FAIL + "本周需要准备的食材:"
    flag = 1
    if len(plans) == 1:
        flag = 7
    for k, v in wf.week_food.items():
        if v * flag > 0:
            print(Logger.FAIL + "\t%s份\t%s" % ('%.1f' % (v * flag), k))

    print('')
    print "平均数据:"
    print('')
    print("\t基础代谢: \t\t%skcal" % ('%.0f' % bmi))
    print("\t活动代谢: \t\t%skcal" % ('%.0f' % bee))
    print("\t日平均摄入: \t\t%skcal" % ('%.0f' % (week_kcal_total / len(plans))))
    mean_kcal = (week_kcal_total - bee * len(plans)) / len(plans)
    if mean_kcal > 0:
        print("\t日平均热量盈余: \t%skcal" % ('%.0f' % mean_kcal))
    else:
        print("\t日平均热量缺口: \t%skcal" % ('%.0f' % mean_kcal))
    print('')
    if len(plans) == 7:
        print("以计划饮食热量推测:")
        print("\t本周预计体重: \t%s kg" % ('%.2f' % wf.current_weight))
        if lose_fat > 0:
            print("\t本周预计减脂: \t%s kg" % ('%.2f' % lose_fat))
        else:
            print("\t本周预计增重: \t%s kg" % ('%.2f' % (lose_fat * -1)))

    if prediction:
        print("减至目标体重%skg 预计还需约 %s周" % (
            target_weight, ('%.2f' % ((wf.current_weight - target_weight) * 7700 / ((bee - week_kcal_total / 7) * 7)))))
    print(Logger.OKGREEN + "-------------------------------------------" + Logger.ENDC)
    print('')

    if prediction:
        if wf.current_weight > target_weight:
            # 使用当前体重递归计算
            simulate(wf.current_weight, target_weight, food_menu, plans, sex, age, height, activity, bfr, week,
                     prediction)
        else:
            print(Logger.HEADER + "-------------------------------------------" + Logger.ENDC)
            print('预计需历时%s周, 达到目标体重%skg' % (week, '%.2f' % wf.current_weight))
            print(Logger.HEADER + "-------------------------------------------" + Logger.ENDC)
            return


class Prepare:
    parser = None

    def __init__(self):
        parser = argparse.ArgumentParser(description='饮食管理')
        parser.add_argument("-s", "--sex", default="man",
                            help="性别",
                            choices=['man', 'woman'])
        parser.add_argument("-w", "--weight", help="当前体重", type=float)
        parser.add_argument("-a", "--age", help="年龄", type=int, default=27)
        parser.add_argument("-g", "--height", help="身高", type=int, default=180)
        parser.add_argument("--bfr", help="体脂率", type=float, default=0.0)
        parser.add_argument("--activity", help="活动强度",
                            type=float,
                            default=1.55,
                            choices=[1.2, 1.375, 1.55, 1.725, 1.9])
        # 几乎不动Calorie-Calculation=BMRx1.2
        # 稍微运动（每周1-3次）总需=BMRx1.375
        # 中度运动（每周3-5次）总需=BMRx1.55
        # 积极运动（每周6-7次）总需=BMRx1.725
        # 专业运动（2倍运动量）总需=BMRx1.9

        parser.add_argument("--plans",
                            nargs='+',
                            help="碳水循环参数",
                            type=str,
                            default=["middle", "low", "middle", "middle", "low", "none", "high"],
                            choices=["middle", "low", "none", "high", "increase", "rest"]
                            )

        group = parser.add_argument_group('prediction weight')
        group.add_argument("-p", "--prediction", help="是否预测", action="store_true")

        group.add_argument("-t", "--target_weight", help="目标体重", type=float)

        self.parser = parser

    def run(self, argv):
        args = self.parser.parse_args(argv)
        if args.prediction:
            if not args.target_weight:
                print('指定参数 -p 时, 必须指定目标体重 -t')
                return
        if args.prediction and len(args.plans) != 7:
            print('指定 -p 参数时, 参数--plans 长度必须为7')
            return
        # 食物列表
        food_menu = collections.OrderedDict()
        food_menu['egg'] = 3
        food_menu['powder'] = 2
        food_menu['milk'] = 3
        food_menu['beef'] = 3
        food_menu['oil'] = 4
        food_menu['nuts'] = 4
        food_menu['chicken'] = -1
        # 最后再吃碳水类
        food_menu['glucose'] = 6
        food_menu['oat'] = 2
        food_menu['rice'] = -1
        simulate(args.weight,
                 args.target_weight,
                 food_menu,
                 args.plans,
                 args.sex,
                 args.age,
                 args.height,
                 args.activity,
                 args.bfr,
                 prediction=args.prediction)


def main(argv=sys.argv[1:]):
    app = Prepare()
    app.run(argv)


if __name__ == '__main__':
    sys.exit(main())
