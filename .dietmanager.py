#!/usr/bin/python
#-*- coding:utf-8 -*-
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

nutrient_map = {
    "high": {
        "alias": "高碳日",
        "DB": 1.8,
        "ZF": 1.2,
        "TS": 3.5,
    },
    "middle": {
        "alias": "中碳日",
        "DB": 1.8,
        "ZF": 1.2,
        "TS": 2.5,
    },
    "low": {
        "alias": "低碳日",
        "DB": 2,
        "ZF": 1.2,
        "TS": 1.5,
    },
    "none": {
        "alias": "断碳日",
        "DB": 2,
        "ZF": 1.2,
        "TS": 0.5,
    },
    "increase": {
        "alias": "增肌日",
        "DB": 1.6,
        "ZF": 1.2,
        "TS": 4,
    },
}


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
        self.name = name # 名称
        self.type = type # 类型

        if type == 'carbohydrate':
            # 碳水中的蛋白质利用率只有1/2
            self.protein = protein / 2
        else:
            self.protein = protein
        self.fat = fat # 脂肪
        self.carbohydrate = carbohydrate # 碳水
        self.kcal = kcal # 卡路里
        self.unit = unit # 单位
        self.number = 0 # 数量/份

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
        self.protein_total = self.protein_total - self.protein * other
        self.fat_total = self.fat_total - self.fat * other
        self.carbohydrate_total = self.carbohydrate_total - self.carbohydrate * other
        self.kcal_total = self.kcal_total - self.kcal * other
        self.number = self.number - other
        return self

