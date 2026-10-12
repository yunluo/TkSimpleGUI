#! /usr/bin/python3
# -*- coding: utf-8 -*-
import TkSimpleGUI as sg

sg.theme("DefaultNoMoreNagging")

app = sg.TkSimpleEvent()


def make_main_window() -> sg.Window:
    task_list = [
        sg.Frame(
            "Tasks",
            [
                [
                    sg.Input(
                        key="lot1", tooltip="此输入栏输入即事件触发", enable_events=True
                    )
                ],
                [sg.Input(key="lot2", tooltip="此输入框输入后使用回车事件触发")],
                [sg.B("win_fun"), sg.B("val_fun")],
                [
                    sg.B("win_val_fun"),
                    sg.B("no_arg_fun"),
                ],
                [sg.Text("", key="lot3")],
                [sg.Text("", key="lot4")],
            ],
            size=(400, 200),
        )
    ]

    status_bar = [
        sg.StatusBar("版本:"),
        sg.StatusBar("状态:"),
    ]

    menu_def = [
        ["&程序", ["关于", "保存配置", "Exit"]],
        ["&帮助", "&使用说明..."],
    ]

    top_menu = [sg.Menu(menu_def)]

    layout = [top_menu, task_list, status_bar]

    # 3.建窗口
    return sg.Window(
        "测试程式窗口",
        layout,
        keep_on_top=True,
        return_keyboard_events=True,
    )


def on_about():
    sg.popup("软件说明：", "关于事件，点击菜单关于启动", title="关于程序")


@app.bind_event("保存配置")
def on_save_options():
    sg.popup("you click save options")


@app.bind_event("lot1")
def on_input_lot1(window: sg.Window, values: dict):
    window["lot4"].update(values.get("lot1"))


@app.bind_event("lot2")
def on_enter_lot2(window: sg.Window, values: dict):
    new_text = "您输入的是：{}".format(values.get("lot2"))
    window["lot3"].update(new_text)


@app.bind_event(["no_arg_fun", "关于"])
def on_no_arg_fun(event: str):
    sg.popup(
        "软件说明：",
        "新建任务",
        event,
        title="关于程序",
    )


@app.bind_event("win_fun")
def on_win_fun(window: sg.Window):
    sg.popup(
        "软件说明：",
        "新建任务",
        title="关于程序",
    )
    window["lot2"].set_focus(force=True)
    sg._logger.info("sdfgsdf")


@app.bind_event("val_fun")
def on_val_fun(values):
    lot1 = values.get("lot1")
    lot2 = values.get("lot2")
    sg.popup(
        "软件说明：",
        "新建任务",
        lot1,
        lot2,
        title="关于程序",
    )


@app.bind_event(["win_val_fun", "lot2"])
def on_win_val_fun(window, values):
    sg.popup(
        "软件说明：",
        "新建任务",
        title="关于程序",
    )
    lot1 = values.get("lot1")
    window["lot3"].update(lot1)


def main():
    main_window = make_main_window()

    # 增加了一个Exit退出事件
    app.run_event(main_window, "Exit")


if __name__ == "__main__":
    main()
