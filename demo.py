#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySimpleGUI4 综合演示程序
验证所有功能是否正常工作
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import PySimpleGUI4 as sg
import threading
import time


def demo_basic_elements():
    """基本元素演示"""
    print("=" * 50)
    print("演示 1: 基本元素")
    print("=" * 50)

    layout = [
        [sg.Text("姓名:", size=(8, 1)), sg.Input(key="-NAME-", default_text="张三")],
        [
            sg.Text("年龄:", size=(8, 1)),
            sg.Spin(list(range(1, 100)), key="-AGE-", initial_value=25),
        ],
        [
            sg.Text("国家:", size=(8, 1)),
            sg.Combo(
                ["中国", "美国", "日本", "英国"], key="-COUNTRY-", default_value="中国"
            ),
        ],
        [
            sg.Text("爱好:", size=(8, 1)),
            sg.Listbox(["读书", "运动", "音乐", "游戏"], key="-HOBBY-", size=(10, 3)),
        ],
        [sg.Checkbox("订阅邮件", key="-SUBSCRIBE-", default=True)],
        [
            sg.Radio("男", group_id="gender", key="-MALE-"),
            sg.Radio("女", group_id="gender", key="-FEMALE-", default=True),
        ],
        [sg.Slider(range=(0, 100), key="-SLIDER-", default_value=50)],
        [sg.ProgressBar(100, key="-PROGRESS-", current_value=75)],
        [sg.Multiline(key="-MULTILINE-", default_text="多行文本输入", size=(30, 3))],
        [sg.Button("获取值"), sg.Button("更新"), sg.Button("关闭")],
    ]

    window = sg.Window("演示1: 基本元素", layout, finalize=True)

    def auto_close():
        time.sleep(5)
        if window.TKroot and window.TKroot.winfo_exists():
            window.close()

    threading.Thread(target=auto_close, daemon=True).start()

    while True:
        event, values = window.read(timeout=100)
        # if event in (None, "关闭"):
        #     break
        if event == "获取值":
            print("姓名: {}".format(values['-NAME-']))
            print("年龄: {}".format(values['-AGE-']))
            print("国家: {}".format(values['-COUNTRY-']))
            print("爱好: {}".format(values['-HOBBY-']))
            print("订阅: {}".format(values['-SUBSCRIBE-']))
            print("性别: {}".format('男' if values['-MALE-'] else '女'))
            print("滑块: {}".format(values['-SLIDER-']))
            print("进度: {}".format(values['-PROGRESS-']))
            print("多行: {}".format(values['-MULTILINE-']))
        elif event == "更新":
            window["-NAME-"].update("李四")
            window["-AGE-"].update(30)
            window["-COUNTRY-"].update("美国")
            window["-SUBSCRIBE-"].update(True)
            window["-MALE-"].update(True)
            window["-FEMALE-"].update(False)
            window["-SLIDER-"].update(80)
            window["-PROGRESS-"].update(90)
            print("已更新所有值")

    # window.close()
    print("演示1 完成\n")


def demo_container_elements():
    """容器元素演示"""
    print("=" * 50)
    print("演示 2: 容器元素 (Frame, Tab, Column)")
    print("=" * 50)

    frame_layout = [
        [sg.Text("Frame 内部输入:"), sg.Input(key="-FRAME-INPUT-")],
        [sg.Button("Frame按钮")],
    ]

    tab1_layout = [
        [sg.Text("标签页1内容")],
        [sg.Input(key="-TAB1-INPUT-")],
        [sg.Checkbox("Tab1 选项", key="-TAB1-CHECK-")],
    ]

    tab2_layout = [
        [sg.Text("标签页2内容")],
        [sg.Combo(["选项A", "选项B", "选项C"], key="-TAB2-COMBO-")],
    ]

    column_layout = [
        [sg.Text("Column 内"), sg.Input(key="-COLUMN-INPUT-")],
        [sg.Button("Column按钮")],
    ]

    layout = [
        [sg.Frame("我的分组框", frame_layout)],
        [
            sg.TabGroup(
                [[sg.Tab("标签1", tab1_layout), sg.Tab("标签2", tab2_layout)]],
                key="-TABGROUP-",
            )
        ],
        [sg.Column(column_layout)],
        [sg.Button("获取容器值"), sg.Button("关闭")],
    ]

    window = sg.Window("演示2: 容器元素", layout, finalize=True)

    def auto_close():
        time.sleep(8)
        if window.TKroot and window.TKroot.winfo_exists():
            window.close()

    threading.Thread(target=auto_close, daemon=True).start()

    while True:
        event, values = window.read(timeout=100)
        if event in (None, "关闭"):
            break
        elif event == "获取容器值":
            print("Frame输入: {}".format(values['-FRAME-INPUT-']))
            print("Tab1输入: {}".format(values['-TAB1-INPUT-']))
            print("Tab1选项: {}".format(values['-TAB1-CHECK-']))
            print("Tab2选项: {}".format(values['-TAB2-COMBO-']))
            print("Column输入: {}".format(values['-COLUMN-INPUT-']))

    window.close()
    print("演示2 完成\n")