FOOD_MENU = {
    "egg": FoodObject('鸡蛋\t\t', 'protein', 7.3, 6.3, 1.3, 91, '中等'),
    "powder": FoodObject('all max 蛋白粉\t', 'protein', 27, 0, 1, 115, '30g'),
    "beef": FoodObject('牛里脊\t\t', 'protein', 22.2, 0.9, 2.4, 107, '100g'),
    "chicken": FoodObject('鸡胸肉\t\t', 'protein', 19.4, 5, 2.5, 133, '100g'),
    "milk": FoodObject('牛奶\t\t', 'protein', 8.8, 3.8, 12.3, 118, '250ml'),
    "rice": FoodObject('杂米饭\t\t', 'carbohydrate', 4.1, 0.5, 26.8, 125, '100g'),
    "oat": FoodObject('燕麦\t\t', 'carbohydrate', 3, 1.5, 12.5, 76, '25g'),
    "oil": FoodObject('花生油\t\t', 'fat', 0, 5, 0, 44, '5ml'),
    "nuts": FoodObject('夏威夷果\t', 'fat', 0.8, 6.7, 1.9, 71, '10g'),
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
                bmi = (67 + 13.73 * self.current_weight + 5 * self.height - 6.9 * self.age) * 0.95
            else:
                # 基础代谢 女
                bmi = (665 + 9.6 * self.current_weight + 1.8 * self.height - 4.7 * self.age) * 0.95
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
        print('|    ' + nmap['alias'] + '     |')
        print("|---------------|")
        print("")
        print("三大营养素配比:")
        print("\t蛋白质\t\t %sg" % ('%.0f' % DB))
        print("\t脂肪\t\t %sg" % ('%.0f' % ZF))
        print("\t碳水\t\t %sg" % ('%.0f' % TS))
        print('')
        print('参考饮食可食用食物份量:')
        practical_kcal = self.reference_food(DB, ZF, TS)
        print("")
        print("计划饮食总热量: %skcal" % ('%.0f' % plan_kcal_total))
        print("参考饮食总热量: %skcal" % ('%.2f' % practical_kcal))
        print('')
        print((Logger.FAIL + '参考饮食外最多还可摄入%skcal, 建议以蔬菜作为补充' + Logger.ENDC) % ('%.0f' % (plan_kcal_total - practical_kcal)))
        print('')
        print("计划饮食总热量大于基础代谢 %s kcal, 小于活动代谢 %s kcal" % ('%.0f' % (plan_kcal_total - self.bmi), '%.0f' % (plan_kcal_total - self.bee)))
        print(
        "参考饮食总热量大于基础代谢 %s kcal, 小于活动代谢 %s kcal" % ('%.0f' % (practical_kcal - self.bmi), '%.0f' % (practical_kcal - self.bee)))
        print('')
        print(Logger.HEADER + '*****************************************************' + Logger.ENDC)

        return plan_kcal_total

    def control_fat(self, plans):
        """
        碳水循环法
        """
        week_kacl_total = 0
        for index, val in enumerate(plans):
            print("|---------------|")
            print('|    星期 %s     |' % (index + 1))
            print("|---------------|")
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
        print("")
        print('\t%s 份\t\t%s\t热量:\t%skcal' % ('%.2f' % food.number, food_name, '%.2f' % food.kcal_total))

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
                    if ZF > (eat.protein_total + food.protein_total):
                        break
                    food.sub(0.1)
            if food.type == 'carbohydrate' and TS < record_eat.carbohydrate_total:
                while food.number > 0:
                    if TS > (eat.protein_total + food.protein_total):
                        break
                    food.sub(0.1)

            self.write_off_weight(eat, food)

    def reference_food(self, DB, ZF, TS):
        """参考食用的食物"""
        prepare_food = {}
        record_eat = Eat()
        # 先添加指定数量的食物
        for food_name, number in self.food_menu.items():
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
        self.judge_eat(DB, ZF, TS, eat, record_eat, prepare_food.get('carbohydrate'))
        self.judge_eat(DB, ZF, TS, eat, record_eat, prepare_food.get('protein'))
        self.judge_eat(DB, ZF, TS, eat, record_eat, prepare_food.get('fat'))


        # # 剩余可食用脂肪
        zf_residue = ZF - eat.fat_total
        db_residue = DB - eat.protein_total
        ts_residue = TS - eat.carbohydrate_total
        kcal_residue = zf_residue * 9 + (db_residue + ts_residue) * 4
        print("")
        print("还可额外摄入:")
        print("\t脂肪:\t\t %sg" % ('%.0f' % zf_residue))
        print("\t蛋白质:\t\t %sg" % ('%.0f' % db_residue))
        print("\t碳水:\t\t %sg" % ('%.0f' % ts_residue))
        print("\t相当于:\t\t %skcal" % ('%.0f' % kcal_residue))
        print("")
        return eat.kcal_total


def simulate(weight, target_weight, food_menu, plans, sex, age, height, activity, bfr, week=0, prediction=False):
    """模拟体重下降的的饮食参考"""
    wf = WeightControlFactory(weight, sex, age, height, food_menu, activity, bfr)
    print("-------------第%s周-------------" % (week + 1))

    bmi = wf.bmi
    bee = wf.bee
    # 一周摄入的总热量

    week_kcal_total = wf.control_fat(plans)

    # 计算当前体重
    wf.current_weight = wf.current_weight + (week_kcal_total - bee * 7) / 7700
    week += 1
    print('')
    print Logger.FAIL + "本周需要准备的食材:"
    for k, v in wf.week_food.items():
        print(Logger.FAIL + "\t%s:\t%s份" % (k, '%.0f' % v))

    print('')

    print "周平均数据:"
    print("\t日基础代谢: \t\t%skcal" % ('%.0f' % bmi))
    print("\t日活动代谢: \t\t%skcal" % ('%.0f' % bee))
    print("\t日平均摄入: \t\t%skcal" % ('%.0f' % (week_kcal_total / 7)))
    print("\t日平均热量缺口: \t%skcal" % ('%.0f' % ((week_kcal_total - bee * 7) / 7)))
    print('')
    print("以计划饮食热量推测:")
    print("\t本周体重预计为: \t%s" % ('%.2f' % wf.current_weight))
    print("\t周预计燃烧脂肪: \t%s kg" % ('%.2f' % ((week_kcal_total - bee * 7) / 7700)))
    # print("周摄入总热量 %s kcal" % ('%.0f' % week_total))
    if prediction:
        print("减至目标体重%skg 预计还需约 %s周" % (
            target_weight, ('%.2f' % ((wf.current_weight - target_weight) * 7700 / ((bee - week_kcal_total / 7) * 7)))))
    print(Logger.OKGREEN + "------------------------------------------------------" + Logger.ENDC)
    print('')

    if prediction:
        if wf.current_weight > target_weight:
            # 使用当前体重递归计算
            simulate(wf.current_weight, target_weight, food_menu, plans, sex, age, height, activity, bfr, week, prediction)
        else:
            print(Logger.HEADER + "------------------------------------------------------" + Logger.ENDC)
            print('预计需历时%s周, 达到目标体重%skg' % (week, '%.2f' % wf.current_weight))
            print(Logger.HEADER + "------------------------------------------------------" + Logger.ENDC)
            return


class Prepare:
    parser = None

    def __init__(self):
        parser = argparse.ArgumentParser(description='饮食管理')
        parser.add_argument("-s", "--sex", default="man",
                            help="性别",
                            choices=['man', 'woman'])
        parser.add_argument("-w", "--weight", help="当前体重", type=float)
        parser.add_argument("-a", "--age", help="年龄", type=int)
        parser.add_argument("-g", "--height", help="身高", type=int)
        parser.add_argument("--bfr", help="体脂率", type=float, default=0.0)
        parser.add_argument("--activity", help="活动强度",
                            type=float,
                            default=1.55,
                            choices=[1.2, 1.375, 1.55, 1.725, 1.9])

        parser.add_argument("--plans",
                            nargs='+',
                            help="碳水循环参数",
                            type=str,
                            default=["middle", "low", "middle", "middle", "low", "none", "high"],
                            choices=["middle", "low", "none", "high", "increase"]
                            )

        group = parser.add_argument_group('prediction weight')
        group.add_argument("-p", "--prediction", help="是否预测", action="store_true")

        group.add_argument("-t", "--target_weight", help="目标体重", type=float)

        self.parser = parser

    def run(self, argv):
        args = self.parser.parse_args(argv)
        if args.prediction:
            if not args.target_weight:
                print('指定参数-p 时, 必须指定目标体重 -t')
                return
        if len(args.plans) != 7:
            print('参数--plans 长度必须为7')
            return
        # 食物列表
        food_menu = collections.OrderedDict()
        food_menu['egg'] = 3
        food_menu['powder'] = 2
        food_menu['milk'] = 1
        food_menu['beef'] = 1
        food_menu['oil'] = 2
        food_menu['nuts'] = 1
        food_menu['chicken'] = -1
        # 最后再吃碳水类
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