def demo_table_tree():
    """Table 和 Tree 演示"""
    print("=" * 50)
    print("演示 3: Table 和 Tree 元素")
    print("=" * 50)

    table_values = [
        ["张三", 25, "北京"],
        ["李四", 30, "上海"],
        ["王五", 35, "广州"],
        ["赵六", 28, "深圳"],
    ]

    layout = [
        [sg.Text("数据表格:")],
        [
            sg.Table(
                values=table_values,
                headings=["姓名", "年龄", "城市"],
                key="-TABLE-",
                size=(40, 5),
            )
        ],
        [sg.Button("更新表格"), sg.Button("选择行"), sg.Button("清除选择")],
        [sg.Text("树形结构:")],
        [sg.Tree(headings=["名称", "类型"], key="-TREE-", auto_size_columns=True)],
        [sg.Button("添加节点"), sg.Button("删除节点"), sg.Button("展开/折叠")],
        [sg.Button("获取选择"), sg.Button("关闭")],
    ]

    window = sg.Window("演示3: Table 和 Tree", layout, finalize=True)

    tree = window["-TREE-"]
    tree.insert("", "root1", "根节点1", values=["根", "类型A"])
    tree.insert("root1", "child1", "子节点1-1", values=["子1", "类型B"])
    tree.insert("root1", "child2", "子节点1-2", values=["子2", "类型C"])
    tree.insert("", "root2", "根节点2", values=["根2", "类型D"])

    def auto_close():
        time.sleep(10)
        if window.TKroot and window.TKroot.winfo_exists():
            window.close()

    threading.Thread(target=auto_close, daemon=True).start()

    while True:
        event, values = window.read(timeout=100)
        if event in (None, "关闭"):
            break
        elif event == "更新表格":
            new_values = [
                ["新张三", 26, "新北京"],
                ["新李四", 31, "新上海"],
            ]
            window["-TABLE-"].update(values=new_values)
            print("表格已更新")
        elif event == "选择行":
            window["-TABLE-"].update(select_rows=[0, 2])
            print("已选择第1和第3行")
        elif event == "清除选择":
            window["-TABLE-"].update(select_rows=[])
            print("已清除选择")
        elif event == "添加节点":
            tree.insert("child1", "grandchild", "孙节点", values=["孙", "类型E"])
            print("已添加孙节点")
        elif event == "删除节点":
            tree.delete("child2")
            print("已删除 child2")
        elif event == "展开/折叠":
            if hasattr(tree, "expand"):
                tree.expand("root1")
            print("已展开 root1")
        elif event == "获取选择":
            table_selected = values["-TABLE-"]
            print("表格选择: {}".format(table_selected))

    window.close()
    print("演示3 完成\n")


def demo_graph():
    """Graph 元素演示"""
    print("=" * 50)
    print("演示 4: Graph 元素")
    print("=" * 50)

    layout = [
        [
            sg.Graph(
                canvas_size=(400, 300),
                graph_bottom_left=(0, 0),
                graph_top_right=(100, 100),
                key="-GRAPH-",
            )
        ],
        [
            sg.Button("画圆"),
            sg.Button("画线"),
            sg.Button("画点"),
            sg.Button("画矩形"),
            sg.Button("画文字"),
            sg.Button("清除"),
            sg.Button("关闭"),
        ],
    ]

    window = sg.Window("演示4: Graph 元素", layout, finalize=True)
    graph = window["-GRAPH-"]

    def auto_close():
        time.sleep(10)
        if window.TKroot and window.TKroot.winfo_exists():
            window.close()

    threading.Thread(target=auto_close, daemon=True).start()

    while True:
        event, values = window.read(timeout=100)
        if event in (None, "关闭"):
            break
        elif event == "画圆":
            graph.draw_circle((50, 50), 10, fill_color="red", line_color="blue")
            print("画了一个圆")
        elif event == "画线":
            graph.draw_line((0, 0), (100, 100), color="green", width=2)
            print("画了一条线")
        elif event == "画点":
            graph.draw_point((30, 70), size=10, color="yellow")
            print("画了一个点")
        elif event == "画矩形":
            graph.draw_rectangle(
                (20, 20), (40, 40), fill_color="purple", line_color="orange"
            )
            print("画了一个矩形")
        elif event == "画文字":
            graph.draw_text(
                "Hello PySimpleGUI4!", (50, 50), color="white", font=("Arial", 12)
            )
            print("写了文字")
        elif event == "清除":
            graph.erase()
            print("已清除")

    window.close()
    print("演示4 完成\n")


def demo_window_methods():
    """Window 方法演示"""
    print("=" * 50)
    print("演示 5: Window 方法")
    print("=" * 50)

    layout = [
        [sg.Text("测试窗口方法")],
        [sg.Input(key="-TEST-INPUT-", default_text="测试文本")],
        [
            sg.Button("设置焦点"),
            sg.Button("隐藏行"),
            sg.Button("显示行"),
            sg.Button("保存状态"),
            sg.Button("加载状态"),
            sg.Button("关闭"),
        ],
    ]

    window = sg.Window("演示5: Window 方法", layout, finalize=True)

    def auto_close():
        time.sleep(12)
        if window.TKroot and window.TKroot.winfo_exists():
            window.close()

    threading.Thread(target=auto_close, daemon=True).start()

    while True:
        event, values = window.read(timeout=100)
        if event in (None, "关闭"):
            break
        elif event == "设置焦点":
            input_elem = window["-TEST-INPUT-"]
            window.set_focus(input_elem)
            print("已设置输入框焦点")
        elif event == "隐藏行":
            input_elem = window["-TEST-INPUT-"]
            window.hide_row(input_elem)
            print("已隐藏输入框所在行")
        elif event == "显示行":
            input_elem = window["-TEST-INPUT-"]
            window.unhide_row(input_elem)
            print("已显示输入框所在行")
        elif event == "保存状态":
            window.SaveToDisk("test_window_state.pkl")
            print("已保存窗口状态到文件")
        elif event == "加载状态":
            window.LoadFromDisk("test_window_state.pkl")
            print("已从文件加载窗口状态")

    window.close()
    print("演示5 完成\n")


def demo_complete_application():
    """完整应用演示"""
    print("=" * 50)
    print("演示 6: 完整应用 (联系信息管理)")
    print("=" * 50)

    menu_def = [
        ["文件", ["打开", "保存", "退出"]],
        ["编辑", ["复制", "粘贴"]],
        ["帮助", ["关于"]],
    ]

    tab_contact = [
        [sg.Text("姓名:", size=(10, 1)), sg.Input(key="-NAME-")],
        [sg.Text("电话:", size=(10, 1)), sg.Input(key="-PHONE-")],
        [sg.Text("邮箱:", size=(10, 1)), sg.Input(key="-EMAIL-")],
        [sg.Text("地址:", size=(10, 1)), sg.Input(key="-ADDRESS-")],
    ]

    tab_notes = [
        [sg.Multiline(key="-NOTES-", size=(40, 8))],
    ]

    contacts_data = [
        ["张三", "13800138001", "zhangsan@email.com", "北京"],
        ["李四", "13800138002", "lisi@email.com", "上海"],
    ]

    layout = [
        [sg.Menu(menu_def)],
        [sg.TabGroup([[sg.Tab("联系信息", tab_contact), sg.Tab("备注", tab_notes)]])],
        [sg.Text("联系人列表:")],
        [
            sg.Table(
                contacts_data,
                headings=["姓名", "电话", "邮箱", "地址"],
                key="-CONTACTS-",
                size=(50, 5),
            )
        ],
        [
            sg.Button("添加"),
            sg.Button("编辑"),
            sg.Button("删除"),
            sg.Button("保存"),
            sg.Button("退出"),
        ],
    ]

    window = sg.Window("演示6: 联系信息管理", layout, finalize=True)

    def auto_close():
        time.sleep(15)
        if window.TKroot and window.TKroot.winfo_exists():
            window.close()

    threading.Thread(target=auto_close, daemon=True).start()

    while True:
        event, values = window.read(timeout=100)
        if event in (None, "退出", "关闭"):
            break
        elif event == "添加":
            print("添加新联系人")
        elif event == "编辑":
            print("编辑联系人")
        elif event == "删除":
            print("删除联系人")
        elif event == "保存":
            print("保存联系人列表")
            window["-CONTACTS-"].update(
                values=[
                    ["王五", "13900139001", "wangwu@email.com", "广州"],
                ]
            )
        elif event == "打开":
            print("打开文件")
        elif event == "保存" in str(event):
            print("保存文件")
        elif event == "退出":
            break
        elif event == "关于":
            print("关于 PySimpleGUI4 Demo")

    window.close()
    print("演示6 完成\n")


def main():
    """主函数 - 运行所有演示"""
    print("\n" + "=" * 60)
    print("  PySimpleGUI4 综合演示程序")
    print("  测试所有功能是否正常工作")
    print("=" * 60 + "\n")

    print("每个演示窗口会在几秒后自动关闭...")
    print("你可以观察窗口是否正常显示和响应操作。\n")

    demos = [
        ("基本元素", demo_basic_elements),
        ("容器元素", demo_container_elements),
        ("Table和Tree", demo_table_tree),
        ("Graph元素", demo_graph),
        ("Window方法", demo_window_methods),
        ("完整应用", demo_complete_application),
    ]

    # for name, demo_func in demos:
    #     try:
    #         demo_func()
    #     except Exception as e:
    #         print("演示 '{}' 出错: {}".format(name, e))
    #         import traceback

    #         traceback.print_exc()
    demo_basic_elements()

    print("=" * 60)
    print("  所有演示完成！")
    print("=" * 60)
    print("\n如果所有窗口都正常显示并自动关闭，")
    print("说明 PySimpleGUI4 核心功能工作正常。")
    print()


if __name__ == "__main__":
    main()
